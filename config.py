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

host = "api.rxivist.org" # for building redirects

# Whether to launch the application with gunicorn as the web server, or
# with Bottle's default. The default can be handy for development because
# it includes the option to reload the application any time there is a
# code change.
use_prod_webserver = False

# how many search results are returned at a time
default_page_size = 20

# the most results an API user can request at one time
max_page_size_api = 250

# Amount of time that can pass since an article has been updated before
# it is included in the tally of "outdated" articles
outdated_limit = "4 weeks"

# The entity ID provided by Google Analytics
google_tag = "UA-125076477-1"
# The validation file provided by the Google Webmaster Tools.
# (Should be placed in the /static directory)
google_validation_file = "google3d18e8a680b87e67.html"

# When displaying a leaderboard of author rankings, how many names should appear
author_ranks_limit = 200
