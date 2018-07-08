import bottle
import db
import endpoints
import config

connection = db.Connection(config.db["host"], config.db["user"], config.db["password"])

# - ROUTES -

# ---- Homepage
@bottle.get('/')
@bottle.view('index')
def index():
  if connection is None:
    bottle.response.status = 421
    return "Database is initializing."
  rankings = endpoints.most_popular(connection)["results"]
  return bottle.template('index', rankings=rankings)

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
  return bottle.template('db', current=table, tables=table_names, headers=column_names, results=data)

@bottle.get('/papers')
def get_papers():
  results = endpoints.get_papers(connection)
  return results

@bottle.get('/popularity/downloads')
def get_popular():
  results = endpoints.most_popular(connection)
  return results

@bottle.get('/papers/<id:int>')
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

# ---- Errors
@bottle.error(404)
def error404(error):
  return 'Not all those who wander are lost. But you are.'

# - SERVER -
@bottle.route('/static/<path:path>')
def callback(path):
  return bottle.static_file(path, root='./')

bottle.run(host='0.0.0.0', port=80, server="gunicorn", debug=True, reloader=True) # TODO: Remove debug and reloader options for prod
