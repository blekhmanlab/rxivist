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

import db
import helpers
import endpoints
import config
import models
import docs

connection = db.Connection(config.db["host"], config.db["db"], config.db["user"], config.db["password"])

# - ROUTES -

#  paper query endpoint
@bottle.get('/api/v1/papers')
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
        error = "There was a problem with the submitted query: {} is not a recognized category.".format(cat)
        bottle.response.status = 500
        return {"error": error}

  if page == "":
    page = 0
  else:
    try:
      page = int(page)
    except Exception as e:
      error = "Problem recognizing specified page number: {}".format(e)

  if page_size == "":
    page_size = config.default_page_size
  else:
    try:
      page_size = int(page_size)
    except Exception as e:
      error = "Problem recognizing specified page size: {}".format(e)
      page_size = 0

  if page_size > config.max_page_size_api:
    page_size = config.max_page_size_api # cap the page size users can ask for

  results = {} # a list of articles for the current page
  totalcount = 0 # how many results there are in total

  if error == "": # if nothing's gone wrong yet, fetch results:
    try:
      results, totalcount = endpoints.paper_query(connection, query, category_filter, timeframe, metric, page, page_size)
    except Exception as e:
      error = "There was a problem with the submitted query: {}".format(e)
      bottle.response.status = 500
      return {"error": error}
  resp = models.PaperQueryResponse(results, query, timeframe, category_filter, metric, entity, page, page_size, totalcount)
  return resp.json()

# paper details
@bottle.get('/api/v1/papers/<id:int>')
def paper_details(id):
  try:
    paper = endpoints.paper_details(connection, id)
  except helpers.NotFoundError as e:
    bottle.response.status = 404
    return {"error": e.message}
  except ValueError as e:
    bottle.response.status = 500
    return {"error": "Server error – {}".format(e)}
  return paper.json()

# paper download stats
@bottle.get('/api/v1/papers/<id:int>/downloads')
def paper_downloads(id):
  try:
    details = endpoints.paper_downloads(connection, id)
  except helpers.NotFoundError as e:
    bottle.response.status = 404
    return {"error": e.message}
  except ValueError as e:
    bottle.response.status = 500
    return {"error": "Server error – {}".format(e)}
  return details

# author details page
@bottle.get('/api/v1/authors/<author_id:int>')
def display_author_details(author_id):
  try:
    author = endpoints.author_details(connection, author_id)
  except helpers.NotFoundError as e:
    bottle.response.status = 404
    return {"error": e.message}
  except ValueError as e:
    bottle.response.status = 500
    return {"error": "Server error – {}".format(e)}
  return author.json()

# categories list endpoint
@bottle.get('/api/v1/data/collections')
def get_category_list():
  try:
    category_list = endpoints.get_categories(connection)
  except Exception as e:
    bottle.response.status = 500
    return {"error": "Server error – {}".format(e)}
  return {
    "results": category_list
  }

# stat distributions endpoint
@bottle.get('/api/v1/data/distributions/<entity>/<metric>')
def get_distros(entity, metric):
  if entity not in ["paper", "author"]:
    bottle.response.status = 404
    return {"error": "Unknown entity: expected 'paper' or 'author'; got '{}'".format(entity)}
  if metric not in ["downloads"]:
    bottle.response.status = 404
    return {"error": "Unknown entity: expected 'downloads'; got '{}'".format(metric)}
  if entity == "paper": # TODO: Fix this silliness
    entity = "alltime"

  try:
    results, averages = endpoints.get_distribution(connection, entity, metric)
  except Exception as e:
    bottle.response.status = 500
    return {"error": "Server error – {}".format(e)}
  return {
    "results": {
      "histogram": [{"bucket_min": x[0], "count": x[1]} for x in results],
      "averages": {
        "mean": averages["mean"],
        "median": averages["median"]
      }
    }
  }

@bottle.get('/api/v1/data/counts')
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
