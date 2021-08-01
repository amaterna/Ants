import pygame
import math
import random
from itertools import chain

NUM_OF_ANTS = 100
NUM_OF_FOOD_SOURCES = 1
MAX_FOOD_AMOUNT = 1000
WORLD_SIZE = 200

RADIUS = 10


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visited_no_food_counter = 0
        self.visited_with_food_counter = 0


class Nest:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Grid:
    def __init__(self, size_x, size_y):
        self.size_x = size_x
        self.size_y = size_y
        self.cells = [[Cell(j, i) for j in range(size_x)] for i in range(size_y)]

    def inc_no_food_counter(self, x, y):
        self.cells[y][x].visited_no_food_counter += 50

    def inc_with_food_counter(self, x, y):
        self.cells[y][x].visited_with_food_counter += 50


class World:
    def __init__(self, size_x, size_y):
        self.size_x = size_x
        self.size_y = size_y


class Food:
    def __init__(self, x, y, amount):
        self.x = x
        self.y = y
        self.amount = amount

    def decrease_amount(self):
        if self.amount > 0:
            self.amount -= 1

    def is_empty(self):
        if self.amount > 0:
            return False
        else:
            return True


class Ant:
    def __init__(self, x, y, direction, size_x, size_y, food_sources=None, speed=1.0, grid=None):
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.size_x = size_x
        self.size_y = size_y
        self.food_sources = food_sources
        self.has_food = False
        self.grid = grid

    def get_int_pos(self):
        return math.floor(self.x), math.floor(self.y)

    def update_position(self, neighbour_cells=[]):
        self.update_direction(neighbour_cells)
        self.x += self.speed * math.cos(self.direction)
        self.y += self.speed * math.sin(self.direction)
        if self.x <= 0:
            self.x = 0.0001
            self.direction = math.pi - self.direction
        if self.x >= self.size_x:
            self.x = self.size_x - 0.0001
            self.direction = math.pi - self.direction

        if self.y <= 0:
            self.y = 0.0001
            self.direction *= -1
        if self.y >= self.size_y:
            self.y = self.size_y - 0.0001
            self.direction *= -1

        # self.update_direction()

    def randomize_direction(self):
        self.direction += random.choice([-1, 1]) * random.random() / 10.0

    def update_direction(self, neighbour_cells=[]):
        if self.has_food:
            delta_x = - self.x + self.start_x
            delta_y = - self.y + self.start_y
            dist = math.sqrt(delta_x * delta_x + delta_y * delta_y)
            if dist < 10:
                self.direction = math.atan2(delta_y, delta_x)
                if dist < 3:
                    self.has_food = False
                return

            max_food_counter = 0
            max_food_counter_id = -1
            max_cell = None
            for idx, cell in enumerate(neighbour_cells):
                with_food_counter = cell.visited_no_food_counter
                if with_food_counter > 0:
                    if with_food_counter > max_food_counter:
                        max_food_counter = with_food_counter
                        max_food_counter_id = idx
                        max_cell = cell

            if max_cell is not None:
                delta_x = - self.x + max_cell.x
                delta_y = - self.y + max_cell.y
                self.direction = math.atan2(delta_y, delta_x)
                return
            self.randomize_direction()
            return

        if self.food_sources is not None:
            min_distance = 1000000
            min_index = 0
            min_radians = 0

            for idx, food in enumerate(self.food_sources):
                delta_x = - self.x + food.x
                delta_y = - self.y + food.y
                dist = math.sqrt(delta_x*delta_x + delta_y*delta_y)
                if dist < min_distance and not food.is_empty():
                    min_distance = dist
                    min_index = idx
                    min_radians = math.atan2(delta_y, delta_x)

        if min_distance < 10:
            if min_distance < 3:
                self.has_food = True
                self.food_sources[min_index].decrease_amount()
            self.direction = min_radians
            return

        max_food_counter = 0
        max_food_counter_id = -1
        max_cell = None
        for idx, cell in enumerate(neighbour_cells):
            with_food_counter = cell.visited_with_food_counter
            if with_food_counter > 0:
                if with_food_counter > max_food_counter:
                    max_food_counter = with_food_counter
                    max_food_counter_id = idx
                    max_cell = cell

        if max_cell is not None:
            delta_x = - self.x + max_cell.x
            delta_y = - self.y + max_cell.y
            self.direction = math.atan2(delta_y, delta_x)
            return

        self.randomize_direction()


class AntsAlgorithm:
    def __init__(self):
        self.size = WORLD_SIZE
        self.world = World(self.size, self.size)
        pygame.init()
        pygame.display.set_caption("Ants Algorithm")
        self.screen = pygame.display.set_mode((self.world.size_x, self.world.size_y))
        self.clock = pygame.time.Clock()
        self.food_sources = self.create_food_sources()
        self.nest = None
        self.ants = self.create_ants()
        self.grid = Grid(size_x=self.size, size_y=self.size)


    def create_ants(self):
        ants = []
        start_x = random.randint(0, self.world.size_x)
        start_y = random.randint(0, self.world.size_y)
        self.nest = Nest(start_x, start_y)
        for i in range(NUM_OF_ANTS):
            # ants.append(Ant(random.randint(0, self.world.size_x), random.randint(0, self.world.size_y),
            #                 random.randint(0, 1500), self.world.size_x, self.world.size_y))

            ants.append(Ant(start_x, start_y, random.randint(0, 1500), self.world.size_x, self.world.size_y,
                            self.food_sources))
            # ants.append(Ant(i, i, i, self.world.size_x, self.world.size_y, speed=random.randint(1, 2)))
        return ants

    def create_food_sources(self):
        food_sources = []
        for i in range(NUM_OF_FOOD_SOURCES):
            food_sources.append(Food(random.randint(0, self.world.size_x), random.randint(0, self.world.size_y),
                                     random.randint(1, MAX_FOOD_AMOUNT)))
        return food_sources

    def process_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                quit()

    def update_positions(self):
        for ant in self.ants:
            neighbour_cells = []
            for dist_x in chain(range(-RADIUS, -1), range(1, RADIUS)):
                for dist_y in chain(range(-RADIUS, -1), range(1, RADIUS)):
                    curr_x, curr_y = ant.get_int_pos()
                    neighbour_x = curr_x + dist_x
                    neighbour_y = curr_y + dist_y
                    if neighbour_x < 0 or neighbour_x > self.size - 1:
                        continue
                    if neighbour_y < 0 or neighbour_y > self.size - 1:
                        continue
                    cell = self.grid.cells[neighbour_y][neighbour_x]
                    delta_x = - ant.x + cell.x
                    delta_y = - ant.y + cell.y
                    direction = math.atan2(delta_y, delta_x)
                    dir_diff = math.fabs(direction - ant.direction)
                    if dir_diff < math.pi/2:
                        neighbour_cells.append(self.grid.cells[neighbour_y][neighbour_x])

            ant.update_position(neighbour_cells)
            int_x, int_y = ant.get_int_pos()
            # print(f'int x {int_x} int y {int_y}')
            if ant.has_food:
                self.grid.inc_with_food_counter(int_x, int_y)
            else:
                self.grid.inc_no_food_counter(int_x, int_y)

    def decrease_pheromones(self):
        for col in range(self.grid.size_x):
            for row in range(self.grid.size_y):
                cell = self.grid.cells[row][col]
                if cell.visited_no_food_counter > 0:
                    cell.visited_no_food_counter -= 1
                if cell.visited_with_food_counter > 0:
                    cell.visited_with_food_counter -= 1

    def process_logic(self):
        self.update_positions()
        self.decrease_pheromones()

    def render_scene(self):
        self.screen.fill((10, 10, 10))
        for col in range(self.grid.size_x):
            for row in range(self.grid.size_y):
                cell = self.grid.cells[row][col]
                if cell.visited_no_food_counter > 0:
                    pygame.draw.rect(self.screen, pygame.Color(0, 0, min(100 + 6*cell.visited_no_food_counter, 255)),
                                     (cell.x, cell.y, 1, 1))
                    continue
                if cell.visited_with_food_counter > 0:
                    pygame.draw.rect(self.screen, pygame.Color(0, min(100 + 6*cell.visited_no_food_counter, 255), 0),
                                     (cell.x, cell.y, 1, 1))
                    continue
        if self.nest is not None:
            pygame.draw.circle(self.screen, pygame.Color(255, 255, 100), pygame.math.Vector2(self.nest.x, self.nest.y),
                               4)

        for food in self.food_sources:
            pygame.draw.circle(self.screen, pygame.Color(0, 250, 0), pygame.math.Vector2(food.x, food.y),
                               math.sqrt(food.amount))

        for ant in self.ants:
            color = pygame.Color(180, 180, 180)
            if ant.has_food:
                color = pygame.Color(0, 200, 100)
            pygame.draw.circle(self.screen, color, pygame.math.Vector2(ant.x, ant.y), 2)

        pygame.display.flip()

    def process_frame(self):
        # self.clock.tick(60)
        self.process_input()
        self.process_logic()
        self.render_scene()

    def run(self):
        while True:
            self.process_frame()
