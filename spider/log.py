import config
from datetime import datetime

class Logger:
  def __init__(self):
    self.filename = datetime.now().strftime('./log/%Y-%m-%d_%H-%M-%S.log')
    self.file = open(self.filename, "a+", 2) # No buffered writes

  def __del__(self):
    if self.file is not None:
      self.file.close()

  @staticmethod
  def level(level):
    return ["debug", "info", "warn", "error", "fatal"].index(level)

  def record(self, message, level="info"):
    message = message.encode('utf-8')
    if config.log_to_stdout is True:
      try:
        print(message.decode('utf-8'))
      except Exception:
        print(message)
    if config.log_to_file is True:
      if self.level(level) >= self.level(config.log_level):
        self.file.write("{} {}: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), level.upper(), message))
    if level == "fatal":
      raise ValueError(message)
