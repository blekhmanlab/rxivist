from requests_html import HTMLSession

class article(object):
	# This function expects an "Element" object from requests_html
	# that contains information about only one article.
	def __init__(self, html):
		self.title = self.get_title(html)
		self.url = self.get_url(html)

	@staticmethod
	def get_title(html):
		x = entry.find(".highwire-cite-title")
		# this looks weird because the title is wrapped
		# in 2 <span> tags with identical classes:
		return x[0].text

	@staticmethod
	def get_url(html):
		return html.absolute_links.pop() # absolute_links is a set


if __name__ == "__main__":
	session = HTMLSession()
	r = session.get("https://www.biorxiv.org/collection/bioinformatics")
	entries = r.html.find(".highwire-article-citation")
	articles = []
	for entry in entries:
		articles.append(article(entry))

	for z in articles:
		print(z.url)
