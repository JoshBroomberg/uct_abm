from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule

from .model import ProtestModel

from .portrayal import element_portrayal

# Manual positioning
# obstacles = co_ords_for_area(25, 50, 0, 4) + co_ords_for_area(70, 95, 0, 4)
# flags = co_ords_for_area(51, 69, 0, 4)
# cops = co_ords_for_area(55, 65, 5, 9) + co_ords_for_area(57, 63, 10, 11)

args = {
  "initial_num_citizens":400,
  "initial_num_media":5,
  "hardcore_density":0.2,
  "hanger_on_density":0.5,
  "observer_density":0.3,
  "agent_vision_radius": 3,
  "agent_move_falibility":0.1,
  "default_hardcore_move_vector": [4, 2, 0, 4, 3, 4, -1],
  "default_hanger_on_move_vector": [1, 1, 0, 1, 3, 2, -1],
  "default_observer_move_vector": [-5, -1, 0, -5, 3, 0, -1],
  "default_cop_move_vector": [1, 0, 0, 5, 0, 5, 0],
  "default_media_move_vector": [3, 1, -1, 3, 2, 2, -1],
  "citizen_jailed_sensitivity":5,
  "citizen_pictures_sensitivity":2,
  "citizen_cops_sensitivity":10,
  "max_days": 100,
  "height": 20,
  "width": 90,
  "agent_regions": [{"x_0": 10, "x_1": 80, "y_0": 10, "y_1": 19}],
  "obstacle_regions": [
    {"x_0": 10, "x_1": 35, "y_0": 0, "y_1": 4},
    {"x_0": 55, "x_1": 80, "y_0": 0, "y_1": 4},
  ],
  "flag_regions": [{"x_0": 36, "x_1": 54, "y_0": 0, "y_1": 2}],
  "cop_regions": [
    {"x_0": 36, "x_1": 54, "y_0": 3, "y_1": 3, "frozen": True},
    {"x_0": 37, "x_1": 53, "y_0": 4, "y_1": 4, "frozen": True},
    {"x_0": 38, "x_1": 52, "y_0": 5, "y_1": 5, "frozen": True},
    {"x_0": 40, "x_1": 50, "y_0": 6, "y_1": 6, "frozen": False},
    {"x_0": 41, "x_1": 49, "y_0": 7, "y_1": 8, "frozen": False},
  ],
  "arrest_delay": 5,
  "jail_time": 4
}

def model_instance():
  return ProtestModel(**args)

def server_instance():
  legitimacy = ChartModule([{"Label": "Average legitimacy", 
                      "Color": "Blue"}],
                    data_collector_name='datacollector')

  ripeness = ChartModule([{"Label": "Average ripeness", 
                      "Color": "Red"}],
                    data_collector_name='datacollector')

  protesting = ChartModule([{"Label": "Protesting", 
                      "Color": "Black"}],
                    data_collector_name='datacollector')

  canvas_element = CanvasGrid(element_portrayal, args["width"], args["height"], args["width"]*10, args["height"]*10)
  return ModularServer(ProtestModel, [canvas_element, legitimacy, ripeness, protesting], "UCT Protests", **args)
