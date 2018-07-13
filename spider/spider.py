import re
from collections import defaultdict
import sys

from requests_html import HTMLSession
import psycopg2

import db
import config

TESTING = True    # this is just for testing, so we don't crawl the whole site during development TODO delete

class Author(object):
  def __init__(self, given, surname):
    self.given = given
    self.surname = surname

  def name(self):
    if self.surname != "":
      return "{} {}".format(self.given, self.surname)
    else: # if author only has one name
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
    
  def process_results_entry(self, html):
    self._find_title(html)
    self._find_url(html)
    self._find_authors(html)
    # NOTE: We don't get abstracts from search result pages
    # because they're loaded asynchronously and it would be
    # annoying to load every one separately.

  def _find_title(self, html):
    x = html.find(".highwire-cite-title")
    # this looks weird because the title is wrapped
    # in 2 <span> tags with identical classes:
    self.title = x[0].text

  def _find_url(self, html):
    self.url = html.absolute_links.pop() # absolute_links is a set

  def _find_authors(self, html):
    entries = html.find(".highwire-citation-author")
    self.authors = []
    for entry in entries:
      # Sometimes an author's name is actually the name of a group of collaborators
      if(len(entry.find(".nlm-collab")) > 0):
        first = entry.find(".nlm-collab")[0].text
        last = ""
      else:
        first = entry.find(".nlm-given-names")[0].text
        last = entry.find(".nlm-surname")[0].text
      self.authors.append(Author(first, last))

  def record(self, connection):
    with connection.db.cursor() as cursor:
      try:
        cursor.execute("INSERT INTO articles (url, title) VALUES (%s, %s) RETURNING id;", (self.url, self.title))
      except psycopg2.IntegrityError as err:
        if repr(err).find('duplicate key value violates unique constraint "articles_pkey"', 1):
          print("Found article already: {}".format(self.title))
          return False
        else:
          raise
      finally:
        connection.db.commit() # Needed to end the botched transaction
      self.id = cursor.fetchone()[0]

      author_ids = self._record_authors(connection)
      self._link_authors(author_ids, connection)
      print("Recorded article {}".format(self.title))
    return True
  
  def _record_authors(self, connection):
    author_ids = []
    for a in self.authors:
      a.record(connection)
      author_ids.append(a.id)
    return author_ids
  
  def _link_authors(self, author_ids, connection):
    with connection.db.cursor() as cursor:
      sql = "INSERT INTO article_authors (article, author) VALUES (%s, %s) RETURNING id;"
      cursor.executemany(sql, [(self.id, x) for x in author_ids])
      connection.db.commit()

def determine_page_count(html):
  # takes a biorxiv results page and
  # finds the highest page number listed
  return int(html.find(".pager-last")[0].text)

def pull_out_articles(html):
  entries = html.find(".highwire-article-citation")
  articles = []
  for entry in entries:
    a = Article()
    a.process_results_entry(entry)
    articles.append(a)
  return articles

class Spider(object):
  def __init__(self):
    self.connection = db.Connection(config.db["host"], config.db["user"], config.db["password"])
    self.session = HTMLSession(mock_browser=False)
    self.session.headers['User-Agent'] = "rxivist web crawler (rxivist.org)"

  def find_record_new_articles(self, collection="bioinformatics"):
    # we need to grab the first page to figure out how many pages there are
    r = self.session.get("https://www.biorxiv.org/collection/{}".format(collection))
    results = pull_out_articles(r.html)
    keep_going = self.record_articles(results)
    if not keep_going: return # if we already knew about the first entry, we're done

    pagecount = 50 if TESTING else determine_page_count(r.html) # Also just for testing TODO delete
    for p in range(1, pagecount): # iterate through pages
      r = self.session.get("https://www.biorxiv.org/collection/{}?page={}".format(collection, p))
      results = pull_out_articles(r.html)
      keep_going = self.record_articles(results)
      if not keep_going: break # If we encounter a recognized article, we're done

  def refresh_article_details(self):
    print("Refreshing article details...")
    with self.connection.db.cursor() as cursor:
      # find abstracts for any articles without them
      cursor.execute("SELECT id, url FROM articles WHERE abstract IS NULL;")
      for article in cursor:
        url = article[1]
        article_id = article[0]
        abstract = self.get_article_abstract(url)
        if abstract: self.update_article(article_id, abstract)

      # fetch updated stats for everything
      cursor.execute("SELECT id, url FROM articles;") # TODO: Add "where" clause based on date
      for article in cursor:
        url = article[1]
        article_id = article[0]
        stat_table = self.get_article_stats(url)
        self.save_article_stats(article_id, stat_table)

  def get_article_abstract(self, url):
    resp = self.session.get(url)
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
    with self.connection.db.cursor() as cursor:
      # we check for which ones are already recorded because
      # the postgres UPSERT feature is bananas
      cursor.execute("SELECT month, year FROM article_traffic WHERE article=%s", (article_id,))
      # associate each year with which months are already recorded
      done = defaultdict(lambda: [])
      for record in cursor:
        print(record[0], record[1])
        done[record[1]].append(record[0])
      # make a list that excludes the records we already know about
      to_record = []
      for i, record in enumerate(stats):
        print(record)
        month = record[0]
        year = record[1]
        if year in done.keys() and month in done[year]:
          print("Found, not recording")
        else:
          to_record.append(record)
      # save the remaining ones in the DB
      sql = "INSERT INTO article_traffic (article, month, year, abstract, pdf) VALUES (%s, %s, %s, %s, %s);"
      params = [(article_id, x[0], x[1], x[2], x[3]) for x in to_record]
      cursor.executemany(sql, params)
      print("Recorded {} stats for ID {}".format(cursor.rowcount, article_id))
      self.connection.db.commit()

  def rank_articles(self):
    # pulls together all the separate ranking calls
    # self._rank_articles_alltime()
    self._rank_articles_ytd()
    # self._rank_articles_bouncerate()

  def _rank_articles_alltime(self):
    print("Ranking papers by popularity...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE alltime_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic GROUP BY article ORDER BY downloads DESC") # LIMIT 50")
      sql = "INSERT INTO alltime_ranks_working (article, rank, downloads) VALUES (%s, %s, %s);"
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]
      cursor.executemany(sql, params)
      self.connection.db.commit()

      # once it's all done, shuffle the tables around so the new results are active
      cursor.execute("ALTER TABLE alltime_ranks RENAME TO alltime_ranks_temp")
      cursor.execute("ALTER TABLE alltime_ranks_working RENAME TO alltime_ranks")
      cursor.execute("ALTER TABLE alltime_ranks_temp RENAME TO alltime_ranks_working")
      self.connection.db.commit()
  
  def _rank_articles_bouncerate(self):
    # Ranking articles by the proportion of abstract views to downloads
    print("Ranking papers by bounce rate...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE bounce_ranks_working")
      # TODO: only calculate ranks for papers with more than some minimum number of downloads
      cursor.execute("SELECT article, CAST (SUM(pdf) AS FLOAT)/SUM(abstract) AS bounce FROM article_traffic GROUP BY article ORDER BY bounce DESC")
      sql = "INSERT INTO bounce_ranks_working (article, rank, rate) VALUES (%s, %s, %s);"
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]
      cursor.executemany(sql, params)
      self.connection.db.commit()

      # once it's all done, shuffle the tables around so the new results are active
      cursor.execute("ALTER TABLE bounce_ranks RENAME TO bounce_ranks_temp")
      cursor.execute("ALTER TABLE bounce_ranks_working RENAME TO bounce_ranks")
      cursor.execute("ALTER TABLE bounce_ranks_temp RENAME TO bounce_ranks_working")
      self.connection.db.commit()

  def _rank_articles_ytd(self):
    print("Ranking papers by popularity, year to date...")
    with self.connection.db.cursor() as cursor:
      cursor.execute("TRUNCATE ytd_ranks_working")
      cursor.execute("SELECT article, SUM(pdf) as downloads FROM article_traffic WHERE year = 2018 GROUP BY article ORDER BY downloads DESC") # LIMIT 50")
      sql = "INSERT INTO ytd_ranks_working (article, rank, downloads) VALUES (%s, %s, %s);"
      params = [(record[0], rank, record[1]) for rank, record in enumerate(cursor, start=1)]
      cursor.executemany(sql, params)
      self.connection.db.commit()

      # once it's all done, shuffle the tables around so the new results are active
      cursor.execute("ALTER TABLE ytd_ranks RENAME TO ytd_ranks_temp")
      cursor.execute("ALTER TABLE ytd_ranks_working RENAME TO ytd_ranks")
      cursor.execute("ALTER TABLE ytd_ranks_temp RENAME TO ytd_ranks_working")
      self.connection.db.commit()

  def update_article(self, article_id, abstract):
    # TODO: seems like this thing should be in the Article class maybe?
    with self.connection.db.cursor() as cursor:
      cursor.execute("UPDATE articles SET abstract = %s WHERE id = %s;", (abstract, article_id))
      self.connection.db.commit()
      print("Recorded abstract for ID {}".format(article_id, abstract))

  def record_articles(self, articles):
    # return value is whether we encountered any articles we had already
    for x in articles:
      if not x.record(self.connection): return False
    return True

if __name__ == "__main__":
  spider = Spider()
  if len(sys.argv) == 1: # if no action is specified, do everything
    spider.find_record_new_articles("bioinformatics")
    spider.refresh_article_details()
    spider.rank_articles()
  elif sys.argv[1] == "rankings":
    spider.rank_articles()
