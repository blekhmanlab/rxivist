import os

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
refresh_interval = "14 days"
limit_refresh = True
refresh_category_cap = 250

# Which actions to take as part of the crawling session
crawl = {
  "fetch_new": True, # Check for new papers in each collection
  "fetch_crossref": False, # Update daily Crossref stats
  "refresh_stats": False, # Look for articles with outdated download info and re-crawl them
  "fetch_pubstatus": True, # Check for whether a paper has been published during stat refresh
  "fetch_pubdates": True, # Check for publication dates for any papers that have been published
  "fetch_missing_fields": True # Get URLs and dates for papers that are missing them
}

repos = {
  'biorxiv': False,
  'medrxiv': True
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

# Information about how to connect to a postgres database will
# all the Rxivist data
db = {
  "host": os.environ['RX_DBHOST'],
  "db": "rxdb",
  "user": "root",
  "password": os.environ['RX_DBPASSWORD'],
  "schema": "prod"
}

# How much output to send to application logs
log_level = "info"
# Whether to print messages to stdout
log_to_stdout = False
# Whether to record messages in a timestamped file
log_to_file = True

# how the web crawler should identify itself when sending http requests
# to sites such as bioRxiv and crossref
user_agent = "rxivist web crawler (YOUR_URL_HERE.org)"

# whether to add pauses at several places in the crawl
polite = True

# Occasionally, the bioRxiv endpoint we use to check the publication status
# of a preprint will stop responding. Pausing for a minute generally fixes this,
# but sometimes it doesn't. If reset_pubstatus is set to True, consecutive errors
# from the publication status endpoint will trigger a change that simply stops
# calling that endpoint for the current web crawling session. Set this to False
# if you would rather the spider exit completely instead of just not checking
# the status.
reset_pubstatus = False

# whether to stop crawling once we've encountered a set
# number of papers that we've already recorded. setting this
# to 0 would make sense, except if papers are added to a
# collection WHILE you're indexing it, the crawler dies early.
# (if this is set to False, the crawler will go through every
# single page of results for a collection, which is probably
# wasteful.)
stop_on_recognized = True

# The crawler uses temporary files to speed up database writes.
# Setting this flag to True will delete them after they're processed.
delete_csv = True

# Normally, a paper's author list is refreshed only when a revision is
# posted, NOT when the download stats are periodically updated. Flip this
# setting to True to re-evaluate the authors every time.
record_authors_on_refresh = False

# information about the biorxiv web addresses to be scraped
biorxiv = {
  "endpoints": {
    "collection": "https://www.biorxiv.org/collection",
    "recent": "https://www.biorxiv.org/content/early/recent",
    "api": "https://api.biorxiv.org"
  }
}

crossref = {
  "endpoints": {
    "events": "https://api.eventdata.crossref.org/v1/events"
  },
  "parameters": {
    "email": "rxivist@YOUR_URL_HERE.org" # an email address to attach to each Crossref call, per their request
  }
}

# The graphs for the distribution of downloads for articles and authors
# uses a log scale because the data is so heavily skewed toward the beginning
# of the distribution. This controls the base of the log. (2 would be most
# expected here, but that tends to result in a very compressed-looking graph
# with buckets that are too large to be interesting.)
distribution_log_articles = 1.5
distribution_log_authors = 1.5
