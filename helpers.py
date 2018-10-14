"""Utilities for interpreting data that arrives in impractical formats.

This module stores helper functions that transform data for the controllers.
"""

class NotFoundError(Exception):
  """
  Helper exception for when we should probably be returning 404s.

  """
  def __init__(self, id):
    """Sets the exception message.

    Arguments:
      - id: The requested ID of the entity that couldn't be found.

    """
    self.message = "Entity could not be found with id {}".format(id)

def num_to_month(monthnum):
  """Converts a (1-indexed) numerical representation of a month
  of the year into a three-character string for printing. If
  the number is not recognized, it returns an empty string.

  Arguments:
    - monthnum: The numerical representation of a month

  Returns:
    - The three-character abbreviation of the specified month

  """
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
