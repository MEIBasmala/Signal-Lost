import pygame
import math
from settings import *


class GhostFrame:
    """A single pose/state in a ghost sequence."""
    def __init__(self, x, y, action, duration, text=None, text_source='vesna_f2'):
        self.x = float(x)
        self.y = float(y)
        self.action = action        # 'idle', 'walk_to', 'write', 'look', 'dragged'
        self.duration = duration    # frames
        self.text = text            # optional narrative line triggered mid-frame
        self.text_source = text_source


class GhostSequence:
    """
    A scripted sequence of ghost frames, only visible on a specific frequency.
    Plays once when the player enters range; can be watched again.
    """
    def __init__(self, frames, frequency=2, trigger_rect=None, once=True):
        self.frames = frames
        self.frequency = frequency
        self.trigger_rect = trigger_rect    # pygame.Rect — area that starts playback
        self.once = once

        self.active = False
        self.triggered = False
        self.current_frame_idx = 0
        self.frame_timer = 0

        # Ghost sprite pos (interpolated during walk_to)
        self.ghost_x = float(frames[0].x) if frames else 0.0
        self.ghost_y = float(frames[0].y) if frames else 0.0

        # Track which texts have been fired this playback
        self._text_fired = False

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def check_trigger(self, player_rect, current_freq):
        """Returns True (and starts sequence) if conditions are met."""
        if self.triggered and self.once:
            return False
        if current_freq != self.frequency:
            return False
        if self.trigger_rect and not self.trigger_rect.colliderect(player_rect):
            return False
        if not self.active:
            self._start()
        return True

    def update(self, narrative_manager):
        """Call every frame when active."""
        if not self.active:
            return

        frame = self.frames[self.current_frame_idx]

        # Fire attached text once per frame
        if not self._text_fired and frame.text:
            narrative_manager.add_text(frame.text, frame.text_source)
            self._text_fired = True

        # Animate ghost position for walk_to frames
        if frame.action == 'walk_to':
            dx = frame.x - self.ghost_x
            dy = frame.y - self.ghost_y
            dist = math.sqrt(dx**2 + dy**2)
            speed = 1.8
            if dist > speed:
                self.ghost_x += (dx / dist) * speed
                self.ghost_y += (dy / dist) * speed
            else:
                self.ghost_x = frame.x
                self.ghost_y = frame.y

        elif frame.action == 'dragged':
            # Rapid jerk movement — pulled eastward
            self.ghost_x += 4.0
            self.ghost_y -= 1.0

        self.frame_timer += 1
        if self.frame_timer >= frame.duration:
            self._next_frame()

    def draw(self, screen, current_freq):
        if not self.active or current_freq != self.frequency:
            return

        frame = self.frames[self.current_frame_idx]
        alpha = self._get_alpha(frame)
        if alpha <= 0:
            return

        self._draw_ghost_figure(screen, self.ghost_x, self.ghost_y, frame.action, alpha)

        # Draw clipboard during 'write' action
        if frame.action == 'write':
            self._draw_clipboard(screen, self.ghost_x, self.ghost_y, alpha)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _start(self):
        self.active = True
        self.triggered = True
        self.current_frame_idx = 0
        self.frame_timer = 0
        self._text_fired = False
        if self.frames:
            self.ghost_x = float(self.frames[0].x)
            self.ghost_y = float(self.frames[0].y)

    def _next_frame(self):
        self.frame_timer = 0
        self._text_fired = False
        self.current_frame_idx += 1
        if self.current_frame_idx >= len(self.frames):
            self.active = False     # sequence complete

    def _get_alpha(self, frame):
        """Fade in at start of frame, fade out during 'dragged'."""
        if frame.action == 'dragged':
            # Fade out as dragged
            progress = self.frame_timer / max(1, frame.duration)
            return int(255 * (1.0 - progress))
        # Standard: fade in over first 10 frames of sequence
        if self.current_frame_idx == 0:
            return min(255, int(self.frame_timer * 12))
        return 200   # slightly transparent ghost throughout

    def _draw_ghost_figure(self, screen, x, y, action, alpha):
        """Simple silhouette — 24x32 soldier shape in translucent blue-white."""
        ghost_surf = pygame.Surface((24, 32), pygame.SRCALPHA)
        body_color = (140, 180, 255, alpha)
        outline_color = (180, 220, 255, min(255, alpha + 40))

        # Body
        pygame.draw.rect(ghost_surf, body_color, (4, 12, 16, 18))
        # Head
        pygame.draw.circle(ghost_surf, body_color, (12, 8), 7)
        # Outline
        pygame.draw.rect(ghost_surf, outline_color, (4, 12, 16, 18), 1)
        pygame.draw.circle(ghost_surf, outline_color, (12, 8), 7, 1)

        if action == 'dragged':
            # Motion blur suggestion — draw stretched horizontally
            for i in range(1, 4):
                blur = ghost_surf.copy()
                blur.set_alpha(alpha // (i * 2))
                screen.blit(blur, (int(x) - i * 6, int(y)))

        screen.blit(ghost_surf, (int(x), int(y)))

    def _draw_clipboard(self, screen, x, y, alpha):
        """Clipboard with partial code visible — key visual showing 3__7."""
        clip_surf = pygame.Surface((28, 22), pygame.SRCALPHA)
        clip_color = (200, 190, 140, alpha)
        pygame.draw.rect(clip_surf, clip_color, (0, 0, 28, 22))
        pygame.draw.rect(clip_surf, (150, 140, 100, alpha), (0, 0, 28, 22), 1)

        font = pygame.font.SysFont("Courier New", 10, bold=True)
        # Yuri wrote the first and last digits — middle two smeared/blocked
        code_surf = font.render("3  7", True, (20, 15, 10))
        code_surf.set_alpha(alpha)
        clip_surf.blit(code_surf, (4, 7))

        screen.blit(clip_surf, (int(x) + 18, int(y) + 8))


# ------------------------------------------------------------------ #
#  Factory — build Yuri's sequence for B3                             #
# ------------------------------------------------------------------ #

def make_yuri_sequence():
    """
    Yuri's ghost plays out in B3 on Freq 2:
    1. Enters from west, walks to east bunk area
    2. Crouches — picks up his log, reads it (write pose)
    3. Looks back toward barracks center (look)
    4. Walks north toward keypad area with clipboard (walk_to)
    5. 'Types' at keypad position — shows 3_ _7 on clipboard (write)
    6. Hesitates — looks back south (look)
    7. Door opens (narrative text)
    8. Gets dragged eastward — freezes mid-scream (dragged → idle frozen)
    """
    start_x = 6 * TILE_SIZE
    start_y = 8 * TILE_SIZE   # central corridor

    east_bunk_x = 20 * TILE_SIZE
    east_bunk_y = 2 * TILE_SIZE

    keypad_x = 12 * TILE_SIZE - 12
    keypad_y = 4 * TILE_SIZE

    door_x = 12 * TILE_SIZE - 12
    door_y = 1 * TILE_SIZE

    frames = [
        # Frame 0: Ghost appears in corridor walking east.
        # Text fires immediately — names him so player knows who this is.
        GhostFrame(
            start_x, start_y, 'walk_to', 80,
            text="Volkov, Yuri. Last seen: 04:12.",
            text_source='vesna_f2'
        ),
        # Frame 1: Reaches his bunk in east alcove.
        GhostFrame(
            east_bunk_x, east_bunk_y + TILE_SIZE, 'walk_to', 100,
            text=None
        ),
        # Frame 2: Crouches — reads his own log. His words appear.
        GhostFrame(
            east_bunk_x, east_bunk_y + TILE_SIZE, 'write', 90,
            text="[VOLKOV] She kept saying numbers. I wrote down what I could.",
            text_source='yuri_log'
        ),
        # Frame 3: Stands, looks toward north wall (the door).
        # VESNA's voice — she's warning him. He doesn't listen.
        GhostFrame(
            east_bunk_x, east_bunk_y + TILE_SIZE, 'look', 60,
            text="Do not go north. Yuri. Do not go north.",
            text_source='vesna_f2'
        ),
        # Frame 4: Walks toward keypad. Clipboard now visible.
        # No text — let the clipboard do the work.
        GhostFrame(
            keypad_x, keypad_y + TILE_SIZE, 'walk_to', 100,
            text=None
        ),
        # Frame 5: Types at keypad. Clipboard shows 3_ _7.
        # Text fires: player now knows there are two missing digits.
        GhostFrame(
            keypad_x, keypad_y, 'write', 110,
            text="The other two — she was still transmitting them. Channel 3.",
            text_source='yuri_log'
        ),
        # Frame 6: Hesitates. Looks back at the barracks.
        # Last human moment before what happens next.
        GhostFrame(
            keypad_x, keypad_y, 'look', 50,
            text=None
        ),
        # Frame 7: Walks through the door.
        GhostFrame(
            door_x, door_y, 'walk_to', 55,
            text=None
        ),
        # Frame 8: Gets dragged. Fast. East wall.
        # His own log, finishing the sentence he never finished.
        GhostFrame(
            door_x + 3 * TILE_SIZE, door_y, 'dragged', 35,
            text="Static. Then they came.",
            text_source='yuri_log'
        ),
        # Frame 9: Gone. Door swings shut behind him.
        GhostFrame(
            door_x + 3 * TILE_SIZE, door_y, 'idle', 20,
            text=None
        ),
    ]

    # Trigger zone: player enters east bunk area on Freq 2
    trigger = pygame.Rect(
        14 * TILE_SIZE, 1 * TILE_SIZE,
        6 * TILE_SIZE, 4 * TILE_SIZE
    )

    return GhostSequence(frames, frequency=2, trigger_rect=trigger, once=True)