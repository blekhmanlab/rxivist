import unittest
from requests_html import HTMLSession
import spider

class TestResultPageParsing(unittest.TestCase):
	# @classmethod
	# def setUpClass(self):
	# 	session = HTMLSession()
	# 	self.results = session.get("https://www.biorxiv.org/collection/bioinformatics")

	def test_find_entries_on_page(self):
		session = HTMLSession()
		entries = session.get("https://www.biorxiv.org/collection/bioinformatics").html.find(".highwire-article-citation")
		single = spider.Article()
		single._find_title(entries[0])
		self.assertEqual(single.title, "Capturing variation impact on molecular interactions: the IMEx Consortium mutations data set")

	def test_isupper(self):
		self.assertTrue('FOO'.isupper())
		self.assertFalse('Foo'.isupper())

	def test_split(self):
		s = 'hello world'
		self.assertEqual(s.split(), ['hello', 'world'])
		# check that s.split fails when the separator is not a string
		with self.assertRaises(TypeError):
			s.split(2)

if __name__ == '__main__':
	unittest.main()
