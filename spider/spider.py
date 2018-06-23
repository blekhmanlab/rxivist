import re

from requests_html import HTMLSession
import psycopg2

import db

TESTING = True		# this is just for testing, so we don't crawl the whole site during development TODO delete

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
			self.id = cursor.fetchone()[0]
			connection.db.commit()

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
		self.connection = db.Connection("testdb", "postgres", "mysecretpassword")  # TODO: Make this configurable
		self.session = HTMLSession()
	
	def find_record_new_articles(self, collection="bioinformatics"):
		# we need to grab the first page to figure out how many pages there are
		r = self.session.get("https://www.biorxiv.org/collection/{}".format(collection))
		results = pull_out_articles(r.html)
		keep_going = self.record_articles(results)
		if not keep_going: exit(0) # if we already knew about the first entry, we're done

		pagecount = 2 if TESTING else determine_page_count(r.html) # Also just for testing TODO delete
		for p in range(1, pagecount): # iterate through pages
			r = self.session.get("https://www.biorxiv.org/collection/{}?page={}".format(collection, p))
			results = pull_out_articles(r.html)
			keep_going = self.record_articles(results)
			if not keep_going: break # If we encounter a recognized article, we're done

	def refresh_article_details(self):
		pass

	def record_articles(self, articles):
		# return value is whether we encountered any articles we had already
		for x in articles:
			if not x.record(self.connection): return False
		return True

if __name__ == "__main__":
	spider = Spider()
	spider.find_record_new_articles("bioinformatics")
	spider.refresh_article_details()