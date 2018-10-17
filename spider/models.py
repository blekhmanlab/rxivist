import re

import psycopg2

class Author:
  def __init__(self, given, surname):
    self.given = given
    self.surname = surname

  def name(self):
    if self.surname != "":
      if self.given != "":
        return "{} {}".format(self.given, self.surname)
      return self.surname
    return self.given

  def record(self, connection, log):
    with connection.db.cursor() as cursor:
      cursor.execute("SELECT id FROM authors WHERE given = %s and surname = %s;", (self.given, self.surname))
      a_id = cursor.fetchone()
      if a_id is not None:
        self.id = a_id[0]
        log.record("Author {} exists with ID {}".format(self.name(), self.id), "debug")
        return
      cursor.execute("INSERT INTO authors (given, surname) VALUES (%s, %s) RETURNING id;", (self.given, self.surname))
      self.id = cursor.fetchone()[0]
      connection.db.commit()
      log.record("Recorded author {} with ID {}".format(self.name(), self.id), "debug")

class DetailedAuthor:
  def __init__(self, name, institution, email, orcid=None):
    if institution == "":
      institution = None
    if email == "":
      email = None
    if orcid == "":
      orcid = None

    self.name = name
    self.institution = institution
    self.email = email
    self.orcid = orcid
    self.id = None

  def record(self, connection, log):
    recorded = False
    with connection.db.cursor() as cursor:
      if self.orcid is not None:
        log.record("Author has ORCiD; determining whether they exist in DB.", "debug")
        cursor.execute("SELECT id FROM detailed_authors WHERE orcid = %s;", (self.orcid,))
        a_id = cursor.fetchone()
        if a_id is not None:
          self.id = a_id[0]
          log.record("ORCiD: Author {} exists with ID {}".format(self.name, self.id), "debug")
          log.record("Recording ORCiD {} for known author".format(self.orcid), "info")
          if self.institution is not None: # institution should always be set to the one we've seen most recently
            log.record("Updating author institution")
            cursor.execute("UPDATE detailed_authors SET institution=%s WHERE id=%s;", (self.institution, self.id))

      if self.id is None:
        # if they don't have an ORCiD, check for duplicates based on name.
        # NOTE: We don't use email as a signifier of uniqueness because some authors who hate
        # me record the same email address for multiple people.
        cursor.execute("SELECT id FROM detailed_authors WHERE name = %s;", (self.name,))
        a_id = cursor.fetchone()
        if a_id is not None:
          self.id = a_id[0]
          log.record("Name: Author {} exists with ID {}".format(self.name, self.id), "debug")
          recorded = True

          # if they have an orcid but we didn't know about it before:
          if self.orcid is not None:
            log.record("Recording ORCiD {} for known author".format(self.orcid), "info")
            cursor.execute("UPDATE detailed_authors SET orcid=%s WHERE id=%s;", (self.orcid, self.id))
          if self.institution is not None:
            log.record("Updating author institution")
            cursor.execute("UPDATE detailed_authors SET institution=%s WHERE id=%s;", (self.institution, self.id))

      if self.id is None: # if they're definitely brand new
        cursor.execute("INSERT INTO detailed_authors (name, orcid, institution) VALUES (%s, %s, %s) RETURNING id;", (self.name, self.orcid, self.institution))
        self.id = cursor.fetchone()[0]
        log.record("Recorded detailed author {} with ID {}".format(self.name, self.id), "info")
        recorded = True

      if self.email is not None:
        # check if we know about this email already:
        cursor.execute("SELECT COUNT(id) FROM detailed_authors_email WHERE author=%s AND email=%s", (self.id,self.email))
        emailcount = cursor.fetchone()[0]
        if emailcount == 0:
          log.record("Recording email {} for author".format(self.email), "debug")
          cursor.execute("INSERT INTO detailed_authors_email (author, email) VALUES (%s, %s);", (self.id, self.email))

class Article:
  def __init__(self):
    pass

  def process_results_entry(self, html, collection, log):
    self._find_title(html)
    self._find_url(html)
    self._find_authors(html, log)
    self._find_doi(html, log)
    self.collection = collection
    # NOTE: We don't get abstracts from search result pages
    # because they're loaded asynchronously and it would be
    # annoying to load every one separately.

  def _find_title(self, html):
    x = html.find(".highwire-cite-title")
    # this looks weird because the title is wrapped
    # in 2 <span> tags with identical classes:
    self.title = x[0].text

  def _find_doi(self, html, log):
    x = html.find(".highwire-cite-metadata-doi")
    if len(x) == 0:
      log.record("Did not find DOI HTML element for article. Exiting to avoid losing the entry.", "fatal")
      return
    try:
      m = re.search('https://doi.org/(.*)', x[0].text)
    except:
      log.record("Error in searching for DOI string for article. Exiting to avoid losing the entry.", "fatal")
      return
    if len(m.groups()) > 0:
      self.doi = m.group(1)
    else:
      log.record("Did not find DOI string for article. Exiting to avoid losing the entry.", "fatal")
      return

  def _find_url(self, html):
    self.url = html.absolute_links.pop() # absolute_links is a set

  def _find_authors(self, html, log):
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
        log.record("NOT adding author to list: {} {}".format(first, last), "warn")

  def record(self, connection, spider):
    with connection.db.cursor() as cursor:
      # check to see if we've seen this article before
      if self.doi == "":
        spider.log.record("Won't record a paper without a DOI: {}".format(self.url), "fatal")
      cursor.execute("SELECT url, id FROM articles WHERE doi=%s", (self.doi,))
      response = cursor.fetchone()

      if response is not None and len(response) > 0:
        if response[0] == self.url:
          spider.log.record("Found article already: {}".format(self.title), "debug")
          connection.db.commit()
          return False
        else:
          cursor.execute("UPDATE articles SET url=%s, title=%s, collection=%s WHERE doi=%s RETURNING id;", (self.url, self.title, self.collection, self.doi))
          self.id = cursor.fetchone()[0]
          stat_table, detailed_authors = spider.get_article_stats(self.url)
          spider._record_detailed_authors(self.id, detailed_authors)
          if stat_table is not None:
            spider.save_article_stats(self.id, stat_table, None)
          spider.log.record("Updated revision for article DOI {}: {}".format(self.doi, self.title), "info")
          connection.db.commit()
          return True
    # If it's brand new:
    with connection.db.cursor() as cursor:
      try:
        cursor.execute("INSERT INTO articles (url, title, doi, collection) VALUES (%s, %s, %s, %s) RETURNING id;", (self.url, self.title, self.doi, self.collection))
      except Exception as e:
        spider.log.record("Couldn't record article '{}': {}".format(self.title, e), "error")
      self.id = cursor.fetchone()[0]

      author_ids, author_string = self._record_authors(connection, spider.log)
      self._link_authors(author_ids, connection, spider.log)

      cursor.execute("UPDATE articles SET author_vector=to_tsvector(coalesce(%s,'')) WHERE id=%s;", (author_string, self.id))
      spider.log.record("Recorded article {}".format(self.title))

      spider.log.record("Recording stats for new article", "debug")
      stat_table = None
      try:
        stat_table, detailed_authors = spider.get_article_stats(self.url)
      except Exception as e:
        spider.log.record("Error fetching stats: {}. Trying one more time...".format(e), "warn")
      try:
        stat_table, detailed_authors = spider.get_article_stats(self.url)
      except Exception as e:
        spider.log.record("Error fetching stats again. Giving up on this one.", "error")

      spider._record_detailed_authors(self.id, detailed_authors)
      posted = spider.get_article_posted_date(self.url)
      if stat_table is not None:
        spider.save_article_stats(self.id, stat_table, posted)
    return True

  def _record_authors(self, connection, log):
    author_ids = []
    author_string = "" # For calculating a searchable vector
    for a in self.authors:
      author_string += "{}, ".format(a.name())
      a.record(connection, log)
      author_ids.append(a.id)

    return (author_ids, author_string)

  def _link_authors(self, author_ids, connection, log):
    try:
      with connection.db.cursor() as cursor:
        sql = "INSERT INTO article_authors (article, author) VALUES (%s, %s);"
        cursor.executemany(sql, [(self.id, x) for x in author_ids])
        connection.db.commit()
    except Exception as e:
      # If there's an error associating all the authors with their paper all at once,
      # send separate queries for each one
      # (This came up last time because an author was listed twice on the same paper.)
      log.record("Error associating authors to paper: {}".format(e), "warn")
      log.record("Recording article associations one at a time.")
      for x in author_ids:
        try:
          with connection.db.cursor() as cursor:
            cursor.execute("INSERT INTO article_authors (article, author) VALUES (%s, %s);", (self.id, x))
            connection.db.commit()
        except Exception as e:
          log.record("Another problem associating author {} to article {}. Moving on.".format(x, self.id), "error")
          pass