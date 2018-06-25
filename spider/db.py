import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class Connection(object):
	def __init__(self, host, user, password):
		dbname = "rxdb" # TODO: Make this configurable
		self.db = None
		self._ensure_database_exists(dbname, host, user, password)

		params = 'host={} dbname={} user={} password={}'.format(host, dbname, user, password)
		self.db = psycopg2.connect(params)
		self.cursor = self.db.cursor()

		self._ensure_tables_exist()

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
	
	def _ensure_tables_exist(self):
		self.cursor.execute("CREATE TABLE IF NOT EXISTS articles (id SERIAL PRIMARY KEY, url text UNIQUE, title text NOT NULL, abstract text);")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS authors (id SERIAL PRIMARY KEY, given text NOT NULL, surname text, UNIQUE (given, surname));")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS article_authors (id SERIAL PRIMARY KEY, article integer NOT NULL, author integer NOT NULL, UNIQUE (article, author));")
		self.cursor.execute("CREATE TABLE IF NOT EXISTS article_traffic (id SERIAL PRIMARY KEY, article integer NOT NULL, month integer, year integer NOT NULL, abstract integer, pdf integer, UNIQUE (article, month, year));")
		self.db.commit()
	
	def __del__(self):
		if self.db is not None:
			self.db.close()
