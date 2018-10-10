import os

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

# Whether to launch the application with gunicorn as the web server, or
# with Bottle's default. The default can be handy for development because
# it includes the option to reload the application any time there is a
# code change.
use_prod_webserver = False

# how many search results are returned at a time
default_page_size = 20

# the largest page a web user can request
max_page_size_site = 100
# the most results an API user can request at one time
max_page_size_api = 250

# The entity ID provided by Google Analytics
google_tag = "UA-125076477-1"
# The validation file provided by the Google Webmaster Tools.
# (Should be placed in the /static directory)
google_validation_file = "google3d18e8a680b87e67.html"

# Whether to allow access to the /db endpoints. Should be FALSE in production.
allow_db_dashboard = True

# When accessing a table's data in the db admin dashboard, the maximum number of
# results to display.
db_admin_return_limit = 100

# When displaying a leaderboard of author rankings, how many names should appear
author_ranks_limit = 200
