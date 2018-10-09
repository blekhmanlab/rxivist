"""Functions linked directly to functionality called from API endpoints.

This module is used to pull logic out of the controllers in main.py.
Some of these functions maybe called from MULTIPLE controllers, so
look around before modifying the API of one of them.
"""

import bottle
import db
import helpers
import models
import config

def get_categories(connection):
  """Returns a list of all known bioRxiv categories.

  bioRxiv separates all papers into categories (or "collections"), such
  as "bioinformatics", "genomics", etc. This function lists all the ones
  we've pulled from the site so far. Used to generate the "select categories"
  selector in the advanced search interface.

  """
  results = []
  categories = connection.read("SELECT DISTINCT collection FROM articles ORDER BY collection;")
  for cat in categories:
    if len(cat) > 0:
      results.append(cat[0])
  return results

def most_popular(connection, q, categories, timeframe, metric, page, page_size):
  """Returns a list of the 20 most downloaded papers that meet a given set of constraints.

  Arguments:
    - connection: a database connection object.
    - q:  A search string to compare against article abstracts
          and titles. (Title matches are weighted more heavily.)
    - categories: A list of bioRxiv categories the results can be in.
    - timeframe: A description of the range of dates on which to
          base the rankings (i.e. "alltime" or "lastmonth")
    - metric: Which article-level statistic to use when sorting results
    - page: Which page of the results to display (0 indexed)
    - page_size: How many entries should be returned
  Returns:
    - An ordered list of Article objects that meet the search criteria.

  """

  # We build two queries, 'select' and 'countselect': one to get the
  # current page of results, and one to figure out the total number
  # of results
  select = "SELECT "
  if metric == "downloads":
    select += "r.downloads"
  elif metric == "crossref":
    select += "SUM(r.count)"
  select += ", a.id, a.url, a.title, a.abstract, a.collection, a.origin_month, a.origin_year, a.posted, a.doi"

  countselect = "SELECT COUNT(DISTINCT a.id)"
  params = ()

  query = ""
  if q != "": # if there's a text search specified
    params = (q,)
  query += " FROM articles AS a INNER JOIN "
  if metric == "crossref":
    query += "crossref_daily"
  elif metric == "downloads":
    query_times = {
      "alltime": "alltime_ranks",
      "ytd": "ytd_ranks",
      "lastmonth": "month_ranks",
    }
    query += query_times[timeframe]

  if metric == "crossref":
    query += " AS r ON r.doi=a.doi"
  elif metric == "downloads":
    query += " AS r ON r.article=a.id"

  if q != "":
    query += """, plainto_tsquery(%s) query,
    coalesce(setweight(a.title_vector, 'A') || setweight(a.abstract_vector, 'C') || setweight(a.author_vector, 'D')) totalvector
    """
  query += " WHERE "
  if metric == "downloads":
    query += "r.downloads > 0"
    if q != "" or len(categories) > 0:
      query += " AND "
  if q != "":
    query += "query @@ totalvector "
    if len(categories) > 0 or metric == "crossref":
      query += " AND "

  if len(categories) > 0:
    query += "collection=ANY(%s)"
    if q != "":
      params = (q,categories)
    else:
      params = (categories,)
    if metric == "crossref":
      query += " AND "
  if metric == "crossref":
    query += "r.source_date > now() - interval "
    query_times = {
      "day": 2,
      "week": 7,
      "month": 30,
      "year": 365
    }
    query += "'{} days' ".format(query_times[timeframe])
  # this is the last piece of the query we need for the one
  # that counts the total number of results
  countselect += query
  with connection.db.cursor() as cursor:
    cursor.execute(countselect, params)
    total = cursor.fetchone()[0]

  if metric == "crossref":
    query += "GROUP BY a.id"
  query += " ORDER BY "
  if metric == "downloads":
    query += "r.rank ASC"
  elif metric == "crossref":
    query += "SUM(r.count) DESC"

  query += " LIMIT {}".format(page_size)
  if page > 0:
    query += " OFFSET {}".format(page * page_size)
  query += ";"
  select += query
  with connection.db.cursor() as cursor:
    cursor.execute(select, params)
    results = [models.SearchResultArticle(a, connection) for a in cursor]
  return results, total

def author_rankings(connection, category_list=[]):
  """Returns a list of authors with the most cumulative downloads

  Arguments:
    - connection: a database connection object.
    - category: can specify a single bioRxiv collection to base download rankings on.
  Returns:
    - An ordered list of Author objects that meet the search criteria.

  """
  if len(category_list) == 0:
    category = ""
  else:
    category = category_list[0] # only one category at a time for author searches

  if category == "": # all time, all categories
    table = "author_ranks" # TODO: just make a category called "alltime"
    where = ""
    params = ()
  else:
    table = "author_ranks_category"
    where = "WHERE r.category=%s"
    params = (category,)
  query = """
    SELECT a.id, a.given, a.surname, r.rank, r.downloads, r.tie
    FROM authors AS a
    INNER JOIN {} r ON a.id=r.author
    {}
    ORDER BY r.rank
    LIMIT {}
  """.format(table, where, config.author_ranks_limit)

  with connection.db.cursor() as cursor:
    cursor.execute(query, params)
    return [models.SearchResultAuthor(*a) for a in cursor]

def table_results(connection, q):
  """Returns data about every paper in the db and makes the browser sort em out.

  Arguments:
    - connection: a database connection object.
    - q:  A search string to compare against article abstracts
          and titles. (Title matches are weighted more heavily.)
  Returns:
    - An ordered list of Article objects that meet the search criteria.

  """

  query = "SELECT alltime.downloads, ytd.downloads, lastmonth.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.origin_month, a.origin_year"
  params = ()
  if q != "": # if there's a text search specified
    params = (q,)
    query += ", ts_rank_cd(totalvector, query) as rank"
  query += """
  FROM articles AS a
  INNER JOIN alltime_ranks AS alltime ON alltime.article=a.id
  INNER JOIN ytd_ranks AS ytd ON ytd.article=a.id
  INNER JOIN month_ranks AS lastmonth ON lastmonth.article=a.id
  """

  if q != "":
    query += """, plainto_tsquery(%s) query,
    coalesce(setweight(a.title_vector, 'A') || setweight(a.abstract_vector, 'C') || setweight(a.author_vector, 'D')) totalvector
    WHERE query @@ totalvector
    """
  query += " LIMIT 400;" # TODO: Paginate this response like the standard one
  with connection.db.cursor() as cursor:
    cursor.execute(query, params)
    results = [models.TableSearchResultArticle(a, connection) for a in cursor]
  return results

def author_details(connection, id):
  """Returns a dict of information about a single author, including a list of
      all their papers.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the author being queried.
  Returns:
    - An Author object containing information about that
        author's publications.

  """

  authorq = connection.read("SELECT id, given, surname FROM authors WHERE id = %s;", (id,))
  if len(authorq) == 0:
    raise helpers.NotFoundError(id)
  if len(authorq) > 1:
    raise ValueError("Multiple authors found with id {}".format(id))
  authorq = authorq[0]
  result = models.Author(authorq[0], authorq[1], authorq[2])
  downloadsq = connection.read("SELECT rank, tie, downloads FROM author_ranks WHERE author=%s;", (id,))
  if len(downloadsq) == 1:
    author_count = connection.read("SELECT COUNT(id) FROM authors;")
    author_count = author_count[0][0]
    result.alltime_rank = models.RankEntry(downloadsq[0][0], author_count, downloadsq[0][1], downloadsq[0][2])

  categoryq = connection.read("SELECT rank, tie, downloads, category FROM author_ranks_category WHERE author = %s;", (id,))
  if len(categoryq) > 0:
    result.categories = [models.RankEntry(cat[0], 0, cat[1], cat[2], cat[3]) for cat in categoryq]
  for entry in result.categories:
    query = "SELECT COUNT(author) FROM author_ranks_category WHERE category=%s"
    author_in_category = connection.read(query, (entry.category,))
    entry.out_of = author_in_category[0][0]


  sql = db.QUERIES["article_ranks"] + "WHERE article_authors.author=%s ORDER BY alltime_ranks.rank"
  articles = connection.read(sql, (id,))

  alltime_count = connection.read("SELECT COUNT(id) FROM articles")
  alltime_count = alltime_count[0][0]
  # NOTE: alltime_count will not be a count of all the papers on the site,
  #   it excludes papers that don't have any traffic data.

  result.articles = [models.ArticleDetails(a, alltime_count, connection) for a in articles]

  # once we're done processing the results of the last query, go back
  # and query for some extra info about each article
  for article in result.articles:
    query = "SELECT COUNT(id) FROM articles WHERE collection=%s"
    collection_count = connection.read(query, (article.collection,))
    article.ranks.collection.out_of = collection_count[0][0]

  return result

def paper_details(connection, id):
  """Returns a dict of information about a single paper.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the author being queried.
  Returns:
    - A Paper object containing details about the paper and
        its authors.

  """
  alltime_count = connection.read("SELECT COUNT(id) FROM articles")
  alltime_count = alltime_count[0][0]

  sql = db.QUERIES["article_ranks"] + "WHERE articles.id=%s"
  paperq = connection.read(sql, (id,))
  if len(paperq) == 0:
    raise helpers.NotFoundError(id)

  paperq = paperq[0] # we get one entry for each author, but don't need them here
  result = models.ArticleDetails(paperq, alltime_count, connection)
  # once we're done processing the results of the last query, go back
  # and query for some extra info about each article
  query = "SELECT COUNT(id) FROM articles WHERE collection=%s"
  collection_count = connection.read(query, (result.collection,))
  result.ranks.collection.out_of = collection_count[0][0]

  return result

def paper_downloads(connection, a_id):
  result = models.Article(a_id)
  result.GetDetailedTraffic(connection)
  return {
    "query": {
      "id": a_id
    },
    "results": [{"month": x.month, "year": x.year, "downloads": x.downloads} for x in result.traffic]
  }

def download_distribution(connection, category):
  data = connection.read("SELECT bucket, count FROM download_distribution WHERE category=%s ORDER BY bucket", (category,))
  results = [(entry[0], entry[1]) for entry in data]
  averages = {}
  for avg in ["mean", "median"]:
    cat = "{}_{}".format(category, avg)
    answer = connection.read("SELECT count FROM download_distribution WHERE category=%s", (cat,))
    averages[avg] = answer[0][0]
  return results, averages
