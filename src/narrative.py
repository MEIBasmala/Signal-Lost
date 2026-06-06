import pygame
from settings import *

class NarrativeText:
    COLORS = {
        'vesna_f1': (120, 120, 120),
        'vesna_f2': (100, 150, 255),
        'vesna_f3': (50, 255, 100),
        'env':      (255, 255, 255),
        'yuri_log': (255, 250, 220),
    }

    def __init__(self, text, source='env', x=None, y=None,
                 type_speed=None, hold_time=None, fade_time=None, width=500):
        self.full_text = text
        self.source = source
        self.color = self.COLORS.get(source, self.COLORS['env'])
        self.type_speed = type_speed if type_speed is not None else NARRATIVE_TYPE_SPEED
        # Auto-adjust hold time based on text length — longer texts need more time
        if hold_time is not None:
            self.hold_time = hold_time
        elif len(text) > 80:
            self.hold_time = NARRATIVE_LONG_HOLD  # 8s for long texts
        else:
            self.hold_time = NARRATIVE_HOLD_TIME  # 6s for short texts
        self.fade_time = fade_time if fade_time is not None else NARRATIVE_FADE_TIME
        self.revealed_chars = 0
        self.timer = 0
        self.state = 'typing'
        self.x = x if x is not None else SCREEN_WIDTH // 2
        self.y = y if y is not None else SCREEN_HEIGHT - 100
        self.font = pygame.font.SysFont("Courier New", 16)
        self.glitch_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        self.show_glitch = (source == 'vesna_f3')
        self.glitch_timer = 0
        self.dismissed = False  # player can press Enter to dismiss early

    def dismiss(self):
        '''Player pressed Enter to skip/dismiss this text.'''
        if self.state in ('typing', 'holding'):
            self.state = 'fading'
            self.timer = 0
            self.revealed_chars = len(self.full_text)

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
        text = self.full_text[:int(self.revealed_chars)]
        if self.show_glitch and self.state == 'typing':
            self.glitch_timer += 1
            if self.glitch_timer % 8 < 3:
                glitched = list(text)
                for i in range(len(glitched)):
                    if glitched[i].isalpha() and pygame.time.get_ticks() % (i + 7) == 0:
                        glitched[i] = self.glitch_chars[pygame.time.get_ticks() % len(self.glitch_chars)]
                return ''.join(glitched)
        return text

    def get_alpha(self):
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
        # Word-wrap into lines that fit the screen
        max_width = SCREEN_WIDTH - 80
        words = text.split(' ')
        lines = []
        current = ''
        for word in words:
            test = (current + ' ' + word).strip()
            if self.font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        line_h = self.font.get_linesize() + 2
        total_h = line_h * len(lines)
        base_y = self.y - total_h

        for i, line in enumerate(lines):
            surf = self.font.render(line, True, self.color)
            surf.set_alpha(alpha)
            rect = surf.get_rect(centerx=self.x, top=base_y + i * line_h)
            screen.blit(surf, rect)


class TriggerZone:
    def __init__(self, x, y, width, height, text, source='env', frequency=None, once=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.source = source
        self.frequency = frequency
        self.once = once
        self.triggered = False

    def check(self, player_rect, current_freq, narrative_manager):
        if self.triggered and self.once:
            return
        if self.frequency is not None and current_freq != self.frequency:
            return
        if self.rect.colliderect(player_rect):
            narrative_manager.add_text(self.text, self.source)
            self.triggered = True


class NarrativeManager:
    def __init__(self):
        self.texts = []
        self.triggers = []

    def add_text(self, text, source='env', x=None, y=None):
        self.texts.append(NarrativeText(text, source, x, y))

    def add_trigger(self, trigger):
        self.triggers.append(trigger)

    def update(self, player_rect, current_freq):
        for trigger in self.triggers:
            trigger.check(player_rect, current_freq, self)
        for text in self.texts:
            text.update()
        self.texts = [t for t in self.texts if not t.is_dead()]

    def draw(self, screen):
        for text in self.texts:
            text.draw(screen)

# ---- patch: stack draw ----
_orig_draw = NarrativeManager.draw

def _stacked_draw(self, screen):
    slot_y = SCREEN_HEIGHT - 60
    for text in reversed(self.texts):
        text.y = slot_y
        text.draw(screen)
        font_h = text.font.get_linesize() + 2
        current_display = text.get_display_text()
        if current_display:
            max_width = SCREEN_WIDTH - 80
            words = current_display.split(' ')
            lines, curr = [], ''
            for word in words:
                test = (curr + ' ' + word).strip()
                if text.font.size(test)[0] <= max_width:
                    curr = test
                else:
                    if curr:
                        lines.append(curr)
                    curr = word
            if curr:
                lines.append(curr)
            slot_y -= font_h * len(lines) + 10

NarrativeManager.draw = _stacked_draw