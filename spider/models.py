import config
from datetime import datetime as dt
import re

import psycopg2
import requests

class Author:
  def __init__(self, name, institution, email, orcid=None):
    if institution == "":
      institution = None
    if email == "":
      email = None
    if orcid == "":
      orcid = None

    self.name = name
    # lots of "institution" strings from biorxiv for some reason end in semicolons
    if institution is not None:
      self.institution = re.sub(r";$", "", institution)
    else:
      self.institution = None
    self.email = email
    self.orcid = orcid
    self.id = None

  def record(self, connection, log):
    recorded = False
    with connection.db.cursor() as cursor:
      if self.orcid is not None:
        cursor.execute("SELECT id FROM authors WHERE orcid = %s;", (self.orcid,))
        a_id = cursor.fetchone()
        if a_id is not None:
          self.id = a_id[0]
          log.record(f"ORCiD: Author {self.name} exists with ID {self.id}", "debug")

          # HACK: This name update should probably be temporary, but bioRxiv went back and changed all
          # the author names on old papers to reflect the PDF rather than what was input by the users,
          # so we may be able to consolidate some records by updating the names associated with ORCIDs.
          log.record("Updating author name", 'debug')
          cursor.execute("UPDATE authors SET name=%s, noperiodname=%s WHERE id=%s;", (self.name, self.name.replace(".", ""), self.id))

          if self.institution is not None: # institution should always be set to the one we've seen most recently,
            # BUT if record_authors_on_refresh is set, then we might actually be looking at the author's OLDEST
            # paper right now, so don't update those things
            if config.record_authors_on_refresh is not True:
              log.record("Updating author institution", 'debug')
              cursor.execute("UPDATE authors SET name=%s, noperiodname=%s, institution=%s WHERE id=%s;", (self.name, self.name.replace(".", ""), self.institution, self.id))

      if self.id is None:
        # if they don't have an ORCiD, check for duplicates based on name.
        # NOTE: We don't use email as a signifier of uniqueness because some authors who hate
        # me record the same email address for multiple people.
        cursor.execute("SELECT id, orcid FROM authors WHERE noperiodname = %s;", (self.name.replace(".", ""),))
        entries = []
        for entry in cursor:
          entries.append(entry)

        for entry in entries:
          if entry is not None and entry[1] is not None:
            # It's possible that one name ends up with two entries, one associated with an ORCID
            # and one not associated with one. If an author's name has multiple entries in the DB,
            # this step makes sure they're matched with the one that has the ORCID already.
            self.id = entry[0]
            log.record(f"Name: Author {self.name} exists with ID {self.id}; preference given to entry with ORCID", "debug")
            break
        else:
          if len(entries) > 0 and entries[0] is not None:
            self.id = entries[0][0]
            log.record(f"Name: Author {self.name} exists with ID {self.id}", "debug")

        if self.id is not None:
          recorded = True
          # if they report an orcid on this paper but we didn't know about it before:
          if self.orcid is not None:
            log.record(f"Recording ORCiD {self.orcid} for known author", "info")
            cursor.execute("UPDATE authors SET orcid=%s WHERE id=%s;", (self.orcid, self.id))
          if self.institution is not None and config.record_authors_on_refresh is not True:
            log.record("Updating author institution", 'debug')
            cursor.execute("UPDATE authors SET institution=%s WHERE id=%s;", (self.institution, self.id))

      if self.id is None: # if they're definitely brand new
        cursor.execute("INSERT INTO authors (name, orcid, institution, noperiodname) VALUES (%s, %s, %s, %s) RETURNING id;", (self.name, self.orcid, self.institution, self.name.replace(".", "")))
        self.id = cursor.fetchone()[0]
        log.record(f"Recorded author {self.name} with ID {self.id}", "info")
        recorded = True

      if self.email is not None:
        # check if we know about this email already:
        cursor.execute("SELECT COUNT(id) FROM author_emails WHERE author=%s AND email=%s", (self.id,self.email))
        emailcount = cursor.fetchone()[0]
        if emailcount == 0:
          log.record(f"Recording email {self.email} for author", "debug")
          cursor.execute("INSERT INTO author_emails (author, email) VALUES (%s, %s);", (self.id, self.email))

class Article:
  # This class is disconcertingly intermingled with the Spider class,
  # a problem that is probably most easily remedied by folding the whole
  # thing into the spider rather than trying to pry them apart, unfortunately
  def __init__(self, entry):
    self.title = entry.get('title')
    self.doi = entry.get('doi')
    self.collection = entry.get('category')
    self.collection = None
    self.abstract = entry.get('abstract')
    self.version = entry.get('version')
    self.posted = entry.get('date')
    self.url = f"https://biorxiv.org/content/{self.doi}v{self.version}"

  def record(self, connection, spider): # TODO: requiring the whole spider here is code smell of the first order
    with connection.db.cursor() as cursor:
      if self.doi in ["", None]:
        spider.log.record(f"Won't record a paper without a DOI: {self.url}", "fatal")
      cursor.execute("SELECT id, last_crawled FROM articles WHERE doi=%s", (self.doi,))
      response = cursor.fetchone()

      if response is not None and len(response) > 0:
        # We only get to this point if we already have a record
        # of the preprint. If we already have a record, but the
        # URL confirms it's version 1, then we know we've seen this
        # specific paper already.
        if self.version == '1':
          spider.log.record(f"Found article already: {self.title}", "debug")
          return False
        # If the revision was posted before the "last crawled" date, we
        # likewise know it's safe to skip. This could conceivably miss
        # papers that had two versions posted on the same day, but it
        # saves enough time (and DB calls) that it's probably not worth
        # dealing with.
        posted = dt.strptime(self.posted, "%Y-%m-%d")
        if response[1] >= posted.date():
          spider.log.record('Revision already observed. Skipping.')
          return False

        # If it's a revision
        cursor.execute("UPDATE articles SET title=%s, abstract=%s, title_vector=NULL, abstract_vector=NULL, author_vector=NULL WHERE doi=%s RETURNING id;", (self.title, self.abstract, self.doi))
        self.id = cursor.fetchone()[0]
        stat_table, authors = spider.get_article_stats(self.url)
        spider._record_authors(self.id, authors, True)
        if stat_table is not None:
          spider.save_article_stats(self.id, stat_table)
        spider.log.record(f"Updated revision for article DOI {self.doi}: {self.title}", "info")
        connection.db.commit()
        return None
    # If it's brand new:
    with connection.db.cursor() as cursor:
      try:
        cursor.execute("INSERT INTO articles (title, doi, url, collection, abstract) VALUES (%s, %s, %s, %s, %s) RETURNING id;", (self.title, self.doi, self.url, self.collection, self.abstract))
      except Exception as e:
        spider.log.record(f"Couldn't record article '{self.title}': {e}", "error")
      self.id = cursor.fetchone()[0]

      spider.log.record("Recording stats for new article", "debug")
      stat_table = None
      try:
        stat_table, authors = spider.get_article_stats(self.url)
      except Exception as e:
        spider.log.record(f"Error fetching stats: {e}. Trying one more time...", "warn")
        try:
          stat_table, authors = spider.get_article_stats(self.url)
        except Exception as e:
          spider.log.record("Error fetching stats again. Giving up on this one.", "error")

      spider._record_authors(self.id, authors)
      self._record_posted_date(spider)
      if stat_table is not None:
        spider.save_article_stats(self.id, stat_table)
      spider.log.record(f"Recorded NEW article {self.title}", 'info')
    return True

  def _record_posted_date(self, spider):
    date = None
    if self.version == 1:
      spider.log.record('First version posted; recording article date.')
      date = self.posted
    else:
      spider.log.record('Revision posted; fetching original article date.')
      # if the first time we see an article ISN'T the first version, we should
      # check to get the date from V1.
      spider.record_article_posted_date(self.id, self.doi)

  def get_id(self, connection):
    with connection.db.cursor() as cursor:
      cursor.execute("SELECT id FROM articles WHERE doi=%s", (self.doi,))
      response = cursor.fetchone()
      if response is None or len(response) == 0:
        return False
      self.id = response[0]
    return True
