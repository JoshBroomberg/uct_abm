from mesa import Agent
from utils import ConfigError
from .objects import Object
import numpy as np

import random
import math

class Person(Agent):

  move_vector_order = [ "violent", "active", "quiet", "cop", "media", "flag", "obstacle"]

  def __init__(self, unique_id, model, position, vision_radius,
    violent_affinity, active_affinity, quiet_affinity, cop_affinity,
    media_affinity, flag_affinity, obstacle_affinity):
      super().__init__(unique_id, model)

      self.vision_radius = vision_radius
      
      # Movement desire vector values
      self.violent_affinity = violent_affinity
      self.active_affinity = active_affinity
      self.quiet_affinity = quiet_affinity
      self.cop_affinity = cop_affinity
      self.media_affinity = media_affinity
      self.flag_affinity = flag_affinity
      self.obstacle_affinity = obstacle_affinity

      # State tracking
      self.state = None
      self.planned_state = None

      # Location tracking
      self.position = position
      self.planned_position = None

      if np.max(np.absolute(self.inherent_movement_desire_vector())) > 5:
        raise ConfigError("No move vector value may be greater than 5 in magnititude")

  # The cells the agent can see, returned as a list of coord tuples.
  def percept(self):
      self.neighborhood = self.model.grid.get_neighborhood(self.pos,
        moore=True, radius=self.vision_radius, include_center=False)

  # Maps percepts to type of agent/object in each grid
  def percept_contents(self):
    percept_contents = {}
    for co_ord in self.percept():
      cell_contents = self.model.grid[co_ord[0]][co_ord[1]]
      if issubclass(cell_contents, Cop):
        percept_contents[co_ord] = "cop"
      elif issubclass(cell_contents, Media):
        percept_contents[co_ord] = "media"
      elif issubclass(cell_contents, Citizen):
        percept_contents[co_ord] = cell_contents.state
      elif issubclass(cell_contents, Object):
        percept_contents[co_ord] = cell_contents.citizen_type
      elif self.model.grid.is_cell_empty(co_ord):
        percept_contents[co_ord] = "empty"
      else:
        raise ValueError("Unexpected object type")

  # Returns the agents inherent, fixed move vector.
  def inherent_movement_desire_vector(self):
    return np.array([self.violent_affinity, self.active_affinity, self.quiet_affinity,
      self.cop_affinity, self.media_affinity, self.flag_affinity, self.obstacle_affinity])

  # Returns move vector, adjusted for current state
  def adjusted_movement_desire_vector(self):
    raise ConfigError("Agent default adjusted_movement_desire_vector function not overridden")
  
  # Returns the penalty value for a given co_ordinate
  def penalty_value(self, x, y):
    percept = self.percept()
    adjusted_move_vector = self.adjusted_move_vector()

    if (x, y) not in percept:
      raise ValueError("Can only evaluate potential move within percept")

    # Calculate distances to objects in percept

    cummulative_distances = {
      "violent": 0,
      "active": 0,
      "quiet": 0,
      "cop": 0,
      "media": 0,
      "flag": 0,
      "obstacle": 0
    }

    percept_contents = self.percept_contents()
    for co_ord in self.percept():
      distance = math.sqrt(((co_ord[0]-x)**2) + ((co_ord[1]-y)**2))
      interpretted_cell_content = percept_contents[co_ord]
      cummulative_distances[interpretted_cell_content] += distance

    distance_vector = np.array([cummulative_distances[content_type] for content_type in move_vector_order])

    # Calulate penalty based on unit vector derived from adjusted move desire vector
    adjusted_move_vector = self.adjusted_movement_desire_vector()
    adjusted_move_vector_magnitude = np.linalg.norm(adjusted_move_vector)
    adjusted_move_vector = adjusted_move_vector/adjusted_move_vector_magnitude
    penalty_vector = adjusted_move_vectore * distance_vector

    return np.sum(penalty_vector)

  def plan_move(self):
    viable_moves = filter(lambda co_ord: self.model.grid.is_cell_empty(co_ord), self.percept())

    best_move = viable_moves[0]
    best_penalty = self.penalty_value(viable_moves[0][0], viable_moves[0][1])

    # Find best move in percept based on penalty
    for move in viable_moves:
      move_penalty = self.penalty_value(move[0], move[1])
      if move_penalty < best_penalty:
        best_penalty, best_move = move_penalty, move

    # Account for failure to fully, rationally evaluate the percept.
    if random.random() < self.model.agent_move_falibility:
      best_move = random.choice(viable_moves)

    self.planned_position = best_move

  # Can be overriden
  def plan_state(self):
    self.planned_state = self.state

  def plan(self):
    self.plan_move()
    self.plan_state()

  def step(self):
    # Planning is done so that the move and state are decided
    # on current information before updates occur so that the update of one
    # doesn't affect the calculation of the other.
    self.plan()
    self.state = self.planned_state
    self.model.grid[self.position[0]][self.position[1]] = None
    self.position = self.planned_position
    self.model.grid[self.position[0]][self.position[1]] = self

class Citizen(Person):
  citizen_types = ["hardcore", "hanger_on", "observer"]
  states = ["quiet", "active", "violent", "fighting"]

  def __init__(self, unique_id, model, position, vision_radius,
    violent_affinity, active_affinity, quiet_affinity, cop_affinity,
    media_affinity, flag_affinity, obstacle_affinity,
    citizen_type, state, hardship, perceived_legitimacy, risk_tolerance,
    arrest_delay, threshold):

    super().__init__(unique_id, model, position, vision_radius,
    violent_affinity, active_affinity, quiet_affinity, cop_affinity,
    media_affinity, flag_affinity, obstacle_affinity)

    self.citizen_type = citizen_type
    self.state = state

    if citizen_type not in citizen_types:
      raise ConfigError("invalid citizen type.")

    if state not in states:
      raise ConfigError("invalid state.")

    self.hardship = hardship
    self.perceived_legitimacy = perceived_legitimacy
    self.risk_tolerance = risk_tolerance

    self.arrest_delay = arrest_delay
    self.arrested = False
    self.arrested_count = 0
    self.jail_time = 0

    # Expected utility of not acting.
    self.threshold = threshold

  def update_legitimacy(self)
    num_jailed = self.model.jailed_count
    num_pictures = self.model.pictures_count
    num_cops_on_campus = self.model.cops_count

    previous_day_jailed_count = self.model.previous_day_jailed_count
    previous_day_pictures_count = self.model.previous_day_pictures_count
    previous_day_cops_count = self.model.previous_day_cops_count

    delta_jailed = num_jailed - previous_day_jailed_count
    delta_pictures = num_pictures - previous_day_pictures_count
    delta_cops = num_cops - previous_day_cops_count

    jailed_effect = delta_jailed * self.model.citizen_jailed_sensitivity
    pictures_effect = delta_pictures * self.model.citizen_pictures_sensitivity
    cops_effect = delta_cops * self.model.citizen_cops_sensitivity

    legitimacy_modifier = 1 - (1.0/math.exp(jailed_effect + pictures_effect + cops_effect))

    # if num jailed, pictures of violence, or cops go down, legitimacy may increase.
    self.perceived_legitimacy = self.perceived_legitimacy - legitimacy_modifier

  def perceived_risk(self):
    visible_objects = self.model.grid.get_cell_list_contents(self.percept())
    
    visible_cops = len(filter(lambda object: type(object) == Cop, visible_objects))
    visible_active_agents = len(filter(lambda object: (type(object) == Citizen) and
      (object.state in ["active", "violent"]), visible_objects))

    if self.state in ["active", "violent"]:
     visible_active_agents += 1

    arrest_constant = self.model.arrest_constant

    return (1 - (1.0/math.exp(arrest_constant*(float(visible_cops)/visible_active_agents))))

  def jail_time_for_arrest(self):
    return self.model.jail_time * max(1, self.arrested_count)

  def net_risk(self, state):
    if state == "active":
      return self.perceived_risk() * (1-self.risk_tolerance)
    elif state == "violent":
      return self.perceived_risk() * (1-self.risk_tolerance) * self.jail_time_for_arrest()
    else:
      return 0

  # Override some generic agent methods:
  def plan_state(self):
    perceived_gain = self.hardship * (1 - self.perceived_legitimacy)
    should_go_active = perceived_gain - self.net_risk("active") > self.threshold
    should_go_violent = perceived_gain - self.net_risk("violent") > self.threshold
    
    if not self.state == "fighting":
      if should_go_violent:
        self.state = "violent"
      elif should_go_active:
        self.state = "active"
      else:
        self.state = "quiet"
    else:
      self.arrest_delay = self.arrest_delay - 1

  # Way people react to context is dependant on who they are
  # not their current state
  # But the features observed are "visible elements" of people
  # ie, state, not type.
  def adjusted_movement_desire_vector(self):
    # vector order:
    # [violent, active, quiet, cop, media, flag, obstacle]

    inherent_move_vector = self.inherent_movement_desire_vector()

    if self.type == "hardcore":
      
      flag_visible = len(filter(lambda object: (type(object) == Object) and (object.object_type == "flag"),
        self.model.grid.get_cell_list_contents(self.percept()))) > 0
      
      visible_cops = len(filter(lambda object: type(object) == Cop, visible_objects))
      visible_active_agents = len(filter(lambda object: (type(object) == Citizen) and
        (object.state in ["active", "violent"]), visible_objects))

      # If flag visible, and cops outnumbered, desire is to
      # cluster with other violent agents and advance on flag
      # The notion of outnumbered comes from the 2:1 arrest ratio for cops to arrest
      if flag_visible and visible_active_agents > (0.5 * visible_cops):
        inherent_move_vector[0] += 2 #violent
        inherent_move_vector[1] -= 2 #active

      # If no flag, but agents in advantage, pursue cops
      elif visible_active_agents > (0.5 * visible_cops):
        inherent_move_vector[3] += 2 #violent

      # If agents are outnumbered, avoid cops
      elif visible_active_agents < (0.5 * visible_cops):
        inherent_move_vector[3] -= 4 #cops

    elif self.type == "hanger_on":
      # If violent, assume the personality of a hardcore agent,
      # without additional context modifications
      if self.state == "violent":
        inherent_move_vector = self.model.default_hardcore_move_vector

      # if active, approach other actives
      elif self.state == "active":
        inherent_move_vector[1] += 2 #actives

      # If quiet, avoid violent agents
      elif self.state == "quiet":
        inherent_move_vector[0] -= 2 #violent

    elif self.type == "observer":
      # If violent, assume the personality of a hardcore agent,
      # without additional context modifications
      if self.state == "violent":
        inherent_move_vector = self.model.default_hardcore_move_vector

      elif self.state == "active":
        inherent_move_vector[1] += 2 #actives

      # If quiet, strongly avoid violent and active agents
      elif self.state == "quiet":
        inherent_move_vector[0] -= 3 #violent
        inherent_move_vector[1] -= 2 #active

    return inherent_move_vector





