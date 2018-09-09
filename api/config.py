import os

db = {
  "host": os.environ['RX_DBHOST'],
  "db": "rxdb",
  "user": "root",
  "password": os.environ['RX_DBPASSWORD']
}

# how many search results are returned at a time
page_size = 20

google_tag = "UA-125076477-1"