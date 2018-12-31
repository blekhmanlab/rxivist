#     Rxivist, a system for crawling papers published on bioRxiv
#     and organizing them in ways that make it easier to find new
#     or interesting research. Includes a web application for
#     the display of data.
#     Copyright (C) 2018 Regents of the University of Minnesota

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, version 3.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

#     Any inquiries about this software or its use can be directed to
#     Professor Ran Blekhman at the University of Minnesota:
#     email: blekhman@umn.edu
#     mail: MCB 6-126, 420 Washington Avenue SE, Minneapolis, MN 55455
#     http://blekhmanlab.org/

"""Definition of web service and initialization of the server.

This is the entrypoint for the application, the script called
when the server is started and the router for all user requests.
"""
import re

import bottle

import config
import db
import endpoints
import helpers
import models

connection = db.Connection(config.db["host"], config.db["db"], config.db["user"], config.db["password"])

# - ROUTES -

#  paper query endpoint
@bottle.get('/v1/papers')
def index():
  query = bottle.request.query.q
  timeframe = bottle.request.query.timeframe
  category_filter = bottle.request.query.getall('category') # multiple params possible
  metric = bottle.request.query.metric
  entity = "papers"
  page = bottle.request.query.page
  page_size = bottle.request.query.page_size
  error = ""

  if metric not in ["downloads", "twitter"]:
    metric = "twitter"
  if metric == "twitter":
    if timeframe not in ["alltime", "day", "week", "month", "year"]:
      timeframe = "day"
  elif metric == "downloads":
    if timeframe not in ["alltime", "ytd", "lastmonth"]:
      timeframe = "alltime"

  category_list = endpoints.get_categories(connection) # list of all article categories

  # Get rid of a category filter that's just one empty parameter:
  if len(category_filter) == 1 and category_filter[0] == "":
    category_filter = []
  else:
    # otherwise validate that the categories are valid
    for cat in category_filter:
      if cat not in category_list:
        error = f"There was a problem with the submitted query: {cat} is not a recognized category."
        bottle.response.status = 500
        return {"error": error}

  if page == "" or page == None:
    page = 0
  else:
    try:
      page = int(page)
    except Exception as e:
      error = f"Problem recognizing specified page number: {e}"
  if page < 0:
    page = 0

  if page_size == "":
    page_size = config.default_page_size
  else:
    try:
      page_size = int(page_size)
    except Exception as e:
      error = f"Problem recognizing specified page size: {e}"
      page_size = 0

  if page_size > config.max_page_size:
    page_size = config.max_page_size # cap the page size users can ask for

  results = {} # a list of articles for the current page
  totalcount = 0 # how many results there are in total

  if error == "": # if nothing's gone wrong yet, fetch results:
    try:
      results, totalcount = endpoints.paper_query(query, category_filter, timeframe, metric, page, page_size, connection)
    except Exception as e:
      error = f"There was a problem with the submitted query: {e}"
      bottle.response.status = 500
      return {"error": error}

  # CACHE CONTROL
  # website front page
  if bottle.request.query_string == "":
    bottle.response.set_header("Cache-Control", f'max-age={config.cache["front_page"]}, stale-while-revalidate=172800')
  # if it's a simple query:
  if query == "" and page < 3 and page_size == config.default_page_size:
    bottle.response.set_header("Cache-Control", f'max-age={config.cache["simple"]}, stale-while-revalidate=172800')

  resp = models.PaperQueryResponse(results, query, timeframe, category_filter, metric, page, page_size, totalcount)
  return resp.json()

# paper details
@bottle.get('/v1/papers/<id:path>')
def paper_details(id):
  print(f"GOT {id}")
  # if the ID passed in isn't an integer, assume it's a DOI
  try:
    article_id = int(id)
  except Exception:
    print("\n\n\nNOT AN INT")
    new_id = helpers.doi_to_id(id, connection)
    print(f'New ID is {new_id}')
    if new_id:
      print(f"{config.host}/v1/papers/{new_id}")
      return bottle.redirect(f"{config.host}/v1/papers/{new_id}", 301)
    else:
      bottle.response.status = 404
      return {"error": "Could not find bioRxiv paper with that DOI"}
  try:
    paper = endpoints.paper_details(id, connection)
  except helpers.NotFoundError as e:
    bottle.response.status = 404
    return {"error": e.message}
  except ValueError as e:
    bottle.response.status = 500
    return {"error": f"Server error – {e}"}
  return paper.json()

# paper download stats
@bottle.get('/v1/downloads/<id>')
def paper_downloads(id):
  try:
    details = endpoints.paper_downloads(id ,connection)
  except helpers.NotFoundError as e:
    bottle.response.status = 404
    return {"error": e.message}
  except ValueError as e:
    bottle.response.status = 500
    return {"error": f"Server error – {e}"}
  return details

# author rankings
@bottle.get('/v1/authors')
def alltime_author_ranks():
  category = bottle.request.query.category
  resp = endpoints.author_rankings(connection, category)
  return {
    "results": [x.json() for x in resp]
  }

# author details page
@bottle.get('/v1/authors/<author_id:int>')
def display_author_details(author_id):
  if author_id < 200000: # old author pages indexed by google already
    new_id = helpers.find_new_id(author_id, connection)
    if new_id:
      return bottle.redirect(f"{config.host}/v1/authors/{new_id}", 301)
    else:
      bottle.response.status = 404
      return {"error": f"Could not find author with ID {author_id}"}
  try:
    author = endpoints.author_details(author_id, connection)
  except helpers.NotFoundError as e:
    bottle.response.status = 404
    return {"error": e.message}
  except ValueError as e:
    bottle.response.status = 500
    return {"error": f"Server error – {e}"}
  return author.json()

@bottle.get('/v1/top/<year:int>')
def alltime_author_ranks(year):
  resp = endpoints.top_year(year, connection)
  # bottle.response.set_header("Cache-Control", f'max-age=15552000, stale-while-revalidate=15552000')
  return {
    "results": [x.json() for x in resp]
  }

# categories list endpoint
@bottle.get('/v1/data/categories')
def get_category_list():
  try:
    category_list = endpoints.get_categories(connection)
  except Exception as e:
    bottle.response.status = 500
    return {"error": f"Server error – {e}"}
  return {
    "results": category_list
  }

# stat distributions endpoint
@bottle.get('/v1/data/distributions/<entity>/<metric>')
def get_distros(entity, metric):
  if entity not in ["paper", "author"]:
    bottle.response.status = 404
    return {"error": f"Unknown entity: expected 'paper' or 'author'; got '{entity}'"}
  if metric not in ["downloads"]:
    bottle.response.status = 404
    return {"error": f"Unknown entity: expected 'downloads'; got '{metric}'"}

  try:
    results, averages = endpoints.get_distribution(entity, metric, connection)
  except Exception as e:
    bottle.response.status = 500
    return {"error": f"Server error – {e}"}
  return {
    "histogram": [{"bucket_min": x[0], "count": x[1]} for x in results],
    "averages": {
      "mean": averages["mean"],
      "median": averages["median"]
    }
  }

@bottle.get('/v1/data/stats')
def get_counts():
  return endpoints.site_stats(connection)

# ---- Errors
@bottle.error(404)
def error404(error):
  bottle.response.set_header("Content-Type", "application/json")
  return "{\"error\": \"unrecognized URL\"}"

# - SERVER -
if config.use_prod_webserver:
  bottle.run(host='0.0.0.0', port=80, server="gunicorn")
else:
  bottle.run(host='0.0.0.0', port=80, debug=True, reloader=True)
