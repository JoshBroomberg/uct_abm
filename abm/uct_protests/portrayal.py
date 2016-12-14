from .agents import Citizen, Cop, Media
from .objects import Object

COP_COLOR = "#1A1AFF" #blue
FIGHT_COLOR = "#FFFFFF" #white
AGENT_QUIET_COLOR = "#33FF33" #green
AGENT_ACTIVE_COLOR = "#FF8000" #orange
AGENT_VIOLENT_COLOR = "#FF0000" #red
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
    "r": 0.8,
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
    
    portrayal["Color"] = color

  elif isinstance(agent, Cop):
    portrayal["Color"] = FIGHT_COLOR if agent.engaged_in_fight else COP_COLOR

  elif isinstance(agent, Media):
    portrayal["Color"] = MEDIA_COLOR
  
  return portrayal
