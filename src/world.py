import pygame
from settings import *

# Tile types
FLOOR    = 0
WALL     = 1
WALL_F2  = 2   # only solid on frequency 2 (ghost wall from 1979)
WALL_F3  = 3   # only solid on frequency 3 (VESNA data wall)
PASSAGE  = 4   # looks like wall on F1 but open on F2 — hidden passage

# =====================================================================
# B3 BARRACKS — 25 wide x 20 tall
# =====================================================================
ROOM_B3 = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

B3_PROPS = [
    {'type': 'bunk',      'col': 1, 'row': 1, 'label': 'karim'},
    {'type': 'prayer_rug','col': 2, 'row': 2},
    {'type': 'book',      'col': 3, 'row': 2, 'label': 'quran_radio'},
    {'type': 'bunk',      'col': 20, 'row': 1, 'label': 'yuri'},
    {'type': 'item',      'col': 21, 'row': 2, 'label': 'yuri_log'},
    {'type': 'bunk',      'col': 6, 'row': 4},
    {'type': 'bunk',      'col': 9, 'row': 4},
    {'type': 'bunk',      'col': 15, 'row': 4},
    {'type': 'bunk',      'col': 18, 'row': 4},
    {'type': 'bunk',      'col': 6, 'row': 14},
    {'type': 'bunk',      'col': 9, 'row': 14},
    {'type': 'bunk',      'col': 15, 'row': 14},
    {'type': 'bunk',      'col': 18, 'row': 14},
    {'type': 'poster',    'col': 8,  'row': 3},
    {'type': 'poster',    'col': 16, 'row': 3},
]

B3_DOOR_TILE = (12, 0)      # Exit to B2 (north wall gap)
B3_KEYPAD_POS = (12 * TILE_SIZE + TILE_SIZE // 2, 3 * TILE_SIZE + TILE_SIZE // 2)
B3_EXIT_ZONE = pygame.Rect(11 * TILE_SIZE, -1 * TILE_SIZE, 3 * TILE_SIZE, TILE_SIZE)  # above row 0

# =====================================================================
# B2 CONTROL ROOM — 25 wide x 20 tall
# VESNA's main terminal center. Server racks. Blast door north to B1.
# =====================================================================
ROOM_B2 = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

B2_PROPS = [
    # VESNA Terminal — center of the room (col 12, row 9)
    {'type': 'terminal', 'col': 12, 'row': 9},
    # Server racks — along the back wall (rows 7-13, cols 6-16)
    {'type': 'server_rack', 'col': 6, 'row': 7},
    {'type': 'server_rack', 'col': 7, 'row': 7},
    {'type': 'server_rack', 'col': 8, 'row': 7},
    {'type': 'server_rack', 'col': 9, 'row': 7},
    {'type': 'server_rack', 'col': 10, 'row': 7},
    {'type': 'server_rack', 'col': 11, 'row': 7},
    {'type': 'server_rack', 'col': 13, 'row': 7},
    {'type': 'server_rack', 'col': 14, 'row': 7},
    {'type': 'server_rack', 'col': 15, 'row': 7},
    {'type': 'server_rack', 'col': 16, 'row': 7},
    {'type': 'server_rack', 'col': 6, 'row': 13},
    {'type': 'server_rack', 'col': 7, 'row': 13},
    {'type': 'server_rack', 'col': 8, 'row': 13},
    {'type': 'server_rack', 'col': 9, 'row': 13},
    {'type': 'server_rack', 'col': 10, 'row': 13},
    {'type': 'server_rack', 'col': 11, 'row': 13},
    {'type': 'server_rack', 'col': 13, 'row': 13},
    {'type': 'server_rack', 'col': 14, 'row': 13},
    {'type': 'server_rack', 'col': 15, 'row': 13},
    {'type': 'server_rack', 'col': 16, 'row': 13},
    # Side server racks
    {'type': 'server_rack', 'col': 6, 'row': 8},
    {'type': 'server_rack', 'col': 6, 'row': 9},
    {'type': 'server_rack', 'col': 6, 'row': 10},
    {'type': 'server_rack', 'col': 6, 'row': 11},
    {'type': 'server_rack', 'col': 6, 'row': 12},
    {'type': 'server_rack', 'col': 16, 'row': 8},
    {'type': 'server_rack', 'col': 16, 'row': 9},
    {'type': 'server_rack', 'col': 16, 'row': 10},
    {'type': 'server_rack', 'col': 16, 'row': 11},
    {'type': 'server_rack', 'col': 16, 'row': 12},
    # Emergency lights
    {'type': 'light', 'col': 3, 'row': 1},
    {'type': 'light', 'col': 21, 'row': 1},
    {'type': 'light', 'col': 3, 'row': 18},
    {'type': 'light', 'col': 21, 'row': 18},
]

B2_DOOR_TILE = (12, 0)      # Exit to B1 (north wall gap)
B2_SPAWN_FROM_B3 = (12 * TILE_SIZE, 18 * TILE_SIZE)  # Enter from south
B2_EXIT_ZONE = pygame.Rect(11 * TILE_SIZE, -1 * TILE_SIZE, 3 * TILE_SIZE, TILE_SIZE)


class World:
    def __init__(self, room_data, props=None):
        self.tile_list = []
        self.wall_rects = []
        self.freq2_wall_rects = []
        self.freq3_wall_rects = []
        self.props = props or []
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
                    pygame.draw.rect(screen, (40, 60, 120), rect)
                    pygame.draw.rect(screen, (80, 120, 200), rect, 1)
                else:
                    pygame.draw.rect(screen, (20, 35, 25), rect)
                    pygame.draw.rect(screen, (30, 50, 80), rect, 1)
            elif tile_type == 'wall_f3':
                if current_freq == 3:
                    pygame.draw.rect(screen, (20, 80, 40), rect)
                    pygame.draw.rect(screen, (40, 200, 80), rect, 1)
                else:
                    pygame.draw.rect(screen, (20, 35, 25), rect)
                    pygame.draw.rect(screen, (22, 38, 27), rect, 1)
            elif tile_type == 'passage':
                if current_freq == 2:
                    pygame.draw.rect(screen, (20, 35, 25), rect)
                else:
                    pygame.draw.rect(screen, (60, 60, 70), rect)
                    pygame.draw.rect(screen, (80, 80, 90), rect, 1)

        self.draw_props(screen, current_freq)

    def draw_props(self, screen, current_freq):
        for prop in self.props:
            x = prop['col'] * TILE_SIZE
            y = prop['row'] * TILE_SIZE
            ptype = prop['type']

            if ptype == 'bunk':
                pygame.draw.rect(screen, (45, 40, 35), (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4))
                pygame.draw.rect(screen, (70, 65, 55), (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4), 1)
                pygame.draw.rect(screen, (55, 50, 45), (x + 4, y + 6, TILE_SIZE - 8, TILE_SIZE - 14))

            elif ptype == 'prayer_rug':
                pygame.draw.rect(screen, (80, 20, 20), (x + 4, y + 8, TILE_SIZE - 8, TILE_SIZE - 16))
                pygame.draw.rect(screen, (100, 30, 30), (x + 6, y + 10, TILE_SIZE - 12, 2))
                pygame.draw.rect(screen, (100, 30, 30), (x + 6, y + TILE_SIZE - 14, TILE_SIZE - 12, 2))

            elif ptype == 'book':
                pygame.draw.rect(screen, (180, 160, 80), (x + 4, y + 10, 10, 14))
                pygame.draw.rect(screen, (60, 80, 100), (x + 16, y + 10, 10, 14))

            elif ptype == 'item':
                label = prop.get('label', '')
                color = (255, 250, 180) if 'log' in label else (100, 200, 255)
                cx, cy = x + TILE_SIZE // 2, y + TILE_SIZE // 2
                pygame.draw.circle(screen, color, (cx, cy), 5)
                pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 3)

            elif ptype == 'poster':
                pygame.draw.rect(screen, (90, 20, 20), (x + 6, y + 4, TILE_SIZE - 12, TILE_SIZE - 8))
                pygame.draw.rect(screen, (130, 30, 30), (x + 6, y + 4, TILE_SIZE - 12, TILE_SIZE - 8), 1)

            elif ptype == 'server_rack':
                pygame.draw.rect(screen, (25, 28, 35), (x + 2, y + 1, TILE_SIZE - 4, TILE_SIZE - 2))
                pygame.draw.rect(screen, (50, 55, 70), (x + 2, y + 1, TILE_SIZE - 4, TILE_SIZE - 2), 1)
                tick = pygame.time.get_ticks()
                for led_i in range(4):
                    led_on = (tick // (200 + led_i * 80)) % 2 == 0
                    led_col = (50, 255, 80) if led_on else (20, 60, 30)
                    pygame.draw.rect(screen, led_col, (x + 4 + led_i * 6, y + 4, 4, 3))

            elif ptype == 'terminal':
                pygame.draw.rect(screen, (15, 20, 15), (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4))
                pygame.draw.rect(screen, (30, 100, 50), (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4), 2)
                import math
                pulse = int(abs(math.sin(pygame.time.get_ticks() / 1000)) * 40)
                screen_color = (20, 80 + pulse, 35)
                pygame.draw.rect(screen, screen_color, (x + 5, y + 5, TILE_SIZE - 10, TILE_SIZE - 10))
                pygame.draw.line(screen, (15, 60, 25), (x + 5, y + 12), (x + TILE_SIZE - 5, y + 12))
                pygame.draw.line(screen, (15, 60, 25), (x + 5, y + 17), (x + TILE_SIZE - 5, y + 17))
                font = pygame.font.SysFont("Courier New", 7)
                lbl = font.render("VESNA", True, (80, 200, 100))
                screen.blit(lbl, (x + 5, y + TILE_SIZE - 12))

            elif ptype == 'light':
                tick = pygame.time.get_ticks()
                flicker = (tick // 500) % 7 != 0
                color = (180, 120, 40) if flicker else (60, 40, 15)
                pygame.draw.rect(screen, color, (x + 8, y + 12, TILE_SIZE - 16, 8))