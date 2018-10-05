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

connection = db.Connection(config.db["host"], config.db["db"], config.db["user"], config.db["password"])

# - ROUTES -

# ---- Homepage / search results
@bottle.get('/')
@bottle.view('index')
def index():
  if connection is None:
    bottle.response.status = 421
    return "Database is initializing."

  query = bottle.request.query.q
  timeframe = bottle.request.query.timeframe
  category_filter = bottle.request.query.getall('category') # multiple params possible
  metric = bottle.request.query.metric
  view = bottle.request.query.view # which format to display results
  entity = bottle.request.query.entity
  page = bottle.request.query.page
  page_size = bottle.request.query.page_size
  error = ""

  # set defaults, throw out bogus values
  if entity not in ["papers", "authors"]:
    entity = "papers"
  if entity == "papers":
    if metric not in ["downloads", "crossref"]:
      metric = "crossref"
    if timeframe not in ["alltime", "ytd", "lastmonth", "day", "week", "month", "year"]:
      timeframe = "day"
  elif entity == "authors":
    metric = "downloads"
    timeframe = "alltime"

  # figure out the page title
  if entity == "papers":
    title = "Most "
    if metric == "crossref":
      title += "tweeted"
    elif metric == "downloads":
      title += "downloaded"
    if query != "":
      title += " papers related to \"{},\" ".format(query)
    else:
      title += " bioRxiv papers, "
    printable_times = {
      "alltime": "all time",
      "ytd": "year to date",
      "lastmonth": "since beginning of last month",
      "day": "last 24 hours",
      "week": "last 7 days",
      "month": "last 30 days",
      "year": "last 365 days"
    }
    title += printable_times[timeframe]
  elif entity == "authors":
    title = "Authors with most downloads, all-time"

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
        break

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

  if page_size > config.max_page_size:
    page_size = config.max_page_size # cap the page size users can ask for

  stats = models.SiteStats(connection) # site-wide metrics (paper count, etc)
  results = {} # a list of articles for the current page
  totalcount = 0 # how many results there are in total

  if error == "": # if nothing's gone wrong yet, fetch results:
    try:
      if entity == "authors":
        results = endpoints.author_rankings(connection, category_filter)
      elif entity == "papers":
        if view == "table":
          results = endpoints.table_results(connection, query)
          print("Prepping table view \n\n\n")
        else:
          results, totalcount = endpoints.most_popular(connection, query, category_filter, timeframe, metric, page, page_size)
    except Exception as e:
      print(e)
      error = "There was a problem with the submitted query: {}".format(e)
      bottle.response.status = 500

  # Take the current query string and turn it into a template that any page
  # number can get plugged into:
  if "page=" in bottle.request.query_string:
    pagelink =  "/?{}".format(re.sub(r"page=\d*", "page=", bottle.request.query_string))
  else:
    pagelink = "/?{}&page=".format(bottle.request.query_string)

  return bottle.template('index', results=results,
    query=query, category_filter=category_filter, title=title,
    error=error, stats=stats, category_list=category_list,
    timeframe=timeframe, metric=metric, querystring=bottle.request.query_string,
    view=view, entity=entity, google_tag=config.google_tag, page=page,
    page_size=page_size, totalcount=totalcount, pagelink=pagelink)

# ---- full display thing
@bottle.get('/table')
@bottle.view('table')
def table():
  if connection is None:
    bottle.response.status = 421
    return "Database is initializing."

  query = bottle.request.query.q

  category_list = endpoints.get_categories(connection) # list of all article categories
  stats = models.SiteStats(connection) # site-wide metrics (paper count, etc)
  error = ""
  results = {}

  title = "Most popular papers related to \"{},\" ".format(query) if query != "" else "Most popular bioRxiv papers"

  try:
    results = endpoints.table_results(connection, query)
  except Exception as e:
    print(e)
    error = "There was a problem with the submitted query."
    bottle.response.status = 500

  return bottle.template('table', results=results,
    query=query, title=title,
    error=error, stats=stats,
    category_list=category_list, google_tag=config.google_tag)

# ---- Author details page
@bottle.get('/authors/<id:int>')
@bottle.view('author_details')
def display_author_details(id):
  try:
    author = endpoints.author_details(connection, id)
  except helpers.NotFoundError as e:
    bottle.response.status = 404
    return e.message
  except ValueError as e:
    bottle.response.status = 500
    print(e)
    return {"error": "Server error."}
  download_distribution, averages = endpoints.download_distribution(connection, 'author')
  stats = models.SiteStats(connection)
  return bottle.template('author_details', author=author,
    download_distribution=download_distribution, averages=averages, stats=stats,
    google_tag=config.google_tag)

# ---- Paper details page
@bottle.get('/papers/<id:int>')
@bottle.view('paper_details')
def display_paper_details(id):
  try:
    paper = endpoints.paper_details(connection, id)
  except helpers.NotFoundError as e:
    bottle.response.status = 404
    return e.message
  except ValueError as e:
    bottle.response.status = 500
    print(e)
    return {"error": "Server error."}
  download_distribution, averages = endpoints.download_distribution(connection, 'alltime')
  stats = models.SiteStats(connection)
  return bottle.template('paper_details', paper=paper,
    download_distribution=download_distribution, averages=averages, stats=stats,
    google_tag=config.google_tag)

# ---- DB convenience endpoint
@bottle.get('/db')
@bottle.get('/db/<table>')
@bottle.view('db')
def get_articles_table(table=None):
  if not config.allow_db_dashboard:
    bottle.response.status = 403
    return "Database debugging dashboard is restricted."
  if connection is None:
    bottle.response.status = 421
    return "Database is initializing."
  table_names = connection.fetch_db_tables()
  column_names = []
  data = []
  if table is not None:
    column_names, data = connection.fetch_table_data(table)
  return bottle.template('db', current=table, tables=table_names,
    headers=column_names, results=data)

@bottle.route('/privacy')
@bottle.view('privacy')
def privacy():
  stats = models.SiteStats(connection)
  return bottle.template("privacy", google_tag=config.google_tag, stats=stats)

# Search engine stuff
@bottle.route('/{}'.format(config.google_validation_file))
def callback():
  return bottle.static_file(filename=config.google_validation_file, root='./static/')
@bottle.route('/robots.txt')
def callback():
  return bottle.static_file(filename='robots.txt', root='./static/')
@bottle.route('/favicon.ico')
def callback():
  return bottle.static_file(filename='favicon.ico', root='./static/')

# ---- Errors
@bottle.error(404)
@bottle.view('error')
def error404(error):
  return bottle.template("error", google_tag=config.google_tag)

# - SERVER -
@bottle.route('/static/<path:path>')
def callback(path):
  return bottle.static_file(path, root='./static/')

if config.use_prod_webserver:
  bottle.run(host='0.0.0.0', port=80, server="gunicorn")
else:
  bottle.run(host='0.0.0.0', port=80, debug=True, reloader=True)
