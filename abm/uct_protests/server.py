from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid

from .model import ProtestModel
from .agents import Citizen, Cop, Media
from .objects import Object

from .portrayal import element_portrayal


COP_COLOR = "#000000"
AGENT_QUIET_COLOR = "#0066CC"
AGENT_REBEL_COLOR = "#CC0000"
JAIL_COLOR = "#757575"

width = 21
height = 20
canvas_element = CanvasGrid(element_portrayal, width, height, 500, 500)
server = ModularServer(ProtestModel, [canvas_element],
                        "UCT Protests",
                        initial_num_cops=7,
                        initial_num_citizens=100,
                        initial_num_media=5,
                        hardcore_density=0.1,
                        hanger_on_density=0.5,
                        observer_density=0.4,
                        vision_radius=2,
                        agent_move_falibility=0.1,
                        citizen_jailed_sensitivity=3,
                        citizen_pictures_sensitivity=2,
                        citizen_cops_sensitivity=1,
                        max_days = 10,
                        height = height,
                        width = width,
                        obstacle_positions=[
                          (1, 0),
                          (2, 0),
                          (3, 0),
                          (4, 0),
                          (5, 0),
                          (6, 0),
                          (1, 1),
                          (2, 1),
                          (3, 1),
                          (4, 1),
                          (5, 1),
                          (6, 1),
                          (14, 0),
                          (15, 0),
                          (16, 0),
                          (17, 0),
                          (18, 0),
                          (19, 0),
                          (14, 1),
                          (15, 1),
                          (16, 1),
                          (17, 1),
                          (18, 1),
                          (19, 1),
                        ],
                        flag_positions=[
                          (7, 0),
                          (8, 0),
                          (9, 0),
                          (10, 0),
                          (11, 0),
                          (12, 0),
                          (13, 0),
                        ],
                        cop_positions=[
                          (7, 1),
                          (8, 1),
                          (9, 1),
                          (10, 1),
                          (11, 1),
                          (12, 1),
                          (13, 1),
                        ],
                        arrest_delay=5,
                        jail_time=10
                      )
