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

def month_name(monthnum):
  months = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
  }
  if monthnum is None or monthnum < 1 or monthnum > 12:
    return ""
  return months[monthnum]