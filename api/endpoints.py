"""Functions linked directly to functionality called from API endpoints.

This module is used to pull logic out of the controllers in main.py.
Some of these functions maybe called from MULTIPLE controllers, so
look around before modifying the API of one of them.
"""

import bottle
import db

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

def get_authors(connection, id, full=False):
  """Returns a list of authors associated with a single paper.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the article being queried.
    - full: whether to give the "full" author record,
            separating given name and surname, or just
            return a simplified version that's just a
            string with the person's name.

  """

  authors = []
  author_data = connection.read("SELECT authors.id, authors.given, authors.surname FROM article_authors as aa INNER JOIN authors ON authors.id=aa.author WHERE aa.article={};".format(id))
  if full: return author_data

  for a in author_data:
    name = a[1]
    if len(a) > 2: # TODO: verify this actually works for one-name authors
      name += " {}".format(a[2])
    authors.append({
      "id": a[0],
      "name": name
    })
  return authors

def get_traffic(connection, id):
  """Returns a tuple indicating a single paper's download statistics.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the article being queried.
  Returns:
    - A two-element tuple. The first element is the number of views of
        the paper's abstract; the second is total PDF downloads.

  """

  traffic = connection.read("SELECT SUM(abstract), SUM(pdf) FROM article_traffic WHERE article={};".format(id))
  if len(traffic) == 0:
    raise NotFoundError(id)
  return traffic[0] # array of tuples

def get_papers(connection):
  """Returns a list of all articles in the database.

  """
  # TODO: Update this object with all the new fields that have been added
  results = []
  articles = connection.read("SELECT * FROM articles;")
  for article in articles:
    results.append({
      "id": article[0],
      "url": article[1],
      "title": article[2],
      "abstract": article[3],
      "authors": get_authors(connection, article[0])
    })
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
  results = []
  with connection.db.cursor() as cursor:
    if q != "": # if there's a text search specified
      params = (q,)
      query = """
      SELECT r.rank, r.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.collection_rank, ts_rank_cd(totalvector, query) as rank
      FROM articles AS a
      INNER JOIN alltime_ranks AS r ON r.article=a.id,
        to_tsquery(%s) query,
        coalesce(setweight(a.title_vector, 'A') || setweight(a.abstract_vector, 'D')) totalvector
      WHERE query @@ totalvector """
      if len(categories) > 0:
        query += "AND collection=ANY(%s) "
        params = (q,categories)
      query += "ORDER BY r.rank ASC LIMIT 20;"
    elif len(categories) > 0: # if it's just category filters
      params = (categories,)
      query = """
        SELECT r.rank, r.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.collection_rank
        FROM articles as a
        INNER JOIN alltime_ranks as r ON r.article=a.id
        WHERE collection=ANY(%s)
        ORDER BY r.rank LIMIT 20;
      """
    else: # just show all-time ranks
      params = ()
      query = "SELECT r.rank, r.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.collection_rank FROM articles as a INNER JOIN alltime_ranks as r ON r.article=a.id ORDER BY r.rank LIMIT 20;"

    articles = cursor.execute(query, params)

    for article in cursor:
      results.append({
        "rank": article[0],
        "downloads": article[1],
        "id": article[2],
        "url": article[3],
        "title": article[4],
        "abstract": article[5],
        "collection": article[6],
        "collection_rank": article[7],
        "authors": get_authors(connection, article[2])
      })
  return results

def most_popular_ytd(connection):
  """Returns a list of the papers with the most downloads in the current year.

  """
  results = []
  articles = connection.read("SELECT r.rank, r.downloads, a.id, a.url, a.title, a.abstract, a.collection, a.collection_rank FROM articles as a INNER JOIN ytd_ranks as r ON r.article=a.id ORDER BY r.rank LIMIT 20;")
  for article in articles:
    results.append({
      "rank": article[0],
      "downloads": article[1],
      "id": article[2],
      "url": article[3],
      "title": article[4],
      "abstract": article[5],
      "collection": article[6],
      "collection_rank": article[7],
      "authors": get_authors(connection, article[2])
    })
  return results

def paper_details(connection, id):
  """Returns a dict of information about a single paper.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the article being queried.

  """

  result = {}
  article = connection.read("SELECT * FROM articles WHERE id = {};".format(id))
  if len(article) == 0:
    raise NotFoundError(id)
  if len(article) > 1:
    raise ValueError("Multiple articles found with id {}".format(id))
  article = article[0]

  try:
    abstract, pdf = get_traffic(connection, id)
    abstract = abstract if abstract is not None else 0
    pdf = pdf if pdf is not None else 0
  except NotFoundError:
    abstract = 0
    pdf = 0
  # TODO: add new fields
  result = {
    "id": article[0],
    "url": article[1],
    "title": article[2],
    "abstract": article[3],
    "authors": get_authors(connection, article[0], True),
    "downloads": {
      "abstract": abstract,
      "pdf": pdf
    }
  }

  return result

def author_details(connection, id):
  """Returns a dict of information about a single author, including a list of
      all their papers.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the author being queried.

  """

  result = {}
  author = connection.read("SELECT * FROM authors WHERE id = {};".format(id))
  if len(author) == 0:
    raise NotFoundError(id)
  if len(author) > 1:
    raise ValueError("Multiple authors found with id {}".format(id))
  author = author[0]

  result = {
    "id": author[0],
    "given": author[1],
    "surname": author[2],
    "articles": []
  }

  articles = connection.read("SELECT alltime_ranks.rank, ytd_ranks.rank, articles.id, articles.url, articles.title, articles.abstract, articles.collection, articles.collection_rank FROM articles INNER JOIN article_authors ON article_authors.article=articles.id LEFT JOIN alltime_ranks ON articles.id=alltime_ranks.article LEFT JOIN ytd_ranks ON articles.id=ytd_ranks.article WHERE article_authors.author={}".format(id))

  alltime_count = connection.read("SELECT COUNT(article) FROM alltime_ranks")
  alltime_count = alltime_count[0][0] 
  # NOTE: alltime_count will not be a count of all the papers on the site,
  # it excludes papers that don't have any traffic data.

  for article in articles:
    result["articles"].append({
      "ranks": {
        "alltime": {
          "rank": article[0],
          "out_of": alltime_count
        },
        "ytd": {
          "rank": article[1],
          "out_of": alltime_count
        },
        "collection": {
          "rank": article[7]
        }
      },
      "id": article[2],
      "url": article[3],
      "title": article[4],
      "abstract": article[5],
      "collection": article[6],
      "authors": get_authors(connection, article[2])
    })
  
  # once we're done processing the results of the last query, go back
  # and query for some extra info about each article
  for article in result["articles"]:
    query = "SELECT COUNT(id) FROM articles WHERE collection=%s"
    collection_count = connection.read(query, (article["collection"],))
    article["ranks"]["collection"]["out_of"] = collection_count[0][0]

  return result
