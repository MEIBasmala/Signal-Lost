import pygame
from settings import *

class Keypad:
    def __init__(self, x, y, code, door_rect):
        self.x = x
        self.y = y
        self.code = str(code)  # "3427"
        self.door_rect = door_rect  # pygame.Rect of the door it controls
        self.unlocked = False
        
        self.active = False      # player is interacting
        self.input_buffer = ""
        self.lockout_timer = 0   # ms
        self.shake_timer = 0     # frames
        
        # Visual
        self.box_w = 180
        self.box_h = 100
        self.box = pygame.Rect(0, 0, self.box_w, self.box_h)
        
    def get_rect(self):
        return pygame.Rect(self.x - 16, self.y - 16, 32, 32)
    
    def can_interact(self, player_rect):
        if self.unlocked:
            return False
        dist = ((self.x - player_rect.centerx)**2 + 
                (self.y - player_rect.centery)**2) ** 0.5
        return dist < KEYPAD_RANGE
    
    def activate(self):
        self.active = True
        self.input_buffer = ""
    
    def deactivate(self):
        self.active = False
        self.input_buffer = ""
    
    def handle_input(self, event):
        if not self.active or self.lockout_timer > 0:
            return None  # "locked", "idle", "wrong", or "correct"
        
        if event.key == pygame.K_BACKSPACE:
            self.input_buffer = self.input_buffer[:-1]
            
        elif event.key == pygame.K_RETURN:
            if len(self.input_buffer) == KEYPAD_DIGITS:
                if self.input_buffer == self.code:
                    self.unlocked = True
                    self.active = False
                    return "correct"
                else:
                    self.lockout_timer = KEYPAD_LOCKOUT_TIME
                    self.shake_timer = KEYPAD_SHAKE_DURATION
                    self.input_buffer = ""
                    return "wrong"
                    
        elif event.key in range(pygame.K_0, pygame.K_9 + 1):
            if len(self.input_buffer) < KEYPAD_DIGITS:
                self.input_buffer += str(event.key - pygame.K_0)
        
        return "input"
    
    def update(self, dt):
        if self.lockout_timer > 0:
            self.lockout_timer = max(0, self.lockout_timer - dt)
        if self.shake_timer > 0:
            self.shake_timer -= 1
    
    def draw_world(self, screen, current_freq):
        # Draw keypad on wall
        if self.unlocked:
            color = (40, 80, 40)  # dark green, inactive
        else:
            color = (80, 80, 90)  # metallic grey
            if current_freq == 3:
                color = (100, 255, 100)  # glitch green on F3
        
        # Small box on wall
        rect = self.get_rect()
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (150, 150, 160), rect, 2)
        
        # Tiny LED
        led_color = (50, 255, 50) if not self.unlocked else (255, 50, 50)
        pygame.draw.circle(screen, led_color, (rect.centerx, rect.top - 4), 3)
    
    def draw_overlay(self, screen):
        if not self.active:
            return
        
        # Centered box
        self.box.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # Shake offset
        offset_x, offset_y = 0, 0
        if self.shake_timer > 0:
            offset_x = pygame.time.get_ticks() % 2 * KEYPAD_SHAKE_INTENSITY - KEYPAD_SHAKE_INTENSITY//2
            offset_y = pygame.time.get_ticks() % 3 * KEYPAD_SHAKE_INTENSITY - KEYPAD_SHAKE_INTENSITY//2
        
        # Background
        surf = pygame.Surface((self.box_w, self.box_h), pygame.SRCALPHA)
        surf.fill((10, 10, 15, 230))
        screen.blit(surf, (self.box.x + offset_x, self.box.y + offset_y))
        pygame.draw.rect(screen, (80, 80, 90), 
                        (self.box.x + offset_x, self.box.y + offset_y, self.box_w, self.box_h), 2)
        
        # Title
        font = pygame.font.SysFont("Courier New", 16)
        title = font.render("ENTER CODE", True, (150, 150, 160))
        screen.blit(title, (self.box.centerx - title.get_width()//2 + offset_x, 
                          self.box.y + 10 + offset_y))
        
        # Digits display
        display = ""
        for i in range(KEYPAD_DIGITS):
            if i < len(self.input_buffer):
                display += self.input_buffer[i] + " "
            else:
                display += "_ "
        display = display.strip()
        
        digit_font = pygame.font.SysFont("Courier New", 28, bold=True)
        
        # Lockout = red, normal = white, full = yellow
        if self.lockout_timer > 0:
            text_color = (255, 50, 50)
        elif len(self.input_buffer) == KEYPAD_DIGITS:
            text_color = (255, 255, 100)
        else:
            text_color = WHITE
        
        digits = digit_font.render(display, True, text_color)
        screen.blit(digits, (self.box.centerx - digits.get_width()//2 + offset_x,
                            self.box.y + 40 + offset_y))
        
        # Lockout message
        if self.lockout_timer > 0:
            lock_text = font.render("LOCKED", True, (255, 50, 50))
            screen.blit(lock_text, (self.box.centerx - lock_text.get_width()//2 + offset_x,
                                   self.box.y + 75 + offset_y))