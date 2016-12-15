from .agents import Citizen, Cop, Media
from .objects import Object

COP_COLOR = "#1A1AFF" #blue
FIGHT_COLOR = "#FF0000" #yellow
AGENT_QUIET_COLOR = "#33FF33" #green
AGENT_ACTIVE_COLOR = "#EEEE39" #orange
AGENT_VIOLENT_COLOR = "#FF8000" #red
OBSTACLE_COLOR = "#000000" #black
FLAG_COLOR = "#B8B894" #grey
MEDIA_COLOR = "#FF1AFF" #pink

def element_portrayal(agent):
  if agent is None:
    return

  portrayal = {
    "x": agent.position[0], "y": agent.position[1],
    "Filled": "true",
    "Layer": 0,
    "r": 0.6,
    "Shape": "circle"
    }

  if isinstance(agent, Object):
    portrayal["Color"] = OBSTACLE_COLOR if agent.object_type == "obstacle" else \
      FLAG_COLOR

  elif isinstance(agent, Citizen):
    color = None
    if agent.state == "quiet":
      color = AGENT_QUIET_COLOR
    elif agent.state == "active":
      color = AGENT_ACTIVE_COLOR
    elif agent.state == "violent":
      color = AGENT_VIOLENT_COLOR
    elif agent.state == "fighting":
      color = FIGHT_COLOR
      portrayal["Color"] = 0.9
    
    portrayal["Color"] = color

  elif isinstance(agent, Cop):
    portrayal["Color"] = COP_COLOR
    portrayal["Shape"] = "rect"
    portrayal["w"] = 0.9
    portrayal["h"] = 0.9
  elif isinstance(agent, Media):
    portrayal["Color"] = MEDIA_COLOR
  
  return portrayal
