"""Data models used to organize data mostly for sending to the presentation layer.


"""
import math

import helpers

class PaperQueryResponse(object):
  def __init__(self, results, query, timeframe, category_filter, metric, entity, current_page, page_size, totalcount):
    self.results = results
    self.query = query
    self.timeframe = timeframe
    self.category_filter = category_filter
    self.metric = metric
    self.entity = entity
    self.current_page = current_page
    self.page_size = page_size
    self.final_page = math.ceil(totalcount / page_size) - 1 # zero-indexed

  def json(self):
    return {
      "query": {
        "text_search": self.query,
        "timeframe": self.timeframe,
        "categories": self.category_filter,
        "metric": self.metric,
        "page_size": self.page_size,
        "current_page": self.current_page,
        "final_page": self.final_page
      },
      "results": {
        "ids": [r.id for r in self.results],
        "items": [r.json() for r in self.results]
      }
    }

class Author(object):
  """Class organizing the basic facts about a single
  author. Most other traits (rankings, a list of all
  publications, etc.) is appended later.
  """
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
    self.alltime_rank = RankEntry()
    self.categories = []

  def json(self, full=True):
    return {
      "id": self.id,
      "name": self.full,
    }

class DateEntry(object):
  "Stores paper publication date info."
  def __init__(self, month, year):
    self.month = month
    self.year = year
    self.monthname = helpers.num_to_month(month)

class RankEntry(object):
  """Stores data about a paper's rank within a
  single corpus."""
  def __init__(self, rank=0, out_of=0, tie=False, downloads=0, category="alltime"):
    self.category = category
    self.downloads = downloads
    self.rank = rank
    self.out_of = out_of
    self.tie = tie

class ArticleRanks(object):
  """Stores information about all of an individual article's
  rankings.
  """
  def __init__(self, alltime_count, alltime, ytd, lastmonth, collection):
    self.alltime = RankEntry(alltime, alltime_count)
    self.ytd = RankEntry(ytd, alltime_count)
    self.lastmonth = RankEntry(lastmonth, alltime_count)
    self.collection = RankEntry(collection)

  def json(self):
    return {
      "alltime": {
        "rank": self.alltime.rank,
        "tie": self.alltime.tie
      },
      "ytd": {
        "rank": self.ytd.rank,
        "tie": self.ytd.tie
      },
      "lastmonth": {
        "rank": self.lastmonth.rank,
        "tie": self.lastmonth.tie
      },
      "category": {
        "rank": self.lastmonth.rank,
        "tie": self.lastmonth.tie
      }
    }

class Article:
  """Base class for the different formats in which articles
  are presented throughout the site.
  """
  def __init__(self, a_id=None):
    self.id = a_id
    pass

  def get_authors(self, connection):
    """Fetches information about the paper's authors.

    Arguments:
      - connection: a database connection object.
    Returns nothing. Sets the article's "authors" field to
      a list of Author objects.

    """
    author_data = connection.read("SELECT authors.id, authors.given, authors.surname FROM article_authors as aa INNER JOIN authors ON authors.id=aa.author WHERE aa.article=%s ORDER BY aa.id;", (self.id,))
    self.authors = [Author(a[0], a[1], a[2]) for a in author_data]

  def GetDetailedTraffic(self, connection):
    data = connection.read("SELECT month, year, pdf, abstract FROM article_traffic WHERE article_traffic.article=%s ORDER BY year ASC, month ASC;", (self.id,))
    self.traffic = [TrafficEntry(entry) for entry in data]

class TrafficEntry(object):
  def __init__(self, sql_entry):
    self.month = sql_entry[0]
    self.year = sql_entry[1]
    self.downloads = sql_entry[2]
    self.views = sql_entry[3]

class SearchResultArticle(Article):
  "An article as displayed on the main results page."
  def __init__(self, sql_entry, connection):
    self.downloads = sql_entry[0] # NOTE: This can be "downloads" OR "tweet count"
    self.id = sql_entry[1]
    self.url = sql_entry[2]
    self.title = sql_entry[3]
    self.abstract = sql_entry[4]
    self.collection = sql_entry[5]
    self.date = DateEntry(sql_entry[6], sql_entry[7])
    self.posted = sql_entry[8]
    self.doi = sql_entry[9]
    self.get_authors(connection)

  def json(self):
    return {
      "id": self.id,
      "metric": self.downloads,
      "title": self.title,
      "url": self.url,
      "doi": self.doi,
      "collection": self.collection,
      "first_posted": self.posted.strftime('%d-%m-%Y') if self.posted is not None else "",
      "abstract": self.abstract,
      "authors": [x.full for x in self.authors]
    }

class SearchResultAuthor(object):
  "An author as displayed on the main results page."
  def __init__(self, id, first, last, rank, downloads, tie):
    self.id = id
    self.given = first
    self.surname = last
    if self.surname != "":
      self.full = "{} {}".format(self.given, self.surname)
    else:
      self.full = self.given
    self.rank = RankEntry(rank, 0, tie, downloads)

class TableSearchResultArticle(Article):
  "An article as displayed on the table-based main results page."
  def __init__(self, sql_entry, connection):
    self.alltime_downloads = sql_entry[0]
    self.ytd_downloads = sql_entry[1]
    self.month_downloads = sql_entry[2]
    self.id = sql_entry[3]
    self.url = sql_entry[4]
    self.title = sql_entry[5]
    self.abstract = sql_entry[6]
    self.collection = sql_entry[7]
    self.date = DateEntry(sql_entry[8], sql_entry[9])
    # NOTE: We won't get authors for these results until there's
    # a way to fetch the first author without sending a separate
    # query for each paper in the table.

class ArticleDetails(Article):
  "Detailed article info displayed on, i.e. author pages."
  def __init__(self, sql_entry, alltime_count, connection):
    self.downloads = sql_entry[0]
    self.ranks = ArticleRanks(alltime_count, sql_entry[1], sql_entry[2], sql_entry[3], sql_entry[9])
    self.id = sql_entry[4]
    self.url = sql_entry[5]
    self.title = sql_entry[6]
    self.abstract = sql_entry[7]
    self.collection = sql_entry[8]
    self.date = DateEntry(sql_entry[10], sql_entry[11])
    self.doi = sql_entry[12]
    self.get_authors(connection)

  def json(self):
    return {
      "id": self.id,
      "doi": self.doi,
      "biorxiv_url": self.url,
      "url": "https://rxivist.org/papers/{}".format(self.id),
      "title": self.title,
      "abstract": self.abstract,
      "category": self.collection,
      "downloads": self.downloads,
      "authors": [x.json() for x in self.authors],
      "ranks": self.ranks.json()
    }
