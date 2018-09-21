"""Functions governing the application's interactions with the databas.

There is essentially no business logic in here; it establishes a connection
to the application's Postgres database and stores commonly referenced query
elements.
"""
import time

import psycopg2

import config

def queries(): # TODO: This doesn't need to be a function
  """ Returns a dict of strings containing complex queries
  that are used in multiple locations.

  """

  return {
    "article_ranks": """
      SELECT alltime_ranks.downloads, alltime_ranks.rank, ytd_ranks.rank, month_ranks.rank,
        articles.id, articles.url, articles.title, articles.abstract, articles.collection,
        category_ranks.rank, articles.origin_month, articles.origin_year
      FROM articles
      INNER JOIN article_authors ON article_authors.article=articles.id
      LEFT JOIN alltime_ranks ON articles.id=alltime_ranks.article
      LEFT JOIN ytd_ranks ON articles.id=ytd_ranks.article
      LEFT JOIN month_ranks ON articles.id=month_ranks.article
      LEFT JOIN category_ranks ON articles.id=category_ranks.article
    """
  }

class Connection(object):
  """Data type holding the data required to maintain a database
  connection and perform queries.

  """
  def __init__(self, host, dbname, user, password):
    self.db = None
    self.host = host
    self.dbname = dbname
    self.user = user
    self.password = password
    self._attempt_connect()
    print("Connected!")
    self.cursor = self.db.cursor()

  # TODO: This thing is just for demo purposes. If the API starts
  # but there's no DB, it dies and won't restart. This is probably
  # not good.
  def _attempt_connect(self, attempts=0):
    attempts += 1
    print("Connecting. Attempt {} of {}.".format(attempts, config.db["connection"]["max_attempts"]))
    params = 'host={} dbname={} user={} password={} connect_timeout={}'.format(self.host, self.dbname, self.user, self.password, config.db["connection"]["timeout"])
    try:
      self.db = psycopg2.connect(params)
      self.db.set_session(autocommit=True)
    except:
      if attempts >= config.db["connection"]["max_attempts"]:
        print("Giving up.")
        exit(1) # TODO: this should probably be an exception.
      print("Connection to DB failed. Retrying in {} seconds.".format(config.db["connection"]["attempt_pause"]))
      time.sleep(config.db["connection"]["attempt_pause"])
      self._attempt_connect(attempts)

  def fetch_db_tables(self):
    """Utility function that lists out all tables in the Rxivist database;
    used in admin panel.

    Returns:
      - A list of all tables in the "public" schema.

    """
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
    """Utility function used by the admin panel; returns the contents of
    a DB table. (The "articles" table has a custom parameter applied that
    presents the most recently crawled articles first.)

    Arguments:
      - table: The name of the table for which data is wanted.
    Returns:
      - A list of column headers for the given table.
      - A list of tuples, one for each row in the table.

    """
    headers = []
    data = []
    with self.db.cursor() as cursor:
      cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='{}';".format(table))
      for result in cursor:
        headers.append(result[0])
      extra = ""
      if table == "articles":
        extra = " ORDER BY last_crawled DESC"
      cursor.execute("SELECT * FROM {}{} LIMIT {};".format(table, extra, config.db_admin_return_limit))
      for result in cursor: # can't just return the cursor; it's closed when this function returns
        data.append(result)
    return headers, data

  def read(self, query, params=None):
    """Helper function that converts results returned stored in a
    Psycopg cursor into a less temperamental list format.

    Arguments:
      - query: The SQL query to be executed.
      - params: Any parameters to be substituted into the query. It's
          important to let Psycopg handle this rather than using Python
          string interpolation because it helps mitigate SQL injection.
    Returns:
      - A list of tuples, one for each row of results.

    """
    results = []
    try:
      with self.db.cursor() as cursor:
        if params is not None:
          cursor.execute(query, params)
        else:
          cursor.execute(query)
        for result in cursor:
          results.append(result)
      return results
    except psycopg2.OperationalError as e:
      print("ERROR with db query execution: {}".format(e))
      print("Reconnecting.")
      self._attempt_connect()
      print("Sending query again.")
      return self.read(query, params)

  def __del__(self):
    if self.db is not None:
      self.db.close()