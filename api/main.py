import bottle
import db
import helpers
import endpoints
import config

connection = db.Connection(config.db["host"], config.db["user"], config.db["password"])

# - ROUTES -

# ---- Homepage / search results
@bottle.get('/')
@bottle.view('index')
def index():
  if connection is None:
    bottle.response.status = 421
    return "Database is initializing."

  query = bottle.request.query.q
  category_filter = bottle.request.query.getall('category') # multiple params possible

  category_list = endpoints.get_categories(connection)
  stats = helpers.get_stats(connection)
  error = ""
  results = {}
  title = "Most popular papers related to \"{}\"".format(query) if query != "" else "Most popular bioRxiv papers, all-time"
  
  try:
    results = endpoints.most_popular_alltime(connection, query, category_filter)
  except Exception as e:
    print(e)
    connection.db.commit() # required to end the failed transaction, if it exists (HACK: check if this is needed elsewhere)
    error = "There was a problem with the submitted query."
    bottle.response.status = 500

  return bottle.template('index', results=results,
    query=query, category_filter=category_filter, title=title,
    error=error, stats=stats, category_list=category_list)

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

@bottle.get('/api/papers')
def get_papers():
  results = endpoints.get_papers(connection)
  return {"results": results}

@bottle.get('/api/papers/search')
def get_papers_textsearch():
  q = bottle.request.query.q
  category_filter = bottle.request.query.getall('category') # multiple params possible
  results = []
  try:
    results = helpers.determine_textsearch_query(connection, q, category_filter)
  except Exception as e:
    print(e)
    connection.db.commit() # required to end the failed transaction, if it exists
    bottle.response.status = 500
  return {"results": results}

@bottle.get('/api/popularity/downloads')
def get_popular():
  results = endpoints.most_popular(connection)
  return {"results": results}

@bottle.get('/api/popularity/downloads/ytd')
def get_popular():
  results = endpoints.most_popular_ytd(connection)
  return {"results": results}

@bottle.get('/api/papers/<id:int>')
def get_paper_details(id):
  try:
    result = endpoints.paper_details(connection, id)
  except endpoints.NotFoundError as e:
    bottle.response.status = 404
    return e.message
  except ValueError as e:
    bottle.response.status = 500
    print(e)
    return {"error": "Server error."}
  return result

@bottle.get('/api/categories')
def get_categories():
  categories = endpoints.get_categories(connection)
  return {"results": categories}

@bottle.get('/api/authors')
def get_authors():
  bottle.response.status = 501
  return

@bottle.get('/api/authors/<id:int>')
def get_author_details(id):
  try:
    result = endpoints.author_details(connection, id)
  except endpoints.NotFoundError as e:
    bottle.response.status = 404
    return e.message
  except ValueError as e:
    bottle.response.status = 500
    print(e)
    return {"error": "Server error."}
  return result

@bottle.get('/authors/<id:int>')
@bottle.view('author_details')
def display_author_details(id):
  author = get_author_details(id)
  return bottle.template('author_details', data=author)

# ---- Errors
@bottle.error(404)
def error404(error):
  return 'Not all those who wander are lost. But you are.'

# - SERVER -
@bottle.route('/static/<path:path>')
def callback(path):
  return bottle.static_file(path, root='./')

bottle.run(host='0.0.0.0', port=80, debug=True, reloader=True)
# bottle.run(host='0.0.0.0', port=80, server="gunicorn")
