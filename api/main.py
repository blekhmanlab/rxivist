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
  
  # make sure it's a timeframe we recognize
  if timeframe != "ytd":
    timeframe = "alltime"

  # Get rid of a category filter that's just one empty parameter:
  if len(category_filter) == 1 and category_filter[0] == "":
    category_filter = []

  category_list = endpoints.get_categories(connection) # list of all article categories
  stats = models.SiteStats(connection) # site-wide metrics (paper count, etc)
  error = ""
  results = {}

  title = "Most popular papers related to \"{},\" ".format(query) if query != "" else "Most popular bioRxiv papers, "
  if timeframe == "alltime":
    title += "all time"
  elif timeframe == "ytd":
    title += "year to date"

  try:
    results = endpoints.most_popular(connection, query, category_filter, timeframe)
  except Exception as e:
    print(e)
    error = "There was a problem with the submitted query."
    bottle.response.status = 500

  return bottle.template('index', results=results,
    query=query, category_filter=category_filter, title=title,
    error=error, stats=stats, category_list=category_list,
    timeframe=timeframe)

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
  return bottle.template('author_details', author=author)

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
