import random

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import Grid
from mesa.datacollection import DataCollector

from .agents import Citizen, Media, Cop
from .objects import Object

from utils import ConfigError, co_ords_for_area

class ProtestModel(Model):

  def __init__(self, initial_num_citizens, initial_num_media, hardcore_density, hanger_on_density, observer_density,
    agent_vision_radius, agent_move_falibility,
    default_hardcore_move_vector, default_hanger_on_move_vector, default_observer_move_vector, default_cop_move_vector, default_media_move_vector,
    citizen_jailed_sensitivity, citizen_pictures_sensitivity, citizen_cops_sensitivity,
    max_days, height, width,
    agent_regions, obstacle_regions, flag_regions, cop_regions,
    arrest_delay, jail_time):

    super().__init__()
    self.steps_per_day = 12

    # Population initialisation
    self.initial_num_cops = len(co_ords_for_area(cop_regions))
    self.initial_num_citizens = initial_num_citizens
    self.initial_num_media = initial_num_media
    self.hardcore_density = hardcore_density
    self.hanger_on_density = hanger_on_density
    self.hanger_on_density = observer_density

    # Agent init

    # Agent movement factors
    self.agent_vision_radius = agent_vision_radius
    self.agent_move_falibility = agent_move_falibility

    # vector order:
    # [violent, active, quiet, cop, media, flag, obstacle]
    self.default_hardcore_move_vector = default_hardcore_move_vector
    self.default_hanger_on_move_vector = default_hanger_on_move_vector
    self.default_observer_move_vector = default_observer_move_vector
    self.default_cop_move_vector = default_cop_move_vector
    self.default_media_move_vector = default_media_move_vector

    # Citizen legitimacy update factors
    self.citizen_jailed_sensitivity = citizen_jailed_sensitivity
    self.citizen_pictures_sensitivity = citizen_pictures_sensitivity
    self.citizen_cops_sensitivity = citizen_cops_sensitivity

    # Core model code
    # Model step represents 2 hours
    self.max_iters = max_days * self.steps_per_day
    self.iterations = 0
    self.schedule = RandomActivation(self)
    self.grid = Grid(width, height, torus=False)
    self.height = height
    self.width = width
    self.running = True

    self.previous_day_jailed_count = 0
    self.previous_day_pictures_count = 0
    self.previous_day_cops_count = self.initial_num_cops
    self.jailed_count = 0
    self.pictures_count = 0
    self.cops_count = self.initial_num_cops

    # Set such that when cops/agents are 2:1, the perceived arrest chance is 0.9
    self.arrest_delay = arrest_delay
    self.arrest_constant = 1.15
    self.jail = [] # stores jailed agents
    self.jail_time = jail_time # Represents "harshness" of current regime.

    if not (hardcore_density + hanger_on_density + observer_density == 1):
      raise ConfigError("Protestor densities must add up to 1")

    if self.initial_num_cops + initial_num_citizens + initial_num_media > (height * width):
      raise ConfigError("Too many humans for the given grid")

    self.total_fights = 0
    self.total_jailed = 0
    self.hours_without_protest = 0
    self.hours_without_conflict = 0

    self.datacollector = DataCollector(
      model_reporters={
        "Quiet": lambda model: model.num_in_state("quiet"),
        "Active": lambda model: model.num_in_state("active"),
        "Violent": lambda model: model.num_in_state("violent"),
        "Fighting": lambda model: model.num_in_state("fighting"),
        "Protesting": lambda model: model.num_protesting(),
        "Jailed": lambda model: model.num_jailed(),
        "Frustrated": lambda model: model.num_frustrated(),
        "Average legitimacy": lambda model: model.average_legitimacy(),
        "Average grievance": lambda model: model.average_grievance(),
        "Average ripeness": lambda model: model.average_grievance()*model.num_in_state("quiet")/float(model.average_risk_aversion()),
        "Cop count": lambda model: model.num_cops(),
        "Num pictures": lambda model: model.num_pictures(),
        "Total fights": lambda model: model.total_fights,
        "Total jailed": lambda model: model.total_jailed,
        "Protest waiting time": lambda model: model.hours_without_protest,
        "Conflict waiting time": lambda model: model.hours_without_conflict,
      },

      agent_reporters={
        "perceived_gain": lambda agent: agent.perceived_gain() if isinstance(agent, Citizen) else 0,
        "net_risk_active": lambda agent: agent.net_risk("active") if isinstance(agent, Citizen) else 0,
        "net_risk_violent": lambda agent: agent.perceived_gain() - agent.net_risk("violent") if isinstance(agent, Citizen) else 0,
        "act_utils": lambda agent: agent.net_risk("violent") if isinstance(agent, Citizen) else 0,
        "threshold": lambda agent: agent.threshold if isinstance(agent, Citizen) else 0,
      } 
    )

    self.agent_regions = agent_regions
    self.cop_regions = cop_regions
    self.flag_regions = flag_regions
    self.obstacle_regions = obstacle_regions

    # Place objects
    for position in co_ords_for_area(obstacle_regions):
      self.grid[position[0]][position[1]] = Object("obstacle", position)

    for position in co_ords_for_area(flag_regions):
      self.grid[position[0]][position[1]] = Object("flag", position)

    unique_id = 1
    
    for cop_region in cop_regions:
      frozen = cop_region["frozen"]

      for position in co_ords_for_area([cop_region]):
        self.add_cop(unique_id, frozen, position[0], position[1])
        unique_id += 1

    placed_media = 0
    placed_citizens = 0
    population = initial_num_media + initial_num_citizens
    while (placed_media + placed_citizens) < population:
      (x, y) = random.choice(co_ords_for_area(agent_regions))
      
      if self.grid.is_cell_empty((x, y)):
        seed = random.random()

        # Optimised for adding citizens
        if seed > (float(initial_num_media)/population):
          if placed_citizens < initial_num_citizens:
            self.add_citizen(unique_id, x, y)
            placed_citizens += 1

        else:
          if placed_media < initial_num_media:
            placed_media += 1
            self.add_media(unique_id, x, y)

        unique_id += 1 

  def add_cop(self, id, frozen, x, y):
    vector = self.default_cop_move_vector
    cop = Cop(
      id, #unique_id,
      self, #model,
      (x, y), #position,
      self.agent_vision_radius, #agent_vision_radius,
      vector[0], #violent_affinity,
      vector[1], #active_affinity,
      vector[2], #quiet_affinity,
      vector[3], #cop_affinity,
      vector[4], #media_affinity,
      vector[5], #flag_affinity,
      vector[6], #obstacle_affinity,
      frozen
    )
    self.add_agent(cop, x, y)

  def add_citizen(self, id, x, y):
    seed = random.random()
    if seed < self.hardcore_density:
      agent_type = "hardcore"
      vector = self.default_hardcore_move_vector
      risk_lower = 0.8
      risk_upper = 0.95
    elif seed < self.hardcore_density + self.hanger_on_density:
      agent_type = "hanger_on"
      vector = self.default_hanger_on_move_vector
      risk_lower = 0.4
      risk_upper = 0.6
    else:
      agent_type = "observer"
      vector = self.default_observer_move_vector
      risk_lower = 0
      risk_upper = 0.32

    citizen = Citizen(
      id, #unique_id,
      self, #model,
      (x, y), #position,
      self.agent_vision_radius, #agent_vision_radius,
      vector[0], #violent_affinity,
      vector[1], #active_affinity,
      vector[2], #quiet_affinity,
      vector[3], #cop_affinity,
      vector[4], #media_affinity,
      vector[5], #flag_affinity,
      vector[6], #obstacle_affinity,
      agent_type, #citizen_type,
      "quiet", #state: starts are quiet for all
      random.uniform(0, 0.2), #hardship: uniform distribution between 0 and 1, type independant.
      random.uniform(0.7, 0.9), #perceived_legitimacy: uniform distribution between 0 and 1, type independant.
      random.uniform(risk_lower, risk_upper), #risk_tolerance: type dependant
      1 - random.uniform(risk_lower, risk_upper) #threshold: type dependant, but reversed from risk profile
    )
    self.add_agent(citizen, x, y)

  def add_media(self, id, x, y):
    vector = self.default_media_move_vector
    media = Media(
      id, #unique_id,
      self, #model,
      (x, y), #position,
      self.agent_vision_radius, #agent_vision_radius,
      vector[0], #violent_affinity,
      vector[1], #active_affinity,
      vector[2], #quiet_affinity,
      vector[3], #cop_affinity,
      vector[4], #media_affinity,
      vector[5], #flag_affinity,
      vector[6] #obstacle_affinity,
    )
    self.add_agent(media, x, y)

  def add_agent(self, agent, x, y):
    self.grid[x][y] = agent
    self.schedule.add(agent)

  def num_jailed(self):
    return len(list(filter(lambda agent: ((type(agent) == Citizen) and (agent.arrested)),  self.schedule.agents)))

  def agents_in_state(self, state):
    return list(filter(lambda agent: ((type(agent) == Citizen) and (agent.state == state)),  self.schedule.agents))

  def num_in_state(self, state):
    return len(self.agents_in_state(state))

  def num_protesting(self):
    return self.num_in_state("fighting") + self.num_in_state("violent") + self.num_in_state("active")

  def num_frustrated(self):
    return len(list(filter(lambda agent: ((type(agent) == Citizen) and 
      (agent.perceived_gain() > agent.threshold) and 
      (agent.state not in ["violent", "active", "fighting"])),  self.schedule.agents)))

  def average_legitimacy(self):
    citizen_legitimacy = list(map(lambda a: a.perceived_legitimacy, (list(filter(lambda agent: (type(agent) == Citizen),  self.schedule.agents)))))
    summed_legitimacy = sum(citizen_legitimacy)
    count = len(citizen_legitimacy)
    return summed_legitimacy/float(count)*100

  def average_grievance(self):
    citizen_grievance = list(map(lambda a: a.perceived_gain(), (list(filter(lambda agent: (type(agent) == Citizen),  self.schedule.agents)))))
    summed_grievance = sum(citizen_grievance)
    count = len(citizen_grievance)
    return summed_grievance/float(count)*100

  def average_risk_aversion(self):
    citizen_ra = list(map(lambda a: (1-a.risk_tolerance), (list(filter(lambda agent: (type(agent) == Citizen),  self.schedule.agents)))))
    summed_ra = sum(citizen_ra)
    count = len(citizen_ra)
    return summed_ra/float(count)*100

  def num_pictures(self):
    media_agents = list(filter(lambda agent: (type(agent) == Media),  self.schedule.agents))
    return sum(map(lambda agent: agent.picture_count, media_agents))

  def num_cops(self):
    return len(list(filter(lambda agent: (type(agent) == Cop),  self.schedule.agents)))

  def free_agent_from_jail(self, agent):
    placed = False
    while not placed:
      position = random.choice(co_ords_for_area(self.agent_regions))
      if self.grid.is_cell_empty(position):
        self.grid[position[0]][position[1]] = agent
        return position

  def jail_agent(self, agent):
    self.grid[agent.position[0]][agent.position[1]] = None
    agent.position = None
    agent.planned_position = None
    self.total_jailed += 1

  def daily_update(self):
    self.previous_day_jailed_count = self.jailed_count
    self.previous_day_pictures_count = self.pictures_count
    self.previous_day_cops_count = self.cops_count
    self.jailed_count = self.num_jailed()
    self.pictures_count = self.num_pictures()
    self.cops_count = self.num_cops()

    # Adjust perceived legitimacy of all agents based on arrests, cops and pictures of fights.
    citizen_agents = list(filter(lambda agent: (type(agent) == Citizen),  self.schedule.agents))
    
    for citizen in citizen_agents:
      citizen.update_legitimacy()

    # Reset number of pictures taken by reporters
    media_agents = list(filter(lambda agent: (type(agent) == Media),  self.schedule.agents))
    for media in media_agents:
      media.picture_count = 0

  def experimental_changes(self):
    initial_spark_iteration = 5

    spark_hardship_increase = 0.25
    spark_legitimacy_decrease = 0.4

    protest_response_iteration = 30
    protest_response = "none"
    cop_modifier = 150

    if self.iterations == initial_spark_iteration:
      citizen_agents = list(filter(lambda agent: (type(agent) == Citizen),  self.schedule.agents))
    
      for citizen in citizen_agents:
          citizen.hardship += spark_hardship_increase
          citizen.perceived_legitimacy -= spark_legitimacy_decrease

    if self.iterations == protest_response_iteration:
      if protest_response == "cops":
        max_id = max(list(map(lambda agent: agent.unique_id, self.schedule.agents)))
        unique_id = max_id + 1
        
        placed = 0
        while placed < cop_modifier:
          position = random.choice(co_ords_for_area(self.agent_regions))
          if self.grid.is_cell_empty(position):
            self.add_cop(unique_id, False, position[0], position[1])
            unique_id += 1
            placed += 1

      elif protest_response == "remove_cops":
        removed = 0
        while removed < cop_modifier and self.num_cops() > 0:
          cop = random.choice(list(filter(lambda agent: (type(agent) == Cop),  self.schedule.agents)))
          self.schedule.remove(cop)
          self.grid[cop.position[0]][cop.position[1]] = None
          removed += 1

  # Advance the model a single iteration.
  def step(self):

    # Collect waiting time information.
    if self.num_protesting() > (0.25 * self.initial_num_citizens):
      self.hours_without_protest = 0
    else:
      self.hours_without_protest +=1
    
    if self.num_in_state("fighting") + self.num_in_state("violent") > (0.15 * self.initial_num_citizens):
      self.hours_without_conflict = 0
    else:
      self.hours_without_conflict +=1

    # Run data collector.
    self.datacollector.collect(self)

    # Step the model
    self.schedule.step()
    self.iterations += 1
    if self.iterations > self.max_iters:
        self.running = False

    # Perform updates that occur once per 'day', ie: on a non-iteration basis, 
    if self.iterations % self.steps_per_day == 0:
      self.daily_update()

    # Check for experimental changes once per iteration.
    self.experimental_changes()

