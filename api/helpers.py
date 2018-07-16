import endpoints

def get_stats(connection):
  results = {"paper_count": 0, "author_count": 0}
  resp = connection.read("SELECT COUNT(id) FROM articles;")
  if len(resp) != 1 or len(resp[0]) != 1:
    return results
  results["paper_count"] = resp[0][0]

  resp = connection.read("SELECT COUNT(id) FROM authors;")
  if len(resp) != 1 or len(resp[0]) != 1:
    return results
  results["author_count"] = resp[0][0]
  return results

def get_categories(connection):
  results = []
  categories = connection.read("SELECT DISTINCT collection FROM articles ORDER BY collection;")
  for cat in categories: 
    if len(cat) > 0:
      results.append(cat[0])
  return results

def determine_textsearch_query(connection, q, category_filter):
  if(q is not "" or len(category_filter) > 0): # If the user submitted a search query
    return endpoints.get_papers_textsearch(connection, q, category_filter)
  # default homepage list:
  return endpoints.most_popular_alltime(connection)
