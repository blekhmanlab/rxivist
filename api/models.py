import helpers

class SiteStats(object):
  def __init__(self, connection):
    resp = connection.read("SELECT COUNT(id) FROM articles;")
    if len(resp) != 1 or len(resp[0]) != 1:
      self.paper_count = 0
    else:
      self.paper_count = resp[0][0]

    resp = connection.read("SELECT COUNT(id) FROM authors;")
    if len(resp) != 1 or len(resp[0]) != 1:
      self.author_count = 0
    else:
      self.author_count = resp[0][0]

class Author(object):
  def __init__(self, id, first, last):
    self.id = id
    self.articles = []
    self.given = first
    self.surname = last
    if self.surname != "":
      self.full = "{} {}".format(self.given, self.surname)
    else:
      self.full = self.given
    self.downloads = 0
    self.rank = RankEntry()

class DateEntry(object):
  # Used to store paper publication date info
  def __init__(self, month, year):
    self.month = month
    self.year = year
    self.monthname = helpers.month_name(month)

class RankEntry(object):
  def __init__(self, rank=0, out_of=0, tie=False):
    self.rank = rank
    self.out_of = out_of
    self.tie = tie

class ArticleRanks(object):
  # Stores information about an individual article's rankings
  def __init__(self, alltime_count, alltime, ytd, lastmonth, collection):
    self.alltime = RankEntry(alltime, alltime_count)
    self.ytd = RankEntry(ytd, alltime_count)
    self.lastmonth = RankEntry(lastmonth, alltime_count)
    self.collection = RankEntry(collection)

class Article:
  def __init(self):
    pass

  def get_authors(self, connection):
    author_data = connection.read("SELECT authors.id, authors.given, authors.surname FROM article_authors as aa INNER JOIN authors ON authors.id=aa.author WHERE aa.article=%s;", (self.id,))
    self.authors = [Author(a[0], a[1], a[2]) for a in author_data]

class SearchResultArticle(Article):
  # An article as displayed on the main results page
  def __init__(self, sql_entry, connection):
    self.downloads = sql_entry[0]
    self.id = sql_entry[1]
    self.url = sql_entry[2]
    self.title = sql_entry[3]
    self.abstract = sql_entry[4]
    self.collection = sql_entry[5]
    self.date = DateEntry(sql_entry[6], sql_entry[7])
    self.get_authors(connection)

class ArticleDetails(Article):
  # detailed article info displayed on, i.e. author pages
  def __init__(self, sql_entry, alltime_count, connection):
    self.downloads = sql_entry[0]
    self.ranks = ArticleRanks(alltime_count, sql_entry[1], sql_entry[2], sql_entry[3], sql_entry[9])
    self.id = sql_entry[4]
    self.url = sql_entry[5]
    self.title = sql_entry[6]
    self.abstract = sql_entry[7]
    self.collection = sql_entry[8]
    self.date = DateEntry(sql_entry[10], sql_entry[11])
    self.get_authors(connection)
