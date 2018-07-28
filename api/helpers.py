
def get_traffic(connection, id):
  """Returns a tuple indicating a single paper's download statistics.

  Arguments:
    - connection: a database connection object.
    - id: the ID given to the article being queried.
  Returns:
    - A two-element tuple. The first element is the number of views of
        the paper's abstract; the second is total PDF downloads.

  """

  traffic = connection.read("SELECT SUM(abstract), SUM(pdf) FROM article_traffic WHERE article={};".format(id))
  if len(traffic) == 0:
    raise NotFoundError(id)
  return traffic[0] # array of tuples

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