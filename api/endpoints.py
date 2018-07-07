import bottle
import db

def get_papers(connection):
  # TODO: Memoize this response
  results = {}
  articles = connection.read("SELECT * FROM articles;")
  for article in articles:
    author_data = connection.read("SELECT authors.given, authors.surname FROM article_authors as aa INNER JOIN authors ON authors.id=aa.author WHERE aa.article={};".format(article[0]))
    authors = []
    for a in author_data:
      if len(a) > 1:
        authors.append("{} {}".format(a[0], a[1]))
      else:
        authors.append(a[0])
    results[article[0]] = {
      "id": article[0],
      "url": article[1],
      "title": article[2],
      "abstract": article[3],
      "authors": authors
    }
  
  return results