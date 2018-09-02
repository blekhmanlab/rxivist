"""Definition of web service and initialization of the server.

This is the entrypoint for the application, the script called
when the server is started and the router for all user requests.
"""

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

  if metric not in ["downloads", "altmetric"]:
    metric = "altmetric"

  if entity not in ["papers", "authors"]:
    entity = "papers"

  # make sure it's a timeframe we recognize
  if timeframe not in ["ytd", "lastmonth", "weighted"]:
    timeframe = "alltime"


  if entity == "papers":
    title = "Most "
    if metric == "altmetric":
      timeframe = "day" # only option for now
      title += "discussed"
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
      "weighted": "time-weighted score score",
      "day": "last 24 hours"
    }
    title += printable_times[timeframe]
  elif entity == "authors":
    title = "Authors with most downloads, all-time"

  # Get rid of a category filter that's just one empty parameter:
  if len(category_filter) == 1 and category_filter[0] == "":
    category_filter = []

  category_list = endpoints.get_categories(connection) # list of all article categories
  stats = models.SiteStats(connection) # site-wide metrics (paper count, etc)
  error = ""
  results = {}

  try:
    if entity == "authors":
      results = endpoints.author_rankings(connection)
    elif entity == "papers":
      if view == "table":
        results = endpoints.table_results(connection, query)
        print("Prepping table view \n\n\n")
      else:
        results = endpoints.most_popular(connection, query, category_filter, timeframe, metric)
  except Exception as e:
    print(e)
    error = "There was a problem with the submitted query."
    bottle.response.status = 500

  return bottle.template('index', results=results,
    query=query, category_filter=category_filter, title=title,
    error=error, stats=stats, category_list=category_list,
    timeframe=timeframe, metric=metric, querystring=bottle.request.query_string,
    view=view, entity=entity)

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
    category_list=category_list)

# ---- Author details page
@bottle.get('/authors/<id:int>')
@bottle.view('author_details')
def display_author_details(id):
  try:
    author = endpoints.author_details(connection, id)
  except endpoints.NotFoundError as e:
    bottle.response.status = 404
    return e.message
  except ValueError as e:
    bottle.response.status = 500
    print(e)
    return {"error": "Server error."}
  download_distribution, averages = endpoints.download_distribution(connection, 'author')
  return bottle.template('author_details', author=author,
    download_distribution=download_distribution, averages=averages)

# ---- Paper details page
@bottle.get('/papers/<id:int>')
@bottle.view('paper_details')
def display_paper_details(id):
  try:
    paper = endpoints.paper_details(connection, id)
  except endpoints.NotFoundError as e:
    bottle.response.status = 404
    return e.message
  except ValueError as e:
    bottle.response.status = 500
    print(e)
    return {"error": "Server error."}
  download_distribution, averages = endpoints.download_distribution(connection, 'alltime')
  return bottle.template('paper_details', paper=paper,
    download_distribution=download_distribution, averages=averages)

# ---- DB convenience endpoint
@bottle.get('/db')
@bottle.get('/db/<table>')
@bottle.view('db')
def get_articles_table(table=None):
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

# Search engine stuff
@bottle.route('/google3d18e8a680b87e67.html')
def callback():
  return bottle.static_file(filename='google3d18e8a680b87e67.html', root='./static/')
@bottle.route('/robots.txt')
def callback():
  return bottle.static_file(filename='robots.txt', root='./static/')

# ---- Errors
@bottle.error(404)
@bottle.view('error')
def error404(error):
  return bottle.template("error")

# - SERVER -
@bottle.route('/static/<path:path>')
def callback(path):
  return bottle.static_file(path, root='./static/')

bottle.run(host='0.0.0.0', port=80, debug=True, reloader=True)
# bottle.run(host='0.0.0.0', port=80, server="gunicorn")
