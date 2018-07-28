class SiteStats(object):
  def __init__(self, authors=0, papers=0):
    self.author_count = authors
    self.paper_count = papers

def get_stats(connection):
  result = SiteStats()
  resp = connection.read("SELECT COUNT(id) FROM articles;")
  if len(resp) != 1 or len(resp[0]) != 1:
    return result
  result.paper_count = resp[0][0]

  resp = connection.read("SELECT COUNT(id) FROM authors;")
  if len(resp) != 1 or len(resp[0]) != 1:
    return result
  result.author_count = resp[0][0]
  return result

class Author(object):
  def __init__(self, id, first, last):
    self.id = id
    self.given = first
    self.surname = last
    if self.surname != "": # TODO: verify this actually works for one-name authors
      self.full = "{} {}".format(self.given, self.surname)
    else:
      self.full = self.given
    
    self.articles = []

def get_authors(connection, id):
  """Returns a list of authors associated with a single paper.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the article being queried.
    - full: whether to give the "full" author record,
            separating given name and surname, or just
            return a simplified version that's just a
            string with the person's name.

  """

  author_data = connection.read("SELECT authors.id, authors.given, authors.surname FROM article_authors as aa INNER JOIN authors ON authors.id=aa.author WHERE aa.article={};".format(id))
  return [Author(a[0], a[1], a[2]) for a in author_data]

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