from datetime import datetime

import config

class Logger:
  """Stores the settings and mechanisms for logging messages emitted
  by other parts of the application.

  """
  def __init__(self):
    "Opens the log file, if the app is configured to write to a file."
    if config.log_to_file is True:
      self.filename = datetime.now().strftime('./log/%Y-%m-%d_%H-%M-%S.log')
      self.file = open(self.filename, "a+", 2) # No buffered writes

  def __del__(self):
    "Closes any open log files."
    if config.log_to_file is True and self.file is not None:
      self.file.close()

  @staticmethod
  def level(level):
    "Converts a string expressing a log level into an int, to allow comparisons"
    return ["debug", "info", "warn", "error", "fatal"].index(level)

  def record(self, message, level="info"):
    """Processes a single log message in whichever ways are configured.

    Arguments:
      - message: A string indicating a message to be logged.
      - level: The level of the provided message; this is compared
          to the configured log level, and is used to decide whether
          to ignore the provided message.

    """
    message = message.encode('utf-8')
    if config.log_to_stdout is True:
      if self.level(level) >= self.level(config.log_level):
        try:
          print(message.decode('utf-8'))
        except Exception:
          print(message)
    if config.log_to_file is True:
      if self.level(level) >= self.level(config.log_level):
        self.file.write("{} {}: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), level.upper(), message))
    if level == "fatal":
      raise ValueError(message)
