import bottle
import db
import endpoints

connection = db.Connection("rxdb", "postgres", "mysecretpassword")  # TODO: Make this configurable

# - ROUTES -
@bottle.get('/hello')
def hello():
  return "Hello World!"

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

@bottle.get('/papers/<id>')
def get_paper_details(id):
  try:
    result = endpoints.paper_details(connection, id)
  except endpoints.NotFoundError as e:
    bottle.response.status = 404
    return e.message
  except ValueError as e:
    bottle.response.status = 500
    print(e)
    return {"error": "Multiple papers located with same internal ID."}
  return result

# ---- Errors
@bottle.error(404)
def error404(error):
  return 'Not all those who wander are lost. But you are.'

# - SERVER -
@bottle.route('/static/<path:path>')
def callback(path):
  return bottle.static_file(path, root='./')

bottle.run(host='0.0.0.0', port=8080, debug=True, reloader=True) # TODO: Remove debug and reloader options for prod
