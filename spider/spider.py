from requests_html import HTMLSession
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import re

class Author(object):
	def __init__(self, given, surname):
		self.given = given
		self.surname = surname

	def name(self):
		if surname != "":
			return "{} {}".format(self.given, self.surname)
		else: # if author only has one name
			return self.given

class Article(object):
	def __init__(self):
		pass
		
	def process_results_page(self, html):
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

def determine_page_count(html):
	# takes a biorxiv results page and
	# finds the highest page number listed
	return int(html.find(".pager-last")[0].text)

def process_page(html):
	entries = html.find(".highwire-article-citation")
	articles = []
	for entry in entries:
		a = Article()
		a.process_results_page(entry)
		articles.append(a)
	return articles

class DB(object):
	def __init__(self, host, user, password):
		dbname = "testdb" # TODO: Make this configurable

		self._ensure_database_exists(dbname, host, user, password)

		params = 'host={} dbname={} user={} password={}'.format(host, dbname, user, password)
		self.db = psycopg2.connect(params)
		self.cursor = self.db.cursor()
		self.cursor.execute("CREATE TABLE IF NOT EXISTS articles (url text PRIMARY KEY, title text NOT NULL);")
		self.db.commit()

	def _ensure_database_exists(self, dbname, host, user, password):
		params = 'host={} dbname=postgres user={} password={}'.format(host, user, password)
		db = psycopg2.connect(params)
		db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # for creating DB
		cursor = db.cursor()
		cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
		for result in cursor:
			if result[0] == dbname: break
		else:
			cursor.execute("CREATE DATABASE {};".format(dbname))
		db.close()

	def record_article(self, article):
		try:
			self.cursor.execute("INSERT INTO articles VALUES (%s, %s);", (article.url, article.title))
			self.db.commit()
		except psycopg2.IntegrityError as err:
			if repr(err).find('duplicate key value violates unique constraint "articles_pkey"', 1):
				return False
			else:
				raise
		print("Recorded {}".format(article.title))
		return True

if __name__ == "__main__":
	db = DB("testdb", "postgres", "mysecretpassword")  # TODO: Make this configurable
	session = HTMLSession()
	# we need to grab the first page to figure out how many pages there are
	r = session.get("https://www.biorxiv.org/collection/bioinformatics")
	results = process_page(r.html)
	for p in range(1, determine_page_count(r.html)): # iterate through pages
		r = session.get("https://www.biorxiv.org/collection/bioinformatics?page={}".format(p))
		results += process_page(r.html)

	for x in results:
		# keep recording until we hit one that's already been done
		if not db.record_article(x): break