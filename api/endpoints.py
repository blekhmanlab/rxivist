import bottle
import db

class NotFoundError(Exception):
  def __init__(self, id):
    self.message = "Entity could not be found with id {}".format(id)

def get_authors(connection, id, full=False):
  # Returns the authors associated with a given article ID. If "full" is
  # true, the response separates given and surnames
  authors = []
  author_data = connection.read("SELECT authors.given, authors.surname FROM article_authors as aa INNER JOIN authors ON authors.id=aa.author WHERE aa.article={};".format(id))
  if full: return author_data

  for a in author_data:
    if len(a) > 1:
      authors.append("{} {}".format(a[0], a[1]))
    else: # TODO: verify this actually works for one-name authors
      authors.append(a[0])
  return authors

def get_traffic(connection, id):
  traffic = connection.read("SELECT SUM(abstract), SUM(pdf) FROM article_traffic WHERE article={};".format(id))
  if len(traffic) == 0:
    raise NotFoundError(id)
  return traffic[0] # array of tuples

def get_papers(connection):
  # TODO: Memoize this response
  results = {}
  articles = connection.read("SELECT * FROM articles;")
  for article in articles:
    results[article[0]] = {
      "id": article[0],
      "url": article[1],
      "title": article[2],
      "abstract": article[3],
      "authors": get_authors(connection, article[0])
    }
  return results

def most_popular(connection):
  results = {"results": []} # can't return a list
  articles = connection.read("SELECT r.rank, r.downloads, a.id, a.url, a.title, a.abstract FROM articles as a INNER JOIN alltime_ranks as r ON r.article=a.id ORDER BY r.rank LIMIT 20;")
  for article in articles:
    results["results"].append({
      "rank": article[0],
      "downloads": article[1],
      "id": article[2],
      "url": article[3],
      "title": article[4],
      "abstract": article[5],
      "authors": get_authors(connection, article[2])
    })
  return results

def paper_details(connection, id):
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

  articles = connection.read("SELECT alltime_ranks.rank, alltime_ranks.downloads, articles.id, articles.url, articles.title, articles.abstract FROM articles INNER JOIN article_authors ON article_authors.article=articles.id LEFT JOIN alltime_ranks ON articles.id=alltime_ranks.article WHERE article_authors.author={}".format(id))

  alltime_count = connection.read("SELECT COUNT(article) FROM alltime_ranks")
  alltime_count = alltime_count[0][0]

  for article in articles:
    result["articles"].append({
      "rank": article[0],
      "out_of": alltime_count,
      "downloads": article[1],
      "id": article[2],
      "url": article[3],
      "title": article[4],
      "abstract": article[5],
      "authors": get_authors(connection, article[2])
    })

  return result
