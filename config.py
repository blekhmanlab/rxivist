"""Application-specific settings and configuration to
dictate the behavior of the API.

"""

import os

cache = {
  "front_page": 600,
  "simple": 7200,
  "paper": 604800, # 1 week
  "author": 604800 # 1 week
}

# For the "summary statistics" endpoint, the download metrics
# for a given month are hidden until X days after the month has
# ended, because those numbers could lag weeks behind the calendar
# date. This setting indicates how many days should elapse before
# a month's download numbers should be included.
summary_download_age = 14

# Information about how to connect to a postgres database will
# all the Rxivist data
db = {
  "host": os.environ['RX_DBHOST'],
  "db": "rxdb",
  "user": os.environ['RX_DBUSER'],
  "password": os.environ['RX_DBPASSWORD'],
  "schema": 'prod', # Each environment has a schema, theoretically
  "connection": {
    "timeout": 3,
    "max_attempts": 10,
    "attempt_pause": 3, # how long to wait between connection attempts
  },
}

# Hostname (and protocol) where users will find your site.
# This is needed to build redirect URLs that don't
# break when the web server is behind a reverse proxy.
host = "https://api.url_goes_in_here.org"

# Whether to launch the application with gunicorn as the web server, or
# with Bottle's default. The default can be handy for development because
# it includes the option to reload the application any time there is a
# code change.
use_prod_webserver = True

# how many search results are returned at a time
default_page_size = 20

# the most results an API user can request at one time
max_page_size = 250

# Amount of time that can pass since an article has been updated before
# it is included in the tally of "outdated" articles
outdated_limit = "4 weeks"

# When displaying a leaderboard of author rankings, how many names should appear
author_ranks_limit = 200
