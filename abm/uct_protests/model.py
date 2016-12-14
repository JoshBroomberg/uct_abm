import random

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import Grid

from .agents import Citizen, Media, Cop

from utils import ConfigError

class ProtestModel(Model):

  def __init__(self, height, width,
    initial_num_cops, initial_num_citizens, initial_num_media, hardcore_density, hanger_on_density, observer_density,
    vision_radius, agent_move_falibility,
    citizen_jailed_sensitivity, citizen_pictures_sensitivity, citizen_cops_sensitivity
    max_days, schedule, grid, height, width)

    super().__init__()
    
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
    self.default_hardcore_move_vector = [4, 2, 0, 4, 3, 5, -1]
    self.default_hanger_on_move_vector = [1, 1, 0, 1, 3, 1, -1]
    self.default_observer_move_vector = [-1, -1, 0, -1, 3, 0, -1]

    # Citizen legitimacy update factors
    self.citizen_jailed_sensitivity = citizen_jailed_sensitivity
    self.citizen_pictures_sensitivity = citizen_pictures_sensitivity
    self.citizen_cops_sensitivity = citizen_cops_sensitivity

    # Core model code
    # Model step represents an hour
    self.max_iters = max_days * 24
    self.iterations = 0
    self.schedule = RandomActivation(self)
    self.grid = Grid(height, width, torus=True)
    self.height = height
    self.width = width
    self.running = False

    self.previous_day_jailed_count = 0
    self.previous_day_pictures_count = 0
    self.previous_day_cops_count = initial_num_cops
    self.jailed_count = 0
    self.pictures_count = 0
    self.cops_count = initial_num_cops

    # Set such that when cops/agents are 2:1, the perceived arrest chance is 0.9
    self.arrest_constant = 1.15

    # Represents "harshness" of current regime.
    self.jail_time = 10

    if not (hardcore_density + hanger_on_density + observer_density == 1):
      raise ConfigError("Protestor densities must add up to 1")

    if initial_num_cops + initial_num_citizens + initial_num_media > (height * width):
      raise ConfigError("Too many humans for the given grid")

    placed_cops = 0
    placed_media = 0
    placed_citizens = 0

    population = initial_cops + initial_media + initial_citizens
    while (placed_cops + placed_media + placed_citizens) < population
      for (cell_contents, x, y) in self.grid.coord_iter():
        if self.grid.is_cell_empty((x, y)):
          seed = random.random()
          if seed < (float(initial_cops)/population):
            # cop = cop()
            self.add_agent(cop, x, y)

          elif seed < (float(initial_cops)/population) + (float(initial_media)/population):
            # media = media()
            self.add_agent(media, x, y)

          else:
            # citizen = citizen() (must be of random citizen type)
            self.add_agent(citizen, x, y)

  def add_agent(self, agent, x, y):
    self.grid[x][y] = agent
    self.schedule.add(agent)

  def num_jailed(self)
    return len(filter(lambda agent: ((type(agent) == Citizen) and (agent.arrested)),  self.schedule.agents))

  def num_pictures(self):
    media_agents = filter(lambda agent: (type(agent) == Media),  self.schedule.agents)
    return sum(map(lambda agent: agent.picture_count, media_agents))

  def num_cops(self):
    return len(filter(lambda agent: (type(agent) == Cop),  self.schedule.agents))

  def daily_update(self)
    self.previous_day_jailed_count = jailed_count
    self.previous_day_pictures_count = pictures_count
    self.previous_day_cops_count = cops_count
    self.jailed_count = self.num_jailed()
    self.pictures_count = self.num_pictures()
    self.cops_count = self.num_cops()

    citizen_agents = filter(lambda agent: (type(agent) == Citizen),  self.schedule.agents)
    for citizen in citizen_agents:
      citizen.update_legitimacy()

  def step(self):
    self.schedule.step()
    self.iterations += 1
    if self.iteration > self.max_iters:
        self.running = False
    if iteractions%24 == 0:
      self.daily_update()
