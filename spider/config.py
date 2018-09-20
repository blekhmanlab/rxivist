import os

db = {
  "host": os.environ['RX_DBHOST'],
  "db": "rxdb",
  "user": "root",
  "password": os.environ['RX_DBPASSWORD']
}

log_level = "debug"

# how the web crawler should identify itself when sending http requests
# to sites such as bioRxiv and altmetric
user_agent = "rxivist web crawler (rxivist.org)"

# this is just for testing, so we don't crawl
# the whole site during development TODO delete
TESTING = False

# how many pages to grab from a single collection
# before bailing, if TESTING is True
testing_pagecount = 50

# whether to add pauses at several places in the crawl
polite = True

# whether to stop crawling once we've encountered a set
# number of papers that we've already recorded. setting this
# to 0 would make sense, except if papers are added to a
# collection WHILE you're indexing it, the crawler dies early.
# (if this is set to False, the crawler will go through every
# single page of results for a collection, which is probably
# wasteful.)
stop_on_recognized = True

# if stop_on_recognized is True, how many papers we have
# to recognize *in a row* before we assume that we've indexed
# all the papers at that point in the chronology.
recognized_limit = 18

# When writing a large number of rows to the database (during
# the ranking of authors and papers), a helper function can
# log progress through the process. This is how many rows should
# be written before each update.
progress_update_interval = 10000

# The crawler uses temporary files to speed up database writes.
# Setting this flag to True will delete them after they're processed.
delete_csv = True

# When updating the statistics of papers that probably have new
# download information ready, we don't have to get every single
# outdated paper in one run of the spider. limit_refresh caps
# how many "refresh download stats" calls are made before the
# crawler just leaves the rest for next time.
# refresh_interval is a string expressing how old a paper's
# stats should be before we refresh them. (This string MUST
# be able to be interpreted by Postgres as a time interval
# to subtract from the current date.)
refresh_interval = "4 weeks"
limit_refresh = True
refresh_session_cap = 700

# information about the altmetric API endpoints
altmetric = {
  "endpoints": {
    "daily": "https://api.altmetric.com/v1/citations/1d"
  },
  "doi_prefix": "10.1101"
}
# TODO: Validate that DOI prefix 10.1101 is bioRxiv, and that we won't miss
# papers that somehow get another prefix.

# information about the biorxiv web addresses to be scraped
biorxiv = {
  "endpoints": {
    "collection": "https://www.biorxiv.org/collection"
  }
}

perform_ranks = {
  "alltime": True,
  "ytd": True,
  "month": True,
  "bouncerate": False,
  "authors": True,
  "article_categories": True,
  "author_categories": True
}

# The graphs for the distribution of downloads for articles and authors
# uses a log scale because the data is so heavily skewed toward the beginning
# of the distribution. This controls the base of the log. (2 would be most
# expected here, but that tends to result in a very compressed-looking graph
# with buckets that are too large to be interesting.)
distribution_log_articles = 1.5
distribution_log_authors = 1.5
