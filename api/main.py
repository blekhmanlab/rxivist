import bottle

import db

# ---- ROUTES ----
@bottle.get('/hello')
def hello():
	return "Hello World!"

# ------- DB convenience endpoints
# articles (id SERIAL PRIMARY KEY, url text UNIQUE, title text NOT NULL, abstract text);")
# authors (id SERIAL PRIMARY KEY, given text NOT NULL, surname text, UNIQUE (given, surname));")
# article_authors (id SERIAL PRIMARY KEY, article integer NOT NULL, author integer NOT NULL, UNIQUE (article, author));")
# article_traffic (id SERIAL PRIMARY KEY, article integer NOT NULL, month integer, year integer NOT NULL, abstract integer, pdf integer, UNIQUE (article, month, year));")

@bottle.get('/db/articles')
@bottle.view('db')
def get_articles_table():
	with connection.db.cursor() as cursor:
		# find abstracts for any articles without them
		cursor.execute("SELECT * FROM articles;")
		return bottle.template('db', results=cursor)

@bottle.get('/papers')
def list_papers():
	bottle.response.status = 501
	return "not implemented"

@bottle.error(404)
def error404(error):
	return 'Not all those who wander are lost. But you are.'

# ---- SERVER ----
connection = db.Connection("testdb", "postgres", "mysecretpassword")  # TODO: Make this configurable
bottle.run(host='0.0.0.0', port=8080, debug=True, reloader=True) # TODO: Remove debug and reloader options for prod
