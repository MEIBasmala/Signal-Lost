import pygame
from settings import *

class NarrativeText:
    """Floating text that appears, types out, then fades."""
    
    # Color coding per design doc
    COLORS = {
        'vesna_f1': (120, 120, 120),      # dim grey
        'vesna_f2': (100, 150, 255),      # soft blue
        'vesna_f3': (50, 255, 100),       # glitch green
        'env': (255, 255, 255),            # white
        'yuri_log': (255, 250, 220),      # yellowed white
    }
    
    def __init__(self, text, source='env', x=None, y=None, 
                 type_speed=2,      # chars per frame
                 hold_time=180,     # frames to stay after typing (3s)
                 fade_time=60,      # frames to fade out (1s)
                 width=500):        # max text width before wrap
        self.full_text = text
        self.source = source
        self.color = self.COLORS.get(source, self.COLORS['env'])
        self.type_speed = type_speed
        self.hold_time = hold_time
        self.fade_time = fade_time
        
        self.revealed_chars = 0
        self.timer = 0           # frames since created
        self.state = 'typing'    # typing → holding → fading → dead
        
        # Position: screen center if not specified
        self.x = x if x is not None else SCREEN_WIDTH // 2
        self.y = y if y is not None else SCREEN_HEIGHT - 100
        
        # Font
        self.font = pygame.font.SysFont("Courier New", 16)
        
        # Glitch effect for VESNA F3
        self.glitch_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        self.show_glitch = (source == 'vesna_f3')
        self.glitch_timer = 0
    
    def update(self):
        self.timer += 1
        
        if self.state == 'typing':
            self.revealed_chars += self.type_speed
            if self.revealed_chars >= len(self.full_text):
                self.revealed_chars = len(self.full_text)
                self.state = 'holding'
                self.timer = 0
        
        elif self.state == 'holding':
            if self.timer >= self.hold_time:
                self.state = 'fading'
                self.timer = 0
        
        elif self.state == 'fading':
            if self.timer >= self.fade_time:
                self.state = 'dead'
    
    def get_display_text(self):
        """Return text with glitch effect for F3."""
        text = self.full_text[:self.revealed_chars]
        
        if self.show_glitch and self.state == 'typing':
            # Occasionally replace chars with wrong ones, then correct
            self.glitch_timer += 1
            if self.glitch_timer % 8 < 3:  # glitch for 3 of every 8 frames
                glitched = list(text)
                for i in range(len(glitched)):
                    if glitched[i].isalpha() and pygame.time.get_ticks() % (i + 7) == 0:
                        glitched[i] = self.glitch_chars[pygame.time.get_ticks() % len(self.glitch_chars)]
                return ''.join(glitched)
        
        return text
    
    def get_alpha(self):
        """Calculate current opacity."""
        if self.state == 'fading':
            return max(0, 255 - int((self.timer / self.fade_time) * 255))
        return 255
    
    def is_dead(self):
        return self.state == 'dead'
    
    def draw(self, screen):
        alpha = self.get_alpha()
        if alpha <= 0:
            return
        
        text = self.get_display_text()
        if not text:
            return
        
        # Render with alpha
        surf = self.font.render(text, True, self.color)
        surf.set_alpha(alpha)
        
        # Center horizontally
        rect = surf.get_rect(centerx=self.x, bottom=self.y)
        screen.blit(surf, rect)


class TriggerZone:
    """Invisible area that spawns narrative text once when entered."""
    
    def __init__(self, x, y, width, height, text, source='env', 
                 frequency=None,  # None = all frequencies, or 1/2/3
                 once=True):      # True = trigger only once
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.source = source
        self.frequency = frequency
        self.once = once
        self.triggered = False
    
    def check(self, player_rect, current_freq, narrative_manager):
        if self.triggered and self.once:
            return
        
        # Check frequency requirement
        if self.frequency is not None and current_freq != self.frequency:
            return
        
        # Check overlap
        if self.rect.colliderect(player_rect):
            narrative_manager.add_text(self.text, self.source)
            self.triggered = True


class NarrativeManager:
    """Handles all active narrative texts."""
    
    def __init__(self):
        self.texts = []
        self.triggers = []
    
    def add_text(self, text, source='env', x=None, y=None):
        self.texts.append(NarrativeText(text, source, x, y))
    
    def add_trigger(self, trigger):
        self.triggers.append(trigger)
    
    def update(self, player_rect, current_freq):
        # Check triggers
        for trigger in self.triggers:
            trigger.check(player_rect, current_freq, self)
        
        # Update texts
        for text in self.texts:
            text.update()
        
        # Remove dead texts
        self.texts = [t for t in self.texts if not t.is_dead()]
    
    def draw(self, screen):
        for text in self.texts:
            text.draw(screen)