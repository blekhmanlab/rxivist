from collections import defaultdict
from datetime import datetime
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

import db
import config

class Author(object):
  def __init__(self, given, surname):
    self.given = given
    self.surname = surname

  def name(self):
    if self.surname != "":
      if self.given != "":
        return "{} {}".format(self.given, self.surname)
      return self.surname
    return self.given

  def record(self, connection):
    with connection.db.cursor() as cursor:
      cursor.execute("SELECT id FROM authors WHERE given = %s and surname = %s;", (self.given, self.surname))
      a_id = cursor.fetchone()
      if a_id is not None:
        self.id = a_id[0]
        print("Author {} exists with ID {}".format(self.name(), self.id))
        return
      cursor.execute("INSERT INTO authors (given, surname) VALUES (%s, %s) RETURNING id;", (self.given, self.surname))
      self.id = cursor.fetchone()[0]
      connection.db.commit()
      print("Recorded author {} with ID {}".format(self.name(), self.id))

class Article(object):
  def __init__(self):
    pass

  def process_results_entry(self, html, collection):
    self._find_title(html)
    self._find_url(html)
    self._find_authors(html)
    self._find_doi(html)
    self.collection = collection
    # NOTE: We don't get abstracts from search result pages
    # because they're loaded asynchronously and it would be
    # annoying to load every one separately.

  def _find_title(self, html):
    x = html.find(".highwire-cite-title")
    # this looks weird because the title is wrapped
    # in 2 <span> tags with identical classes:
    self.title = x[0].text

  def _find_doi(self, html):
    x = html.find(".highwire-cite-metadata-doi")
    if len(x) == 0:
      return
    try:
      m = re.search('https://doi.org/(.*)', x[0].text)
    except:
      return
    if len(m.groups()) > 0:
      self.doi = m.group(1)

  def _find_url(self, html):
    self.url = html.absolute_links.pop() # absolute_links is a set

  def _find_authors(self, html):
    entries = html.find(".highwire-citation-author")
    self.authors = []
    for entry in entries:
      first = ""
      last = ""
      # Sometimes an author's name is actually the name of a group of collaborators
      if(len(entry.find(".nlm-collab")) > 0):
        first = entry.find(".nlm-collab")[0].text
      else:
        if len(entry.find(".nlm-given-names")) > 0:
          first = entry.find(".nlm-given-names")[0].text
        if len(entry.find(".nlm-surname")) > 0:
          last = entry.find(".nlm-surname")[0].text
      if (first != "") or (last != ""): # if we have a name at all
        self.authors.append(Author(first, last))
      else:
        print("\n\n\nNOT adding author to list: {} {}".format(first, last))

  def record(self, connection, spider):
    with connection.db.cursor() as cursor:
      # check to see if we've seen this article before
      responses = []
      cursor.execute("SELECT url FROM articles WHERE doi=%s", (self.doi,))
      for x in cursor: # TODO: Look at using cursor.fetchone() here
        responses.append(x)
      if len(responses) > 0 and len(responses[0]) > 0:
        if responses[0][0] == self.url:
          print("Found article already: {}".format(self.title))
          connection.db.commit()
          return False
        else:
          cursor.execute("UPDATE articles SET url=%s, title=%s, collection=%s WHERE doi=%s RETURNING id;", (self.url, self.title, self.collection, self.doi))
          print("Updated revision for article DOI {}: {}".format(self.doi, self.title))
          connection.db.commit()
          return True
    # If it's brand new:
    with connection.db.cursor() as cursor:
      try:
        cursor.execute("INSERT INTO articles (url, title, doi, collection) VALUES (%s, %s, %s, %s) RETURNING id;", (self.url, self.title, self.doi, self.collection))
      finally:
        connection.db.commit() # Needed to end the botched transaction TODO (this may not be true with autocommit now)
      self.id = cursor.fetchone()[0]

      author_ids, author_string = self._record_authors(connection)
      self._link_authors(author_ids, connection)

      cursor.execute("UPDATE articles SET author_vector=to_tsvector(coalesce(%s,'')) WHERE id=%s;", (author_string, self.id))
      print("Recorded article {}".format(self.title))

      # fetch traffic stats for the new article
      # TODO: this should be a method for Article, not Spider
      print("Recording stats for new article:")
      stat_table = None
      try:
        stat_table = spider.get_article_stats(self.url)
      except Exception as e:
        print("Error fetching stats. Trying one more time...")
      try:
        stat_table = spider.get_article_stats(self.url)
      except Exception as e:
        print("Error fetching stats again. Giving up on this one.")

      if stat_table is not None:
        spider.save_article_stats(self.id, stat_table)
    return True

  def _record_authors(self, connection):
    author_ids = []
    author_string = "" # For calculating a searchable vector
    for a in self.authors:
      author_string += "{}, ".format(a.name())
      a.record(connection)
      author_ids.append(a.id)

    return (author_ids, author_string)

  def _link_authors(self, author_ids, connection):
    try:
      with connection.db.cursor() as cursor:
        sql = "INSERT INTO article_authors (article, author) VALUES (%s, %s);"
        cursor.executemany(sql, [(self.id, x) for x in author_ids])
        connection.db.commit()
    except Exception as e:
      # If there's an error associating all the authors with their paper all at once,
      # send separate queries for each one
      # (This came up last time because an author was listed twice on the same paper.)
      print("ERROR associating authors to paper: {}".format(e))
      print("Recording article associations one at a time.")
      for x in author_ids:
        try:
          with connection.db.cursor() as cursor:
            cursor.execute("INSERT INTO article_authors (article, author) VALUES (%s, %s);", (self.id, x))
            connection.db.commit()
        except Exception as e:
          print("ERROR: Another problem associating author {} to article {}. Moving on.".format(x, self.id))
          pass

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

def pull_out_articles(html, collection):
  entries = html.find(".highwire-article-citation")
  articles = []
  for entry in entries:
    a = Article()
    a.process_results_entry(entry, collection)
    articles.append(a)
  return articles

def record_ranks_db(to_record, sql, db):
  print("Recording {} entries...".format(len(to_record)))
  start = 0
  interval = config.progress_update_interval
  db.set_session(autocommit=False)
  with db.cursor() as cursor:
    while True:
      end = start + interval if start + interval < len(to_record) else len(to_record)
      print("{} Recording ranks {} through {}.".format(datetime.now(), start, end-1))
      cursor.executemany(sql, to_record[start:end])
      if end == len(to_record):
        break
      start += interval
  db.commit()
  db.set_session(autocommit=True)

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
    self.session.headers['User-Agent'] = "rxivist web crawler (rxivist.org)"

  def pull_altmetric_data(self):
    headers = {'user-agent': 'rxivist web crawler (rxivist.org)'}
    print("Removing earlier data from same day")
    # (If we have multiple results for the same 24-hour period, the
    # query that displays the most popular displays the same articles
    # multiple times, and the aggregation function to clean that up
    # would be too complicated to bother with right now.)
    with self.connection.db.cursor() as cursor:
      cursor.execute("DELETE FROM altmetric_daily WHERE crawled > now() - interval '1 days';")
    print("Fetching Altmetric data")
    r = requests.get("https://api.altmetric.com/v1/citations/1d?num_results=100&doi_prefix=10.1101&page=1", headers=headers)
    if r.status_code != 200:
      print("ERROR: Got weird status code: {}. {}".format(r.status_code, r.text()))
      return
    results = r.json()
    result_count = 1
    if "query" in results.keys() and "total" in results["query"]:
      result_count = results["query"]["total"]
    last_page = math.ceil(result_count / 100)
    print("Total results are {}, meaning {} pages".format(result_count, last_page))
    for page in range(1, last_page + 1):
      found = 0
      time.sleep(1) # 1 per second limit
      print("Fetching page {}".format(page))
      # TODO: Validate that DOI prefix 10.1101 is bioRxiv, and that we won't miss
      # papers that somehow get another prefix.
      try:
        r = requests.get("https://api.altmetric.com/v1/citations/1d?num_results=100&doi_prefix=10.1101&page={}".format(page), headers=headers)
        results = r.json()
      except json.decoder.JSONDecodeError:
        print("Error encountered; bailing.")
        break
      for result in results["results"]:
        if "doi" not in result.keys():
          continue
        with self.connection.db.cursor() as cursor:
          cursor.execute("SELECT id FROM articles WHERE doi=%s;", (result["doi"],))
          article_id = cursor.fetchone()
          if article_id is None or len(article_id) == 0: # if we don't know about the article that was mentioned, bail
            continue
          article_id = article_id[0]
          found += 1
          sql = "INSERT INTO altmetric_daily (article, score, day_score, week_score, tweets, altmetric_id) VALUES (%s, %s, %s, %s, %s, %s);"
          score = result.get("score", 0)
          day_score = result["history"].get("1d", 0)
          week_score = result["history"].get("1w", 0)
          tweets = result.get("cited_by_tweeters_count", 0)
          altmetric_id = result.get("altmetric_id", 0)
          cursor.execute(sql, (article_id, score, day_score, week_score, tweets, altmetric_id))
      print("Recorded {} recognized articles on page".format(found))

  def find_record_new_articles(self, collection):
    # we need to grab the first page to figure out how many pages there are
    print("\n---\n\nFetching page 0 in {}".format(collection))
    r = self.session.get("https://www.biorxiv.org/collection/{}".format(collection))
    results = pull_out_articles(r.html, collection)
    consecutive_recognized = 0
    for x in results:
      if not x.record(self.connection, self): # TODO: don't pass the whole damn spider here
        consecutive_recognized += 1
        if consecutive_recognized >= config.recognized_limit and config.stop_on_recognized: return
      else:
        consecutive_recognized = 0

    pagecount = config.testing_pagecount if config.TESTING else determine_page_count(r.html) # Also just for testing TODO delete
    for p in range(1, pagecount): # iterate through pages
      if config.polite:
        time.sleep(3)
      print("\n---\n\nFetching page {} in {}".format(p, collection)) # pages are zero-indexed
      r = self.session.get("https://www.biorxiv.org/collection/{}?page={}".format(collection, p))
      results = pull_out_articles(r.html, collection)
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
        abstract = self.get_article_abstract(url)
        if abstract: self.update_article(article_id, abstract)

  def refresh_article_stats(self, collection, cap=100000):
    print("Refreshing article download stats for collection {}...".format(collection))
    print(cap)
    with self.connection.db.cursor() as cursor:
      cursor.execute("SELECT id, url FROM articles WHERE collection=%s AND last_crawled < now() - interval '3 weeks';", (collection,))
      updated = 0
      for article in cursor:
        if config.polite:
          time.sleep(1)
        url = article[1]
        article_id = article[0]
        stat_table = self.get_article_stats(url)
        self.save_article_stats(article_id, stat_table)
        updated += 1
        if updated >= cap:
          print("Maximum articles reached for this session. Returning.")
          break
    print("{} articles refreshed in {}.".format(updated, collection))
    return updated

  def get_article_abstract(self, url, retry=True):
    if config.polite:
      time.sleep(1)
    try:
      resp = self.session.get(url)
    except Exception as e:
      print("Error fetching abstract: {}".format(e))
      if retry:
        print("Retrying:")
        time.sleep(3)
        return self.get_article_abstract(url, False)
      else:
        print("Giving up on this one for now.")
        return False # TODO: this should be an exception
    abstract = resp.html.find("#p-2")
    if len(abstract) < 1:
      return False # TODO: this should be an exception
    return abstract[0].text

  def get_article_stats(self, url):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    months_to_num = dict(zip(months, range(1,13)))
    resp = self.session.get("{}.article-metrics".format(url))
    entries = iter(resp.html.find("td"))
    stats = []
    for entry in entries:
      date = entry.text.split(" ")
      month = months_to_num[date[0]]
      year = int(date[1])
      abstract = int(next(entries).text)
      pdf = int(next(entries).text)
      stats.append((month, year, abstract, pdf))
    return stats

  def save_article_stats(self, article_id, stats):
    # First, delete the most recently fetched month, because it was probably recorded before
    # that month was complete:
    with self.connection.db.cursor() as cursor:
      cursor.execute("SELECT MAX(month) FROM article_traffic WHERE year = 2018 AND article=%s;", (article_id,))
      month = cursor.fetchone()
      if month is not None and len(month) > 0:
        month = month[0]
        cursor.execute("DELETE FROM article_traffic WHERE year = 2018 AND article=%s AND month = %s", (article_id, month))
    with self.connection.db.cursor() as cursor:
      # we check for which ones are already recorded because
      # the postgres UPSERT feature is bananas
      cursor.execute("SELECT month, year FROM article_traffic WHERE article=%s", (article_id,))
      # associate each year with which months are already recorded
      done = defaultdict(lambda: [])
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

      # figure out the earliest date
      try:
        # TODO: Should this be run every time we get traffic? No, right?
        cursor.execute("SELECT MIN(year) FROM article_traffic WHERE article=%s", (article_id,))
        year = cursor.fetchone()
        recorded = False
        if year is not None:
          cursor.execute("SELECT MIN(month) FROM article_traffic WHERE article=%s AND year=%s", (article_id,year))
          month = cursor.fetchone()
          if month is not None:
            cursor.execute("UPDATE articles SET origin_month = %s, origin_year = %s, last_crawled = CURRENT_DATE WHERE id=%s", (month, year, article_id))
            recorded = True
        if not recorded:
          cursor.execute("UPDATE articles SET last_crawled = CURRENT_DATE WHERE id=%s", (article_id,))
      except Exception as e:
        print("ERROR determining age of article: {}".format(e))
      finally:
        self.connection.db.commit()
      print("Recorded {} stats for ID {}".format(len(to_record), article_id))

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
    print("{} - Starting full ranking process.".format(start))
    self._rank_articles_alltime()
    self._rank_articles_ytd()
    self._rank_articles_month()
    self._rank_articles_bouncerate()

    load_rankings_from_files("all_articles")
    self.activate_tables("alltime_ranks")
    self.activate_tables("ytd_ranks")
    self.activate_tables("month_ranks")

    self._rank_authors_alltime()
    load_rankings_from_files("all_authors")
    self.activate_tables("author_ranks")

    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE author_ranks_category_working")
      cursor.execute("TRUNCATE category_ranks_working")
    for category in self.fetch_categories():
      self._rank_articles_categories(category)
      load_rankings_from_files("category_articles")
      self._rank_authors_category(category)
      load_rankings_from_files("category_authors")
    # we wait until all the categories have been loaded before
    # swapping in the fresh batch
    self.activate_tables("category_ranks")
    self.activate_tables("author_ranks_category")

    self._calculate_download_distributions()
    end = datetime.now()
    print("{} - Full ranking process complete after {}.".format(end, end-start))

  def activate_tables(self, table):
    print("Activating tables for {}".format(table))
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
      print("Deleting {}".format(to_delete))
      try:
        os.remove(to_delete)
      except Exception as e:
        print("Problem deleting {}: {}".format(to_delete, e))

  def _calculate_download_distributions(self):
    print("Calculating distribution of download counts with logarithmic scales.")
    tasks = [
      {
        "name": "alltime",
        "scale_power": 1.5
      },
      {
        "name": "author",
        "scale_power": 1.5
      },
    ]
    for task in tasks:
      results = defaultdict(int)
      print("Calculating download distributions for {}".format(task["name"]))
      with self.connection.db.cursor() as cursor:
        # first, figure out the biggest bucket:
        cursor.execute("SELECT MAX(downloads) FROM {}_ranks;".format(task["name"]))
        biggest = cursor.fetchone()[0]
        # then set up all the empty buckets (so they aren't missing when we draw the graph)
        buckets = [0, task["scale_power"]]
        current = task["scale_power"]
        while True:
          current = current * task["scale_power"]
          buckets.append(current)
          if current > biggest:
            break
        print("Buckets determined! {} buckets between 0 and {}".format(len(buckets), buckets[-1]))
        for bucket in buckets:
          results[bucket] = 0
        # now fill in the buckets:
        cursor.execute("SELECT downloads FROM {}_ranks ORDER BY downloads ASC;".format(task["name"]))
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
        print("Recording...")
        cursor.executemany(sql, params)

        print("Calculating median for {}".format(task["name"]))
        if len(values) % 2 == 1:
          median = values[int((len(values) - 1) / 2)]
        else:
          median = (values[int((len(values)/ 2) - 1)] + values[int(len(values)/ 2)]) / 2
        print("Median is {}".format(median))
        # HACK: This data doesn't fit in this table. Maybe move to site stats table?
        cursor.execute("DELETE FROM download_distribution WHERE category='{}_median' AND bucket=1".format(task["name"]))
        sql = "INSERT INTO download_distribution (category, bucket, count) VALUES ('{}_median', 1, %s);".format(task["name"])
        cursor.execute(sql, (median,))

        print("Calculating mean for {}".format(task["name"]))
        total = 0
        for x in values:
          total += x
        mean = total / len(values)
        print("Mean is {}".format(mean))
        cursor.execute("DELETE FROM download_distribution WHERE category='{}_mean' AND bucket=1".format(task["name"]))
        sql = "INSERT INTO download_distribution (category, bucket, count) VALUES ('{}_mean', 1, %s);".format(task["name"])
        cursor.execute(sql, (mean,))

  def _rank_articles_alltime(self):
    print("Ranking papers by popularity...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE alltime_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic GROUP BY article ORDER BY downloads DESC")
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]
    print("Retrieved download data.")
    record_ranks_file(params, "alltime_ranks_working")

  def _rank_articles_categories(self, category):
    print("Ranking papers by popularity in category {}...".format(category))
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
    print("Ranking papers by bounce rate...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE bounce_ranks_working")
      # TODO: only calculate ranks for papers with more than some minimum number of downloads
      cursor.execute("SELECT article, CAST (SUM(pdf) AS FLOAT)/SUM(abstract) AS bounce FROM article_traffic GROUP BY article ORDER BY bounce DESC")
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]

    record_ranks_file(params, "bounce_ranks_working")

  def _rank_articles_ytd(self):
    print("Ranking papers by popularity, year to date...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE ytd_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic WHERE year = 2018 GROUP BY article ORDER BY downloads DESC") # TODO don't hard-code the year
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]

    record_ranks_file(params, "ytd_ranks_working")

  def _rank_articles_month(self):
    print("Ranking papers by popularity, since last month...")
    with self.connection.db.cursor() as cursor:
      # Determine most recent month
      cursor.execute("SELECT MAX(month) FROM article_traffic WHERE year = 2018;")
      month = cursor.fetchone()
      if month is None or len(month) < 1:
        print("**WARNING: Could not determine current month**")
        return
      month = month[0] - 1 # "since LAST month" prevents nonsense results early in the current month

    with self.connection.db.cursor() as cursor:
      print("Ranking articles based on traffic since {}/2018".format(month))
      cursor.execute("TRUNCATE month_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic WHERE year = 2018 AND month >= %s GROUP BY article ORDER BY downloads DESC", (month,)) # TODO don't hard-code the year
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]

    record_ranks_file(params, "month_ranks_working")

  def _rank_authors_alltime(self):
    # NOTE: The main query of this function (three lines down from here)
    # relies on data generated during the spider._rank_articles_alltime()
    # method, so that one should be called first.
    print("Ranking authors by popularity...")
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
      print("Retrieved download data.")
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
    print("Ranking authors by popularity, category {}...".format(category))
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
      """, (category,)) # NOTE: This used to have a "LIMIT 10000" on it, consider putting it back
      print("Retrieved download data for category {}.".format(category))
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

  def update_article(self, article_id, abstract):
    # TODO: seems like this thing should be in the Article class maybe?
    with self.connection.db.cursor() as cursor:
      cursor.execute("UPDATE articles SET abstract = %s WHERE id = %s;", (abstract, article_id))
      self.connection.db.commit()
      print("Recorded abstract for ID {}".format(article_id, abstract))

  def calculate_vectors(self):
    print("Calculating vectors...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("UPDATE articles SET title_vector = to_tsvector(coalesce(title,'')) WHERE title_vector IS NULL;")
      cursor.execute("UPDATE articles SET abstract_vector = to_tsvector(coalesce(abstract,'')) WHERE abstract_vector IS NULL;")
      self.connection.db.commit()

  def build_sitemap(self):
    print("Building sitemap...")
    filecount = 0
    f = open('sitemaps/sitemap00.txt', 'w')
    with self.connection.db.cursor() as cursor:
      # find abstracts for any articles without them
      cursor.execute("SELECT id FROM articles ORDER BY id;")
      print("Recording papers.")
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
      print("Papers complete.")
      cursor.execute("SELECT id FROM authors ORDER BY id;")
      print("Recording authors.")
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
      print("Authors complete.")
    f.close()
    print("Sitemapping complete.")

def load_rankings_from_files(batch):
  os.environ["PGPASSWORD"] = config.db["password"]
  to_delete = None
  if batch == "all_articles":
    print("Loading alltime_ranks from file.")
    queries = [
      "\copy alltime_ranks_working (article, rank, downloads) FROM 'alltime_ranks_working.csv' with (format csv);",
      "\copy ytd_ranks_working (article, rank, downloads) FROM 'ytd_ranks_working.csv' with (format csv);",
      "\copy month_ranks_working (article, rank, downloads) FROM 'month_ranks_working.csv' with (format csv);"
    ]
  elif batch == "all_authors":
    queries = [
      "\copy author_ranks_working (author, rank, downloads, tie) FROM 'author_ranks_working.csv' with (format csv);",
    ]
  elif batch == "category_authors":
    queries = [
      "\copy author_ranks_category_working (author, category, rank, downloads, tie) FROM 'author_ranks_category_working.csv' with (format csv);",
    ]
    to_delete = "author_ranks_category_working.csv"
  elif batch == "category_articles":
    queries = [
      "\copy category_ranks_working (article, rank) FROM 'category_ranks_working.csv' with (format csv);",
    ]
    to_delete = "category_ranks_working.csv"
  for query in queries:
    subprocess.run(["psql", "-h", config.db["host"], "-U", config.db["user"], "-d", config.db["db"], "-c", query], check=True)
  # Some files get rewritten a bunch of times; if we encounter one of those,
  # delete it before the next iteration starts.
  if to_delete is not None:
    os.remove(to_delete)


def full_run(spider, collection=None):
  if collection is not None:
    spider.find_record_new_articles(collection)
  else:
    print("No collection specified, iterating through all known categories.")
    refreshed = 0
    for collection in spider.fetch_categories():
      spider.find_record_new_articles(collection)
      if config.limit_refresh:
        if refreshed < config.refresh_session_cap:
          refreshed += spider.refresh_article_stats(collection, config.refresh_session_cap - refreshed)
      else:
        spider.refresh_article_stats(collection) # TODO: There's probably a more succinct way to do this rather than two different calls to refresh_article_stats
  spider.fetch_abstracts()
  spider.pull_altmetric_data()

  spider.calculate_vectors()
  spider.process_rankings()

# helper method to fill in newly added field author_vector
def fill_in_author_vectors(spider):
  print("Filling in empty author_vector fields for all articles.")
  article_ids = []
  with spider.connection.db.cursor() as cursor:
    cursor.execute("SELECT id FROM articles WHERE author_vector IS NULL;")
    for record in cursor:
      if len(record) > 0:
        article_ids.append(record[0])

  to_do = len(article_ids)
  print("Obtained {} article IDs.".format(to_do))
  with spider.connection.db.cursor() as cursor:
    for article in article_ids:
      author_string = ""
      cursor.execute("SELECT authors.given, authors.surname FROM article_authors as aa INNER JOIN authors ON authors.id=aa.author WHERE aa.article=%s;", (article,))
      for record in cursor:
        author_string += "{} {}, ".format(record[0], record[1])
      cursor.execute("UPDATE articles SET author_vector=to_tsvector(coalesce(%s,'')) WHERE id=%s;", (author_string, article))
      to_do -= 1
      if to_do % 100 == 0:
        print("{} - {} left to go.".format(datetime.now(), to_do))

def concat_abstracts(spider):
  done = 0
  with spider.connection.db.cursor() as cursor, open('abstracts.txt', 'w') as f:
    cursor.execute("SELECT abstract FROM articles;")
    for record in cursor:
      f.write('{}\n'.format(record[0]))
      done += 1
      if done % 10000 == 0:
        print("DONE {} so far".format(done))

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
      print("Must specify collection to refresh traffic stats for.")
  elif sys.argv[1] == "distro":
    spider._calculate_download_distributions()
  elif sys.argv[1] == "altmetric":
    spider.pull_altmetric_data()
  elif sys.argv[1] == "authorvector":
    fill_in_author_vectors(spider)
  elif sys.argv[1] == "sitemap":
    spider.build_sitemap()
  elif sys.argv[1] == "test": # placeholder for temporary commands
    spider._rank_articles_alltime()
  else:
    full_run(spider, sys.argv[1])
