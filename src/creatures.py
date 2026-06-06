import pygame
import math
from settings import *

class Creature(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_start, patrol_end, frequency=1):
        super().__init__()
        
        self.image = pygame.Surface((24, 32))
        self.image.fill((180, 40, 40))  # red — obviously dangerous
        
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos_x = float(x)
        self.pos_y = float(y)
        
        # Patrol points
        self.patrol_start = patrol_start
        self.patrol_end = patrol_end
        self.patrol_direction = 1
        
        # Frequency it exists on
        self.frequency = frequency
        
        # State
        self.state = 'patrol'
        
        # Forced chase (keypad noise attraction)
        self.forced_target = None
        self.forced_timer = 0

    def patrol(self):
        target_x = self.patrol_end[0] if self.patrol_direction == 1 else self.patrol_start[0]
        target_y = self.patrol_end[1] if self.patrol_direction == 1 else self.patrol_start[1]
        
        dx = target_x - self.pos_x
        dy = target_y - self.pos_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 4:
            self.patrol_direction *= -1
            return
        
        self.pos_x += (dx / distance) * CREATURE_SPEED_PATROL
        self.pos_y += (dy / distance) * CREATURE_SPEED_PATROL

    def chase(self, target_x, target_y):
        dx = target_x - self.pos_x
        dy = target_y - self.pos_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            return
            
        self.pos_x += (dx / distance) * CREATURE_SPEED_CHASE
        self.pos_y += (dy / distance) * CREATURE_SPEED_CHASE

    def force_chase_toward(self, x, y, duration):
        """Temporarily chase a specific point (sound attraction from wrong keypad)"""
        self.forced_target = (x, y)
        self.forced_timer = duration
        self.state = 'chase'

    def update(self, current_freq, player_rect):
        # Not on our frequency — freeze
        if current_freq != self.frequency:
            return
        
        # Handle forced chase first (keypad noise)
        if self.forced_timer > 0:
            self.forced_timer -= 1
            self.chase(self.forced_target[0], self.forced_target[1])
            self.rect.x = int(self.pos_x)
            self.rect.y = int(self.pos_y)
            return  # skip normal AI during forced chase
        
        # Normal AI: distance to player
        dx = player_rect.centerx - self.pos_x
        dy = player_rect.centery - self.pos_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < CREATURE_DETECT_RANGE:
            self.state = 'chase'
        else:
            self.state = 'patrol'
        
        if self.state == 'patrol':
            self.patrol()
        elif self.state == 'chase':
            self.chase(player_rect.centerx, player_rect.centery)
        
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

    def draw(self, screen, current_freq):
        if current_freq != self.frequency:
            return
        screen.blit(self.image, self.rect)