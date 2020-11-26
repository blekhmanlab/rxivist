import psycopg2
import config

class Connection(object):
  def __init__(self, host, db, user, password):
    dbname = db
    self.db = None
    self._ensure_database_exists(dbname, host, user, password)

    self.db = psycopg2.connect(
      host=host,
      dbname=dbname,
      user=user,
      password=password,
      options=f'-c search_path={config.db["schema"]}'
    )
    self.db.set_session(autocommit=True)
    self.cursor = self.db.cursor()

    self._ensure_tables_exist()

  def _ensure_database_exists(self, dbname, host, user, password):
    """Connects to the database server and makes sure the specified database exists there;
    if it doesn't, this method creates it.

    """
    params = f'host={host} dbname={dbname} user={user} password={password}'
    db = psycopg2.connect(params)
    cursor = db.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    for result in cursor:
      if result[0] == dbname: break
    else:
      cursor.execute("CREATE DATABASE %s;", (dbname,))
    db.close()

  def _ensure_tables_exist(self):
    """Creates any missing tables that are expected to exist in the application database.
    Does NOT verify whether the current columns are accurate.

    """
    self.cursor.execute("CREATE TABLE IF NOT EXISTS articles (id SERIAL PRIMARY KEY, url text UNIQUE, title text NOT NULL, abstract text, doi text UNIQUE, posted date, collection text, title_vector tsvector, abstract_vector tsvector, author_vector tsvector, last_crawled DATE NOT NULL DEFAULT CURRENT_DATE, repo text);")

    # The "doi" column can't have a "UNIQUE" constraint because sometimes a paper will be
    # posted to bioRxiv under two different titles, so they will show up as two different
    # bioRxiv papers that will eventually share a single journal DOI.
    self.cursor.execute("CREATE TABLE IF NOT EXISTS article_publications (article integer PRIMARY KEY, doi text, publication text);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS publication_dates (article integer PRIMARY KEY, date date);")

    self.cursor.execute("CREATE TABLE IF NOT EXISTS authors (id SERIAL PRIMARY KEY, name text NOT NULL, institution text, orcid text UNIQUE, noperiodname text);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS author_emails (id SERIAL PRIMARY KEY, author integer NOT NULL, email text);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS article_authors (id SERIAL PRIMARY KEY, article integer NOT NULL, author integer NOT NULL, institution text, UNIQUE (article, author));")

    self.cursor.execute("CREATE TABLE IF NOT EXISTS institutions (id SERIAL PRIMARY KEY, name text NOT NULL, ror text, grid text, country text);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS affiliation_institutions (affiliation text PRIMARY KEY, institution integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS countries (alpha2 text PRIMARY KEY, name text NOT NULL, continent text);")

    self.cursor.execute("CREATE TABLE IF NOT EXISTS article_traffic (id SERIAL PRIMARY KEY, article integer NOT NULL, month integer, year integer NOT NULL, abstract integer, pdf integer, UNIQUE (article, month, year));")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS crossref_daily (id SERIAL PRIMARY KEY, source_date DATE, doi text NOT NULL, count integer, crawled DATE NOT NULL DEFAULT CURRENT_DATE, UNIQUE(doi, source_date));")

    self.cursor.execute("CREATE TABLE IF NOT EXISTS alltime_ranks          (article integer PRIMARY KEY, rank integer NOT NULL, downloads integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS alltime_ranks_working  (article integer PRIMARY KEY, rank integer NOT NULL, downloads integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS category_ranks         (article integer PRIMARY KEY, rank integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS category_ranks_working (article integer PRIMARY KEY, rank integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS ytd_ranks              (article integer PRIMARY KEY, rank integer NOT NULL, downloads integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS ytd_ranks_working      (article integer PRIMARY KEY, rank integer NOT NULL, downloads integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS month_ranks            (article integer PRIMARY KEY, rank integer NOT NULL, downloads integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS month_ranks_working    (article integer PRIMARY KEY, rank integer NOT NULL, downloads integer NOT NULL);")

    self.cursor.execute("CREATE TABLE IF NOT EXISTS author_ranks           (author integer PRIMARY KEY, rank integer NOT NULL, tie boolean, downloads integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS author_ranks_working   (author integer PRIMARY KEY, rank integer NOT NULL, tie boolean, downloads integer NOT NULL);")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS author_ranks_category  (id SERIAL PRIMARY KEY, author integer, category text NOT NULL, rank integer NOT NULL, tie boolean, downloads integer NOT NULL, UNIQUE (author, category));")
    self.cursor.execute("CREATE TABLE IF NOT EXISTS author_ranks_category_working   (id SERIAL PRIMARY KEY, author integer, category text NOT NULL,  rank integer NOT NULL, tie boolean, downloads integer NOT NULL, UNIQUE (author, category));")

    self.cursor.execute("CREATE TABLE IF NOT EXISTS download_distribution (id SERIAL PRIMARY KEY, bucket integer NOT NULL, count integer NOT NULL, category text NOT NULL);")
    self.db.commit()

  def __del__(self):
    if self.db is not None:
      self.db.close()
