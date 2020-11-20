#     Rxivist, a system for crawling papers published on bioRxiv
#     and organizing them in ways that make it easier to find new
#     or interesting research. Includes a web application for
#     the display of data.
#     Copyright (C) 2019 Regents of the University of Minnesota

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, version 3.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

#     Any inquiries about this software or its use can be directed to
#     Professor Ran Blekhman at the University of Minnesota:
#     email: blekhman@umn.edu
#     mail: MCB 6-126, 420 Washington Avenue SE, Minneapolis, MN 55455
#     http://blekhmanlab.org/

from collections import defaultdict
from datetime import datetime, timedelta
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.parse

import psycopg2
from requests_html import HTMLSession
import requests

import config
import db
from log import Logger
import models


def determine_page_count(html):
  # takes a biorxiv results page and
  # finds the highest page number listed
  last = html.find(".pager-last")
  if len(last) > 0:
    return int(last[0].text)
  # if there isn't a break in the list of page numbers (i.e. when there are
  # only a couple pages of results), pager-last won't be there, so just grab
  # the highest page number:
  pages = html.find(".pager-item")
  if len(pages) > 0:
    return int(pages[-1].text)
  return 0

def pull_out_articles(html, log):
  entries = html.find(".highwire-article-citation")
  articles = []
  for entry in entries:
    a = models.Article()
    a.process_results_entry(entry, log)
    articles.append(a)
  return articles

def record_ranks_file(to_record, filename):
  with open(f"{filename}.csv", 'w') as f:
    for entry in to_record:
      to_write = ""
      for i, field in enumerate(entry):
        to_write += str(field)
        if i < len(entry) - 1:
          to_write += ","
      to_write += "\n"
      f.write(to_write)

class Spider(object):
  def __init__(self):
    self.connection = db.Connection(config.db["host"], config.db["db"], config.db["user"], config.db["password"])
    self.session = HTMLSession(mock_browser=False)
    self.session.headers['User-Agent'] = config.user_agent
    self.log = Logger()

  def get_urls(self):
    # fills in URLs for papers that are for some reason missing them. Determines URLs
    # by resolving the DOI.
    self.log.record('Fetching URLs for papers without them', 'info')
    to_save = []
    with self.connection.db.cursor() as cursor:
      cursor.execute(f"SELECT id, doi FROM {config.db['schema']}.articles WHERE url IS NULL OR url='';")
      for x in cursor:
        try:
          r = requests.get(f"https://doi.org/{x[1]}", timeout=10)
        except Exception as e:
          self.log.record(f'Problem resolving DOI: {e}', 'error')
          continue
        if r.status_code != 200:
          self.log.record(f"Got weird status code resolving DOI {x[1]}: {r.status_code}", "error")
          continue
        to_save.append((r.url, x[0]))
        self.log.record(f'Found URL for {x[0]}: {r.url}', 'debug')
    with self.connection.db.cursor() as cursor:
      self.log.record(f'Saving {len(to_save)} URLS.', 'info')
      cursor.executemany(f"UPDATE {config.db['schema']}.articles SET url=%s WHERE id=%s;", to_save)

  def get_posted_dates(self):
    # fills in URLs for papers that are for some reason missing them. Determines URLs
    # by resolving the DOI.
    self.log.record('Fetching dates for papers without them', 'info')
    to_save = []
    with self.connection.db.cursor() as cursor:
      cursor.execute(f"SELECT id, doi FROM {config.db['schema']}.articles WHERE posted IS NULL;")
      for x in cursor:
        if x[1] is not None:
          self.log.record(f'Fetching date for {x[0]}.')
          self.record_article_posted_date(x[0], x[1])

  def _pull_crossref_data_date(self, datestring, retry=True):
    # Datestring should be format YYYY-MM-DD
    self.log.record(f"Beginning retrieval of Crossref data for {datestring}", "info")
    headers = {'user-agent': config.user_agent}
    try:
      r = requests.get("{0}?obj-id.prefix=10.1101&from-occurred-date={1}&until-occurred-date={1}&source=twitter&mailto={2}&rows=10000".format(config.crossref["endpoints"]["events"], datestring, config.crossref["parameters"]["email"]), headers=headers, timeout=30)
    except Exception as e:
      self.log.record(f'Problem sending request to Crossref: {e}.', 'error')
      if retry: # only retry once
        self.log.record("Retrying request: {0}?obj-id.prefix=10.1101&from-occurred-date={1}&until-occurred-date={1}&source=twitter&mailto={2}&rows=10000".format(config.crossref["endpoints"]["events"], datestring, config.crossref["parameters"]["email"]), 'info')
        time.sleep(6)
        return self._pull_crossref_data_date(datestring, retry=False)
      else:
        self.log.record('No more retries. Exiting.', 'fatal')
        return

    if r.status_code != 200:
      self.log.record(f"Got weird status code: {r.status_code}", "error")
      if retry:
        self.log.record("Retrying request: {0}?obj-id.prefix=10.1101&from-occurred-date={1}&until-occurred-date={1}&source=twitter&mailto={2}&rows=10000".format(config.crossref["endpoints"]["events"], datestring, config.crossref["parameters"]["email"]), 'info')
        time.sleep(6)
        return self._pull_crossref_data_date(datestring, retry=False)
      return
    results = r.json()

    if results["status"] != "ok":
      self.log.record(f'Crossref responded, but with unexpected status: {results["status"]}', "error")
      if retry:
        self.log.record("Retrying request: {0}?obj-id.prefix=10.1101&from-occurred-date={1}&until-occurred-date={1}&source=twitter&mailto={2}&rows=10000".format(config.crossref["endpoints"]["events"], datestring, config.crossref["parameters"]["email"]), 'info')
        time.sleep(6)
        return self._pull_crossref_data_date(datestring, retry=False)
      return
    if "message" not in results.keys() or "events" not in results["message"].keys() or len(results["message"]["events"]) == 0:
      self.log.record("Events not found in response.", "error")
      # this retry has never worked
      # if retry:
      #   self.log.record("Retrying request: {0}?obj-id.prefix=10.1101&from-occurred-date={1}&until-occurred-date={1}&source=twitter&mailto={2}&rows=10000".format(config.crossref["endpoints"]["events"], datestring, config.crossref["parameters"]["email"]), 'info')
      #   time.sleep(6)
      #   return self._pull_crossref_data_date(datestring, retry=False)
      return

    tweets = defaultdict(list)
    if results["message"]["total-results"] > 10000:
      # Odds are we're never going to get more than one page here, so
      # let's put off the implemention of pagination until that day
      # is upon us
      self.log.record(f'TOO MANY RESULTS: {results["message"]["total-results"]}', "fatal")
    for event in results["message"]["events"]:
      if event.get("source_id") != "twitter": # double-check that it's filtering right
        self.log.record(f'Unrecognized source_id field: {event.get("source_id", "(not provided)")}. Skipping.', "info")
        continue
      try:
        doi_search = re.search('https://doi.org/(.*)', event["obj_id"])
      except:
        self.log.record("Could not determine DOI number for object. Skipping.", "warn")
        continue
      if len(doi_search.groups()) == 0:
        self.log.record("No DOI number found. Skipping.", "warn")
        continue
      doi = doi_search.group(1)
      if "subj" in event and "original-tweet-url" in event['subj']:
        tweets[doi].append(event["subj"]["original-tweet-url"])

    # (If we have multiple results for the same 24-hour period, the
    # query that displays the most popular displays the same articles
    # multiple times, and the aggregation function to clean that up
    # would be too complicated to bother with right now.)
    if len(tweets) > 0:
      with self.connection.db.cursor() as cursor:
        self.log.record("Removing earlier data from same day")
        cursor.execute("DELETE FROM crossref_daily WHERE source_date=%s;", (datestring,))

    sql = f"INSERT INTO {config.db['schema']}.crossref_daily (source_date, doi, count) VALUES (%s, %s, %s);"
    params = [(datestring, doi, len(tweets[doi])) for doi in tweets]
    self.log.record(f"Saving tweet data for {len(tweets.keys())} DOI entries.")
    with self.connection.db.cursor() as cursor:
      cursor.executemany(sql, params)
    self.log.record("Done with crossref.", "debug")

  def find_record_new_articles(self, cursorid=0, current=None):
    if config.polite:
      time.sleep(3)

    if current is None:
      # we pass the date in as a parameter in case the computer's date
      # changes in the middle of us scanning through pages
      current = datetime.now()
    start = (current - timedelta(days=1)).strftime('%Y-%m-%d')
    end = current.strftime('%Y-%m-%d')
    self.log.record(f"Fetching new preprints data from within 1 day of {start} (cursor: {cursorid})", 'debug')
    url = f'{config.biorxiv["endpoints"]["api"]}/details/biorxiv/{start}/{end}/{cursorid}'
    try:
      r = requests.get(url)
    except Exception as e:
      self.log.record(f"Error requesting results from new preprints endpoint. Retrying: {e}", "error")
      try:
        r = requests.get(url)
      except Exception as e:
        self.log.record(f"Error AGAIN requesting new preprints. Bailing: {e}", "error")
        return

    resp = r.json()
    if 'messages' not in resp.keys() or len(resp['messages']) == 0:
      spider.log.record(f"Couldn't validate response from preprints endpoint.", 'error')
      return

    meta = resp['messages'][0]

    if meta.get('status') != 'ok':
      spider.log.record(f"Preprints endpoint responded with non-ok status", 'error')
      return

    if 'collection' not in resp.keys() or len(resp['collection']) == 0:
      spider.log.record(f"No results in response from preprints endpoint.", 'error')
      return

    # turn results into a list
    spider.log.record(f"Retrieved {len(resp['collection'])} entries on page.")

    for entry in resp['collection']:
      if config.polite:
        time.sleep(1)
      article = models.Article(entry)
      spider.log.record(f'Evaluating article {article.doi}','debug')
      recorded = article.record(self.connection, self)

    # request next page
    if meta['count'] + int(meta['cursor']) < meta['total']:
      spider.log.record('Retrieving next page of results.')
      self.find_record_new_articles(cursorid+meta['count'], current)

  def fetch_published(self, cursorid=0, current=None):
    if config.polite:
      time.sleep(3)

    if current is None:
      # we pass the date in as a parameter in case the computer's date
      # changes in the middle of us scanning through pages
      current = datetime.now()
    start = (current - timedelta(days=3)).strftime('%Y-%m-%d')
    end = current.strftime('%Y-%m-%d')
    self.log.record(f"Fetching publication data from within 3 days of {start} (cursor: {cursorid})", 'debug')
    try:
      r = requests.get(f'{config.biorxiv["endpoints"]["api"]}/pub/{start}/{end}/{cursorid}')
    except Exception as e:
      self.log.record(f"Error requesting first page of results from publications endpoint. Retrying: {e}", "error")
      try:
        r = requests.get(f'{config.biorxiv["endpoints"]["api"]}/pub/{start}/{end}')
      except Exception as e:
        self.log.record(f"Error AGAIN requesting publications. Bailing: {e}", "error")
        return

    resp = r.json()
    if 'messages' not in resp.keys() or len(resp['messages']) == 0:
      spider.log.record(f"Couldn't validate response from pub endpoint.", 'error')
      return

    meta = resp['messages'][0]

    if meta.get('status') != 'ok':
      spider.log.record(f"Pub endpoint responded with non-ok status", 'error')
      return

    if 'collection' not in resp.keys() or len(resp['collection']) == 0:
      spider.log.record(f"No results in response from pub endpoint.", 'error')
      return

    # turn results into a list
    towrite = [(x['biorxiv_doi'], x['published_doi']) for x in resp['collection']]

    for entry in towrite:
      with self.connection.db.cursor() as cursor:
        # first search in the table of publications to make sure we don't
        # know about this one already:
        cursor.execute(f"SELECT id FROM {config.db['schema']}.articles WHERE doi=%s",(entry[0],))
        x = cursor.fetchone()
        article_id = None
        if x is not None and len(x) > 0:
          article_id = x[0]
        if article_id is None:
          # if we don't have an article with that DOI, move on
          continue

        # if the article exists, check whether we already know it's published
        cursor.execute(f"SELECT COUNT(article) FROM {config.db['schema']}.article_publications WHERE article=%s",(article_id,))
        for x in cursor:
          if len(x) > 0:
            count = x[0]
        # if we don't have it already, record it:
        if count == 0:
          self.log.record(f'recording {entry[0]} - article {article_id}!','debug')
          cursor.execute(f"INSERT INTO {config.db['schema']}.article_publications (article, doi) VALUES (%s, %s);", (article_id, entry[1]))

    # if there are more pages to go, make another call
    # (the 'cursor' field becomes a string if it's greater than 0?)
    if meta['count'] + int(meta['cursor']) < meta['total']:
      self.fetch_published(cursorid+meta['count'], current)

  def refresh_article_stats(self, collection=None, cap=10000, id=None, get_authors=False):
    """Normally, "collection" is specified, and the function will
    iterate through outdated articles in the given collection. However,
    specifying "id" instead will update the entry for a single article.
    """
    self.log.record(f"Refreshing article download stats for collection {collection}...")
    with self.connection.db.cursor() as cursor:
      if id is None:
        if get_authors: # if we're just trying to update papers without authors
          self.log.record(f'Refreshing stats for papers without authors.', 'debug')
          sql = f"""
            SELECT id, url, doi
              FROM (
                SELECT
                  a.id, a.url, a.doi, COUNT(w.author) AS authors
                FROM {config.db["schema"]}.articles a
                LEFT JOIN {config.db["schema"]}.article_authors w ON w.article=a.id
                GROUP BY a.id
                ORDER BY authors
              ) AS authorcount
              WHERE authors=0;
          """
          cursor.execute(sql)
        elif collection is None:
          cursor.execute("SELECT id, url, doi FROM articles WHERE collection IS NULL AND last_crawled < now() - interval %s;", (config.refresh_interval,))
        else:
          cursor.execute(f"SELECT id, url, doi FROM {config.db['schema']}.articles WHERE collection=%s AND last_crawled < now() - interval %s ORDER BY last_crawled ASC;", (collection, config.refresh_interval))
      else:
        cursor.execute("SELECT id, url, doi FROM articles WHERE id=%s;", (id,))
      updated = 0
      consec_errors = 0
      for article in cursor:
        if consec_errors > 10:
          self.log.record('Too many errors in a row. Exiting.', 'fatal')
        article_id = article[0]
        url = article[1]
        doi = article[2]
        self.log.record(f"\nRefreshing article {article_id}", "debug")
        if url is None:
          self.log.record(f'No URL for article {article_id}. Skipping.', 'warn')
          continue
        if config.polite:
          time.sleep(1)
        stat_table, authors = self.get_article_stats(url)
        if stat_table is None:
          self.log.record('No results returned. Moving on to next article.', 'warn')
          consec_errors += 1
          continue
        else:
          consec_errors = 0

        self.save_article_stats(article_id, stat_table)

        overwrite = False
        if config.record_authors_on_refresh is True or id is not None:
          # Always refresh authors if a specific article ID is given
          overwrite = True
        self._record_authors(article_id, authors, overwrite)
        updated += 1
        if config.limit_refresh is not False and updated >= cap:
          self.log.record("Maximum articles reached for this session. Returning.")
          break
    self.log.record(f"{updated} articles refreshed in {collection}.")
    return updated

  def get_article_abstract(self, url, retry=True):
    if url is None:
      self.log.record('No URL supplied. Skipping.', 'warn')
      return
    if config.polite:
      time.sleep(1)
    try:
      resp = self.session.get(url)
    except Exception as e:
      self.log.record(f"Error fetching abstract: {e}", "warn")
      if retry:
        self.log.record("Retrying:")
        time.sleep(10)
        return self.get_article_abstract(url, False)
      else:
        self.log.record("Giving up on this one for now.", "error")
        raise ValueError("Encountered exception making HTTP call to fetch paper information.")
    abstract = resp.html.find('meta[name="DC.Description"]', first=True)
    if abstract is not None and abstract.attrs['content'] != '':
      abstract = abstract.attrs['content']
    else:
      self.log.record('Primary source of abstract missing. Trying secondary option.','debug')
      abstract = resp.html.find("#p-2")
      if len(abstract) < 1 or abstract[0].text == '':
        raise ValueError("Successfully made HTTP call to fetch paper information, but did not find an abstract.")
      abstract = abstract[0].text
    return abstract

  def get_article_stats(self, url, retry_count=0):
    try:
      resp = self.session.get(f"{url}.article-metrics")
    except Exception as e:
      if retry_count < 3:
        self.log.record(f"Error requesting article metrics. Retrying: {e}", "error")
        return self.get_article_stats(url, retry_count+1)
      else:
        self.log.record(f"Error AGAIN requesting article metrics. Bailing: {e}", "error")
        return (None, None)
    if resp.status_code != 200:
      spider.log.record(f"  Got weird status code: {resp.status_code}", 'warn')
      if retry_count < 2:
        time.sleep(5)
        return self.get_article_stats(url, retry_count+1)
      else:
        # 403s here appear to be mostly caused by papers being "processed"
        return (None, None)
        #self.log.record('Something unusual going on. Not retrying.', 'fatal')
    authors = find_authors(resp)

    # The download metrics table is shaped differently if there's
    # a column for "Full-text downloads" (which appears in the HTML as only
    # "Full"), so we check here to see whether it's there:
    headers = iter(resp.html.find("th"))
    full_available = False
    for header in headers:
      if header.text == 'Full':
        full_available = True
    # Then iterate through the table:
    entries = iter(resp.html.find("td"))
    stats = []
    for entry in entries:
      date = entry.text.split(" ")
      month = month_to_num(date[0])
      year = int(date[1])
      abstract = int(next(entries).text)
      if full_available:
        full = int(next(entries).text) # TODO: this doesn't get recorded now
      pdf = int(next(entries).text)
      stats.append((month, year, abstract, pdf))
    return stats, authors

  def record_article_posted_date(self, article_id, doi, retry_count=0):
    self.log.record(f'Filling in date for article {article_id}.','debug')

    url = f'{config.biorxiv["endpoints"]["api"]}/details/biorxiv/{doi}'
    try:
      r = requests.get(url)
    except Exception as e:
      self.log.record(f"Error requesting preprint details. Retrying: {e}", "error")
      try:
        r = requests.get(url)
      except Exception as e:
        self.log.record(f"Error AGAIN requesting preprint details. Bailing: {e}", "error")
        return
    resp = r.json()
    if 'messages' not in resp.keys() or len(resp['messages']) == 0:
      spider.log.record(f"Couldn't validate response from details endpoint.", 'error')
      return

    meta = resp['messages'][0]

    if meta.get('status') != 'ok':
      spider.log.record(f"Details endpoint responded with non-ok status", 'error')
      return

    if 'collection' not in resp.keys() or len(resp['collection']) == 0:
      spider.log.record(f"No results in response from details endpoint.", 'error')
      return
    for entry in resp['collection']:
      if entry.get('version') == '1':
        date = entry.get('date')
        break
    if date is not None:
      with self.connection.db.cursor() as cursor:
        spider.log.record(f'Setting posted date {date} for article {article_id}')
        cursor.execute("UPDATE articles SET posted=%s WHERE id=%s;", (date, article_id))

  def save_article_stats(self, article_id, stats):
    # First, delete the most recently fetched month, because it was probably recorded before
    # that month was complete:
    with self.connection.db.cursor() as cursor:
      cursor.execute("SELECT MAX(year) FROM article_traffic WHERE article=%s;", (article_id,))
      max_year = cursor.fetchone()
    if max_year is not None and len(max_year) > 0:
      max_year = max_year[0]
      with self.connection.db.cursor() as cursor:
        cursor.execute("SELECT MAX(month) FROM article_traffic WHERE year = %s AND article=%s;", (max_year, article_id))
        month = cursor.fetchone()
        if month is not None and len(month) > 0:
          cursor.execute("DELETE FROM article_traffic WHERE year = %s AND month = %s AND article=%s", (max_year, month[0], article_id))

    with self.connection.db.cursor() as cursor:
      # we check for which ones are already recorded because
      # the postgres UPSERT feature is bananas
      cursor.execute("SELECT month, year FROM article_traffic WHERE article=%s", (article_id,))
      # associate each year with which months are already recorded
      done = defaultdict(list)
      for record in cursor:
        done[record[1]].append(record[0])
      # make a list that excludes the records we already know about
      to_record = []
      for i, record in enumerate(stats):
        month = record[0]
        year = record[1]
        if year not in done.keys() or month not in done[year]:
          to_record.append(record)
      # save the remaining ones in the DB
      sql = f"INSERT INTO {config.db['schema']}.article_traffic (article, month, year, abstract, pdf) VALUES (%s, %s, %s, %s, %s);"
      params = [(article_id, x[0], x[1], x[2], x[3]) for x in to_record]
      cursor.executemany(sql, params)

      cursor.execute(f"UPDATE {config.db['schema']}.articles SET last_crawled = CURRENT_DATE WHERE id=%s", (article_id,))

      self.log.record(f"Recorded {len(to_record)} stats for ID {article_id}", "debug")

  def _record_authors(self, article_id, authors, overwrite=False):
    with self.connection.db.cursor() as cursor:
      cursor.execute(f'SELECT COUNT(article) FROM {config.db["schema"]}.article_authors WHERE article=%s;', (article_id,))
      count = cursor.fetchone()[0]
      if count > 0 and not overwrite: # If the paper already has authors, we're done
        return

    to_write = []
    for a in authors:
      a.record(self.connection, self.log)
      to_write.append((article_id, a.id, a.institution))

    if overwrite:
      if len(to_write) > 0:
        # "overwrite" means re-link all the authors to the paper, but only do it
        # if there are NEW authors to actually link. Otherwise don't mess with it,
        # len(to_write) is only 0 if bioRxiv is listing zero authors for a paper
        # and that's not right.
        with self.connection.db.cursor() as cursor:
          self.log.record("Deleting previously recorded author links.", "debug")
          cursor.execute(f'DELETE FROM {config.db["schema"]}.article_authors WHERE article=%s;',(article_id,))
      else:
        self.log.record("Not removing previous author links because there aren't any new authors to replace them with.", "warn")
    if len(to_write) > 0:
      try:
        with self.connection.db.cursor() as cursor:
          self.log.record("Saving NEW author links.", "debug")
          sql = f'INSERT INTO {config.db["schema"]}.article_authors (article, author, institution) VALUES (%s, %s, %s);'
          cursor.executemany(sql, to_write)
      except Exception as e:
        # If there's an error associating all the authors with their paper all at once,
        # send separate queries for each one
        # (This came up last time because an author was listed twice on the same paper.)
        self.log.record(f"Error associating authors to paper: {e}", "warn")
        self.log.record("Recording article associations one at a time.", "info")
        for x in to_write:
          try:
            with self.connection.db.cursor() as cursor:
              cursor.execute(f'INSERT INTO {config.db["schema"]}.article_authors (article, author, institution) VALUES (%s, %s, %s);', x)
          except Exception as e:
            self.log.record(f"Another problem associating author {x} to article {article_id}. Moving on.", "error")
            pass

  def fetch_category_list(self):
    categories = []
    with self.connection.db.cursor() as cursor:
      cursor.execute("SELECT DISTINCT collection FROM articles ORDER BY collection;")
      for cat in cursor:
        if len(cat) > 0:
          categories.append(cat[0])
    return categories

  def process_rankings(self):
    # pulls together all the separate ranking calls
    start = datetime.now()
    self.log.record(f"{start} - Starting full ranking process.")
    # "not False" is used here because we want these to process if the flag
    # is set to True OR not set at all ("None is not False" evaluates True)

    if config.perform_ranks["alltime"] is not False:
      self._rank_articles_alltime()
      load_rankings_from_file("alltime_ranks", self.log)
      self.activate_tables("alltime_ranks")
    if config.perform_ranks["ytd"] is not False:
      self._rank_articles_ytd()
      load_rankings_from_file("ytd_ranks", self.log)
      self.activate_tables("ytd_ranks")
    if config.perform_ranks["month"] is not False:
      self._rank_articles_month()
      load_rankings_from_file("month_ranks", self.log)
      self.activate_tables("month_ranks")
    if config.perform_ranks["authors"] is not False:
      self._rank_authors_alltime()
      load_rankings_from_file("author_ranks", self.log)
      self.activate_tables("author_ranks")

    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE author_ranks_category_working")
      cursor.execute("TRUNCATE author_ranks_category_working")
      cursor.execute("TRUNCATE category_ranks_working")
    self.log.record('Starting categorical ranking process.', 'info')
    for category in self.fetch_category_list():
      if config.perform_ranks["article_categories"] is not False:
        self._rank_articles_categories(category)
        load_rankings_from_file("category_ranks", self.log)
      if config.perform_ranks["author_categories"] is not False:
        self._rank_authors_category(category)
        load_rankings_from_file("author_ranks_category", self.log)
    # we wait until all the categories have been loaded before
    # swapping in the fresh batch
    if config.perform_ranks["article_categories"] is not False:
      self.activate_tables("category_ranks")
    if config.perform_ranks["author_categories"] is not False:
      self.activate_tables("author_ranks_category")

    self._calculate_download_distributions()
    end = datetime.now()
    self.log.record(f"{end} - Full ranking process complete after {end-start}.")

  def activate_tables(self, table):
    self.log.record(f"Activating tables for {table}", 'debug')
    queries = [
      f"ALTER TABLE {table} RENAME TO {table}_temp",
      f"ALTER TABLE {table}_working RENAME TO {table}",
      f"ALTER TABLE {table}_temp RENAME TO {table}_working"
    ]
    to_delete = f"{table}_working.csv"
    with self.connection.db.cursor() as cursor:
      for query in queries:
        cursor.execute(query)
    if config.delete_csv == True:
      self.log.record(f"Deleting {to_delete}", 'debug')
      try:
        os.remove(to_delete)
      except Exception as e:
        if to_delete not in [ # HACK These aren't there on the last loop
          'category_ranks_working.csv',
          'author_ranks_category_working.csv'
        ]:
          self.log.record(f"Problem deleting {to_delete}: {e}", "warn")

  def _calculate_download_distributions(self):
    self.log.record("Calculating distribution of download counts with logarithmic scales.")
    tasks = [
      {
        "name": "alltime", # NOTE: this means alltime for PAPERS
        "scale_power": config.distribution_log_articles
      },
      {
        "name": "author",
        "scale_power": config.distribution_log_authors
      },
    ]
    for task in tasks:
      results = defaultdict(int)
      self.log.record(f'Calculating download distributions for {task["name"]}', 'debug')
      with self.connection.db.cursor() as cursor:
        # first, figure out the biggest bucket:
        cursor.execute(f'SELECT MAX(downloads) FROM {task["name"]}_ranks;')
        biggest = cursor.fetchone()[0]
        # then set up all the empty buckets (so they aren't missing when we draw the graph)
        buckets = [0, round(task["scale_power"])]
        current = round(task["scale_power"])
        while True:
          next_bucket = round(current * task["scale_power"])
          if next_bucket == current: # making sure we don't get stuck at 1.0
            current += 1
          else:
            current = next_bucket
          buckets.append(current)
          if None in [current, biggest] or current > biggest:
            break
        self.log.record(f"Buckets determined! {len(buckets)} buckets between 0 and {buckets[-1]}", 'debug')
        for bucket in buckets:
          results[bucket] = 0
        # now fill in the buckets:
        cursor.execute(f'SELECT downloads FROM {task["name"]}_ranks ORDER BY downloads ASC;')
        values = []
        for entity in cursor:
          if len(entity) > 0:
            values.append(entity[0])
            # determine what bucket it's in:
            target = 0
            for bucket_num, bucket in enumerate(buckets):
              if entity[0] < bucket:
                results[buckets[bucket_num-1]] += 1
                break
        cursor.execute("DELETE FROM download_distribution WHERE category=%s", (task["name"],))
        sql = f"INSERT INTO {config.db['schema']}.download_distribution (bucket, count, category) VALUES (%s, %s, %s);"
        params = [(bucket, count, task["name"]) for bucket, count in results.items()]
        self.log.record("Recording distributions...")
        cursor.executemany(sql, params)

        self.log.record(f'Calculating median for {task["name"]}', 'debug')
        if len(values) % 2 == 1:
          median = values[int((len(values) - 1) / 2)]
        else:
          median = (values[int((len(values)/ 2) - 1)] + values[int(len(values)/ 2)]) / 2
        self.log.record(f"Median is {median}", "debug")
        # HACK: This data doesn't fit in this table. Maybe move to site stats table?
        cursor.execute(f"DELETE FROM download_distribution WHERE category='{task['name']}_median'")
        sql = f"INSERT INTO {config.db['schema']}.download_distribution (category, bucket, count) VALUES ('{task['name']}_median', 0, %s);"
        cursor.execute(sql, (median,))

        self.log.record(f'Calculating mean for {task["name"]}', 'debug')
        total = 0
        for x in values:
          total += x
        mean = total / len(values)
        self.log.record(f"Mean is {mean}", "debug")
        cursor.execute(f"DELETE FROM download_distribution WHERE category='{task['name']}_mean'")
        sql = f"INSERT INTO {config.db['schema']}.download_distribution (category, bucket, count) VALUES ('{task['name']}_mean', 0, %s);"
        cursor.execute(sql, (mean,))

  def _rank_articles_alltime(self):
    self.log.record("Ranking papers by popularity...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE alltime_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic GROUP BY article ORDER BY downloads DESC")
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]
    self.log.record("Retrieved download data.", "debug")
    record_ranks_file(params, "alltime_ranks_working")

  def _rank_articles_categories(self, category):
    self.log.record(f"Ranking papers by popularity in category {category}...", 'debug')
    with self.connection.db.cursor() as cursor:
      query = """
        SELECT t.article, SUM(t.pdf) as downloads
        FROM article_traffic AS t
        INNER JOIN articles AS a ON t.article=a.id
        WHERE a.collection=%s
        GROUP BY t.article
        ORDER BY downloads DESC
      """
      cursor.execute(query, (category,))
      params = [(record[0], rank) for rank, record in enumerate(cursor, start=1)]
    record_ranks_file(params, "category_ranks_working")

  def _rank_articles_ytd(self):
    self.log.record("Ranking papers by popularity, year to date...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("SELECT MAX(year) FROM article_traffic;")
      max_year = cursor.fetchone()
      if max_year is None or len(max_year) == 0:
        self.log.record("Could not determine current year for ranking YTD; exiting", "fatal")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE ytd_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic WHERE year = %s GROUP BY article ORDER BY downloads DESC", (max_year,))
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]

    record_ranks_file(params, "ytd_ranks_working")

  def _rank_articles_month(self):
    with self.connection.db.cursor() as cursor:
      cursor.execute("SELECT MAX(year) FROM article_traffic")
      year = cursor.fetchone()
      if year is None or len(year) == 0:
        self.log.record("Couldn't determine year for monthly rankings; bailing on this ranking", "error")
        return
      year = year[0]
    self.log.record("Ranking papers by popularity, since last month...")
    with self.connection.db.cursor() as cursor:
      # Determine most recent month
      cursor.execute("SELECT MAX(month) FROM article_traffic WHERE year = %s;", (year,))
      month = cursor.fetchone()
      if month is None or len(month) < 1:
        self.log.record("Could not determine current month.", "error")
        return
      month = month[0] - 1 # "since LAST month" prevents nonsense results early in the current month
      if month == 0: # if it's January, roll back one year
        month =  12
        year = year - 1
    with self.connection.db.cursor() as cursor:
      self.log.record(f"Ranking articles based on traffic since {month}/{year}")
      cursor.execute("TRUNCATE month_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic WHERE year = %s AND month >= %s GROUP BY article ORDER BY downloads DESC", (year, month))
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]

    record_ranks_file(params, "month_ranks_working")

  def _rank_authors_alltime(self):
    # NOTE: The main query of this function (three lines down from here)
    # relies on data generated during the spider._rank_articles_alltime()
    # method, so that one should be called first.
    self.log.record("Ranking authors by popularity...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE author_ranks_working")
      cursor.execute("""
      SELECT article_authors.author, SUM(alltime_ranks.downloads) as downloads
      FROM article_authors
      LEFT JOIN alltime_ranks ON article_authors.article=alltime_ranks.article
      WHERE downloads > 0
      GROUP BY article_authors.author
      ORDER BY downloads DESC, article_authors.author DESC
      """)
      self.log.record("Retrieved download data.", "debug")
      ranks = []
      rankNum = 0
      for record in cursor:
        rankNum = rankNum + 1
        tie = False
        rank = rankNum # changes if it's a tie

        # if the author has the same download count as the
        # previous author in the list, record a tie:
        if len(ranks) > 0:
          if record[1] == ranks[len(ranks) - 1]["downloads"]:
            ranks[len(ranks) - 1]["tie"] = True
            tie = True
            rank = ranks[len(ranks) - 1]["rank"]
        ranks.append({
          "id": record[0],
          "downloads": record[1],
          "rank": rank,
          "tie": tie
        })
    params = [(record["id"], record["rank"], record["downloads"], record["tie"]) for record in ranks]

    record_ranks_file(params, "author_ranks_working")

  def _rank_authors_category(self, category):
    self.log.record(f"Ranking authors by popularity in category {category}...", 'debug')
    with self.connection.db.cursor() as cursor:
      cursor.execute("""
      SELECT article_authors.author, SUM(alltime_ranks.downloads) as downloads
      FROM article_authors
      LEFT JOIN alltime_ranks ON article_authors.article=alltime_ranks.article
      LEFT JOIN articles ON article_authors.article=articles.id
      WHERE downloads > 0 AND
      articles.collection=%s
      GROUP BY article_authors.author
      ORDER BY downloads DESC, article_authors.author DESC
      """, (category,))
      ranks = []
      rankNum = 0
      for record in cursor:
        rankNum = rankNum + 1
        tie = False
        rank = rankNum # changes if it's a tie

        # if the author has the same download count as the
        # previous author in the list, record a tie:
        if len(ranks) > 0:
          if record[1] == ranks[len(ranks) - 1]["downloads"]:
            ranks[len(ranks) - 1]["tie"] = True
            tie = True
            rank = ranks[len(ranks) - 1]["rank"]
        ranks.append({
          "id": record[0],
          "downloads": record[1],
          "rank": rank,
          "tie": tie
        })

    params = [(record["id"], category, record["rank"], record["downloads"], record["tie"]) for record in ranks]

    record_ranks_file(params, "author_ranks_category_working")

  def pull_todays_crossref_data(self):
    current = datetime.now()
    with self.connection.db.cursor() as cursor:
      self.log.record("Determining if Crossref data from yesterday needs to be refreshed.")
      cursor.execute("SELECT COUNT(id) FROM crossref_daily WHERE source_date=%s", (current.strftime('%Y-%m-%d'),))
      data_count = cursor.fetchone()[0]
      if data_count == 0:
        spider.log.record("Fetching yesterday's Crossref data one more time.", "info")
        spider._pull_crossref_data_date((current - timedelta(days=1)).strftime('%Y-%m-%d'))
    self.log.record("Fetching today's Crossref data.")
    self._pull_crossref_data_date(current.strftime('%Y-%m-%d'))

  def update_article(self, article_id, abstract):
    with self.connection.db.cursor() as cursor:
      cursor.execute(f"UPDATE {config.db['schema']}.articles SET abstract = %s WHERE id = %s;", (abstract, article_id))
      self.connection.db.commit()
      self.log.record(f"Recorded abstract for ID {article_id}", "debug")

  def calculate_vectors(self):
    self.log.record("Calculating vectors...")
    with self.connection.db.cursor() as cursor:
      cursor.execute(f"UPDATE {config.db['schema']}.articles SET title_vector = to_tsvector(coalesce(title,'')) WHERE title_vector IS NULL;")
      cursor.execute(f"UPDATE {config.db['schema']}.articles SET abstract_vector = to_tsvector(coalesce(abstract,'')) WHERE abstract_vector IS NULL;")
      self.fill_in_author_vectors()

  def fill_in_author_vectors(self):
    self.log.record("Filling in empty author_vector fields.", 'debug')
    article_ids = []
    with self.connection.db.cursor() as cursor:
      cursor.execute("SELECT id FROM articles WHERE author_vector IS NULL;")
      for record in cursor:
        if len(record) > 0:
          article_ids.append(record[0])

    to_do = len(article_ids)
    if to_do > 0:
      self.log.record(f"Obtained {to_do} article IDs.", 'debug')
    with self.connection.db.cursor() as cursor:
      for article in article_ids:
        author_string = ""
        cursor.execute("SELECT authors.name FROM article_authors as aa INNER JOIN authors ON authors.id=aa.author WHERE aa.article=%s;", (article,))
        for record in cursor:
          author_string += f"{record[0]}, "
        cursor.execute(f"UPDATE {config.db['schema']}.articles SET author_vector=to_tsvector(coalesce(%s,'')) WHERE id=%s;", (author_string, article))
        to_do -= 1
        # if to_do % 100 == 0:
        #   self.log.record(f"{datetime.now()} - {to_do} left to go.", 'debug')

  def remove_orphan_authors(self):
    # Removes authors who are no longer associated with any papers.
    with self.connection.db.cursor() as cursor:
      cursor.execute("""
        SELECT COUNT(id)
        FROM (
          SELECT a.id, COUNT(z.article) AS num
          FROM prod.authors a
          LEFT JOIN prod.article_authors z ON a.id=z.author
          GROUP BY 1
          ORDER BY 2 DESC
        ) AS asdf
        WHERE num = 0
        """)
      authorcount = cursor.fetchone()[0]
      self.log.record(f'Removing {authorcount} authors with no papers.', 'info')
      time.sleep(10)
      # Remove the author email addresses:
      self.log.record('Removing author emails.', 'debug')
      cursor.execute(f"""
        DELETE FROM {config.db["schema"]}.author_emails
        WHERE author IN (SELECT id
          FROM (
            SELECT a.id, COUNT(z.article) AS num
            FROM prod.authors a
            LEFT JOIN prod.article_authors z ON a.id=z.author
            GROUP BY 1
            ORDER BY 2 DESC
          ) AS asdf
          WHERE num = 0)
        """)
      # then from the rank tables:
      for table in ['author_ranks','author_ranks_working','author_ranks_category','author_ranks_category_working']:
        self.log.record(f'Removing author ranks from table {table}.', 'debug')
        cursor.execute(f"""
          DELETE FROM {config.db["schema"]}.{table}
          WHERE author IN (SELECT id
            FROM (
              SELECT a.id, COUNT(z.article) AS num
              FROM prod.authors a
              LEFT JOIN prod.article_authors z ON a.id=z.author
              GROUP BY 1
              ORDER BY 2 DESC
            ) AS asdf
            WHERE num = 0)
          """)
      self.log.record('Removing author entries.', 'debug')
      cursor.execute(f"""
        DELETE FROM {config.db["schema"]}.authors
        WHERE id IN (SELECT id
          FROM (
            SELECT a.id, COUNT(z.article) AS num
            FROM prod.authors a
            LEFT JOIN prod.article_authors z ON a.id=z.author
            GROUP BY 1
            ORDER BY 2 DESC
          ) AS asdf
          WHERE num = 0)
        """)

def load_rankings_from_file(batch, log):
  os.environ["PGPASSWORD"] = config.db["password"]
  to_delete = None
  log.record(f"Loading {batch} from file.", 'debug')
  if batch in ["alltime_ranks", "ytd_ranks", "month_ranks"]:
    query = f'\copy {config.db["schema"]}.{batch}_working (article, rank, downloads) FROM \'{batch}_working.csv\' with (format csv);'
  elif batch == "author_ranks":
    query = f'\copy {config.db["schema"]}.author_ranks_working (author, rank, downloads, tie) FROM \'author_ranks_working.csv\' with (format csv);'
  elif batch == "author_ranks":
    query = f'\copy author_ranks_working (author, rank, downloads, tie) FROM \'author_ranks_working.csv\' with (format csv);'
  elif batch == "author_ranks_category":
    query = f'\copy {config.db["schema"]}.author_ranks_category_working (author, category, rank, downloads, tie) FROM \'author_ranks_category_working.csv\' with (format csv);'
    to_delete = "author_ranks_category_working.csv"
  elif batch == "author_ranks_category":
    query = f'\copy {config.db["schema"]}.author_ranks_category_working (author, category, rank, downloads, tie) FROM \'author_ranks_category_working.csv\' with (format csv);'
    to_delete = "author_ranks_category_working.csv"
  elif batch == "category_ranks":
    query = f'\copy {config.db["schema"]}.category_ranks_working (article, rank) FROM \'category_ranks_working.csv\' with (format csv);'
    to_delete = "category_ranks_working.csv"
  else:
    log.record(f'Unrecognized rankings source passed to load_rankings_from_file: {batch}', "warn")
    return

  subprocess.run(["psql", "-h", config.db["host"], "-U", config.db["user"], "-d", config.db["db"], "-c", query], check=True)
  # Some files get rewritten a bunch of times; if we encounter one of those,
  # delete it before the next iteration starts.
  if to_delete is not None:
    os.remove(to_delete)

def full_run(spider):
  if config.crawl["fetch_missing_fields"] is not False:
    spider.get_urls()
    spider.get_posted_dates()
    spider.refresh_article_stats(get_authors=True) # Fix authorless papers
    spider.remove_orphan_authors()

  if config.crawl["fetch_new"] is not False:
    spider.find_record_new_articles()
  else:
    spider.log.record("Skipping search for new articles: disabled in configuration file.", 'debug')

  if config.crawl["fetch_pubstatus"] is not False:
    spider.fetch_published()
    get_journal_names(spider)

  for collection in spider.fetch_category_list():
    if config.crawl["refresh_stats"] is not False:
      spider.refresh_article_stats(collection, config.refresh_category_cap)
      # HACK: There are way more neuro papers, so we check twice as many in each run
      if collection == 'neuroscience':
        spider.refresh_article_stats(collection, config.refresh_category_cap)

  if config.crawl["refresh_stats"] is not False:
    # Refresh the articles without a collection:
    spider.refresh_article_stats()

  if config.crawl["fetch_crossref"] is not False:
    spider.pull_todays_crossref_data()
  else:
    spider.log.record("Skipping call to fetch Crossref Twitter data: disabled in configuration file.", 'debug')

  if config.crawl["fetch_pubdates"] is not False:
    get_publication_dates(spider)
  else:
    spider.log.record("Skipping call to fetch Crossref publication data: disabled in configuration file.", 'debug')

  spider.calculate_vectors()

  if config.perform_ranks["enabled"] is not False:
    spider.process_rankings()
  else:
    spider.log.record("Skipping all ranking steps: disabled in configuration file.", 'debug')

def find_authors(response):
  # Determine author details:
  authors = []
  author_tags = response.html.find('meta[name^="citation_author"]')
  current_name = ""
  current_institution = ""
  current_email = ""
  current_orcid = ""
  for tag in author_tags:
    if tag.attrs["name"] == "citation_author":
      if current_name != "": # if this isn't the first author
        authors.append(models.Author(current_name, current_institution, current_email, current_orcid))
      current_name = tag.attrs["content"]
      current_institution = ""
      current_email = ""
      current_orcid = ""
    elif tag.attrs["name"] == "citation_author_institution":
      current_institution = tag.attrs["content"]
    elif tag.attrs["name"] == "citation_author_email":
      current_email = tag.attrs["content"]
    elif tag.attrs["name"] == "citation_author_orcid":
      current_orcid = tag.attrs["content"]
  # since we record each author once we find the beginning of the
  # next author's entry, the last step has to be to record whichever
  # author we were looking at when the author list ended:
  if current_name != "": # if we somehow didn't find a single author
    authors.append(models.Author(current_name, current_institution, current_email, current_orcid))
  return authors

def month_to_num(month):
  # helper for converting month names (string) to numbers (int)
  if len(month) > 3: # if it's the full name, truncate it
    month = month[:3]
  months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  months_to_num = dict(zip(months, range(1,13)))
  return months_to_num[month]

def pieces_to_date(pieces):
  if len(pieces) == 3:
    return f'{pieces[0]}-{pieces[1]}-{pieces[2]}'
  else:
    return False

def get_publication_dates(spider):
  with spider.connection.db.cursor() as cursor:
    cursor.execute(f"""
    SELECT p.article, p.doi
    FROM {config.db['schema']}.article_publications p
    LEFT JOIN {config.db['schema']}.publication_dates d ON p.article=d.article
    WHERE d.date IS NULL
    """)
    todo = []
    for article in cursor:
      todo.append((article[0], article[1]))

  for article in todo:
    answer = None
    if config.polite:
      time.sleep(3)
    article_id = article[0]
    doi = article[1]
    spider.log.record(f"Checking DOI {doi}", 'debug')
    headers = {'user-agent': config.user_agent}
    try:
      r = requests.get(f"https://api.crossref.org/works/{doi}?mailto={config.crossref['parameters']['email']}", headers=headers)
    except Exception as e:
      spider.log.record(f"  Error calling crossref API for publication data: {e}", 'error')
      continue

    if r.status_code != 200:
      if r.status_code == 404:
        spider.log.record("  Not found.", 'debug')
        # HACK: This makes it simpler to skip missing papers in the future
        answer = (article_id, '1900-01-01')

    else:
      resp = r.json()
      if "message" not in resp.keys():
        spider.log.record("  No message found.", 'debug')
        continue
      if "published-online" in resp['message']:
        if 'date-parts' in resp['message']['published-online']:
          pieces = resp['message']['published-online']['date-parts'][0]
          dateparts = pieces_to_date(pieces)
          if dateparts:
            spider.log.record(f"  FOUND DATE (online): {dateparts}", 'info')
            answer = (article_id, dateparts)
      if "published-print" in resp['message'] and answer is None:
        if 'date-parts' in resp['message']['published-print']:
          pieces = resp['message']['published-print']['date-parts'][0]
          dateparts = pieces_to_date(pieces)
          if dateparts:
            spider.log.record(f"  FOUND DATE (print): {dateparts}", 'info')
            answer = (article_id, dateparts)
      if "created" in resp['message'] and answer is None:
        if 'date-parts' in resp['message']['created']:
          pieces = resp['message']['created']['date-parts'][0]
          dateparts = pieces_to_date(pieces)
          if dateparts:
            spider.log.record(f"  FOUND DATE (created): {dateparts}", 'info')
            answer = (article_id, dateparts)
    if answer is not None:
      with spider.connection.db.cursor() as cursor:
        sql = f"INSERT INTO {config.db['schema']}.publication_dates (article, date) VALUES (%s, %s);"
        cursor.execute(sql, answer)
        spider.log.record("  Recorded.", 'debug')

def get_journal_names(spider):
  # TODO: combine this with the publication dates call
  spider.log.record('Fetching journal names for published preprints', 'info')
  with spider.connection.db.cursor() as cursor:
    cursor.execute(f"""
    SELECT article, doi
    FROM {config.db['schema']}.article_publications
    WHERE publication IS NULL
    """)
    todo = []
    for article in cursor:
      todo.append((article[0], article[1]))

  for article in todo:
    answer = None
    if config.polite:
      time.sleep(3)
    article_id = article[0]
    doi = article[1]
    spider.log.record(f"Checking journal for DOI {doi}", 'debug')
    headers = {'user-agent': config.user_agent}
    try:
      r = requests.get(f"https://api.crossref.org/works/{doi}?mailto={config.crossref['parameters']['email']}", headers=headers)
    except Exception as e:
      spider.log.record(f"  Error calling crossref API for publication data: {e}", 'error')
      continue

    if r.status_code != 200:
      if r.status_code == 404:
        spider.log.record("  Not found.", 'debug')
        # HACK: This makes it simpler to skip missing papers in the future
        answer = 'unknown?'

    else:
      resp = r.json()
      if "message" not in resp.keys():
        spider.log.record("  No message found.", 'debug')
        continue
      if "container-title" in resp['message'] and len(resp['message']['container-title']) > 0:
        answer = resp['message']['container-title'][0]
      elif "short-container-title" in resp['message'] and len(resp['message']['short-container-title']) > 0:
        answer = resp['message']['short-container-title'][0]
    if answer is not None:
      with spider.connection.db.cursor() as cursor:
        cursor.execute(f"UPDATE {config.db['schema']}.article_publications SET publication=%s WHERE article=%s;", (answer, article_id))
        spider.log.record("  Recorded.", 'debug')

if __name__ == "__main__":
  spider = Spider()
  if len(sys.argv) == 1: # if no action is specified, do everything
    full_run(spider)
  elif sys.argv[1] == "crossref":
    if len(sys.argv) > 2:
      spider._pull_crossref_data_date(sys.argv[2])
    else:
      spider.pull_todays_crossref_data()
  elif sys.argv[1] == "pubdates":
    # This task probably doesn't need to be run during EVERY refresh
    get_publication_dates(spider)
  elif sys.argv[1] == "refresh":
    if len(sys.argv) == 3:
      # if the ID of a specific article is given,
      # only update that one
      spider.refresh_article_stats(id=sys.argv[2])
    else:
      config.crawl = {
        "fetch_new": False, # Check for new papers in each collection
        "fetch_crossref": False, # Update daily Crossref stats
        "refresh_stats": True, # Look for articles with outdated download info and re-crawl them
        "fetch_pubstatus": True, # Check for whether papers have been published
        "fetch_pubdates": True, # Check for publication dates for any papers that have been published
        "fetch_missing_fields": False
      }
      full_run(spider)
