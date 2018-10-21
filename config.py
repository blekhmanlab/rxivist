"""Application-specific settings and configuration to
dictate the behavior of the API.

"""

import os

# Information about how to connect to a postgres database will
# all the Rxivist data
db = {
  "host": os.environ['RX_DBHOST'],
  "db": "rxdb",
  "user": "root",
  "password": os.environ['RX_DBPASSWORD'],
  "connection": {
    "timeout": 3,
    "max_attempts": 10,
    "attempt_pause": 3, # how long to wait between connection attempts
  },
}

host = "api.rxivist.org" # for building redirects behind a CDN

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
