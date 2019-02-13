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

  def _pull_crossref_data_date(self, datestring):
    # Datestring should be format YYYY-MM-DD
    self.log.record(f"Beginning retrieval of Crossref data for {datestring}", "info")
    # (If we have multiple results for the same 24-hour period, the
    # query that displays the most popular displays the same articles
    # multiple times, and the aggregation function to clean that up
    # would be too complicated to bother with right now.)
    with self.connection.db.cursor() as cursor:
      self.log.record("Removing earlier data from same day")
      cursor.execute("DELETE FROM crossref_daily WHERE source_date=%s;", (datestring,))

    headers = {'user-agent': config.user_agent}
    r = requests.get("{0}?obj-id.prefix=10.1101&from-occurred-date={1}&until-occurred-date={1}&source=twitter&mailto={2}&rows=10000".format(config.crossref["endpoints"]["events"], datestring, config.crossref["parameters"]["email"]), headers=headers)
    if r.status_code != 200:
      self.log.record(f"Got weird status code: {r.status_code}. {r.text()}", "error")
      return
    results = r.json()

    if results["status"] != "ok":
      self.log.record(f'Crossref responded, but with unexpected status: {results["status"]}', "error")
      return
    if "message" not in results.keys() or "events" not in results["message"].keys() or len(results["message"]["events"]) == 0:
      self.log.record("Events not found in response.", "error")
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

    sql = f"INSERT INTO {config.db['schema']}.crossref_daily (source_date, doi, count) VALUES (%s, %s, %s);"
    params = [(datestring, doi, len(tweets[doi])) for doi in tweets]
    self.log.record(f"Saving tweet data for {len(tweets.keys())} DOI entries.")
    with self.connection.db.cursor() as cursor:
      cursor.executemany(sql, params)
    self.log.record("Done with crossref.", "debug")

  def find_record_new_articles(self):
    # we need to grab the first page to figure out how many pages there are
    self.log.record(f"Fetching page 0")
    try:
      r = self.session.get(config.biorxiv["endpoints"]["recent"])
    except Exception as e:
      self.log.record(f"Error requesting first page of recent results. Retrying: {e}", "error")
      try:
        r = self.session.get(config.biorxiv["endpoints"]["recent"])
      except Exception as e:
        self.log.record(f"Error AGAIN requesting first page of results. Bailing: {e}", "error")
        return

    results = pull_out_articles(r.html, self.log)
    consecutive_recognized = 0
    for article in results:
      recorded = article.record(self.connection, self)
      if recorded  == False:
        # if it was a paper that we'd already seen before
        consecutive_recognized += 1
        if consecutive_recognized >= config.recognized_limit and config.stop_on_recognized: return
      elif recorded is not None:
        # article.record() returns "None" if the paper was a revisions, because
        # there isn't (for now?) a way to know if it's been previously recorded.
        # This doesn't count as a "recognized" article in our count, but it also
        # doesn't reset the counter.
        consecutive_recognized = 0

    for p in range(1, determine_page_count(r.html)): # iterate through each page of results
      if config.polite:
        time.sleep(3)
      self.log.record(f"\n\nFetching page {p}") # pages are zero-indexed
      try:
        r = self.session.get("{}?page={}".format(config.biorxiv["endpoints"]["recent"], p))
      except Exception as e:
        self.log.record(f"Error requesting page {p} of results. Retrying: {e}", "error")
        try:
          r = self.session.get("{}?page={}".format(config.biorxiv["endpoints"]["recent"], p))
        except Exception as e:
          self.log.record(f"Error AGAIN requesting page of results: {e}", "error")
          self.log.record("Crawling recent papers failed in the middle; unrecorded new articles are likely being skipped. Exiting to avoid losing them.", "fatal")
          return

      results = pull_out_articles(r.html, self.log)
      for x in results:
        recorded = x.record(self.connection, self)
        if recorded == False:
          consecutive_recognized += 1
          if consecutive_recognized >= config.recognized_limit and config.stop_on_recognized: return
        elif recorded is not None:
          # article.record() returns "None" if the paper was a revisions, because
          # there isn't (for now?) a way to know if it's been previously recorded.
          # This doesn't count as a "recognized" article in our count, but it also
          # doesn't reset the counter.
          consecutive_recognized = 0

  def determine_collection(self, collection):
    # we need to grab the first page to figure out how many pages there are
    self.log.record(f"Fetching page 0 in {collection}", 'debug')
    try:
      r = self.session.get(f'{config.biorxiv["endpoints"]["collection"]}/{collection}')
    except Exception as e:
      self.log.record(f"Error requesting first page of results for collection. Retrying: {e}", "error")
      try:
        r = self.session.get(f'{config.biorxiv["endpoints"]["collection"]}/{collection}')
      except Exception as e:
        self.log.record(f"Error AGAIN requesting first page of results for collection. Bailing: {e}", "error")
        return

    results = pull_out_articles(r.html, self.log)
    consecutive_recognized = 0

    # It's fine if we encounter unknown papers at the beginning of the category,
    # but if an unrecognized paper shows up later in the category, something
    # funny's going on
    recognized_any = False

    for article in results: # note: this first loop only for the first page
      article.collection = collection
      # make sure we know about the article already:
      if not article.get_id(self.connection):
        if recognized_any:
          self.log.record(f'Encountered unknown paper in category listings: {article.doi}', 'fatal')
        else:
          self.log.record(f'New paper at top of category listings: {article.doi}', 'debug')
          continue

      recognized_any = True
      if not article.record_category(collection, self.connection, self.log):
        consecutive_recognized += 1
        if consecutive_recognized >= config.cat_recognized_limit and config.stop_on_recognized: return
      else:
        consecutive_recognized = 0

    for p in range(1, determine_page_count(r.html)): # iterate through each page of results
      if config.polite:
        time.sleep(3)
      self.log.record(f"Fetching page {p} in {collection}", 'debug') # pages are zero-indexed
      try:
        r = self.session.get("{}/{}?page={}".format(config.biorxiv["endpoints"]["collection"], collection, p))
      except Exception as e:
        log.record(f"Error requesting page of results for collection {collection}. Retrying: {e}", "error")
        try:
          r = self.session.get("{}/{}?page={}".format(config.biorxiv["endpoints"]["collection"], collection, p))
        except Exception as e:
          log.record(f"Error AGAIN requesting page of results for collection {collection}: {e}", "error")
          log.record("Crawling of category {} failed in the middle; unrecorded new articles are likely being skipped. Exiting to avoid losing them.", "fatal")
          return

      results = pull_out_articles(r.html, self.log)
      for article in results:
        article.collection = collection
        if not article.get_id(self.connection):
          if recognized_any:
            self.log.record(f'Encountered unknown paper in category listings: {article.doi}', 'fatal')
          else:
            self.log.record(f'New paper at top of category listings: {article.doi}', 'debug')
            continue

        recognized_any = True
        if not article.record_category(collection, self.connection, self.log):
          consecutive_recognized += 1
          if consecutive_recognized >= config.cat_recognized_limit and config.stop_on_recognized:
            return
        else:
          consecutive_recognized = 0

  def fetch_abstracts(self):
    with self.connection.db.cursor() as cursor:
      # find abstracts for any articles without them
      cursor.execute(f'SELECT id, url FROM {config.db["schema"]}.articles WHERE abstract IS NULL;')
      for article in cursor:
        url = article[1]
        article_id = article[0]
        try:
          abstract = self.get_article_abstract(url)
          self.update_article(article_id, abstract)
        except ValueError as e:
          self.log.record(f"Error retrieving abstract for {article[1]}: {e}", "error")

  def refresh_article_stats(self, collection=None, cap=10000, id=None, get_authors=False):
    """Normally, "collection" is specified, and the function will
    iterate through outdated articles in the given collection. However,
    specifying "id" instead will update the entry for a single article.
    """
    self.log.record(f"Refreshing article download stats for collection {collection}...")
    with self.connection.db.cursor() as cursor:
      if id is None:
        if get_authors: # if we're just trying to update papers without authors
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
        else:
          cursor.execute("SELECT id, url, doi FROM articles WHERE collection=%s AND last_crawled < now() - interval %s;", (collection, config.refresh_interval))
      else:
        cursor.execute("SELECT id, url, doi FROM articles WHERE id=%s;", (id,))
      updated = 0
      consecutive_errors = 0
      for article in cursor:
        article_id = article[0]
        url = article[1]
        doi = article[2]
        self.log.record(f"\nRefreshing article {article_id}", "debug")
        if config.polite:
          time.sleep(1)
        stat_table, authors = self.get_article_stats(url)

        if config.crawl["fetch_pubstatus"] is not False:
          try:
            pub_data = self.check_publication_status(article_id, doi, True)
          except ValueError:
            consecutive_errors += 1
            if consecutive_errors >= 3:
              self.log.record("Too many errors in a row. Turning off publication status checks for this run.", "error")
              config.crawl["fetch_pubstatus"] = False
            else:
              self.log.record(f"Encountered error ({consecutive_errors} in a row). Waiting five minutes to continue.", "warn")
              time.sleep(300)
              continue
          if pub_data is not None: # if we found something
            self.record_publication_status(article_id, pub_data["doi"], pub_data["publication"])

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

  def check_publication_status(self, article_id, doi, retry=False):
    self.log.record(f"Determining publication status for DOI {doi}.", "debug")
    with self.connection.db.cursor() as cursor:
      # we check for which ones are already recorded because
      # the postgres UPSERT feature is bananas
      cursor.execute("SELECT COUNT(article) FROM article_publications WHERE article=%s", (article_id,))
      pub_count = cursor.fetchone()[0]
      if pub_count > 0:
        self.log.record("Paper already has publication recorded. Skipping.", "debug")
        return
    try:
      resp = self.session.get("{}?doi={}".format(config.biorxiv["endpoints"]["pub_doi"], doi))
    except Exception as e:
      self.log.record(f"Error fetching publication data: {e}", "warn")
      if retry:
        self.log.record("Retrying in 60 seconds:", "debug")
        time.sleep(60)
        return self.check_publication_status(article_id, doi)
      else:
        self.log.record("Giving up on this one for now.", "error")
        raise ValueError("Encountered exception making HTTP call to fetch publication information.")

    try:
      # response is wrapped in parentheses and lots of trailing white space
      parsed = json.loads(re.sub(r'\)\s*$', '', resp.text[1:]))
    except json.decoder.JSONDecodeError as e:
      self.log.record(f"Error encountered decoding JSON: {e}. Bailing.", "error")
      return

    data = parsed.get("pub", [])
    if len(data) == 0:
      self.log.record("No data found", "debug")
      return

    if data[0].get("pub_type") != "published":
      self.log.record(f'Publication found, but not in "published" state: {data[0]["pub_type"]}. Skipping.', 'info')
      return # Don't know what this could mean
    if "pub_doi" not in data[0] or "pub_journal" not in data[0]:
      self.log.record("Publication data found, but missing important field(s). Skipping.")
      return

    self.log.record(f'Publication found: {data[0]["pub_journal"]}', 'debug')

    with self.connection.db.cursor() as cursor:
      self.log.record("Saving publication info.", "debug")
      cursor.execute(f"INSERT INTO {config.db['schema']}.article_publications (article, doi, publication) VALUES (%s, %s, %s);", (article_id, data[0]["pub_doi"], data[0]["pub_journal"]))
      self.log.record(f'Recorded DOI {data[0]["pub_doi"]} for article {article_id}')

  def get_article_abstract(self, url, retry=True):
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
    abstract = resp.html.find("#p-2")
    if len(abstract) < 1:
      raise ValueError("Successfully made HTTP call to fetch paper information, but did not find an abstract.")
    return abstract[0].text

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
    authors = find_authors(resp)

    entries = iter(resp.html.find("td"))
    stats = []
    for entry in entries:
      date = entry.text.split(" ")
      month = month_to_num(date[0])
      year = int(date[1])
      abstract = int(next(entries).text)
      pdf = int(next(entries).text)
      stats.append((month, year, abstract, pdf))
    return stats, authors

  def get_article_posted_date(self, url, retry_count=0):
    self.log.record("Determining posting date.", 'debug')
    try:
      resp = self.session.get(f"{url}.article-info")
    except Exception as e:
      if retry_count < 3:
        self.log.record(f"Error requesting article posted-on date. Retrying: {e}", "error")
        self.get_article_posted_date(url, retry_count+1)
      else:
        self.log.record(f"Error AGAIN requesting article posted-on date. Bailing: {e}", "error")
        return None
    # This assumes that revisions continue to be listed with oldest version first:
    older = resp.html.find('.hw-version-previous-link', first=True)
    # Also grab the "Posted on" date on this page:
    posted = resp.html.find('meta[name="article:published_time"]', first=True)
    if older is not None: # if there's an older version, grab the date
      self.log.record("Previous version detected. Finding date.", 'debug')
      date_search = re.search('(\w*) (\d*), (\d{4})', older.text)
      if len(date_search.groups()) < 3:
        self.log.record("Could not determine date. Skipping.", "warn")
        return None
      month = date_search.group(1)
      day = date_search.group(2)
      year = date_search.group(3)
      datestring = f"{year}-{month_to_num(month)}-{day}"
      self.log.record(f"Determined date: {datestring}", "info")
      return datestring
    elif posted is not None: # if not, just grab the date from the current version
      self.log.record(f'No older version detected; using date from current page: {posted.attrs["content"]}', "debug")
      return posted.attrs['content']
    else:
      self.log.record(f"Could not determine posted date for article at {url}", "warn")

    return None

  def save_article_stats(self, article_id, stats, posted=None):
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

      if posted is not None:
        self.log.record(f"Determined 'posted on' date: {posted}", "debug")
        cursor.execute(f"UPDATE {config.db['schema']}.articles SET posted = %s WHERE id=%s", (posted, article_id))

      self.log.record(f"Recorded {len(to_record)} stats for ID {article_id}", "debug")

  def _record_authors(self, article_id, authors, overwrite=False):
    if overwrite:
      with self.connection.db.cursor() as cursor:
        self.log.record("Marking currently recorded authors for deletion.", "debug")
        # we set the article ID to 0 before deleting them so if the spider dies in
        # between removing the old authors and updating the new ones, we can go in
        # and fix it manually.
        cursor.execute(f'UPDATE {config.db["schema"]}.article_authors SET article=0 WHERE article=%s;', (article_id,))
    else:
      with self.connection.db.cursor() as cursor:
        cursor.execute(f'SELECT COUNT(article) FROM {config.db["schema"]}.article_authors WHERE article=%s;', (article_id,))
        count = cursor.fetchone()[0]
        if count > 0:
          return

    author_ids = []
    for a in authors:
      a.record(self.connection, self.log)
      author_ids.append(a.id)

    try:
      with self.connection.db.cursor() as cursor:
        sql = f'INSERT INTO {config.db["schema"]}.article_authors (article, author) VALUES (%s, %s);'
        cursor.executemany(sql, [(article_id, x) for x in author_ids])
    except Exception as e:
      # If there's an error associating all the authors with their paper all at once,
      # send separate queries for each one
      # (This came up last time because an author was listed twice on the same paper.)
      self.log.record(f"Error associating authors to paper: {e}", "warn")
      self.log.record("Recording article associations one at a time.", "info")
      for x in author_ids:
        try:
          with self.connection.db.cursor() as cursor:
            cursor.execute(f'INSERT INTO {config.db["schema"]}.article_authors (article, author) VALUES (%s, %s);', (article_id, x))
        except Exception as e:
          self.log.record(f"Another problem associating author {x} to article {article_id}. Moving on.", "error")
          pass
    if overwrite:
      # if we marked authors for deletion earlier, it's safe to delete them now.
      self.log.record("Removing outdated authors.", "debug")
      with self.connection.db.cursor() as cursor:
        cursor.execute(f'DELETE FROM {config.db["schema"]}.article_authors WHERE article=0;')

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
  if config.crawl["fetch_new"] is not False:
    spider.find_record_new_articles()
  else:
    spider.log.record("Skipping search for new articles: disabled in configuration file.", 'debug')
  if config.crawl["fetch_abstracts"] is not False:
    spider.fetch_abstracts()
  else:
    spider.log.record("Skipping step to fetch unknown abstracts: disabled in configuration file.", 'debug')

  for collection in spider.fetch_category_list():
    spider.log.record(f"\n\nBeginning category {collection}", "info")
    if config.crawl["fetch_collections"] is not False:
      spider.determine_collection(collection)
    else:
      spider.log.record("Skipping determination of new article collection: disabled in configuration file.", 'debug')
    if config.crawl["refresh_stats"] is not False:
      spider.refresh_article_stats(collection, config.refresh_category_cap)
      # HACK: There are way more neuro papers, so we check twice as many in each run
      if collection == 'neuroscience':
        spider.refresh_article_stats(collection, config.refresh_category_cap)
      spider.refresh_article_stats(get_authors=True)
    else:
      spider.log.record("Skipping refresh of paper download stats: disabled in configuration file.", 'debug')

  if config.crawl["fetch_crossref"] is not False:
    spider.pull_todays_crossref_data()
  else:
    spider.log.record("Skipping call to fetch Crossref data: disabled in configuration file.", 'debug')

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
  for x in range(0,100):
    answers = []
    with spider.connection.db.cursor() as cursor:
      cursor.execute(f"""
      SELECT p.article, p.doi
      FROM {config.db['schema']}.article_publications p
      LEFT JOIN {config.db['schema']}.publication_dates d ON p.article=d.article
      WHERE d.date IS NULL
      """)
      done = 0
      for article in cursor:
        if done >= 100:
          # We do this to save results in batches
          break
        done += 1
        if config.polite:
          time.sleep(2)
        article_id = article[0]
        doi = article[1]
        spider.log.record(f"Checking DOI {doi}", 'debug')
        headers = {'user-agent': config.user_agent}
        r = requests.get(f"https://api.crossref.org/works/{doi}?mailto={config.crossref['parameters']['email']}", headers=headers)
        if r.status_code != 200:
          if r.status_code == 404:
            spider.log.record("  Not found.", 'debug')
            # HACK: This makes it simpler to skip missing papers in the future
            answers.append((article_id, '1900-01-01'))
            continue
          spider.log.record(f"  Got weird status code: {r.status_code}", 'warn')
          continue
        resp = r.json()

        if "message" not in resp.keys():
          spider.log.record("  No message found.", 'debug')
          continue
        if "published-online" in resp['message']:
          if 'date-parts' in resp['message']['published-online']:
            pieces = resp['message']['published-online']['date-parts'][0]
            answer = pieces_to_date(pieces)
            if answer:
              spider.log.record(f"  FOUND DATE (online): {answer}", 'info')
              answers.append((article_id, answer))
              continue
        if "published-print" in resp['message']:
          if 'date-parts' in resp['message']['published-print']:
            pieces = resp['message']['published-print']['date-parts'][0]
            answer = pieces_to_date(pieces)
            if answer:
              spider.log.record(f"  FOUND DATE (print): {answer}", 'info')
              answers.append((article_id, answer))
              continue
        if "created" in resp['message']:
          if 'date-parts' in resp['message']['created']:
            pieces = resp['message']['created']['date-parts'][0]
            answer = pieces_to_date(pieces)
            if answer:
              spider.log.record(f"  FOUND DATE (created): {answer}", 'info')
              answers.append((article_id, answer))
              continue
    spider.log.record("\nRecording batch.", 'debug')
    with spider.connection.db.cursor() as cursor:
      sql = f"INSERT INTO {config.db['schema']}.publication_dates (article, date) VALUES (%s, %s);"
      cursor.executemany(sql, answers)

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
        "fetch_collections": True, # Fill in the collection for new articles
        "fetch_abstracts": True, # Check for any Rxivist papers missing an abstract and fill it in (Papers don't have an abstract when first crawled)
        "fetch_crossref": False, # Update daily Crossref stats
        "refresh_stats": True, # Look for articles with outdated download info and re-crawl them
        "fetch_pubstatus": False # Check for whether a paper has been published during stat refresh
      }
      full_run(spider)