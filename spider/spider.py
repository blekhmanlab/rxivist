#     Rxivist, a system for crawling papers published on bioRxiv
#     and organizing them in ways that make it easier to find new
#     or interesting research. Includes a web application for
#     the display of data.
#     Copyright (C) 2018 Regents of the University of Minnesota

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

def pull_out_articles(html, collection, log):
  entries = html.find(".highwire-article-citation")
  articles = []
  for entry in entries:
    a = models.Article()
    a.process_results_entry(entry, collection, log)
    articles.append(a)
  return articles

def record_ranks_file(to_record, filename):
  with open("{}.csv".format(filename), 'w') as f:
    for entry in to_record:
      to_write = ""
      for i, field in enumerate(entry):
        to_write += "{}".format(field)
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
    self.log.record("Beginning retrieval of Crossref data for {}".format(datestring), "info")
    # (If we have multiple results for the same 24-hour period, the
    # query that displays the most popular displays the same articles
    # multiple times, and the aggregation function to clean that up
    # would be too complicated to bother with right now.)
    with self.connection.db.cursor() as cursor:
      self.log.record("Removing earlier data from same day")
      cursor.execute("DELETE FROM crossref_daily WHERE source_date=%s;", (datestring,))

    headers = {'user-agent': config.user_agent}
    r = requests.get("https://api.eventdata.crossref.org/v1/events?obj-id.prefix=10.1101&from-occurred-date={0}&until-occurred-date={0}&source=twitter&mailto=rabdill@umn.edu&rows=10000".format(datestring), headers=headers)
    if r.status_code != 200:
      self.log.record("Got weird status code: {}. {}".format(r.status_code, r.text()), "error")
      return
    results = r.json()

    if results["status"] != "ok":
      self.log.record("Crossref responded, but with unexpected status: {}".format(results["status"]), "error")
      return
    if "message" not in results.keys() or "events" not in results["message"].keys() or len(results["message"]["events"]) == 0:
      self.log.record("Events not found in response.", "error")
      return

    tweets = defaultdict(list)
    if results["message"]["total-results"] > 10000:
      # Odds are we're never going to get more than one page here, so
      # let's put off the implemention of pagination until that day
      # is upon us
      self.log.record("TOO MANY RESULTS: {}".format(results["message"]["total-results"]), "fatal")
    for event in results["message"]["events"]:
      if event.get("source_id") != "twitter": # double-check that it's filtering right
        self.log.record("Unrecognized source_id field: {}. Skipping.".format(event.get("source_id", "(not provided)")), "info")
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
      tweets[doi].append(event["subj"]["original-tweet-url"])

    sql = "INSERT INTO crossref_daily (source_date, doi, count) VALUES (%s, %s, %s);"
    params = [(datestring, doi, len(tweets[doi])) for doi in tweets]
    self.log.record("Saving tweet data for {} DOI entries.".format(len(tweets.keys())))
    with self.connection.db.cursor() as cursor:
      cursor.executemany(sql, params)
    self.log.record("Done with crossref.", "info")

  def find_record_new_articles(self, collection):
    # we need to grab the first page to figure out how many pages there are
    self.log.record("Fetching page 0 in {}".format(collection))
    r = self.session.get("{}/{}".format(config.biorxiv["endpoints"]["collection"], collection))
    results = pull_out_articles(r.html, collection, self.log)
    consecutive_recognized = 0
    for x in results:
      if not x.record(self.connection, self): # TODO: don't pass the whole damn spider here
        consecutive_recognized += 1
        if consecutive_recognized >= config.recognized_limit and config.stop_on_recognized: return
      else:
        consecutive_recognized = 0

    for p in range(1, determine_page_count(r.html)): # iterate through each page of results
      if config.polite:
        time.sleep(3)
      self.log.record("Fetching page {} in {}".format(p, collection)) # pages are zero-indexed
      r = self.session.get("{}/{}?page={}".format(config.biorxiv["endpoints"]["collection"], collection, p))
      results = pull_out_articles(r.html, collection, self.log)
      for x in results:
        if not x.record(self.connection, self):
          consecutive_recognized += 1
          if consecutive_recognized >= config.recognized_limit and config.stop_on_recognized: return
        else:
          consecutive_recognized = 0

  def fetch_abstracts(self):
    with self.connection.db.cursor() as cursor:
      # find abstracts for any articles without them
      cursor.execute("SELECT id, url FROM articles WHERE abstract IS NULL;")
      for article in cursor:
        url = article[1]
        article_id = article[0]
        try:
          abstract = self.get_article_abstract(url)
          self.update_article(article_id, abstract)
        except ValueError as e:
          self.log.record("Error retrieving abstract: {}".format(e))

  def refresh_article_stats(self, collection, cap=10000): # TODO: should be article method
    self.log.record("Refreshing article download stats for collection {}...".format(collection))
    with self.connection.db.cursor() as cursor:
      # cursor.execute("SELECT id, url, posted, doi FROM articles WHERE collection=%s AND last_crawled < now() - interval %s;", (collection, config.refresh_interval))
      # TODO: UNCOMMENT this piece and remove the line that looks for refresh candidates
      # based on posted date; that's just to accellerate the transition to the improved schema
      cursor.execute("SELECT id, url, posted, doi FROM articles WHERE collection=%s AND posted IS NULL;", (collection,))
      updated = 0
      for article in cursor:
        url = article[1]
        article_id = article[0]
        known_posted = article[2]
        doi = article[3]
        self.log.record("\nRefreshing article {}".format(article_id), "debug")
        if config.polite:
          time.sleep(1)
        stat_table, detailed_authors = self.get_article_stats(url)
        pub_data = self.check_publication_status(article_id, doi, True)
        if pub_data is not None: # if we found something
          self.record_publication_status(article_id, pub_data["doi"], pub_data["publication"])
        posted = None
        if known_posted is None: # record the 'posted on' date if we don't know it
          posted = self.get_article_posted_date(url)
        self.save_article_stats(article_id, stat_table, posted)
        self._record_detailed_authors(article_id, detailed_authors)
        updated += 1
        if config.limit_refresh is not False and updated >= cap:
          self.log.record("Maximum articles reached for this session. Returning.")
          break
    self.log.record("{} articles refreshed in {}.".format(updated, collection))
    return updated

  def check_publication_status(self, article_id, doi, retry=False):
    self.log.record("Determining publication status for DOI {}.".format(doi))
    with self.connection.db.cursor() as cursor:
      # we check for which ones are already recorded because
      # the postgres UPSERT feature is bananas
      cursor.execute("SELECT COUNT(article) FROM article_publications WHERE article=%s", (article_id,))
      pub_count = cursor.fetchone()[0]
      if pub_count > 0:
        self.log.record("Paper already has publication recorded. Skipping.", "debug")
        return
    try:
      resp = self.session.get("https://connect.biorxiv.org/bx_pub_doi_get.php?doi={}".format(doi))
    except Exception as e:
      self.log.record("Error fetching publication data: {}".format(e), "warn")
      if retry:
        self.log.record("Retrying:")
        time.sleep(3)
        return self.check_publication_status(article_id, doi)
      else:
        self.log.record("Giving up on this one for now.", "error")
        raise ValueError("Encountered exception making HTTP call to fetch publication information.")

    try:
      # response is wrapped in parentheses and lots of trailing white space
      parsed = json.loads(re.sub(r'\)\s*$', '', resp.text[1:]))
    except json.decoder.JSONDecodeError as e:
      self.log.record("Error encountered decoding JSON: {}. Bailing.".format(e), "error")
      return

    data = parsed.get("pub", [])
    if len(data) == 0:
      self.log.record("No data found", "debug")
      return

    if data[0].get("pub_type") != "published":
      self.log.record("Publication found, but not in 'published' state: {}. Skipping.".format(data[0]["pub_type"]), "info")
      return # Don't know what this could mean
    if "pub_doi" not in data[0] or "pub_journal" not in data[0]:
      self.log.record("Publication data found, but missing important field(s). Skipping.")
      return

    self.log.record("**Publication found: {}".format(data[0]["pub_journal"]))

    with self.connection.db.cursor() as cursor:
      self.log.record("Saving publication info.", "debug")
      cursor.execute("INSERT INTO article_publications (article, doi, publication) VALUES (%s, %s, %s);", (article_id, data[0]["pub_doi"], data[0]["pub_journal"]))
      self.log.record("Recorded DOI {} for article {}".format(data[0]["pub_doi"], article_id))

  def get_article_abstract(self, url, retry=True):
    if config.polite:
      time.sleep(1)
    try:
      resp = self.session.get(url)
    except Exception as e:
      self.log.record("Error fetching abstract: {}".format(e), "warn")
      if retry:
        self.log.record("Retrying:")
        time.sleep(3)
        return self.get_article_abstract(url, False)
      else:
        self.log.record("Giving up on this one for now.", "error")
        raise ValueError("Encountered exception making HTTP call to fetch paper information.")
    abstract = resp.html.find("#p-2")
    if len(abstract) < 1:
      raise ValueError("Successfully made HTTP call to fetch paper information, but did not find an abstract.")
    return abstract[0].text

  def get_article_stats(self, url): # TODO: This should be an article method, right?
    resp = self.session.get("{}.article-metrics".format(url))

    detailed_authors = find_detailed_authors(resp) # TODO: Record this

    entries = iter(resp.html.find("td"))
    stats = []
    for entry in entries:
      date = entry.text.split(" ")
      month = month_to_num(date[0])
      year = int(date[1])
      abstract = int(next(entries).text)
      pdf = int(next(entries).text)
      stats.append((month, year, abstract, pdf))
    return stats, detailed_authors

  def get_article_posted_date(self, url):
    self.log.record("Determining posting date.")
    resp = self.session.get("{}.article-info".format(url))
    # This assumes that revisions continue to be listed with oldest version first:
    older = resp.html.find('.hw-version-previous-link', first=True)
    # Also grab the "Posted on" date on this page:
    posted = resp.html.find('meta[name="article:published_time"]', first=True)
    if older is not None: # if there's an older version, grab the date
      self.log.record("Previous version detected. Finding date.")
      date_search = re.search('(\w*) (\d*), (\d{4})', older.text)
      if len(date_search.groups()) < 3:
        self.log.record("Could not determine date. Skipping.", "warn")
        return None
      month = date_search.group(1)
      day = date_search.group(2)
      year = date_search.group(3)
      datestring = "{}-{}-{}".format(year, month_to_num(month), day)
      self.log.record("Determined date: {}".format(datestring), "info")
      return datestring
    elif posted is not None: # if not, just grab the date from the current version
      self.log.record("No older version detected; using date from current page: {}".format(posted.attrs['content']), "info")
      return posted.attrs['content']
    else:
      log.record("Could not determine posted date for article at {}".format(url), "warn")

    return None

  def save_article_stats(self, article_id, stats, posted=None):
    # First, delete the most recently fetched month, because it was probably recorded before
    # that month was complete:
    with self.connection.db.cursor() as cursor:
      cursor.execute("SELECT MAX(month) FROM article_traffic WHERE year = 2018 AND article=%s;", (article_id,)) # TODO: don't hardcode the date, good luck
      month = cursor.fetchone()
      if month is not None and len(month) > 0:
        cursor.execute("DELETE FROM article_traffic WHERE year = 2018 AND article=%s AND month = %s", (article_id, month[0]))

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
      sql = "INSERT INTO article_traffic (article, month, year, abstract, pdf) VALUES (%s, %s, %s, %s, %s);"
      params = [(article_id, x[0], x[1], x[2], x[3]) for x in to_record]
      cursor.executemany(sql, params)

      cursor.execute("UPDATE articles SET last_crawled = CURRENT_DATE WHERE id=%s", (article_id,))

      # TODO: once we update the backlog with this info, we can probably clear this part out
      if posted is not None:
        self.log.record("Determined 'posted on' date: {}".format(posted), "debug")
        cursor.execute("UPDATE articles SET posted = %s WHERE id=%s", (posted, article_id))
      self.log.record("Recorded {} stats for ID {}".format(len(to_record), article_id), "debug")

      cursor.execute("SELECT origin_month FROM articles WHERE id=%s", (article_id,))
      paper = cursor.fetchone()
      if len(paper) == 0:
        self.log.record("No origin date recorded for paper; determining.", "info")
        # figure out the earliest date we have traffic, and make that the paper's birthday
        try:
          cursor.execute("SELECT MIN(year) FROM article_traffic WHERE article=%s", (article_id,))
          year = cursor.fetchone()
          if year is not None:
            cursor.execute("SELECT MIN(month) FROM article_traffic WHERE article=%s AND year=%s", (article_id,year))
            month = cursor.fetchone()
            if month is not None:
              cursor.execute("UPDATE articles SET origin_month = %s, origin_year = %s, last_crawled = CURRENT_DATE WHERE id=%s", (month, year, article_id))
        except Exception as e:
          self.log.record("ERROR determining age of article: {}".format(e), "warn")

  def _record_detailed_authors(self, article_id, authors, overwrite=False):
    if overwrite:
      with self.connection.db.cursor() as cursor:
        self.log.record("Marking currently recorded authors for deletion.", "debug")
        # we set the article ID to 0 before deleting them so if the spider dies in
        # between removing the old authors and updating the new ones, we can go in
        # and fix it manually.
        cursor.execute("UPDATE article_detailed_authors SET article=0 WHERE article=%s;", (article_id,))
    else:
      with self.connection.db.cursor() as cursor:
        cursor.execute("SELECT COUNT(article) FROM article_detailed_authors WHERE article=%s;", (article_id,))
        count = cursor.fetchone()[0]
        if count > 0:
          self.log.record("Article authors already recorded; skipping.", "info")
          return

    detailed_author_ids = []
    for a in authors:
      a.record(self.connection, self.log)
      detailed_author_ids.append(a.id)

    try:
      with self.connection.db.cursor() as cursor:
        sql = "INSERT INTO article_detailed_authors (article, author) VALUES (%s, %s);"
        cursor.executemany(sql, [(article_id, x) for x in detailed_author_ids])
    except Exception as e:
      # If there's an error associating all the authors with their paper all at once,
      # send separate queries for each one
      # (This came up last time because an author was listed twice on the same paper.)
      self.log.record("Error associating detailed authors to paper: {}".format(e), "warn")
      self.log.record("Recording article associations one at a time.", "info")
      for x in detailed_author_ids:
        try:
          with self.connection.db.cursor() as cursor:
            cursor.execute("INSERT INTO article_detailed_authors (article, author) VALUES (%s, %s);", (article_id, x))
        except Exception as e:
          self.log.record("Another problem associating detailed author {} to article {}. Moving on.".format(x, article_id), "error")
          pass
    if overwrite:
      # if we marked authors for deletion earlier, it's safe to delete them now.
      self.log.record("Removing outdated authors.", "info")
      cursor.execute("DELETE FROM article_detailed_authors WHERE article=0;")

  def fetch_categories(self):
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
    self.log.record("{} - Starting full ranking process.".format(start))
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
    # if config.perform_ranks["bouncerate"] is not False:
    #   self._rank_articles_bouncerate()
    #   load_rankings_from_file("bounce_ranks", self.log)
    #   self.activate_tables("bounce_ranks")

    if config.perform_ranks["authors"] is not False:
      self._rank_authors_alltime()
      load_rankings_from_file("author_ranks", self.log)
      self.activate_tables("author_ranks")

      self._rank_detailed_authors_alltime()
      load_rankings_from_file("detailed_author_ranks", self.log)
      self.activate_tables("detailed_author_ranks")

    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE author_ranks_category_working")
      cursor.execute("TRUNCATE detailed_author_ranks_category_working")
      cursor.execute("TRUNCATE category_ranks_working")
    for category in self.fetch_categories():
      if config.perform_ranks["article_categories"] is not False:
        self._rank_articles_categories(category)
        load_rankings_from_file("category_ranks", self.log)
      if config.perform_ranks["author_categories"] is not False:
        self._rank_authors_category(category)
        load_rankings_from_file("author_ranks_category", self.log)

        self._rank_detailed_authors_category(category)
        load_rankings_from_file("detailed_author_ranks_category", self.log)
    # we wait until all the categories have been loaded before
    # swapping in the fresh batch
    if config.perform_ranks["article_categories"] is not False:
      self.activate_tables("category_ranks")
    if config.perform_ranks["author_categories"] is not False:
      self.activate_tables("author_ranks_category")
      self.activate_tables("detailed_author_ranks_category")

    self._calculate_download_distributions()
    end = datetime.now()
    self.log.record("{} - Full ranking process complete after {}.".format(end, end-start))

  def activate_tables(self, table):
    self.log.record("Activating tables for {}".format(table))
    queries = [
      "ALTER TABLE {0} RENAME TO {0}_temp".format(table),
      "ALTER TABLE {0}_working RENAME TO {0}".format(table),
      "ALTER TABLE {0}_temp RENAME TO {0}_working".format(table)
    ]
    to_delete = "{}_working.csv".format(table)
    with self.connection.db.cursor() as cursor:
      for query in queries:
        cursor.execute(query)
    if config.delete_csv == True:
      self.log.record("Deleting {}".format(to_delete))
      try:
        os.remove(to_delete)
      except Exception as e:
        self.log.record("Problem deleting {}: {}".format(to_delete, e), "warn")

  def _calculate_download_distributions(self):
    self.log.record("Calculating distribution of download counts with logarithmic scales.")
    tasks = [
      {
        "name": "alltime", # TODO: this should be "papers"
        "scale_power": config.distribution_log_articles
      },
      {
        "name": "author",
        "scale_power": config.distribution_log_authors
      },
    ]
    for task in tasks:
      if task["name"] == "author": # TODO: get rid of this once we're done with the old authors
        table = "detailed_author"
      else:
        table = task["name"]
      results = defaultdict(int)
      self.log.record("Calculating download distributions for {}".format(task["name"]))
      with self.connection.db.cursor() as cursor:
        # first, figure out the biggest bucket:
        cursor.execute("SELECT MAX(downloads) FROM {}_ranks;".format(table))
        biggest = cursor.fetchone()[0]
        # then set up all the empty buckets (so they aren't missing when we draw the graph)
        buckets = [0, task["scale_power"]]
        current = task["scale_power"]
        while True:
          current = current * task["scale_power"]
          buckets.append(current)
          if current > biggest:
            break
        self.log.record("Buckets determined! {} buckets between 0 and {}".format(len(buckets), buckets[-1]))
        for bucket in buckets:
          results[bucket] = 0
        # now fill in the buckets:
        cursor.execute("SELECT downloads FROM {}_ranks ORDER BY downloads ASC;".format(table))
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
        sql = "INSERT INTO download_distribution (bucket, count, category) VALUES (%s, %s, %s);"
        params = [(bucket, count, task["name"]) for bucket, count in results.items()]
        self.log.record("Recording distributions...")
        cursor.executemany(sql, params)

        self.log.record("Calculating median for {}".format(task["name"]))
        if len(values) % 2 == 1:
          median = values[int((len(values) - 1) / 2)]
        else:
          median = (values[int((len(values)/ 2) - 1)] + values[int(len(values)/ 2)]) / 2
        self.log.record("Median is {}".format(median), "debug")
        # HACK: This data doesn't fit in this table. Maybe move to site stats table?
        cursor.execute("DELETE FROM download_distribution WHERE category='{}_median' AND bucket=1".format(task["name"]))
        sql = "INSERT INTO download_distribution (category, bucket, count) VALUES ('{}_median', 1, %s);".format(task["name"])
        cursor.execute(sql, (median,))

        self.log.record("Calculating mean for {}".format(task["name"]))
        total = 0
        for x in values:
          total += x
        mean = total / len(values)
        self.log.record("Mean is {}".format(mean), "debug")
        cursor.execute("DELETE FROM download_distribution WHERE category='{}_mean' AND bucket=1".format(task["name"]))
        sql = "INSERT INTO download_distribution (category, bucket, count) VALUES ('{}_mean', 1, %s);".format(task["name"])
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
    self.log.record("Ranking papers by popularity in category {}...".format(category))
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

  def _rank_articles_bouncerate(self):
    # Ranking articles by the proportion of abstract views to downloads
    self.log.record("Ranking papers by bounce rate...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE bounce_ranks_working")
      # TODO: only calculate ranks for papers with more than some minimum number of downloads
      cursor.execute("SELECT article, CAST (SUM(pdf) AS FLOAT)/SUM(abstract) AS bounce FROM article_traffic GROUP BY article ORDER BY bounce DESC")
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]

    record_ranks_file(params, "bounce_ranks_working")

  def _rank_articles_ytd(self):
    self.log.record("Ranking papers by popularity, year to date...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE ytd_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic WHERE year = 2018 GROUP BY article ORDER BY downloads DESC") # TODO don't hard-code the year
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]

    record_ranks_file(params, "ytd_ranks_working")

  def _rank_articles_month(self):
    self.log.record("Ranking papers by popularity, since last month...")
    with self.connection.db.cursor() as cursor:
      # Determine most recent month
      cursor.execute("SELECT MAX(month) FROM article_traffic WHERE year = 2018;")
      month = cursor.fetchone()
      if month is None or len(month) < 1:
        self.log.record("Could not determine current month.", "error")
        return
      month = month[0] - 1 # "since LAST month" prevents nonsense results early in the current month

    with self.connection.db.cursor() as cursor:
      self.log.record("Ranking articles based on traffic since {}/2018".format(month))
      cursor.execute("TRUNCATE month_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic WHERE year = 2018 AND month >= %s GROUP BY article ORDER BY downloads DESC", (month,)) # TODO don't hard-code the year
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

  def _rank_detailed_authors_alltime(self):
    # NOTE: The main query of this function (three lines down from here)
    # relies on data generated during the spider._rank_articles_alltime()
    # method, so that one should be called first.
    self.log.record("Ranking authors by popularity...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE detailed_author_ranks_working")
      cursor.execute("""
      SELECT article_detailed_authors.author, SUM(alltime_ranks.downloads) as downloads
      FROM article_detailed_authors
      LEFT JOIN alltime_ranks ON article_detailed_authors.article=alltime_ranks.article
      WHERE downloads > 0
      GROUP BY article_detailed_authors.author
      ORDER BY downloads DESC, article_detailed_authors.author DESC
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

    record_ranks_file(params, "detailed_author_ranks_working")

  def _rank_authors_category(self, category):
    self.log.record("Ranking detailed authors by popularity in category {}...".format(category))
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

  def _rank_detailed_authors_category(self, category):
    self.log.record("Ranking detailed authors by popularity in category {}...".format(category))
    with self.connection.db.cursor() as cursor:
      cursor.execute("""
      SELECT article_detailed_authors.author, SUM(alltime_ranks.downloads) as downloads
      FROM article_detailed_authors
      LEFT JOIN alltime_ranks ON article_detailed_authors.article=alltime_ranks.article
      LEFT JOIN articles ON article_detailed_authors.article=articles.id
      WHERE downloads > 0 AND
      articles.collection=%s
      GROUP BY article_detailed_authors.author
      ORDER BY downloads DESC, article_detailed_authors.author DESC
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

    record_ranks_file(params, "detailed_author_ranks_category_working")

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
    # TODO: seems like this thing should be in the Article class maybe?
    with self.connection.db.cursor() as cursor:
      cursor.execute("UPDATE articles SET abstract = %s WHERE id = %s;", (abstract, article_id))
      self.connection.db.commit()
      self.log.record("Recorded abstract for ID {}".format(article_id, abstract), "debug")

  def calculate_vectors(self):
    self.log.record("Calculating vectors...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("UPDATE articles SET title_vector = to_tsvector(coalesce(title,'')) WHERE title_vector IS NULL;")
      cursor.execute("UPDATE articles SET abstract_vector = to_tsvector(coalesce(abstract,'')) WHERE abstract_vector IS NULL;")
      self.connection.db.commit()

  def build_sitemap(self):
    """Utility function used to pull together a list of all pages on the site.
    Not used for day-to-day operations."""
    self.log.record("Building sitemap...")
    filecount = 0
    f = open('sitemaps/sitemap00.txt', 'w')
    with self.connection.db.cursor() as cursor:
      # find abstracts for any articles without them
      cursor.execute("SELECT id FROM articles ORDER BY id;")
      self.log.record("Recording papers.")
      lines = 0
      for a in cursor:
        f.write('https://rxivist.org/papers/{}\n'.format(a[0]))
        lines += 1
        if lines >= 48000:
          lines = 0
          f.close()
          filecount += 1
          append = ""
          if filecount < 10:
            append = "0".format(filecount)
          f = open("sitemaps/sitemap{}{}.txt".format(append, filecount), 'w')
      self.log.record("Papers complete.")
      cursor.execute("SELECT id FROM authors ORDER BY id;")
      self.log.record("Recording authors.")
      for a in cursor:
        f.write('https://rxivist.org/authors/{}\n'.format(a[0]))
        lines += 1
        if lines >= 48000:
          lines = 0
          f.close()
          filecount += 1
          append = ""
          if filecount < 10:
            append = "0".format(filecount)
          f = open("sitemaps/sitemap{}{}.txt".format(append, filecount), 'w')
      self.log.record("Authors complete.")
    f.close()
    self.log.record("Sitemapping complete.")

def load_rankings_from_file(batch, log):
  os.environ["PGPASSWORD"] = config.db["password"]
  to_delete = None
  log.record("Loading {} from file.".format(batch))
  if batch in ["alltime_ranks", "ytd_ranks", "month_ranks"]:
    query = "\copy {0}_working (article, rank, downloads) FROM '{0}_working.csv' with (format csv);".format(batch)
  elif batch == "author_ranks":
    query = "\copy author_ranks_working (author, rank, downloads, tie) FROM 'author_ranks_working.csv' with (format csv);"
  elif batch == "detailed_author_ranks":
    query = "\copy detailed_author_ranks_working (author, rank, downloads, tie) FROM 'detailed_author_ranks_working.csv' with (format csv);"
  elif batch == "author_ranks_category":
    query = "\copy author_ranks_category_working (author, category, rank, downloads, tie) FROM 'author_ranks_category_working.csv' with (format csv);"
    to_delete = "author_ranks_category_working.csv"
  elif batch == "detailed_author_ranks_category":
    query = "\copy detailed_author_ranks_category_working (author, category, rank, downloads, tie) FROM 'detailed_author_ranks_category_working.csv' with (format csv);"
    to_delete = "detailed_author_ranks_category_working.csv"
  elif batch == "category_ranks":
    query = "\copy category_ranks_working (article, rank) FROM 'category_ranks_working.csv' with (format csv);"
    to_delete = "category_ranks_working.csv"
  else:
    log.record("Unrecognized rankings source passed to load_rankings_from_file: {}".format(batch), "warn")
    return # TODO: Should this be an exception?

  subprocess.run(["psql", "-h", config.db["host"], "-U", config.db["user"], "-d", config.db["db"], "-c", query], check=True)
  # Some files get rewritten a bunch of times; if we encounter one of those,
  # delete it before the next iteration starts.
  if to_delete is not None:
    os.remove(to_delete)

def full_run(spider, collection=None):
  if collection is not None:
    spider.find_record_new_articles(collection)
  else:
    spider.log.record("No collection specified, iterating through all known categories.")
    for collection in spider.fetch_categories():
      spider.log.record("\n\nBeginning category {}".format(collection), "info")
      if config.crawl["fetch_new"] is not False:
        spider.find_record_new_articles(collection)
      else:
        spider.log.record("Skipping search for new articles: disabled in configuration file.")

      if config.crawl["refresh_stats"] is not False:
        spider.refresh_article_stats(collection, config.refresh_category_cap)
      else:
        spider.log.record("Skipping refresh of paper download stats: disabled in configuration file.")
  if config.crawl["fetch_abstracts"] is not False:
    spider.fetch_abstracts()
  else:
    spider.log.record("Skipping step to fetch unknown abstracts: disabled in configuration file.")

  if config.crawl["fetch_crossref"] is not False:
    spider.pull_todays_crossref_data()
  else:
    spider.log.record("Skipping call to fetch Crossref data: disabled in configuration file.")

  spider.calculate_vectors()

  if config.perform_ranks["enabled"] is not False:
    spider.process_rankings()
  else:
    spider.log.record("Skipping all ranking steps: disabled in configuration file.")

# helper method to fill in newly added field author_vector
def fill_in_author_vectors(spider):
  spider.log.record("Filling in empty author_vector fields for all articles.")
  article_ids = []
  with spider.connection.db.cursor() as cursor:
    cursor.execute("SELECT id FROM articles WHERE author_vector IS NULL;")
    for record in cursor:
      if len(record) > 0:
        article_ids.append(record[0])

  to_do = len(article_ids)
  spider.log.record("Obtained {} article IDs.".format(to_do))
  with spider.connection.db.cursor() as cursor:
    for article in article_ids:
      author_string = ""
      cursor.execute("SELECT authors.given, authors.surname FROM article_authors as aa INNER JOIN authors ON authors.id=aa.author WHERE aa.article=%s;", (article,))
      for record in cursor:
        author_string += "{} {}, ".format(record[0], record[1])
      cursor.execute("UPDATE articles SET author_vector=to_tsvector(coalesce(%s,'')) WHERE id=%s;", (author_string, article))
      to_do -= 1
      if to_do % 100 == 0:
        spider.log.record("{} - {} left to go.".format(datetime.now(), to_do))

def find_detailed_authors(response):
  # Determine author details:
  detailed_authors = []
  author_tags = response.html.find('meta[name^="citation_author"]')
  current_name = ""
  current_institution = ""
  current_email = ""
  current_orcid = ""
  for tag in author_tags:
    if tag.attrs["name"] == "citation_author":
      if current_name != "": # if this isn't the first author
        detailed_authors.append(models.DetailedAuthor(current_name, current_institution, current_email, current_orcid))
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
    detailed_authors.append(models.DetailedAuthor(current_name, current_institution, current_email, current_orcid))

  return detailed_authors

def month_to_num(month):
  # helper for converting month names (string) to numbers (int)
  if len(month) > 3: # if it's the full name, truncate it
    month = month[:3]
  months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  months_to_num = dict(zip(months, range(1,13)))
  return months_to_num[month]

if __name__ == "__main__":
  spider = Spider()
  if len(sys.argv) == 1: # if no action is specified, do everything
    full_run(spider)
  elif sys.argv[1] == "rankings":
    spider.process_rankings()
  elif sys.argv[1] == "traffic":
    if len(sys.argv) > 2:
      spider.refresh_article_stats(sys.argv[2])
    else:
      spider.log.record("Must specify collection to refresh traffic stats for.", "fatal")
  elif sys.argv[1] == "distro":
    spider._calculate_download_distributions()
  elif sys.argv[1] == "crossref":
    if len(sys.argv) > 2:
      spider._pull_crossref_data_date(sys.argv[2])
    else:
      spider.pull_todays_crossref_data()
  elif sys.argv[1] == "authorvector":
    fill_in_author_vectors(spider)
  elif sys.argv[1] == "sitemap":
    spider.build_sitemap()
  elif sys.argv[1] == "test": # placeholder for temporary commands
    spider._pull_crossref_data("2018-09-27")
  else:
    full_run(spider, sys.argv[1])
