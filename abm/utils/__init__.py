class ConfigError(Exception):
  def __init__(self, message):
    super().__init__(message)

def co_ords_for_area(position_sets):
  co_ords = []
  for position_set in position_sets:
    for x in range(position_set["x_0"], position_set["x_1"]+1):
      for y in range(position_set["y_0"], position_set["y_1"]+1):
        co_ords.append((x, y))
  return co_ords