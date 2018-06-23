import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class Connection(object):
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
	
	def __del__(self):
		self.db.close()