from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid

from .model import ProtestModel

from .portrayal import element_portrayal

def co_ords_for_area(x_start, x_end, y_start, y_end):
  co_ords = []
  for x in range(x_start, x_end+1):
    for y in range(y_start, y_end+1):
      co_ords.append((x, y))
  return co_ords

# Manual positioning
obstacles = co_ords_for_area(25, 50, 0, 8) + co_ords_for_area(70, 95, 0, 8)
flags = co_ords_for_area(51, 69, 0, 8)
cops = co_ords_for_area(55, 65, 9, 13) + co_ords_for_area(57, 63, 14, 15)

args = {
  "initial_num_cops":len(cops),
  "initial_num_citizens":400,
  "initial_num_media":5,
  "hardcore_density":0.1,
  "hanger_on_density":0.5,
  "observer_density":0.4,
  "vision_radius":2,
  "agent_move_falibility":0.1,
  "default_hardcore_move_vector": [5, 2, 0, 4, 3, 5, -1],
  "default_hanger_on_move_vector": [1, 1, 0, 1, 3, 1, -1],
  "default_observer_move_vector": [-1, -1, 0, -1, 3, 0, -1],
  "default_cop_move_vector": [2, 1, 0, 5, 0, 5, 0],
  "default_media_move_vector": [3, 1, -1, 3, 2, 2, -1],
  "citizen_jailed_sensitivity":3,
  "citizen_pictures_sensitivity":2,
  "citizen_cops_sensitivity":1,
  "max_days": 10,
  "height": 50,
  "width": 120,
  "agent_region": {"x_0": 20, "x_1": 100, "y_0": 9, "y_1": 40},
  "obstacle_positions": obstacles,
  "flag_positions":flags,
  "cop_positions":cops,
  "arrest_delay":5,
  "jail_time":10
}

def model_instance():
  return ProtestModel(**args)

def server_instance():
  canvas_element = CanvasGrid(element_portrayal, args["width"], args["height"], args["width"]*10, args["height"]*10)
  return ModularServer(ProtestModel, [canvas_element], "UCT Protests", **args)
