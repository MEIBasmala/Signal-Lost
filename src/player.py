import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        self.image = pygame.Surface(PLAYER_SIZE)
        self.image.fill((200, 200, 200))
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Float position
        self.pos_x = float(x)
        self.pos_y = float(y)
        
        self.vel_x = 0
        self.vel_y = 0
        self.diagonal_factor = 0.7071

        # Health
        self.hearts = PLAYER_MAX_HEARTS
        self.invincible = False
        self.invincibility_timer = 0

    def update(self, keys, walls):
        self.vel_x = 0
        self.vel_y = 0
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.vel_y = -PLAYER_SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.vel_y = PLAYER_SPEED

        if self.vel_x != 0 and self.vel_y != 0:
            self.vel_x *= self.diagonal_factor
            self.vel_y *= self.diagonal_factor

        # Move X axis only
        self.pos_x += self.vel_x
        self.rect.x = int(self.pos_x)
        
        for wall in walls:
            if self.rect.colliderect(wall):
                if self.vel_x > 0:   # moving right, hit left side of wall
                    self.rect.right = wall.left
                elif self.vel_x < 0: # moving left, hit right side of wall
                    self.rect.left = wall.right
                self.pos_x = float(self.rect.x)
        
        # Move Y axis only
        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)
        
        for wall in walls:
            if self.rect.colliderect(wall):
                if self.vel_y > 0:   # moving down, hit top of wall
                    self.rect.bottom = wall.top
                elif self.vel_y < 0: # moving up, hit bottom of wall
                    self.rect.top = wall.bottom
                self.pos_y = float(self.rect.y)


        # Tick invincibility window
        if self.invincible:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

    def take_damage(self):
        if self.invincible:
            return False  # hit ignored
        
        self.hearts -= 1
        self.invincible = True
        self.invincibility_timer = INVINCIBILITY_DURATION
        return True  # hit landed