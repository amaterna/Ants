import pygame
import math
import random
import traceback
from numba import jit

from itertools import chain

RUNNING = True

DARKGREY = (30, 30, 30)
GREY = (100, 100, 100)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
DARKER_GREEN = (0, 180, 0)
RED = (255, 0, 0)
TILEWIDTH = 50

NUM_OF_ANTS = 400
NUM_OF_FOOD_SOURCES = 15
FOOD_SOURCE_SIZE = 10
MIN_FOOD_AMOUNT = 500
MAX_FOOD_AMOUNT = 1000
NEST_SIZE = 10
WORLD_SIZE = 200
NO_FOOD_NEST_VISIT_THRESH = 900

RADIUS = 10
CELL_SIZE = 4
SIZE_X = 250
SIZE_Y = 250

RENDER_SIZE_X = SIZE_X * CELL_SIZE
RENDER_SIZE_Y = SIZE_Y * CELL_SIZE

DRAW_PHEROMONES = False

DRAW_FOOD_PHEROMONES = False
DRAW_NEST_PHEROMONES = False
DRAW_DEAD_PHEROMONES = False

DRAW_HORIZONS = False
RENDER = True
CLOCK_TICK = 20
CLOCK_STEP = 5

# NW = 0
# N = 1
# NE = 2
# W = 3
# E = 4
# SW = 5
# S = 6
# SE = 7

NW = 0
N = 1
NE = 2
E = 3
SE = 4
S = 5
SW = 6
W = 7

# DIRECTIONS = [NW, N, NE, W, E, SW, S, SE]
DIRECTIONS = [NW, N, NE, E, SE, S, SW, W]
DIRECTIONS_LEN = len(DIRECTIONS)
MIRROR = []
# DIR_VECTORS = [(-1, -1), (0, -1), (1, -1),
#                (-1, 0), (1, 0),
#                (-1, 1), (0, 1), (1, 1)]
#               [NW,        N,      NE,       E,      SE,      S,      SW,       W]
DIR_VECTORS = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
VECTORS_TO_DIRS = {
    (-1, -1): NW,
    (0, -1): N,
    (1, -1): NE,
    (1, 0): E,
    (1, 1): SE,
    (0, 1): S,
    (-1, 1): SW,
    (-1, 0): W,
}

EMPTY = 0
NEST = 1
FOOD = 2
PHEROMONE_NO_FOOD = 3
PHEROMONE_FOOD = 4

NO_FOOD_PHEROMONES_INCREASE = 200
WITH_FOOD_PHEROMONES_INCREASE = 200
DEAD_PHEROMONE_INCREASE = 200

RANDOMIZE_POS_RANGE = 1000
RANDOMIZE_POS_THRESHOLD = 900

HORIZON_SIZE = 10


def is_main_direction(direction):
    if direction == N or direction == S or direction == W or direction == E:
        return True
    return False


def get_adjecent_dirs(direction):
    return [
        DIRECTIONS[(direction - 1) % DIRECTIONS_LEN],
        direction,
        DIRECTIONS[(direction + 1) % DIRECTIONS_LEN],
    ]


def get_adjecent_coord(x, y, direction):
    dir_x, dir_y = DIR_VECTORS[direction]
    return x+dir_x, y+dir_y


def get_adjecent_coords(x, y, direction, adjecent_dirs):
    adj_coords = []
    for dir_ in adjecent_dirs:
        dir_x, dir_y = DIR_VECTORS[dir_]
        adj_coords.append((x+dir_x, y+dir_y))
    return adj_coords


CELL_TYPE_EMPTY = 0
CELL_TYPE_NEST = 1
CELL_TYPE_FOOD = 2
CELL_TYPE_PHEROMONES = 3


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visited_no_food_counter = 0
        self.visited_with_food_counter = 0
        self.visited_dead_counter = 0
        self.food = None
        self.type = CELL_TYPE_EMPTY
        self.nest = None

    def __str__(self):
        return f'({self.x} {self.y} no food: {self.visited_no_food_counter} ' \
               f'with food: {self.visited_with_food_counter}) ' \
               f'dead: {self.visited_dead_counter}'

    def draw(self, surface, size):

        if self.type == CELL_TYPE_EMPTY:
            return
        if (DRAW_NEST_PHEROMONES or DRAW_FOOD_PHEROMONES or DRAW_DEAD_PHEROMONES) and self.type == CELL_TYPE_PHEROMONES:
            green_part = min(255, self.visited_with_food_counter)
            blue_part = min(255, self.visited_no_food_counter)
            red_part = min(255, self.visited_dead_counter)

            if green_part == 0 and blue_part == 0 and red_part == 0:
                return

            if DRAW_FOOD_PHEROMONES and green_part > 0:
                pygame.draw.rect(surface, (0, green_part, 0),
                                 (self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE/2, CELL_SIZE/2))

            if DRAW_NEST_PHEROMONES and blue_part > 0:
                pygame.draw.rect(surface, (0, 0, blue_part),
                                 (self.x * CELL_SIZE+CELL_SIZE/2, self.y * CELL_SIZE+CELL_SIZE/2,
                                  CELL_SIZE/2, CELL_SIZE/2))
            if DRAW_DEAD_PHEROMONES and red_part > 0:
                pygame.draw.rect(surface, (red_part, 0, 0),
                                 (self.x * CELL_SIZE + CELL_SIZE / 2, self.y * CELL_SIZE + CELL_SIZE / 2,
                                  CELL_SIZE / 2, CELL_SIZE / 2))

            #
            # color = (0, green_part, blue_part)
            # pygame.draw.rect(surface, color, (self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        if self.type == CELL_TYPE_FOOD:
            self.food.draw(surface, self.x, self.y)

        if self.type == CELL_TYPE_NEST:
            self.nest.draw(surface, self.x, self.y)

    def has_pheromones(self):
        if self.visited_no_food_counter > 0 or self.visited_with_food_counter > 0 or self.visited_dead_counter > 0:
            return True
        return False


class Nest:
    def __init__(self, x, y, radius=NEST_SIZE):
        self.x = x
        self.y = y
        self.radius = radius
        print(f'create nest x: {self.x} y: {self.y} radius: {self.radius}')

    def draw(self, surface, x, y):
        pygame.draw.rect(surface, RED, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))


@jit(nopython=True)
def is_valid_coord(x, y, gridx, gridy):
    if x < 0 or x > gridx - 1:
        return False
    if y < 0 or y > gridy - 1:
        return False
    return True


def cell_visited_no_food_counter(cell):
    # if cell.visited_dead_counter > 0:
    #     return 0
    return max(cell.visited_no_food_counter - cell.visited_dead_counter, 0)


def cell_visited_with_food_counter(cell):
    # if cell.visited_dead_counter > 0:
    #     return 0
    return max(cell.visited_with_food_counter - cell.visited_dead_counter, 0)


def is_cell_nest_type(cell):
    return cell.type == CELL_TYPE_NEST


def is_cell_food_type(cell):
    return cell.type == CELL_TYPE_FOOD


class Grid:
    def __init__(self, size_x, size_y):
        self.size_x = size_x
        self.size_y = size_y
        self.cells = [[Cell(j, i) for j in range(size_x)] for i in range(size_y)]
        self.cell_size = CELL_SIZE
        self.non_empty_cells = set()

    # def is_valid_coord(self, x, y):
    #     return is_valid_coord_numba(x, y, self.size_x, self.size_y)

    def draw(self, surface):
        # for col in range(self.size_x):
        #     pygame.draw.line(surface, GREY, (col*CELL_SIZE, 0), (col*CELL_SIZE, RENDER_SIZE_Y))
        # for row in range(self.size_y):
        #     pygame.draw.line(surface, GREY, (0, row*CELL_SIZE), (RENDER_SIZE_X, row*CELL_SIZE))
        # for col in range(self.size_x):
        #     for row in range(self.size_y):
        #         cell = self.cells[row][col]
        #         cell.draw(surface, self.cell_size)
        for x, y in self.non_empty_cells:
            cell = self.cells[y][x]
            cell.draw(surface, self.cell_size)

    def inc_no_food_counter(self, x, y, amount=NO_FOOD_PHEROMONES_INCREASE):
        if self.cells[y][x].type == CELL_TYPE_NEST or self.cells[y][x].type == CELL_TYPE_FOOD:
            return

        self.cells[y][x].visited_no_food_counter += amount
        self.cells[y][x].visited_no_food_counter = int(max(min(self.cells[y][x].visited_no_food_counter, 1000), 0))
        # print(f'self.cells[y][x].visited_no_food_counter {self.cells[y][x].visited_no_food_counter}')
        self.cells[y][x].type = CELL_TYPE_PHEROMONES
        self.non_empty_cells.add((x, y))

    def inc_with_food_counter(self, x, y, amount=WITH_FOOD_PHEROMONES_INCREASE):
        if self.cells[y][x].type == CELL_TYPE_NEST or self.cells[y][x].type == CELL_TYPE_FOOD:
            return

        self.cells[y][x].visited_with_food_counter += amount
        self.cells[y][x].visited_with_food_counter = int(max(min(self.cells[y][x].visited_with_food_counter, 1000), 0))
        # print(f'self.cells[y][x].visited_with_food_counter {self.cells[y][x].visited_with_food_counter}')
        self.cells[y][x].type = CELL_TYPE_PHEROMONES
        self.non_empty_cells.add((x, y))

    def inc_dead_counter(self, x, y, amount=DEAD_PHEROMONE_INCREASE):
        if self.cells[y][x].type == CELL_TYPE_NEST or self.cells[y][x].type == CELL_TYPE_FOOD:
            return

        self.cells[y][x].visited_dead_counter += amount
        self.cells[y][x].visited_dead_counter = int(max(min(self.cells[y][x].visited_dead_counter, 1000), 0))
        # print(f'self.cells[y][x].visited_with_food_counter {self.cells[y][x].visited_with_food_counter}')
        self.cells[y][x].type = CELL_TYPE_PHEROMONES
        self.non_empty_cells.add((x, y))


    def update(self):
        points_to_remove = []
        # print(f'non empty cells len: {len(self.non_empty_cells)}')
        for x, y in self.non_empty_cells:
            cell = self.cells[y][x]
            if cell.type == CELL_TYPE_PHEROMONES:
                if cell.visited_no_food_counter > 0:
                    cell.visited_no_food_counter -= 1
                if cell.visited_with_food_counter > 0:
                    cell.visited_with_food_counter -= 1
                if cell.visited_dead_counter > 0:
                    cell.visited_dead_counter -= 1
                if not cell.has_pheromones():
                    points_to_remove.append((x, y))
                    cell.type = CELL_TYPE_EMPTY
            elif cell.type == CELL_TYPE_FOOD:
                if cell.food.amount == 0:
                    points_to_remove.append((x, y))
                    cell.type = CELL_TYPE_EMPTY
        for p in points_to_remove:
            self.non_empty_cells.remove(p)

    def set_food(self, food):

        begin_x = food.x
        begin_y = food.y

        for x_ in range(0, FOOD_SOURCE_SIZE):
            for y_ in range(0, FOOD_SOURCE_SIZE):
                x = begin_x + x_
                y = begin_y + y_
                if not is_valid_coord(x, y, self.size_x, self.size_y):
                    continue
                self.cells[y][x].food = food
                self.cells[y][x].type = CELL_TYPE_FOOD
                self.non_empty_cells.add((x, y))

    def set_nest(self, nest):

        center_x = nest.x
        center_y = nest.y
        radius = nest.radius

        for x_ in range(-radius, radius):
            for y_ in range(-radius, radius):
                x = center_x + x_
                y = center_y + y_
                dist = math.sqrt(x_*x_ + y_*y_)
                if dist > radius:
                    continue
                if not is_valid_coord(x, y, self.size_x, self.size_y):
                    continue
                self.cells[y][x].nest = nest
                self.cells[y][x].type = CELL_TYPE_NEST
                self.non_empty_cells.add((x, y))

    def get_horizon_cells(self, direction, x_pos, y_pos):
        ret_cells = []
        dir_x, dir_y = DIR_VECTORS[direction]
        if not is_main_direction(direction):
            range_x = range(0, dir_x*HORIZON_SIZE)
            if dir_x < 0:
                range_x = range(dir_x * HORIZON_SIZE + 1, 1)
            range_y = range(0, dir_y * HORIZON_SIZE)
            if dir_y < 0:
                range_y = range(dir_y * HORIZON_SIZE + 1, 1)

            for x_ in range_x:
                for y_ in range_y:
                    if x_ == 0 and y_ == 0:
                        continue
                    x_n_pos = x_pos + x_
                    y_n_pos = y_pos + y_
                    if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                        continue
                    ret_cells.append(self.cells[y_n_pos][x_n_pos])
        else:
            if dir_x == 0:
                if dir_y > 0:
                    range_y = range(1, HORIZON_SIZE)
                    for y_ in range_y:
                        for x_ in range(-y_, y_+1):
                            x_n_pos = x_pos + x_
                            y_n_pos = y_pos + y_
                            if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                                continue
                            ret_cells.append(self.cells[y_n_pos][x_n_pos])
                else:  # dir_y < 0
                    range_y = range(-HORIZON_SIZE+1, 0)
                    for y_ in range_y:
                        for x_ in range(y_, -y_+1):
                            x_n_pos = x_pos + x_
                            y_n_pos = y_pos + y_
                            if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                                continue
                            ret_cells.append(self.cells[y_n_pos][x_n_pos])
            else:  # dir_y == 0
                if dir_x > 0:
                    range_x = range(1, HORIZON_SIZE)
                    for x_ in range_x:
                        for y_ in range(-x_, x_+1):
                            x_n_pos = x_pos + x_
                            y_n_pos = y_pos + y_
                            if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                                continue
                            ret_cells.append(self.cells[y_n_pos][x_n_pos])
                else:  # dir_x < 0
                    range_x = range(-HORIZON_SIZE+1, 0)
                    for x_ in range_x:
                        for y_ in range(x_, -x_+1):
                            x_n_pos = x_pos + x_
                            y_n_pos = y_pos + y_
                            if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                                continue
                            ret_cells.append(self.cells[y_n_pos][x_n_pos])
        # print(f"s ret cells: {len(ret_cells)}")
        return ret_cells

    def get_best_cell(self, direction, x_pos, y_pos, mode):
        ret_cells = []
        # get_pheromone_level = lambda cell: cell.visited_no_food_counter
        # if mode == MODE_TO_FOOD:
        #     get_pheromone_level = lambda cell: cell.visited_with_food_counter

        # aim_predicate = lambda cell: cell.type == CELL_TYPE_NEST
        # if mode == MODE_TO_FOOD:
        #     aim_predicate = lambda cell: cell.type == CELL_TYPE_FOOD

        get_pheromone_level = cell_visited_no_food_counter
        if mode == MODE_TO_FOOD:
            get_pheromone_level = cell_visited_with_food_counter

        aim_predicate = is_cell_nest_type
        if mode == MODE_TO_FOOD:
            aim_predicate = is_cell_food_type

        best_cell = None
        max_pheromone_level = -1
        closest_aim_cell = None
        candidate_cells = []
        min_dist_aim_cell = 10000000

        dir_x, dir_y = DIR_VECTORS[direction]
        if not is_main_direction(direction):
            range_x = range(0, dir_x*HORIZON_SIZE)
            if dir_x < 0:
                range_x = range(dir_x * HORIZON_SIZE + 1, 1)
            range_y = range(0, dir_y * HORIZON_SIZE)
            if dir_y < 0:
                range_y = range(dir_y * HORIZON_SIZE + 1, 1)

            for x_ in range_x:
                for y_ in range_y:
                    if x_ == 0 and y_ == 0:
                        continue
                    x_n_pos = x_pos + x_
                    y_n_pos = y_pos + y_
                    if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                        continue
                    cell = self.cells[y_n_pos][x_n_pos]
                    if aim_predicate(cell):
                        dist = max(abs(x_), abs(y_))
                        if dist < min_dist_aim_cell:
                            min_dist_aim_cell = dist
                            closest_aim_cell = cell
                        # return cell
                    if cell.visited_dead_counter > 0:
                        continue
                    pheromone_level = get_pheromone_level(cell)
                    if pheromone_level == max_pheromone_level:
                        candidate_cells.append(cell)
                    if pheromone_level > max_pheromone_level:
                        candidate_cells = []
                        max_pheromone_level = pheromone_level
                        best_cell = cell
        else:
            if dir_x == 0:
                if dir_y > 0:
                    range_y = range(1, HORIZON_SIZE)
                    for y_ in range_y:
                        for x_ in range(-y_, y_+1):
                            x_n_pos = x_pos + x_
                            y_n_pos = y_pos + y_
                            if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                                continue
                            cell = self.cells[y_n_pos][x_n_pos]
                            if aim_predicate(cell):
                                dist = max(abs(x_), abs(y_))
                                if dist < min_dist_aim_cell:
                                    min_dist_aim_cell = dist
                                    closest_aim_cell = cell
                                # return cell
                            if cell.visited_dead_counter > 0:
                                continue
                            pheromone_level = get_pheromone_level(cell)
                            if pheromone_level == max_pheromone_level:
                                candidate_cells.append(cell)
                            if pheromone_level > max_pheromone_level:
                                candidate_cells = []
                                max_pheromone_level = pheromone_level
                                best_cell = cell
                else:  # dir_y < 0
                    range_y = range(-HORIZON_SIZE+1, 0)
                    for y_ in range_y:
                        for x_ in range(y_, -y_+1):
                            x_n_pos = x_pos + x_
                            y_n_pos = y_pos + y_
                            if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                                continue
                            cell = self.cells[y_n_pos][x_n_pos]
                            if aim_predicate(cell):
                                dist = max(abs(x_), abs(y_))
                                if dist < min_dist_aim_cell:
                                    min_dist_aim_cell = dist
                                    closest_aim_cell = cell
                                # return cell
                            if cell.visited_dead_counter > 0:
                                continue
                            pheromone_level = get_pheromone_level(cell)
                            if pheromone_level == max_pheromone_level:
                                candidate_cells.append(cell)
                            if pheromone_level > max_pheromone_level:
                                candidate_cells = []
                                max_pheromone_level = pheromone_level
                                best_cell = cell
            else:  # dir_y == 0
                if dir_x > 0:
                    range_x = range(1, HORIZON_SIZE)
                    for x_ in range_x:
                        for y_ in range(-x_, x_+1):
                            x_n_pos = x_pos + x_
                            y_n_pos = y_pos + y_
                            if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                                continue
                            cell = self.cells[y_n_pos][x_n_pos]
                            if aim_predicate(cell):
                                dist = max(abs(x_), abs(y_))
                                if dist < min_dist_aim_cell:
                                    min_dist_aim_cell = dist
                                    closest_aim_cell = cell
                                # return cell
                            if cell.visited_dead_counter > 0:
                                continue
                            pheromone_level = get_pheromone_level(cell)
                            if pheromone_level == max_pheromone_level:
                                candidate_cells.append(cell)
                            if pheromone_level > max_pheromone_level:
                                candidate_cells = []
                                max_pheromone_level = pheromone_level
                                best_cell = cell
                else:  # dir_x < 0
                    range_x = range(-HORIZON_SIZE+1, 0)
                    for x_ in range_x:
                        for y_ in range(x_, -x_+1):
                            x_n_pos = x_pos + x_
                            y_n_pos = y_pos + y_
                            if not is_valid_coord(x_n_pos, y_n_pos, self.size_x, self.size_y):
                                continue
                            cell = self.cells[y_n_pos][x_n_pos]
                            if aim_predicate(cell):
                                dist = max(abs(x_), abs(y_))
                                if dist < min_dist_aim_cell:
                                    min_dist_aim_cell = dist
                                    closest_aim_cell = cell
                                # return cell
                            if cell.visited_dead_counter > 0:
                                continue
                            pheromone_level = get_pheromone_level(cell)
                            if pheromone_level == max_pheromone_level:
                                candidate_cells.append(cell)
                            if pheromone_level > max_pheromone_level:
                                candidate_cells = []
                                max_pheromone_level = pheromone_level
                                best_cell = cell
        # print(f"s ret cells: {len(ret_cells)}")
        # print(best_cell)
        # print(f'pher max: {max_pheromone_level}')
        if closest_aim_cell is not None:
            return closest_aim_cell
        if len(candidate_cells) > 0:
            return random.choice(candidate_cells)
        return best_cell


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

    def draw(self, surface, x, y):
        color = (0, min(255, self.amount/5), 0)
        pygame.draw.rect(surface, color, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))


MODE_TO_NEST = 0
MODE_TO_FOOD = 1
MODE_LEAVING_NEST = 2


def ant_mode_to_str(ant):
    mode_str = f'unknown'
    if ant.mode == MODE_TO_NEST:
        mode_str = "MODE_TO_NEST"
    elif ant.mode == MODE_TO_FOOD:
        mode_str = "MODE_TO_FOOD"
    elif ant.mode == MODE_LEAVING_NEST:
        mode_str = "MODE_LEAVING_NEST"
    return mode_str


def print_ant_mode(ant):
    mode_str = ant_mode_to_str(ant)
    print(mode_str)


class Ant:
    def __init__(self, x, y, direction, size_x, size_y, food_sources=None, speed=1.0, grid=None):
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.world_size_x = size_x
        self.world_size_y = size_y
        self.direction = direction
        self.grid = grid
        self.has_food = False
        self.in_nest = False
        self.mode = MODE_LEAVING_NEST
        self.horizon_cells = []
        self.no_food_nest_visit = 1
        # print(self)

    def __str__(self):
        return f'ant x:{self.x} y: {self.y} dir: {self.direction} v {DIR_VECTORS[self.direction]} mode: {ant_mode_to_str(self)}'

    def get_int_pos(self):
        return math.floor(self.x), math.floor(self.y)

    def mirror_dir_x(self):
        if self.direction == NW:
            self.direction = NE
        elif self.direction == W:
            self.direction = E
        elif self.direction == SW:
            self.direction = SE
        elif self.direction == NE:
            self.direction = NW
        elif self.direction == E:
            self.direction = W
        elif self.direction == SE:
            self.direction = SW

    def mirror_dir_y(self):
        if self.direction == NW:
            self.direction = SW
        elif self.direction == N:
            self.direction = S
        elif self.direction == NE:
            self.direction = SE
        elif self.direction == SW:
            self.direction = NW
        elif self.direction == S:
            self.direction = N
        elif self.direction == SE:
            self.direction = NE

    def move_to_opposite_direction(self):
        vec_x, vec_y = DIR_VECTORS[self.direction]
        self.direction = VECTORS_TO_DIRS[(-vec_x, -vec_y)]
        self.x += -vec_x
        self.y += -vec_y

    def update_position(self):
        # print(f'update_position dir: {self.direction}')
        # print(f' update {self}')
        if self.mode == MODE_LEAVING_NEST:
            # print(f'1 in nest {self}')
            if self.grid.cells[self.y][self.x].type != CELL_TYPE_NEST:
                # print(f'2 in nest {self}')
                self.mode = MODE_TO_FOOD
                # print(f'2.1 in nest {self}')
                return
            # else:
                # print(f'2.3 in nest {self}')
        elif self.mode == MODE_TO_FOOD:
            # print(f'3 in nest {self}')
            if self.grid.cells[self.y][self.x].type == CELL_TYPE_FOOD:
                self.no_food_nest_visit = 1
                # print(f'4 in nest {self}')
                self.mode = MODE_TO_NEST
                self.grid.cells[self.y][self.x].food.decrease_amount()
                self.move_to_opposite_direction()
                # print(f'4.1 in nest {self}')
                return
            elif self.grid.cells[self.y][self.x].type == CELL_TYPE_NEST:
                # print(f'5 in nest {self}')
                self.move_to_opposite_direction()
                # print(f'5.1 in nest {self}')
                return
        elif self.mode == MODE_TO_NEST:
            # print(f'6 in nest {self}')
            if self.grid.cells[self.y][self.x].type == CELL_TYPE_NEST:
                # print(f'7 in nest {self}')
                self.no_food_nest_visit = 1
                self.mode = MODE_TO_FOOD
                self.move_to_opposite_direction()
                # print(f'7.1 in nest {self}')
                return
            elif self.grid.cells[self.y][self.x].type == CELL_TYPE_FOOD:
                # print(f'7 in nest {self}')
                self.move_to_opposite_direction()
                # print(f'7.1 in nest {self}')
                return

        # if random.randint(0, 100) > 30:

        if self.mode == MODE_TO_NEST:
            pheromone_amout = (NO_FOOD_NEST_VISIT_THRESH - self.no_food_nest_visit) / 10
            self.grid.inc_with_food_counter(self.x, self.y, pheromone_amout)
        elif self.mode == MODE_TO_FOOD:
            pheromone_amout = (NO_FOOD_NEST_VISIT_THRESH - self.no_food_nest_visit) / 20
            self.grid.inc_no_food_counter(self.x, self.y, pheromone_amout)
        #
        # if self.in_nest and self.has_food:
        #     self.in_nest = False
        #     self.has_food = False
        self.update_direction()

        dir_x, dir_y = DIR_VECTORS[self.direction]
        self.x += dir_x
        self.y += dir_y

        if self.x < 0:
            self.x = 0
            self.mirror_dir_x()
        if self.x == self.world_size_x:
            self.x = self.world_size_x - 1
            self.mirror_dir_x()

        if self.y < 0:
            self.y = 0
            self.mirror_dir_y()
        if self.y == self.world_size_y:
            self.y = self.world_size_y - 1
            self.mirror_dir_y()

        # self.update_direction()

    def randomize_direction(self):
        # choice = random.choice([-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  1],)
        # choice = random.choice([-1, 0, 0, 0, 0, 1])
        choice = random.choices(population=[-1, 0, 1], weights=[1, 10, 1], k=1)[0]
        # print(f' randomize choice: {choice}')
        # print(f' randomize old: {self.direction}')
        new_direction = self.direction + choice
        # print(f' new < 0 randomize dir: {self.direction}')
        if new_direction < 0:
            self.direction = len(DIRECTIONS) + new_direction
            # print(f' new < 0 randomize dir: {self.direction}')
            return
        if new_direction >= len(DIRECTIONS):
            self.direction = new_direction - len(DIRECTIONS)
            # print(f' new > 0: {self.direction}')
            return
        self.direction = new_direction

    def update_direction(self, neighbour_cells=[]):
        # print(f'1 update dir {self}')
        # self.randomize_direction()
        self.horizon_cells = []
        if DRAW_HORIZONS:
            self.horizon_cells = self.grid.get_horizon_cells(self.direction, self.x, self.y)
        # print_ant_mode(self)
        val = random.randint(0, RANDOMIZE_POS_RANGE)
        if val > RANDOMIZE_POS_THRESHOLD or self.mode == MODE_LEAVING_NEST:
            # print(f'2 update dir {self}')
            self.randomize_direction()
            # print(f'3 update dir {self}')
            return
        best_cell = self.grid.get_best_cell(self.direction, self.x, self.y, self.mode)
        # print(best_cell)
        # print(f'4 update dir {self}')
        if best_cell is not None:
            # print(f'5 update dir {self}')
            # print(f'found best cell at {best_cell.x} {best_cell.y}')
            diff_x = best_cell.x - self.x
            diff_y = best_cell.y - self.y
            dist = max(abs(diff_x), abs(diff_y))
            # print(f'diff  {diff_x} {diff_y} dist {dist}')
            direction = (int(diff_x/dist), int(diff_y/dist))
            # print(f'best dir: {direction}')
            self.direction = VECTORS_TO_DIRS[direction]
            # print(f'6 update dir {self}')
            return

    def draw(self, surface):
        color = YELLOW
        if self.mode == MODE_TO_NEST:
            color = DARKER_GREEN
        pygame.draw.rect(surface, color, (self.x*CELL_SIZE, self.y*CELL_SIZE, CELL_SIZE, CELL_SIZE))

        for cell in self.horizon_cells:
            pygame.draw.rect(surface, (120, 120, 120), (cell.x * CELL_SIZE, cell.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))


class AntsAlgorithm:
    def __init__(self, size_x=SIZE_X, size_y=SIZE_Y):
        self.world = World(size_x, size_y)
        pygame.init()
        pygame.display.set_caption("Ants Algorithm")
        self.screen = pygame.display.set_mode((RENDER_SIZE_X, RENDER_SIZE_Y))
        self.clock = pygame.time.Clock()
        self.grid = Grid(size_x=size_x, size_y=size_y)
        self.create_food_sources()
        self.nest = None
        self.create_nest()
        self.ants = []  # self.create_ants()

    def create_nest(self):
        # nest = Nest(random.randint(10, int((self.world.size_x - 1) / 3)),
        #             random.randint(10, int((self.world.size_y - 1) / 3)))
        nest = Nest(random.randint(int((self.world.size_x - 1) / 3), int((self.world.size_x - 1) / 2)),
                    random.randint(int((self.world.size_y - 1) / 3), int((self.world.size_y - 1) / 2)))
        self.grid.set_nest(nest)
        self.nest = nest

    def create_ants(self):
        ants = []
        for i in range(NUM_OF_ANTS):
            # ants.append(Ant(random.randint(0, self.world.size_x), random.randint(0, self.world.size_y),
            #                 random.randint(0, 1500), self.world.size_x, self.world.size_y))

            ants.append(Ant(self.nest.x, self.nest.y,
                            random.choice(DIRECTIONS), self.world.size_x, self.world.size_y, grid=self.grid))
            # ants.append(Ant(i, i, i, self.world.size_x, self.world.size_y, speed=random.randint(1, 2)))
        return ants

    def create_food_sources(self):
        for i in range(NUM_OF_FOOD_SOURCES):
            food = Food(random.randint(int(0.1*(self.world.size_x-1)), self.world.size_x-1),
                        random.randint(int(0.1*(self.world.size_y-1)), self.world.size_y-1),
                        random.randint(MIN_FOOD_AMOUNT, MAX_FOOD_AMOUNT))
            self.grid.set_food(food)

    def process_input(self):
        global DRAW_PHEROMONES
        global DRAW_HORIZONS
        global CLOCK_TICK
        global RENDER
        global RUNNING
        global DRAW_FOOD_PHEROMONES
        global DRAW_NEST_PHEROMONES
        global DRAW_DEAD_PHEROMONES

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                RUNNING = False
                # quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    DRAW_PHEROMONES = not DRAW_PHEROMONES
                if event.key == pygame.K_f:
                    DRAW_FOOD_PHEROMONES = not DRAW_FOOD_PHEROMONES
                if event.key == pygame.K_n:
                    DRAW_NEST_PHEROMONES = not DRAW_NEST_PHEROMONES
                if event.key == pygame.K_d:
                    DRAW_DEAD_PHEROMONES = not DRAW_DEAD_PHEROMONES
                if event.key == pygame.K_h:
                    DRAW_HORIZONS = not DRAW_HORIZONS
                if event.key == pygame.K_r:
                    RENDER = not RENDER
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # scroll up
                    CLOCK_TICK += CLOCK_STEP
                    print(CLOCK_TICK)
                elif event.button == 5:  # scroll down
                    CLOCK_TICK -= CLOCK_STEP
                    if CLOCK_TICK < 1:
                        CLOCK_TICK = 1
                    print(CLOCK_TICK)

    def update_positions(self):
        to_remove_ids = []
        for idx, ant in enumerate(self.ants):
            ant.no_food_nest_visit += 1
            if ant.no_food_nest_visit > NO_FOOD_NEST_VISIT_THRESH:
                pheromone_amout = ant.no_food_nest_visit/10
                if ant.mode == MODE_TO_NEST:
                    pheromone_amout /= 4
                self.grid.inc_dead_counter(ant.x, ant.y, pheromone_amout)
                for dir_x in range(-HORIZON_SIZE, HORIZON_SIZE+1):
                    for dir_y in range(-HORIZON_SIZE, HORIZON_SIZE+1):
                        if dir_x == 0 and dir_y == 0:
                            continue
                        x = dir_x + ant.x
                        y = dir_y + ant.y
                        if not is_valid_coord(x, y, self.grid.size_x, self.grid.size_y):
                            continue
                        self.grid.inc_dead_counter(x, y, pheromone_amout)

                to_remove_ids.append(idx)
            try:
                ant.update_position()
            except:
                print(traceback.format_exc())
        for idx in reversed(to_remove_ids):
            print(f'removing ant id {idx} {self.ants[idx]}')
            del self.ants[idx]


    def update_grid(self):
        self.grid.update()

    def update_ants(self):
        if len(self.ants) < NUM_OF_ANTS:
            if random.randint(0, 1000) < 600:
                return
            self.ants.append(Ant(self.nest.x, self.nest.y, random.choice(DIRECTIONS), self.world.size_x, self.world.size_y, grid=self.grid))
            # self.ants.append(
            #     Ant(self.nest.x, self.nest.y, E, self.world.size_x, self.world.size_y,
            #         grid=self.grid))

    def process_logic(self):
        self.update_ants()
        self.update_positions()
        self.update_grid()
        # self.log_food_sources()

    def render_scene(self):
        self.screen.fill((10, 10, 10))
        self.grid.draw(self.screen)
        # self.nest.draw(self.screen)
        # for food_source in self.food_sources:
        #     food_source.draw(self.screen)
        for ant in self.ants:
            ant.draw(self.screen)
        pygame.display.flip()

    def process_frame(self):
        self.clock.tick(CLOCK_TICK)
        self.process_input()
        self.process_logic()
        if RENDER:
            self.render_scene()

    def run(self):
        global RUNNING
        while RUNNING:
            self.process_frame()
