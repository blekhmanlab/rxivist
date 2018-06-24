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

	def fetch_db_tables(self):
		tables = []
		with self.db.cursor() as cursor:
			try:
				cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';")
				for result in cursor:
					tables.append(result[0])
			finally:
				self.db.commit()
		return tables
		

	def fetch_table_data(self, table):
		headers = []
		data = []
		with self.db.cursor() as cursor:
			try:
				cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='{}';".format(table))
				for result in cursor:
					headers.append(result[0])
				cursor.execute("SELECT * FROM {};".format(table))
				for result in cursor: # can't just return the cursor; it's closed when this function returns
					data.append(result)
			finally:
				self.db.commit()
			return headers, data
