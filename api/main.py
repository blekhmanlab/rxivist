import bottle

@bottle.get('/hello')
def hello():
	return "Hello World!"

@bottle.get('/papers')
def list_papers():
	return "not implemented"

@bottle.error(404)
def error404(error):
	return 'Nothing here, sorry'

bottle.run(host='0.0.0.0', port=8080, debug=True)
