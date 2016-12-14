import Error

class ConfigError(Error):

  def __init__(self, message):
    super().__init__(message)
