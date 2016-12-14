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
    self.planned_state()

  def step(self):
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
    citizen_type, state, hardship, perceived_legitimacy):

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






