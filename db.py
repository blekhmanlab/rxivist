"""Functions governing the application's interactions with the databas.

There is essentially no business logic in here; it establishes a connection
to the application's database and that's all.
"""
import time

import psycopg2

import config

class Connection(object):
  """Data type holding the data required to maintain a database
  connection and perform queries.

  """
  def __init__(self, host, dbname, user, password):
    """Stores db connection info in memory and initiates a
    connection to the specified db."""

    self.db = None
    self.host = host
    self.dbname = dbname
    self.user = user
    self.password = password

    try:
      self._attempt_connect()
    except RuntimeError as e:
      print("FATAL: {}".format(e))
      exit(1)
    print("Connected!")
    self.cursor = self.db.cursor()

  def _attempt_connect(self, attempts=0):
    """Initiates a connection to the database and tracks retry attempts.

    Arguments:
      - attempts: How many failed attempts have already happened.

    Side effects:
      - self.db: Set on a successful connection attempt.
    """

    attempts += 1
    print("Connecting. Attempt {} of {}.".format(attempts, config.db["connection"]["max_attempts"]))
    try:
      self.db = psycopg2.connect(
        host=self.host,
        dbname=self.dbname,
        user=self.user,
        password=self.password,
        connect_timeout=config.db["connection"]["timeout"],
        options='-c search_path={}'.format(config.db["schema"])
      )
      self.db.set_session(autocommit=True)
    except:
      if attempts >= config.db["connection"]["max_attempts"]:
        print("Giving up.")
        raise RuntimeError("Failed to connect to database.")
      print("Connection to DB failed. Retrying in {} seconds.".format(config.db["connection"]["attempt_pause"]))
      time.sleep(config.db["connection"]["attempt_pause"])
      self._attempt_connect(attempts)

  def read(self, query, params=None):
    """Helper function that converts results returned stored in a
    Psycopg cursor into a less temperamental list format. Note that
    there IS recursive retry logic here; when the connection to the
    database is dropped, the query will fail, prompting this method
    to re-connect and try the query again. This will continue trying
    to reconnect indefinitely. This is probably not ideal.

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
    """Closes the database connection when the Connection object
    is destroyed."""

    if self.db is not None:
      self.db.close()