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
    - An ordered list of article elements that meet the search criteria.

  """

  # TODO: validate that the category filters passed in are actual categories

  query = "SELECT r.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.origin_month, a.origin_year"
  params = ()
  if q != "": # if there's a text search specified
    params = (q,)
    query += ", ts_rank_cd(totalvector, query) as rank"
  query += " FROM articles AS a INNER JOIN "
  if timeframe == "alltime":
    query += "alltime_ranks"
  elif timeframe == "ytd":
    query += "ytd_ranks"
  elif timeframe == "lastmonth":
    query += "month_ranks"
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

def author_details(connection, id):
  """Returns a dict of information about a single author, including a list of
      all their papers.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the author being queried.

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
  articles = connection.read("""
    SELECT alltime_ranks.downloads, alltime_ranks.rank, ytd_ranks.rank, month_ranks.rank,
      articles.id, articles.url, articles.title, articles.abstract, articles.collection,
      articles.collection_rank, articles.origin_month, articles.origin_year
    FROM articles
    INNER JOIN article_authors ON article_authors.article=articles.id
    LEFT JOIN alltime_ranks ON articles.id=alltime_ranks.article
    LEFT JOIN ytd_ranks ON articles.id=ytd_ranks.article
    LEFT JOIN month_ranks ON articles.id=month_ranks.article
    WHERE article_authors.author=%s
    ORDER BY alltime_ranks.rank
  """, (id,))

  alltime_count = connection.read("SELECT COUNT(article) FROM alltime_ranks")
  alltime_count = alltime_count[0][0]
  # NOTE: alltime_count will not be a count of all the papers on the site,
  # it excludes papers that don't have any traffic data.

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

  """
  alltime_count = connection.read("SELECT COUNT(article) FROM alltime_ranks")
  alltime_count = alltime_count[0][0]

  paperq = connection.read("""
    SELECT alltime_ranks.downloads, alltime_ranks.rank, ytd_ranks.rank, month_ranks.rank,
      articles.id, articles.url, articles.title, articles.abstract, articles.collection,
      articles.collection_rank, articles.origin_month, articles.origin_year
    FROM articles
    INNER JOIN article_authors ON article_authors.article=articles.id
    LEFT JOIN alltime_ranks ON articles.id=alltime_ranks.article
    LEFT JOIN ytd_ranks ON articles.id=ytd_ranks.article
    LEFT JOIN month_ranks ON articles.id=month_ranks.article
    WHERE articles.id=%s
  """, (id,))   # TODO: Store this somewhere? It's used in author_details too (though modified)
  if len(paperq) == 0:
    raise NotFoundError(id)
  # if len(paperq) > 1:
    # raise ValueError("Multiple papers found with id {}".format(id))
  paperq = paperq[0]
  # TODO: Figure out which join clause in the query makes a bunch of
  # identical responses come back for this
  result = models.ArticleDetails(paperq, alltime_count, connection)

  # once we're done processing the results of the last query, go back
  # and query for some extra info about each article
  query = "SELECT COUNT(id) FROM articles WHERE collection=%s"
  collection_count = connection.read(query, (result.collection,))
  result.ranks.collection.out_of = collection_count[0][0]

  return result