"""Functions linked directly to functionality called from API endpoints.

This module is used to pull logic out of the controllers in main.py.
Some of these functions maybe called from MULTIPLE controllers, so
look around before modifying the API of one of them.
"""

import bottle
import db
import helpers

class NotFoundError(Exception):
  def __init__(self, id):
    self.message = "Entity could not be found with id {}".format(id)

class DateEntry(object):
  # Used to store paper publication date info
  def __init__(self, month, year):
    self.month = month
    self.year = year
    self.monthname = helpers.month_name(month)

class SearchResultArticle(object):
  # An article as displayed on the main results page
  def __init__(self, sql_entry, connection):
    self.downloads = sql_entry[0]
    self.id = sql_entry[1]
    self.url = sql_entry[2]
    self.title = sql_entry[3]
    self.abstract = sql_entry[4]
    self.collection = sql_entry[5]
    self.date = DateEntry(sql_entry[6], sql_entry[7])
    self.authors = helpers.get_authors(connection, self.id)

class RankEntry(object):
  def __init__(self, rank, out_of=0):
    self.rank = rank
    self.out_of = out_of

class ArticleRanks(object):
  # Stores information about an individual article's rankings
  def __init__(self, alltime_count, alltime, ytd, collection):
    self.alltime = RankEntry(alltime, alltime_count)
    self.ytd = RankEntry(ytd, alltime_count)
    self.collection = RankEntry(collection)

class ArticleDetails(object):
  # detailed article info displayed on, i.e. author pages
  def __init__(self, sql_entry, alltime_count, connection):
    self.downloads = sql_entry[0]
    self.ranks = ArticleRanks(alltime_count, sql_entry[1], sql_entry[2], sql_entry[8])
    self.id = sql_entry[3]
    self.url = sql_entry[4]
    self.title = sql_entry[5]
    self.abstract = sql_entry[6]
    self.collection = sql_entry[7]
    self.date = DateEntry(sql_entry[9], sql_entry[10])
    self.authors = helpers.get_authors(connection, self.id)

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

def most_popular_alltime(connection, q, categories):
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
  if q != "": # if there's a text search specified
    params = (q,)
    query = """
    SELECT r.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.origin_month, a.origin_year, ts_rank_cd(totalvector, query) as rank
    FROM articles AS a
    INNER JOIN alltime_ranks AS r ON r.article=a.id,
      to_tsquery(%s) query,
      coalesce(setweight(a.title_vector, 'A') || setweight(a.abstract_vector, 'D')) totalvector
    WHERE query @@ totalveactor """
    if len(categories) > 0:
      query += "AND collection=ANY(%s) "
      params = (q,categories)
    query += "ORDER BY r.rank ASC LIMIT 20;"
  elif len(categories) > 0: # if it's just category filters
    params = (categories,)
    query = """
      SELECT r.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.origin_month, a.origin_year
      FROM articles as a
      INNER JOIN alltime_ranks as r ON r.article=a.id
      WHERE collection=ANY(%s)
      ORDER BY r.rank LIMIT 20;
    """
  else: # just show all-time ranks
    params = ()
    query = "SELECT r.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.origin_month, a.origin_year FROM articles as a INNER JOIN alltime_ranks as r ON r.article=a.id ORDER BY r.rank LIMIT 20;"
  with connection.db.cursor() as cursor:
    cursor.execute(query, params)
    results = [SearchResultArticle(a, connection) for a in cursor]
  return results

def author_details(connection, id):
  """Returns a dict of information about a single author, including a list of
      all their papers.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the author being queried.

  """

  authorq = connection.read("SELECT id, given, surname FROM authors WHERE id = {};".format(id))
  if len(authorq) == 0:
    raise NotFoundError(id)
  if len(authorq) > 1:
    raise ValueError("Multiple authors found with id {}".format(id))
  authorq = authorq[0]
  result = helpers.Author(authorq[0], authorq[1], authorq[2])

  articles = connection.read("SELECT alltime_ranks.downloads, alltime_ranks.rank, ytd_ranks.rank, articles.id, articles.url, articles.title, articles.abstract, articles.collection, articles.collection_rank, articles.origin_month, articles.origin_year FROM articles INNER JOIN article_authors ON article_authors.article=articles.id LEFT JOIN alltime_ranks ON articles.id=alltime_ranks.article LEFT JOIN ytd_ranks ON articles.id=ytd_ranks.article WHERE article_authors.author={}".format(id))

  alltime_count = connection.read("SELECT COUNT(article) FROM alltime_ranks")
  alltime_count = alltime_count[0][0] 
  # NOTE: alltime_count will not be a count of all the papers on the site,
  # it excludes papers that don't have any traffic data.

  result.articles = [ArticleDetails(a, alltime_count, connection) for a in articles]
  
  # once we're done processing the results of the last query, go back
  # and query for some extra info about each article
  for article in result.articles:
    query = "SELECT COUNT(id) FROM articles WHERE collection=%s"
    collection_count = connection.read(query, (article.collection,))
    article.ranks.collection.out_of = collection_count[0][0]

  return result
