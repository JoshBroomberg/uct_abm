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
  def percept(self, radius=None):
    usable_radius = radius if radius else self.vision_radius

    return self.model.grid.get_neighborhood(self.position,
      moore=True, radius=usable_radius, include_center=False)

  # Maps percepts to type of agent/object in each grid
  def percept_contents(self, radius=None):
    usable_radius = radius if radius else self.vision_radius

    percept_contents = {}
    for co_ord in self.percept(radius=usable_radius):
      cell_contents = self.model.grid[co_ord[0]][co_ord[1]]
      if isinstance(cell_contents, Cop):
        percept_contents[co_ord] = "cop"
      elif isinstance(cell_contents, Media):
        percept_contents[co_ord] = "media"
      elif isinstance(cell_contents, Citizen):
        percept_contents[co_ord] = cell_contents.state
      elif isinstance(cell_contents, Object):
        percept_contents[co_ord] = cell_contents.object_type
      elif self.model.grid.is_cell_empty(co_ord):
        percept_contents[co_ord] = "empty"
      else:
        raise ValueError("Unexpected object type")

    return percept_contents

  # Returns the agents inherent, fixed move vector.
  def inherent_movement_desire_vector(self):
    return np.array([self.violent_affinity, self.active_affinity, self.quiet_affinity,
      self.cop_affinity, self.media_affinity, self.flag_affinity, self.obstacle_affinity])

  # Returns move vector, adjusted for current state
  def adjusted_move_vector(self):
    # raise ConfigError("Agent default adjusted_move_vector function not overridden")
    return self.inherent_movement_desire_vector()
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
      if not self.model.grid.is_cell_empty(co_ord):
        distance = math.sqrt(((co_ord[0]-x)**2) + ((co_ord[1]-y)**2))
        interpretted_cell_content = percept_contents[co_ord]
        cummulative_distances[interpretted_cell_content] += distance

    for (cell_contents, x_feature, y_feature) in self.model.grid.coord_iter():
      if isinstance(cell_contents, Object) and cell_contents.object_type == "flag":
        distance = math.sqrt(((x_feature-x)**2) + ((y_feature-y)**2))
        cummulative_distances["flag"] += distance

    distance_vector = np.array([cummulative_distances[content_type] for content_type in Person.move_vector_order])

    # Calulate penalty based on unit vector derived from adjusted move desire vector
    adjusted_move_vector = self.adjusted_move_vector()
    adjusted_move_vector_magnitude = np.linalg.norm(adjusted_move_vector)
    adjusted_move_vector = adjusted_move_vector/adjusted_move_vector_magnitude
    penalty_vector = adjusted_move_vector * distance_vector

    return np.sum(penalty_vector)

  def plan_move(self):
    viable_moves = list(filter(lambda co_ord: self.model.grid.is_cell_empty(co_ord), self.percept(radius=1)))

    if len(viable_moves) == 0:
      self.planned_position = self.position
    else:
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
    threshold):

    super().__init__(unique_id, model, position, vision_radius,
    violent_affinity, active_affinity, quiet_affinity, cop_affinity,
    media_affinity, flag_affinity, obstacle_affinity)

    self.citizen_type = citizen_type
    self.state = state

    if citizen_type not in Citizen.citizen_types:
      raise ConfigError("invalid citizen type.")

    if state not in Citizen.states:
      raise ConfigError("invalid state.")

    self.hardship = hardship
    self.perceived_legitimacy = perceived_legitimacy
    self.risk_tolerance = risk_tolerance

    self.arrest_delay = self.model.arrest_delay
    self.arrested = False
    self.arrested_count = 0
    self.jail_time = 0

    # Expected utility of not acting.
    self.threshold = threshold

  def __str__(self):
    return self.citizen_type

  def update_legitimacy(self):
    num_jailed = self.model.jailed_count
    num_pictures = self.model.pictures_count
    num_cops_on_campus = self.model.cops_count

    previous_day_jailed_count = self.model.previous_day_jailed_count
    previous_day_pictures_count = self.model.previous_day_pictures_count
    previous_day_cops_count = self.model.previous_day_cops_count

    delta_jailed = num_jailed - previous_day_jailed_count
    delta_pictures = num_pictures - previous_day_pictures_count
    delta_cops = num_cops_on_campus - previous_day_cops_count

    jailed_effect = delta_jailed * self.model.citizen_jailed_sensitivity
    pictures_effect = delta_pictures * self.model.citizen_pictures_sensitivity
    cops_effect = delta_cops * self.model.citizen_cops_sensitivity

    legitimacy_modifier = 1 - (1.0/math.exp(jailed_effect + pictures_effect + cops_effect))

    # if num jailed, pictures of violence, or cops go down, legitimacy may increase.
    self.perceived_legitimacy = self.perceived_legitimacy - legitimacy_modifier

  def perceived_risk(self):
    visible_objects = self.model.grid.get_cell_list_contents(self.percept())
    
    visible_cops = len(list(filter(lambda object: type(object) == Cop, visible_objects)))
    visible_active_agents = len(list(filter(lambda object: (type(object) == Citizen) and \
      (object.state in ["active", "violent"]), visible_objects))) + 1

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
    if self.state == "fighting":
      self.arrest_delay = self.arrest_delay - 1
    
    elif self.arrested:
      self.jail_time = self.jail_time -1

      if self.jail_time == 0:
        self.arrest_delay = self.model.arrest_delay
        self.arrested = False
        self.model.free_agent_from_jail(self)

    else:
      perceived_gain = self.hardship * (1 - self.perceived_legitimacy)
      should_go_active = perceived_gain - self.net_risk("active") > self.threshold
      should_go_violent = perceived_gain - self.net_risk("violent") > self.threshold
      
      if should_go_violent:
        self.planned_state = "violent"
      elif should_go_active:
        self.planned_state = "active"
      else:
        self.planned_state = "quiet"
  # Way people react to context is dependant on who they are
  # not their current state
  # But the features observed are "visible elements" of people
  # ie, state, not type.
  def adjusted_move_vector(self):
    # vector order:
    # [violent, active, quiet, cop, media, flag, obstacle]

    inherent_move_vector = self.inherent_movement_desire_vector()

    if self.citizen_type == "hardcore":
      
      visible_objects = self.model.grid.get_cell_list_contents(self.percept())
      
      flag_visible = len(list(filter(lambda object: (type(object) == Object) and (object.object_type == "flag"),
        visible_objects))) > 0
      
      visible_cops = len(list(filter(lambda object: type(object) == Cop, visible_objects)))
      visible_active_agents = len(list(filter(lambda object: (type(object) == Citizen) and
        (object.state in ["active", "violent"]), visible_objects)))

      # If flag visible, and cops outnumbered, desire is to
      # cluster with other violent agents and advance on flag
      # The notion of outnumbered comes from the 2:1 arrest ratio for cops to arrest
      if flag_visible and visible_active_agents > (0.5 * visible_cops):
        inherent_move_vector[0] += 2 #violent
        inherent_move_vector[1] -= 2 #active

      # If no flag, but agents in advantage, pursue cops
      elif visible_active_agents > (0.5 * visible_cops):
        inherent_move_vector[5] += 2 #flag

      # If agents are outnumbered, avoid cops
      elif visible_active_agents < (0.5 * visible_cops):
        inherent_move_vector[3] -= 4 #cops

    elif self.citizen_type == "hanger_on":
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

    elif self.citizen_type == "observer":
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

  def plan_move(self):
    # Don't move if fighting  
    if (not self.state == "fighting") and (not self.arrested):
      super(Citizen, self).plan_move()

class Cop(Person):
  def __init__(self, unique_id, model, position, vision_radius,
    violent_affinity, active_affinity, quiet_affinity, cop_affinity,
    media_affinity, flag_affinity, obstacle_affinity, frozen):

    super().__init__(unique_id, model, position, vision_radius,
    violent_affinity, active_affinity, quiet_affinity, cop_affinity,
    media_affinity, flag_affinity, obstacle_affinity)

    self.engaged_in_fight = False
    self.supporting_cop = None
    self.target = None
    self.frozen = frozen

  # Override default methods:

  def plan_state(self):
    if self.engaged_in_fight:
      if self.target.arrest_delay == 0:
        self.engaged_in_fight = False
        self.supporting_cop.engaged_in_fight = False
        self.supporting_cop, support_cop.supporting_cop = None, None
        
        target.jail_time = target.jail_time_for_arrest()
        target.arrested_count += 1
        target.arrested = True

        self.model.jail_agent(target)
        self.target = None

    else:
      arrest_region = self.percept(radius=1)
      arrestible_agents = list(filter(lambda object: (type(object) == Citizen) and
        (object.state == "violent"), self.model.grid.get_cell_list_contents(arrest_region)))
      
      for agent in arrestible_agents:
        agent_surrounding = agent.percept_contents(radius=1)
        support_cops = list(filter(lambda object: (type(object) == Cop) and not object.engaged_in_fight, agent_surrounding))
        
        if len(support_cops) >= 1:
          support_cop = random.choice(support_cops)
          support_cop.engaged_in_fight = True
          
          self.supporting_cop, support_cop.supporting_cop = support_cop, self
          
          self.target = agent
          agent.state = "fighting"

          break

  def adjusted_move_vector(self):
    # vector order:
    # [violent, active, quiet, cop, media, flag, obstacle]
    inherent_move_vector = self.inherent_movement_desire_vector()

    visible_objects = self.model.grid.get_cell_list_contents(self.percept())
    visible_cops = len(list(filter(lambda object: type(object) == Cop, visible_objects))) + 1
    
    # Cops only care about violent, not active agents, unlike protestors
    # who are boyed on by both types.
    visible_violent_agents = len(list(filter(lambda object: (type(object) == Citizen) and
      (object.state == "violent"), visible_objects)))

    # If cops outnumber violent agents, pursue violent agents
    if visible_violent_agents < 0.5 * visible_cops:
      inherent_move_vector[0] += 2 #violent

    # else, retreat from crowd
    else:
      inherent_move_vector[0] -= 3 #violent
      inherent_move_vector[1] -= 2 #active

    return inherent_move_vector

  def plan_move(self):
    # Don't move if engaged in fight  
    if not self.engaged_in_fight and not self.frozen:
      super(Cop, self).plan_move()
    else:
      self.planned_position = self.position

class Media(Person):
  def __init__(self, unique_id, model, position, vision_radius,
    violent_affinity, active_affinity, quiet_affinity, cop_affinity,
    media_affinity, flag_affinity, obstacle_affinity):

    super().__init__(unique_id, model, position, vision_radius,
    violent_affinity, active_affinity, quiet_affinity, cop_affinity,
    media_affinity, flag_affinity, obstacle_affinity)

    self.picture_count = 0

    def plan_state(self):
      visible_objects = self.model.grid.get_cell_list_contents(self.percept())
      visible_fights = len(list(filter(lambda object: (type(object) == Citizen) and (object.state == "fighting"), visible_objects)))

      # Take a picture of all visible fights
      self.picture_count += visible_fights

    # No context based rules:
    def adjusted_move_vector(self):
      return self.inherent_movement_desire_vector()

