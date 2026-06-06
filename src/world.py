import pygame
from settings import *


# 0 = floor
# 1 = wall
# 2 = door (we'll use this later)
# Tile types
FLOOR    = 0
WALL     = 1
WALL_F2  = 2   # only solid on frequency 2 (ghost wall from 1979)
WALL_F3  = 3   # only solid on frequency 3 (VESNA data wall)
PASSAGE  = 4   # looks like wall on F1 but open on F2 — hidden passage


ROOM_1 = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,1],
    [1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1],
    [1,4,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,3,3,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,0,0,1,1,1,1,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]


class World:
    def __init__(self, room_data):
        self.tile_list = []
        self.wall_rects = []  # only walls, for collision
        
        self.load_room(room_data)
    
    def load_room(self, room_data):
        self.tile_list = []
        self.wall_rects = []
        self.freq2_wall_rects = []
        self.freq3_wall_rects = []

        for row_index, row in enumerate(room_data):
            for col_index, tile in enumerate(row):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

                if tile == WALL:
                    self.tile_list.append(('wall', rect))
                    self.wall_rects.append(rect)

                elif tile == FLOOR:
                    self.tile_list.append(('floor', rect))

                elif tile == WALL_F2:
                    self.tile_list.append(('wall_f2', rect))
                    self.freq2_wall_rects.append(rect)

                elif tile == WALL_F3:
                    self.tile_list.append(('wall_f3', rect))
                    self.freq3_wall_rects.append(rect)

                elif tile == PASSAGE:
                    self.tile_list.append(('passage', rect))

    def draw(self, screen, current_freq):
        for tile_type, rect in self.tile_list:

            if tile_type == 'wall':
                pygame.draw.rect(screen, (60, 60, 70), rect)
                pygame.draw.rect(screen, (80, 80, 90), rect, 1)

            elif tile_type == 'floor':
                pygame.draw.rect(screen, (20, 35, 25), rect)

            elif tile_type == 'wall_f2':
                if current_freq == 2:
                    # Solid ghost wall — blue-white, slightly transparent feel
                    pygame.draw.rect(screen, (40, 60, 120), rect)
                    pygame.draw.rect(screen, (80, 120, 200), rect, 1)
                else:
                    # Faint ghost outline — visible but clearly not solid
                    pygame.draw.rect(screen, (20, 35, 25), rect)
                    pygame.draw.rect(screen, (30, 50, 80), rect, 1)

            elif tile_type == 'wall_f3':
                if current_freq == 3:
                    # VESNA data wall — harsh green-white glitch look
                    pygame.draw.rect(screen, (20, 80, 40), rect)
                    pygame.draw.rect(screen, (40, 200, 80), rect, 1)
                else:
                    # Nearly invisible on other frequencies
                    pygame.draw.rect(screen, (20, 35, 25), rect)
                    pygame.draw.rect(screen, (22, 38, 27), rect, 1)

            elif tile_type == 'passage':
                if current_freq == 2:
                    # Open passage — draw as floor on Freq 2
                    pygame.draw.rect(screen, (20, 35, 25), rect)
                else:
                    # Looks like a wall on Freq 1 and 3
                    pygame.draw.rect(screen, (60, 60, 70), rect)
                    pygame.draw.rect(screen, (80, 80, 90), rect, 1)