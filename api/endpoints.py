"""Functions linked directly to functionality called from API endpoints.

This module is used to pull logic out of the controllers in main.py.
Some of these functions maybe called from MULTIPLE controllers, so
look around before modifying the API of one of them.
"""

import bottle
import db
import helpers
import models

class NotFoundError(Exception):
  def __init__(self, id):
    self.message = "Entity could not be found with id {}".format(id)

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

def most_popular(connection, q, categories, timeframe):
  """Returns a list of the 20 most downloaded papers that meet a given set of constraints.

  Arguments:
    - connection: a database connection object.
    - q:  A search string to compare against article abstracts
          and titles. (Title matches are weighted more heavily.)
    - categories: A list of bioRxiv categories the results can be in.
  Returns:
    - An ordered list of Article objects that meet the search criteria.

  """

  # TODO: validate that the category filters passed in are actual categories

  query = "SELECT r.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.origin_month, a.origin_year"
  params = ()
  if q != "": # if there's a text search specified
    params = (q,)
    query += ", ts_rank_cd(totalvector, query) as rank"
  query += " FROM articles AS a INNER JOIN "
  query_times = {
    "alltime": "alltime_ranks",
    "ytd": "ytd_ranks",
    "lastmonth": "month_ranks"
  }
  query += query_times[timeframe]
  query += " AS r ON r.article=a.id"

  if q != "":
    query += """, to_tsquery(%s) query,
    coalesce(setweight(a.title_vector, 'A') || setweight(a.abstract_vector, 'D')) totalvector
    """
  if q != "" or len(categories) > 0:
    query += " WHERE "
  if q != "":
    query += "query @@ totalvector "
    if len(categories) > 0:
      query += " AND "

  if len(categories) > 0:
    query += "collection=ANY(%s)"
    if q != "":
      params = (q,categories)
    else:
      params = (categories,)
  query += " ORDER BY r.rank ASC LIMIT 20;"
  with connection.db.cursor() as cursor:
    cursor.execute(query, params)
    results = [models.SearchResultArticle(a, connection) for a in cursor]
  return results

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
    query += """, to_tsquery(%s) query,
    coalesce(setweight(a.title_vector, 'A') || setweight(a.abstract_vector, 'D')) totalvector
    WHERE query @@ totalvector
    """
  query += ";"
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

  # TODO: Memoize all the stuff pulled together in this function,
  # store it in a DB somewhere
  authorq = connection.read("SELECT id, given, surname FROM authors WHERE id = %s;", (id,))
  if len(authorq) == 0:
    raise NotFoundError(id)
  if len(authorq) > 1:
    raise ValueError("Multiple authors found with id {}".format(id))
  authorq = authorq[0]
  result = models.Author(authorq[0], authorq[1], authorq[2])

  downloadsq = connection.read("SELECT rank, downloads, tie FROM author_ranks WHERE author = %s;", (id,))
  if len(downloadsq) == 1:
    author_count = connection.read("SELECT COUNT(author) FROM author_ranks;")
    author_count = author_count[0][0]

    result.downloads = downloadsq[0][1]
    result.rank = models.RankEntry(downloadsq[0][0], author_count, downloadsq[0][2])
  sql = db.queries()["article_ranks"] + "WHERE article_authors.author=%s ORDER BY alltime_ranks.rank"
  articles = connection.read(sql, (id,))

  alltime_count = connection.read("SELECT COUNT(article) FROM alltime_ranks")
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
  alltime_count = connection.read("SELECT COUNT(article) FROM alltime_ranks")
  alltime_count = alltime_count[0][0]

  sql = db.queries()["article_ranks"] + "WHERE articles.id=%s"
  paperq = connection.read(sql, (id,))
  if len(paperq) == 0:
    raise NotFoundError(id)
  # if len(paperq) > 1:
    # raise ValueError("Multiple papers found with id {}".format(id))
  paperq = paperq[0]
  # TODO: Figure out which join clause in the query makes a bunch of
  # identical responses come back for this
  result = models.ArticleDetails(paperq, alltime_count, connection)
  result.GetDetailedTraffic(connection)
  # once we're done processing the results of the last query, go back
  # and query for some extra info about each article
  query = "SELECT COUNT(id) FROM articles WHERE collection=%s"
  collection_count = connection.read(query, (result.collection,))
  result.ranks.collection.out_of = collection_count[0][0]

  return result

def download_distribution(connection):
  data = connection.read("SELECT bucket, count FROM download_distribution WHERE category='alltime' ORDER BY bucket")
  results = [(entry[0], entry[1]) for entry in data]
  return results
