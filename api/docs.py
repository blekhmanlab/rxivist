import docmodels
import endpoints
import config

def build_docs(connection):
  papers = docmodels.Chapter("Papers", "Endpoints for searching all papers or retrieving details.")
  query = papers.add_endpoint("Search", "/api/papers", "Retrieve a list of papers matching the given criteria")
  query.add_argument("get", "query", "A search string to filter results based on their titles, abstracts and authors", "")

  metric = query.add_argument("get", "metric", "Which field to use when sorting results.", "twitter")
  metric.add_values(["downloads", "twitter"])

  timeframe = query.add_argument("get", "timeframe", "How far back to look for the cumulative results of the chosen metric. (\"ytd\" and \"lastmonth\" are only available for the \"downloads\" metric.", "\"day\" for Twitter metrics, \"alltime\" for downloads.")
  timeframe.add_values(["alltime", "ytd", "lastmonth", "day", "week", "month", "year"])

  catfilter = query.add_argument("get", "category_filter", "An array of categories to which the results should be limited.", "[]")
  category_list = endpoints.get_categories(connection) # list of all article categories
  catfilter.add_values(category_list)

  query.add_argument("get", "page", "Number of the page of results to retrieve. Shorthand for an offset based on the specified page_size", 0)

  query.add_argument("get", "page_size", "How many results to return at one time. Capped at {}.".format(config.max_page_size_api), 20)

  docs = docmodels.Documentation([papers])
  return docs
