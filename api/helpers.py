def get_stats(connection):
  results = {"paper_count": 0, "author_count": 0}
  resp = connection.read("SELECT COUNT(id) FROM articles;")
  if len(resp) != 1 or len(resp[0]) != 1:
    return results
  results["paper_count"] = resp[0][0]

  resp = connection.read("SELECT COUNT(id) FROM authors;")
  if len(resp) != 1 or len(resp[0]) != 1:
    return results
  results["author_count"] = resp[0][0]
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

def month_name(monthnum):
  months = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
  }
  if monthnum is None or monthnum < 1 or monthnum > 12:
    return ""
  return months[monthnum]