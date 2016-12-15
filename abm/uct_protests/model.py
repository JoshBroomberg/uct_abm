import random

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import Grid
from mesa.datacollection import DataCollector

from .agents import Citizen, Media, Cop
from .objects import Object

from utils import ConfigError

class ProtestModel(Model):

  def __init__(self, initial_num_cops, initial_num_citizens, initial_num_media, hardcore_density, hanger_on_density, observer_density,
    vision_radius, agent_move_falibility,
    default_hardcore_move_vector, default_hanger_on_move_vector, default_observer_move_vector, default_cop_move_vector, default_media_move_vector,
    citizen_jailed_sensitivity, citizen_pictures_sensitivity, citizen_cops_sensitivity,
    max_days, height, width, agent_region, obstacle_positions, flag_positions, cop_positions, arrest_delay, jail_time):

    super().__init__()
    
    print("model init")
    # Population initialisation
    self.initial_num_cops = initial_num_cops
    self.initial_num_citizens = initial_num_citizens
    self.initial_num_media = initial_num_media
    self.hardcore_density = hardcore_density
    self.hanger_on_density = hanger_on_density
    self.hanger_on_density = observer_density

    # Agent init

    # Agent movement factors
    self.vision_radius = vision_radius
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
    # Model step represents an hour
    self.max_iters = max_days * 24
    self.iterations = 0
    self.schedule = RandomActivation(self)
    self.grid = Grid(width, height, torus=False)
    self.height = height
    self.width = width
    self.running = True

    self.previous_day_jailed_count = 0
    self.previous_day_pictures_count = 0
    self.previous_day_cops_count = initial_num_cops
    self.jailed_count = 0
    self.pictures_count = 0
    self.cops_count = initial_num_cops

    # Set such that when cops/agents are 2:1, the perceived arrest chance is 0.9
    self.arrest_delay = arrest_delay
    self.arrest_constant = 1.15
    self.jail = [] # stores jailed agents
    self.jail_time = jail_time # Represents "harshness" of current regime.

    if not (hardcore_density + hanger_on_density + observer_density == 1):
      raise ConfigError("Protestor densities must add up to 1")

    if initial_num_cops + initial_num_citizens + initial_num_media > (height * width):
      raise ConfigError("Too many humans for the given grid")

    self.datacollector = DataCollector(
      model_reporters={
        "Quiet": lambda model: model.num_in_state("quiet"),
        "Active": lambda model: model.num_in_state("active"),
        "Violent": lambda model: model.num_in_state("violent"),
        "Fighting": lambda model: model.num_in_state("fighting"),
        "Jailed": lambda model: model.num_jailed(),
        "Average legitimacy": lambda model: model.average_legitimacy(),
        "Cop count": lambda model: model.num_cops(),
      }
    )

    # Place objects
    for position in obstacle_positions:
      self.grid[position[0]][position[1]] = Object("obstacle", position)

    for position in flag_positions:
      self.grid[position[0]][position[1]] = Object("flag", position)

    placed_cops = 0
    unique_id = 1
    
    for position in cop_positions:
      self.add_cop(unique_id, False, position[0], position[1])
      unique_id += 1
      placed_cops += 1

    placed_media = 0
    placed_citizens = 0
    population = initial_num_cops + initial_num_media + initial_num_citizens
    while (placed_cops + placed_media + placed_citizens) < population:
      for y in range(agent_region["y_0"], agent_region["y_1"]):
        for x in range(agent_region["x_0"], agent_region["x_1"]):
          if self.grid.is_cell_empty((x, y)):
            seed = random.random()
            
            # Optimised for adding citizens
            if seed > (float(initial_num_cops)/population) + (float(initial_num_media)/population):
              if placed_citizens < initial_num_citizens:
                self.add_citizen(unique_id, x, y)
                placed_citizens += 1
            elif seed > (float(initial_num_cops)/population):
              if placed_media < initial_num_media:
                placed_media += 1
                self.add_media(unique_id, x, y)
            else:
              if placed_cops < initial_num_cops:
                self.add_cop(unique_id, False, x, y)
                placed_cops += 1 

            unique_id += 1 

  def add_cop(self, id, frozen, x, y):
    vector = self.default_cop_move_vector
    cop = Cop(
      id,#unique_id,
      self,#model,
      (x, y),#position,
      self.vision_radius,#vision_radius,
      vector[0],#violent_affinity,
      vector[1],#active_affinity,
      vector[2],#quiet_affinity,
      vector[3],#cop_affinity,
      vector[4],#media_affinity,
      vector[5],#flag_affinity,
      vector[6],#obstacle_affinity,
      frozen
    )
    self.add_agent(cop, x, y)

  def add_citizen(self, id, x, y):
    seed = random.random()
    if seed < self.hardcore_density:
      agent_type = "hardcore"
      vector = self.default_hardcore_move_vector
      risk_lower = 0.66
      risk_upper = 1
    elif seed < self.hardcore_density + self.hanger_on_density:
      agent_type = "hanger_on"
      vector = self.default_hanger_on_move_vector
      risk_lower = 0.33
      risk_upper = 0.65
    else:
      agent_type = "observer"
      vector = self.default_observer_move_vector
      risk_lower = 0
      risk_upper = 0.32

    citizen = Citizen(
      id,#unique_id,
      self,#model,
      (x, y),#position,
      self.vision_radius,#vision_radius,
      vector[0],#violent_affinity,
      vector[1],#active_affinity,
      vector[2],#quiet_affinity,
      vector[3],#cop_affinity,
      vector[4],#media_affinity,
      vector[5],#flag_affinity,
      vector[6],#obstacle_affinity,
      agent_type,#citizen_type,
      "quiet", #state: starts are quiet for all
      random.random(),#hardship: uniform distribution between 0 and 1, type independant.
      random.random(),#perceived_legitimacy: uniform distribution between 0 and 1, type independant.
      random.uniform(risk_lower, risk_upper), #risk_tolerance: type dependant
      1 - random.uniform(risk_lower, risk_upper)#threshold: type dependant, but reversed from risk profile
    )
    self.add_agent(citizen, x, y)

  def add_media(self, id, x, y):
    vector = self.default_media_move_vector
    media = Media(
      id,#unique_id,
      self,#model,
      (x, y),#position,
      self.vision_radius,#vision_radius,
      vector[0],#violent_affinity,
      vector[1],#active_affinity,
      vector[2],#quiet_affinity,
      vector[3],#cop_affinity,
      vector[4],#media_affinity,
      vector[5],#flag_affinity,
      vector[6]#obstacle_affinity,
    )
    self.add_agent(media, x, y)

  def add_agent(self, agent, x, y):
    self.grid[x][y] = agent
    self.schedule.add(agent)

  def num_jailed(self):
    return len(list(filter(lambda agent: ((type(agent) == Citizen) and (agent.arrested)),  self.schedule.agents)))

  def num_in_state(self, state):
    return len(list(filter(lambda agent: ((type(agent) == Citizen) and (agent.state == state)),  self.schedule.agents)))

  def average_legitimacy(self):
    citizen_legitimacy = list(map(lambda a: a.perceived_legitimacy, (list(filter(lambda agent: (type(agent) == Citizen),  self.schedule.agents)))))
    summed_legitimacy = sum(citizen_legitimacy)
    count = len(citizen_legitimacy)
    return summed_legitimacy/float(count)*100

  def num_pictures(self):
    media_agents = list(filter(lambda agent: (type(agent) == Media),  self.schedule.agents))
    return sum(map(lambda agent: agent.picture_count, media_agents))

  def num_cops(self):
    return len(list(filter(lambda agent: (type(agent) == Cop),  self.schedule.agents)))

  def free_agent_from_jail(self, agent):
    for (cell_contents, x, y) in self.grid.coord_iter():
      if self.grid.is_cell_empty((x, y)):
        self.grid[x][y] = agent
        self.jail.remove(agent)

  def jail_agent(self, agent):
    self.jail.append(agent)
    self.grid[agent.position[0]][agent.position[1]] = None

  def daily_update(self):
    self.previous_day_jailed_count = self.jailed_count
    self.previous_day_pictures_count = self.pictures_count
    self.previous_day_cops_count = self.cops_count
    self.jailed_count = self.num_jailed()
    self.pictures_count = self.num_pictures()
    self.cops_count = self.num_cops()

    # Adjust perceived legitimacy
    citizen_agents = list(filter(lambda agent: (type(agent) == Citizen),  self.schedule.agents))
    
    for citizen in citizen_agents:
      citizen.update_legitimacy()

    # Reset number of pictures taken by reporters
    media_agents = list(filter(lambda agent: (type(agent) == Media),  self.schedule.agents))
    for media in media_agents:
      media.picture_count = 0

  def step(self):
    self.datacollector.collect(self)
    self.schedule.step()
    self.iterations += 1
    if self.iterations > self.max_iters:
        self.running = False
    if self.iterations%24 == 0:
      self.daily_update()
