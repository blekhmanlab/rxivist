"""Data models used to organize data mostly for sending to the presentation layer.


"""
import math

import db
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
    self.totalcount = totalcount

  def json(self):
    return {
      "query": {
        "text_search": self.query,
        "timeframe": self.timeframe,
        "categories": self.category_filter,
        "metric": self.metric,
        "page_size": self.page_size,
        "current_page": self.current_page,
        "final_page": self.final_page,
        "total_results": self.totalcount
      },
      "results": [r.json() for r in self.results]
    }

class Author:
  def __init__(self, author_id, name=""):
    self.id = author_id
    # Setting the name initially lets us skip all the extra DB calls when
    # pulling together a list of authors for which we don't need even the
    # basic info
    self.name = name
    self.has_full_info = False
    self.has_basic_info = False

  def GetInfo(self, connection):
    self.name, self.institution, self.orcid = self._find_vitals(connection)
    self.articles = self._find_articles(connection)
    self.emails = self._find_emails(connection)
    self.ranks = self._find_ranks(connection)
    self.has_full_info = True

  def GetBasicInfo(self, connection):
    self.name, self.institution, self.orcid = self._find_vitals(connection)
    self.has_basic_info = True

  def json(self):
    if self.has_full_info:
      return {
        "id": self.id,
        "name": self.name,
        "institution": self.institution,
        "orcid": self.orcid,
        "emails": self.emails,
        "articles": [x.json() for x in self.articles],
        "ranks": [x.json() for x in self.ranks]
      }
    elif self.has_basic_info:
      return {
        "id": self.id,
        "name": self.name,
        "institution": self.institution,
        "orcid": self.orcid
      }
    else:
      return {
        "id": self.id,
        "name": self.name
      }

  def _find_vitals(self, connection):
    authorq = connection.read("SELECT name, institution, orcid FROM detailed_authors WHERE id = %s;", (self.id,))
    if len(authorq) == 0:
      raise helpers.NotFoundError(id)
    if len(authorq) > 1:
      raise ValueError("Multiple authors found with id {}".format(id))
    name, institution, orcid = authorq[0]
    if institution == "":
      institution = None
    if orcid == "":
      orcid = None
    return name, institution, orcid

  def _find_articles(self, connection):
    sql = """
      SELECT articles.id
      FROM articles
      LEFT JOIN article_detailed_authors ON articles.id=article_detailed_authors.article
      LEFT JOIN alltime_ranks ON articles.id=alltime_ranks.article
      WHERE article_detailed_authors.author=%s ORDER BY alltime_ranks.downloads DESC
    """
    articles = connection.read(sql, (self.id,))
    articles = [AuthorArticle(a[0], connection) for a in articles]

    for article in articles:
      query = "SELECT COUNT(id) FROM articles WHERE collection=%s"
      collection_count = connection.read(query, (article.collection,))
      article.ranks.collection.out_of = collection_count[0][0]

    return articles

  def _find_emails(self, connection):
    emails = []
    emailq = connection.read("SELECT email FROM detailed_authors_email WHERE author=%s;", (self.id,))
    for entry in emailq:
      emails.append(entry[0])
    return emails

  def _find_ranks(self, connection):
    ranks = []
    downloadsq = connection.read("SELECT rank, tie, downloads FROM detailed_author_ranks WHERE author=%s;", (self.id,))
    if len(downloadsq) == 1:
      author_count = connection.read("SELECT COUNT(id) FROM detailed_authors;")
      author_count = author_count[0][0]
      ranks.append(AuthorRankEntry(downloadsq[0][0], author_count, downloadsq[0][1], downloadsq[0][2], "alltime"))

    categoryq = connection.read("SELECT rank, tie, downloads, category FROM detailed_author_ranks_category WHERE author = %s;", (self.id,))
    for cat in categoryq:
      authors_in_category = connection.read("SELECT COUNT(author) FROM detailed_author_ranks_category WHERE category=%s", (cat[3],))
      authors_in_category = authors_in_category[0][0]
      entry = AuthorRankEntry(cat[0], authors_in_category, cat[1], cat[2], cat[3]) # TODO: this is all wrong
      ranks.append(entry)

    return ranks

class DateEntry(object):
  "Stores paper publication date info."
  def __init__(self, month, year):
    self.month = month
    self.year = year
    self.monthname = helpers.num_to_month(month)

class ArticleRankEntry(object):
  """Stores data about a paper's rank within a
  single corpus."""
  def __init__(self, rank=0, out_of=0, tie=False, downloads=0):
    self.downloads = downloads
    self.rank = rank
    self.out_of = out_of
    self.tie = tie

  def json(self):
    return {
      "downloads": self.downloads,
      "rank": self.rank,
      "out_of": self.out_of,
      "tie": self.tie
    }

class AuthorRankEntry(object):
  """Stores data about an author's rank within a
  single corpus."""
  def __init__(self, rank=0, out_of=0, tie=False, downloads=0, category=""):
    self.downloads = downloads
    self.rank = rank
    self.out_of = out_of
    self.tie = tie
    self.category = category

  def json(self):
    return {
      "downloads": self.downloads,
      "rank": self.rank,
      "out_of": self.out_of,
      "tie": self.tie,
      "category": self.category
    }

class ArticleRanks(object):
  """Stores information about all of an individual article's
  rankings.
  """
  def __init__(self, article_id, connection):
    sql = """
      SELECT alltime_ranks.rank, ytd_ranks.rank,
        month_ranks.rank, category_ranks.rank, articles.collection,
        alltime_ranks.downloads, ytd_ranks.downloads, month_ranks.downloads
      FROM articles
      LEFT JOIN alltime_ranks ON articles.id=alltime_ranks.article
      LEFT JOIN ytd_ranks ON articles.id=ytd_ranks.article
      LEFT JOIN month_ranks ON articles.id=month_ranks.article
      LEFT JOIN category_ranks ON articles.id=category_ranks.article
      WHERE articles.id=%s
    """
    sql_entry = connection.read(sql, (article_id,))[0]
    category_count = connection.read("SELECT COUNT(id) FROM articles WHERE collection=%s", (sql_entry[4],))
    category_count = category_count[0][0]
    alltime_count = connection.read("SELECT COUNT(id) FROM articles")
    alltime_count = alltime_count[0][0]

    self.alltime = ArticleRankEntry(sql_entry[0], alltime_count, False, sql_entry[5])
    self.ytd = ArticleRankEntry(sql_entry[1], alltime_count, False, sql_entry[6])
    self.lastmonth = ArticleRankEntry(sql_entry[2], alltime_count, False, sql_entry[7])
    self.collection = ArticleRankEntry(sql_entry[3], category_count, False, sql_entry[5])

  def json(self):
    return {
      "alltime": self.alltime.json(),
      "ytd": self.ytd.json(),
      "lastmonth": self.lastmonth.json(),
      "category": self.collection.json(),
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
    self.authors = []
    author_data = connection.read("SELECT detailed_authors.id, detailed_authors.name FROM article_detailed_authors as aa INNER JOIN detailed_authors ON detailed_authors.id=aa.author WHERE aa.article=%s ORDER BY aa.id;", (self.id,))
    if len(author_data) > 0:
      self.authors = [Author(a[0], a[1]) for a in author_data]

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
      "first_posted": self.posted.strftime('%Y-%m-%d') if self.posted is not None else "",
      "abstract": self.abstract,
      "authors": [x.json() for x in self.authors]
    }

class SearchResultAuthor(object):
  "An author as displayed on the main results page."
  def __init__(self, id, name, rank, downloads, tie):
    self.id = id
    self.name = name
    self.rank = AuthorRankEntry(rank, 0, tie, downloads) # we don't need the "out_of" field here, so it's 0

  def json(self):
    return {
      "id": self.id,
      "name": self.name,
      "rank": self.rank.rank,
      "downloads": self.rank.downloads,
      "tie": self.rank.tie
    }

class ArticleDetails(Article):
  "Detailed article info displayed on paper pages."
  def __init__(self, article_id, connection):
    sql = """
      SELECT a.url, a.title, a.collection, a.posted, a.doi, a.abstract, p.publication, p.doi
      FROM articles a
      LEFT JOIN article_publications AS p ON a.id=p.article
      WHERE a.id=%s;
    """
    sql_entry = connection.read(sql, (article_id,))
    if len(sql_entry) == 0:
      raise helpers.NotFoundError(article_id)
    sql_entry = sql_entry[0]

    self.id = article_id
    self.url = sql_entry[0]
    self.title = sql_entry[1]
    self.collection = sql_entry[2]
    self.posted = sql_entry[3]
    self.doi = sql_entry[4]
    self.abstract = sql_entry[5]
    self.ranks = ArticleRanks(self.id, connection)
    self.get_authors(connection)
    self.publication = sql_entry[6]
    self.pub_doi = sql_entry[7]

  def json(self):
    resp = {
      "id": self.id,
      "doi": self.doi,
      "first_posted": self.posted.strftime('%Y-%m-%d') if self.posted is not None else "",
      "biorxiv_url": self.url,
      "url": "https://rxivist.org/papers/{}".format(self.id),
      "title": self.title,
      "category": self.collection,
      "abstract": self.abstract,
      "authors": [x.json() for x in self.authors],
      "ranks": self.ranks.json()
    }
    if self.pub_doi is not None:
      resp["publication"] = {
        "journal": self.publication,
        "doi": self.pub_doi
      }
    else:
      resp["publication"] = {}
    return resp

class AuthorArticle(Article):
  "Detailed article info displayed on author pages. Less data than ArticleDetails class."
  def __init__(self, article_id, connection):
    sql = """
      SELECT url, title, collection, posted, doi
      FROM articles
      WHERE articles.id=%s
    """
    sql_entry = connection.read(sql, (article_id,))
    if len(sql_entry) == 0:
      raise helpers.NotFoundError(article_id)
    sql_entry = sql_entry[0]

    self.id = article_id
    self.url = sql_entry[0]
    self.title = sql_entry[1]
    self.collection = sql_entry[2]
    self.posted = sql_entry[3]
    self.doi = sql_entry[4]
    self.ranks = ArticleRanks(self.id, connection)

  def json(self):
    return {
      "id": self.id,
      "doi": self.doi,
      "biorxiv_url": self.url,
      "url": "https://rxivist.org/papers/{}".format(self.id),
      "title": self.title,
      "category": self.collection,
      "ranks": self.ranks.json()
    }
