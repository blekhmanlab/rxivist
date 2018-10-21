import os

# Information about how to connect to a postgres database will
# all the Rxivist data
db = {
  "host": os.environ['RX_DBHOST'],
  "db": "rxdb",
  "user": "root",
  "password": os.environ['RX_DBPASSWORD']
}

# How much output to send to application logs
log_level = "debug"
# Whether to print messages to stdout
log_to_stdout = True
# Whether to record messages in a timestamped file
log_to_file = False

# how the web crawler should identify itself when sending http requests
# to sites such as bioRxiv and crossref
user_agent = "rxivist web crawler (rxivist.org)"

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

# The crawler uses temporary files to speed up database writes.
# Setting this flag to True will delete them after they're processed.
delete_csv = True

# When updating the statistics of papers that probably have new
# download information ready, we don't have to get every single
# outdated paper in one run of the spider. limit_refresh caps
# how many "refresh download stats" calls are made for a single
# category before the crawler just leaves the rest for next time.
# refresh_category_cap states how many articles should be refreshed
# in a single collection before the spider moves on to the next.
# refresh_interval is a string expressing how old a paper's
# stats should be before we refresh them. (This string MUST
# be able to be interpreted by Postgres as a time interval
# to subtract from the current date.)
refresh_interval = "4 weeks"
limit_refresh = True
refresh_category_cap = 100

# information about the biorxiv web addresses to be scraped
biorxiv = {
  "endpoints": {
    "collection": "https://www.biorxiv.org/collection",
    "pub_doi": "https://connect.biorxiv.org/bx_pub_doi_get.php"
  }
}

crossref = {
  "endpoints": {
    "events": "https://api.eventdata.crossref.org/v1/events"
  },
  "parameters": {
    "email": "blekhmanlab@gmail.com" # an email address to attach to each Crossref call, per their request
  }
}

rxivist = {
  "base_url": "https://rxivist.org" # used for building sitemaps
}

# Which actions to take as part of the crawling session
crawl = {
  "fetch_new": True, # Check for new papers in each collection
  "fetch_abstracts": True, # Check for any Rxivist papers missing an abstract and fill it in (Papers don't have an abstract when first crawled)
  "fetch_crossref": True, # Update daily Crossref stats
  "refresh_stats": True, # Look for articles with outdated download info and re-crawl them
}

perform_ranks = {
  "enabled": True,  # set to False to disable all below
  "alltime": True,
  "ytd": True,
  "month": True,
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
