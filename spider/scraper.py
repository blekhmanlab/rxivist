from requests_html import HTMLSession

class author(object):
	def __init__(self, given, surname):
		self.given = given
		self.surname = surname

	def name(self):
		return "{} {}".format(self.given, self.surname)

class article(object):
	# This function expects an "Element" object from requests_html
	# that contains information about only one article.
	def __init__(self, html):
		self.html = html
		self.find_title()
		self.find_url()
		self.find_authors()
		# NOTE: We don't get abstracts from search result pages
		# because they're loaded asynchronously and it would be
		# annoying to load every one separately.

	def find_title(self):
		x = self.html.find(".highwire-cite-title")
		# this looks weird because the title is wrapped
		# in 2 <span> tags with identical classes:
		self.title = x[0].text

	def find_url(self):
		self.url = self.html.absolute_links.pop() # absolute_links is a set

	def find_authors(self):
		entries = self.html.find(".highwire-citation-author")
		self.authors = []
		for entry in entries:
			first = entry.find(".nlm-given-names")[0].text
			last = entry.find(".nlm-surname")[0].text
			self.authors.append(author(first, last))

def determine_page_count(html):
	# takes a biorxiv results page and
	# finds the highest page number listed
	return int(html.find(".pager-last")[0].text)

def process_page(html):
	entries = html.find(".highwire-article-citation")
	return [article(x) for x in entries]

if __name__ == "__main__":
	session = HTMLSession()
	# we need to grab the first page to figure out how many pages there are
	r = session.get("https://www.biorxiv.org/collection/bioinformatics")
	results = process_page(r.html)
	for p in range(1, determine_page_count(r.html)):
		r = session.get("https://www.biorxiv.org/collection/bioinformatics?page={}".format(p))
		results += process_page(r.html)

	for x in results: print(x.title)