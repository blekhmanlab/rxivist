import bottle

import db

# - ROUTES -
@bottle.get('/hello')
def hello():
	return "Hello World!"

# ---- DB convenience endpoint
@bottle.get('/db/<table>')
@bottle.view('db')
def get_articles_table(table):
	column_names, data = connection.fetch_table_data(table)
	return bottle.template('db', headers=column_names, results=data)

# ---- List all papers
@bottle.get('/papers')
def list_papers():
	bottle.response.status = 501
	return "not implemented"

# ---- Errors
@bottle.error(404)
def error404(error):
	return 'Not all those who wander are lost. But you are.'

# - SERVER -
connection = db.Connection("testdb", "postgres", "mysecretpassword")  # TODO: Make this configurable
bottle.run(host='0.0.0.0', port=8080, debug=True, reloader=True) # TODO: Remove debug and reloader options for prod
