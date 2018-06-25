# TODO: This is a sad graveyard of half-mocked HTML requests.
# Solving this might actually be helpful to someone, but it's
# probably not worth doing right now.

import unittest
from requests_html import HTMLSession
import spider
from unittest import mock

# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
  class MockResponse:
    def __init__(self, htmlstring, status_code):
      with open('tests/fixtures/results_page.html') as f:
        self.html = f.read()
      self.status_code = status_code

  if args[0] == 'http://someurl.com/test.json':
    return MockResponse("<html><body>This isn't how this works</body></html>", 200)
  return MockResponse(None, 404)

class TestResultPageParsing(unittest.TestCase):
  # @classmethod
  # def setUpClass(cls):
  #   session = HTMLSession()
  #   cls.results = session.get("https://www.biorxiv.org/collection/bioinformatics")

  # NOTE to future self: This monkey patch works, but the object is more
  # complicated than the one being cooked up above.
  @mock.patch('requests_html.HTMLSession.get', side_effect=mocked_requests_get)
  def test_find_entries_on_page(self, mock_get):
    session = HTMLSession()
    results = session.get("https://www.biorxiv.org/collection/bioinformatics")
    entries = results.html.find(".highwire-article-citation")
    single = spider.Article()
    single._find_title(entries[0])
    self.assertEqual(single.title, "Capturing variation impact on molecular interactions: the IMEx Consortium mutations data set")

if __name__ == '__main__':
  unittest.main()
