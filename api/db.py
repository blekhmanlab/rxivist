import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class Connection(object):
	def __init__(self, host, user, password):
		dbname = "testdb" # TODO: Make this configurable
		params = 'host={} dbname={} user={} password={}'.format(host, dbname, user, password)
		self.db = psycopg2.connect(params)
		self.cursor = self.db.cursor()
	
	def __del__(self):
		self.db.close()
