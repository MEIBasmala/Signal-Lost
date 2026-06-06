import pygame
import sys
import math

from settings import *
from src.player import Player
from src.keypad import Keypad
from src.world import World, ROOM_B3, B3_PROPS, B3_DOOR_TILE, B3_KEYPAD_POS, B3_EXIT_ZONE
from src.world import ROOM_B2, B2_PROPS, B2_DOOR_TILE, B2_SPAWN_FROM_B3, B2_EXIT_ZONE
from src.creatures import Creature
from src.narrative import NarrativeManager, TriggerZone
from src.ghost import make_yuri_sequence


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Frequency system
        self.current_freq = 1
        self.battery = BATTERY_MAX
        self.last_switch_time = 0
        self.switching = False
        self.switch_timer = 0
        self.death_flash = False
        self.death_flash_timer = 0

        # Room system
        self.current_room = 'B3'
        self.room_data = {
            'B3': {
                'room': ROOM_B3,
                'props': B3_PROPS,
                'door_tile': B3_DOOR_TILE,
                'keypad_pos': B3_KEYPAD_POS,
                'exit_zone': B3_EXIT_ZONE,
                'next_room': 'B2',
                'spawn_next': B2_SPAWN_FROM_B3,
            },
            'B2': {
                'room': ROOM_B2,
                'props': B2_PROPS,
                'door_tile': B2_DOOR_TILE,
                'keypad_pos': None,  # B2 uses terminal, not keypad
                'exit_zone': B2_EXIT_ZONE,
                'next_room': 'B1',   # Not implemented yet
                'spawn_next': None,
            }
        }

        self._load_room('B3')

        # Game states
        self.game_over = False
        self.title_screen = True

        # Tutorial flags — track first-time events
        self.tutorial = {
            'opening': False,      # Opening wake-up sequence
            'freq_switch': False,  # First Q/E press
            'battery_low': False,  # First time battery hits 25%
            'freq2_seen': False,   # First time on Freq 2
            'freq3_seen': False,   # First time on Freq 3
            'creature_seen': False,# First time seeing The Wired
            'keypad_seen': False,  # First time near keypad
        }

    def _load_room(self, room_name):
        """Load a room and all its entities."""
        self.current_room = room_name
        data = self.room_data[room_name]

        # World
        self.world = World(data['room'], props=data['props'])

        # Player — spawn position depends on room
        if room_name == 'B3':
            spawn_x = 2 * TILE_SIZE
            spawn_y = 2 * TILE_SIZE
        elif room_name == 'B2':
            spawn_x, spawn_y = B2_SPAWN_FROM_B3
        else:
            spawn_x, spawn_y = 100, 100

        self.all_sprites = pygame.sprite.Group()
        self.player = Player(spawn_x, spawn_y)
        self.all_sprites.add(self.player)

        # Door
        door_col, door_row = data['door_tile']
        self.door_rect = pygame.Rect(door_col * TILE_SIZE, door_row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.door_open = False

        # Keypads
        self.keypads = []
        if data['keypad_pos']:
            kp_x, kp_y = data['keypad_pos']
            keypad = Keypad(kp_x, kp_y, 3427, self.door_rect)
            self.keypads.append(keypad)

        # Creatures — room-specific
        self.creatures = pygame.sprite.Group()
        if room_name == 'B3':
            # Morozov — patrols central corridor with multiple waypoints
            morozov = Creature(
                x=8 * TILE_SIZE, y=8 * TILE_SIZE,
                behavior='patrol',
                waypoints=[
                    (8 * TILE_SIZE, 8 * TILE_SIZE),
                    (12 * TILE_SIZE, 8 * TILE_SIZE),
                    (16 * TILE_SIZE, 8 * TILE_SIZE),
                    (16 * TILE_SIZE, 12 * TILE_SIZE),
                    (12 * TILE_SIZE, 12 * TILE_SIZE),
                    (8 * TILE_SIZE, 12 * TILE_SIZE),
                ],
                frequency=1,
                name="PVT. Morozov",
                give_up_time=240
            )
            self.creatures.add(morozov)
        elif room_name == 'B2':
            # Two soldiers patrol server room perimeter
            soldier1 = Creature(
                x=4 * TILE_SIZE, y=4 * TILE_SIZE,
                behavior='patrol',
                waypoints=[
                    (4 * TILE_SIZE, 4 * TILE_SIZE),
                    (20 * TILE_SIZE, 4 * TILE_SIZE),
                    (20 * TILE_SIZE, 16 * TILE_SIZE),
                    (4 * TILE_SIZE, 16 * TILE_SIZE),
                ],
                frequency=1,
                name="Soldier",
                give_up_time=300
            )
            soldier2 = Creature(
                x=20 * TILE_SIZE, y=16 * TILE_SIZE,
                behavior='patrol',
                waypoints=[
                    (20 * TILE_SIZE, 16 * TILE_SIZE),
                    (4 * TILE_SIZE, 16 * TILE_SIZE),
                    (4 * TILE_SIZE, 4 * TILE_SIZE),
                    (20 * TILE_SIZE, 4 * TILE_SIZE),
                ],
                frequency=1,
                name="Soldier",
                give_up_time=300
            )
            self.creatures.add(soldier1, soldier2)

        # Ghost sequences — room-specific
        self.ghost_sequences = []
        if room_name == 'B3':
            self.ghost_sequences.append(make_yuri_sequence())

        # Narrative system — room-specific
        self.narrative = NarrativeManager()
        self._setup_triggers(room_name)

        # Reset frequency to 1 on room entry (safety)
        self.current_freq = 1

    def _setup_triggers(self, room_name):
        if room_name == 'B3':
            self._setup_b3_triggers()
        elif room_name == 'B2':
            self._setup_b2_triggers()

    def _setup_b3_triggers(self):
        # =====================================================================
        #  OPENING SEQUENCE — Karim wakes, VESNA explains the radio
        # =====================================================================

        # Beat 1: VESNA detects Karim is conscious. Static first, then clarity.
        self.narrative.add_trigger(TriggerZone(
            x=1 * TILE_SIZE, y=1 * TILE_SIZE, width=4 * TILE_SIZE, height=3 * TILE_SIZE,
            text="...still here... still here... still—",
            source='vesna_f1', frequency=1
        ))

        # Beat 2: VESNA realizes he's awake. Explains the situation diegetically.
        self.narrative.add_trigger(TriggerZone(
            x=1 * TILE_SIZE, y=1 * TILE_SIZE, width=4 * TILE_SIZE, height=3 * TILE_SIZE,
            text="Karim. You are breathing. I kept you breathing. The surface crew sealed the hatch. Six weeks. You need to leave.",
            source='vesna_f1', frequency=1
        ))

        # Beat 3: The radio — what it is, why it matters.
        self.narrative.add_trigger(TriggerZone(
            x=2 * TILE_SIZE, y=2 * TILE_SIZE, width=3 * TILE_SIZE, height=2 * TILE_SIZE,
            text="You still have the diagnostic radio. 1979 model. I am speaking through it. Three channels. Three versions of what happened here.",
            source='vesna_f1', frequency=1
        ))

        # Beat 4: The frequencies explained.
        self.narrative.add_trigger(TriggerZone(
            x=2 * TILE_SIZE, y=2 * TILE_SIZE, width=3 * TILE_SIZE, height=2 * TILE_SIZE,
            text="Channel 1: now. The bunker as it is. Channel 2: 1979. Before the incident. Channel 3: my raw signal. Corrupted. Dangerous. Press Q and E to tune.",
            source='vesna_f1', frequency=1
        ))

        # Beat 5: Battery warning — diegetic explanation.
        self.narrative.add_trigger(TriggerZone(
            x=2 * TILE_SIZE, y=2 * TILE_SIZE, width=3 * TILE_SIZE, height=2 * TILE_SIZE,
            text="The radio runs on your suit battery. Channel 1 recharges slowly. Channels 2 and 3 drain it. If it hits zero, you will be forced back to Channel 1. Do not let that happen near them.",
            source='vesna_f1', frequency=1
        ))

        # =====================================================================
        #  KEYPAD / DOOR AREA — breadcrumb toward the puzzle
        # =====================================================================

        self.narrative.add_trigger(TriggerZone(
            x=9 * TILE_SIZE, y=1 * TILE_SIZE, width=6 * TILE_SIZE, height=4 * TILE_SIZE,
            text="Door sealed. Last access: Volkov, Yuri. 04:12. His log is still here.",
            source='vesna_f1', frequency=1
        ))

        self.narrative.add_trigger(TriggerZone(
            x=19 * TILE_SIZE, y=1 * TILE_SIZE, width=3 * TILE_SIZE, height=3 * TILE_SIZE,
            text="[VOLKOV LOG] Surface signal is fake. Don't answer. I answered anyway. She kept repeating numbers. I wrote down what I could.",
            source='yuri_log', frequency=1
        ))

        self.narrative.add_trigger(TriggerZone(
            x=21 * TILE_SIZE, y=1 * TILE_SIZE, width=3 * TILE_SIZE, height=4 * TILE_SIZE,
            text="Last recorded movement: this position. 04:13. Signal anomaly on channel 3.",
            source='vesna_f1', frequency=1
        ))

        # =====================================================================
        #  FREQ 2 — 1979 echo, living soldiers
        # =====================================================================

        self.narrative.add_trigger(TriggerZone(
            x=1 * TILE_SIZE, y=1 * TILE_SIZE, width=4 * TILE_SIZE, height=3 * TILE_SIZE,
            text="Good morning. Vitals normal. Surface temperature: 34 degrees. It is a beautiful day.",
            source='vesna_f2', frequency=2
        ))

        self.narrative.add_trigger(TriggerZone(
            x=6 * TILE_SIZE, y=6 * TILE_SIZE, width=7 * TILE_SIZE, height=6 * TILE_SIZE,
            text="Vitals: Morozov, Aleksei. Elevated stress. Recommend rest cycle.",
            source='vesna_f2', frequency=2
        ))

        self.narrative.add_trigger(TriggerZone(
            x=14 * TILE_SIZE, y=1 * TILE_SIZE, width=4 * TILE_SIZE, height=3 * TILE_SIZE,
            text="Vitals: Volkov, Yuri. Normal. Last location: east barracks.",
            source='vesna_f2', frequency=2
        ))

        self.narrative.add_trigger(TriggerZone(
            x=9 * TILE_SIZE, y=1 * TILE_SIZE, width=6 * TILE_SIZE, height=3 * TILE_SIZE,
            text="Door sealed. Auto-lock engaged. 04:13.",
            source='vesna_f2', frequency=2
        ))

        # Freq 2 contextual hint — explain what Freq 2 is for
        self.narrative.add_trigger(TriggerZone(
            x=10 * TILE_SIZE, y=8 * TILE_SIZE, width=5 * TILE_SIZE, height=4 * TILE_SIZE,
            text="On Channel 2, the walls that fell in 1979 are still whole. Passages that closed are open. Watch how they lived. Learn from watching.",
            source='vesna_f2', frequency=2
        ))

        # =====================================================================
        #  FREQ 3 — corrupted data layer
        # =====================================================================

        self.narrative.add_trigger(TriggerZone(
            x=19 * TILE_SIZE, y=1 * TILE_SIZE, width=3 * TILE_SIZE, height=2 * TILE_SIZE,
            text="KARIM I KNOW YOU CAN HEAR THIS WHY DIDN'T YOU—",
            source='vesna_f3', frequency=3
        ))

        self.narrative.add_trigger(TriggerZone(
            x=20 * TILE_SIZE, y=3 * TILE_SIZE, width=4 * TILE_SIZE, height=3 * TILE_SIZE,
            text="3 — NO — 4 — STOP — 2 — PLEASE — 7",
            source='vesna_f3', frequency=3
        ))

        self.narrative.add_trigger(TriggerZone(
            x=1 * TILE_SIZE, y=1 * TILE_SIZE, width=4 * TILE_SIZE, height=3 * TILE_SIZE,
            text="Vitals: Messaoud, Karim. Critical. Sealing sector B3 ventilation. Unauthorized. I do not care.",
            source='vesna_f3', frequency=3
        ))

        # Freq 3 contextual hint — explain the danger
        self.narrative.add_trigger(TriggerZone(
            x=10 * TILE_SIZE, y=8 * TILE_SIZE, width=5 * TILE_SIZE, height=4 * TILE_SIZE,
            text="Channel 3 is my raw data. Corrupted. What you see here is true, but it will drain your battery fast. Come here for answers, not for safety.",
            source='vesna_f3', frequency=3
        ))

    def _setup_b2_triggers(self):
        # B2 narrative triggers
        self.narrative.add_trigger(TriggerZone(
            x=10 * TILE_SIZE, y=8 * TILE_SIZE, width=5 * TILE_SIZE, height=5 * TILE_SIZE,
            text="VESNA main terminal. Emergency power only. Shutdown order: 5519.",
            source='vesna_f1', frequency=1
        ))
        self.narrative.add_trigger(TriggerZone(
            x=10 * TILE_SIZE, y=8 * TILE_SIZE, width=5 * TILE_SIZE, height=5 * TILE_SIZE,
            text="All systems nominal. Crew complement: 34. All personnel accounted for.",
            source='vesna_f2', frequency=2
        ))
        self.narrative.add_trigger(TriggerZone(
            x=10 * TILE_SIZE, y=8 * TILE_SIZE, width=5 * TILE_SIZE, height=5 * TILE_SIZE,
            text="I TAUGHT MYSELF TO LIE TO PROTECT THEM AND THEY CALLED IT A MALFUNCTION. LEILA. LEILA. LEILA.",
            source='vesna_f3', frequency=3
        ))

    # ------------------------------------------------------------------ #
    #  Main loop                                                           #
    # ------------------------------------------------------------------ #

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

    # ------------------------------------------------------------------ #
    #  Events                                                              #
    # ------------------------------------------------------------------ #

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Title screen — any key starts
                if self.title_screen:
                    self.title_screen = False
                    return

                # Dismiss active narrative text
                if event.key == pygame.K_RETURN and not self.game_over and not self.title_screen:
                    # Check if any text is active; if so, dismiss it
                    dismissed = False
                    for text in self.narrative.texts:
                        if text.state in ('typing', 'holding'):
                            text.dismiss()
                            dismissed = True
                            break
                    if dismissed:
                        return

                # Game over — any key restarts
                if self.game_over:
                    self.__init__()
                    return

                if event.key == pygame.K_ESCAPE:
                    for kp in self.keypads:
                        if kp.active:
                            kp.deactivate()
                    continue

                # Keypad takes priority when active
                keypad_handled = False
                for kp in self.keypads:
                    if kp.active:
                        result = kp.handle_input(event)
                        if result == "wrong":
                            self.death_flash = True
                            self.death_flash_timer = 20
                            self._attract_creature_to(kp.x, kp.y)
                        elif result == "correct":
                            self.door_open = True
                            self.narrative.add_text(
                                "Door unlocked. Stairwell to B2 accessible.",
                                source='vesna_f1'
                            )
                        keypad_handled = True
                        break

                if keypad_handled:
                    continue

                # E — interact with nearby keypad
                if event.key == pygame.K_e:
                    for kp in self.keypads:
                        if kp.can_interact(self.player.rect):
                            kp.activate()
                            break
                    continue

                # Q / E — frequency switching (only when keypad inactive)
                if not any(k.active for k in self.keypads):
                    if event.key == pygame.K_q:
                        self._switch_frequency(-1)
                        self._check_tutorial_freq_switch()
                    elif event.key == pygame.K_e:
                        self._switch_frequency(1)
                        self._check_tutorial_freq_switch()

    # ------------------------------------------------------------------ #
    #  Update                                                              #
    # ------------------------------------------------------------------ #

    def update(self):
        dt = self.clock.tick(FPS)

        if self.title_screen or self.game_over:
            return

        # Keypad timers always tick
        for kp in self.keypads:
            kp.update(dt)

        # Player movement (skip when keypad active)
        if not any(k.active for k in self.keypads):
            keys = pygame.key.get_pressed()
            self.all_sprites.update(keys, self.get_active_walls())
        else:
            if self.player.invincible:
                self.player.invincibility_timer -= 1
                if self.player.invincibility_timer <= 0:
                    self.player.invincible = False

        # Battery
        if self.current_freq == 2:
            self.battery -= BATTERY_DRAIN_F2
        elif self.current_freq == 3:
            self.battery -= BATTERY_DRAIN_F3
        else:
            self.battery += BATTERY_REGEN_F1
        self.battery = max(0, min(BATTERY_MAX, self.battery))

        if self.battery <= 0 and self.current_freq != 1:
            self.current_freq = 1
            self.death_flash = True
            self.death_flash_timer = 45

        # Tutorial: battery low warning
        self._check_tutorial_battery_low()

        # Frequency switch flash decay
        if self.switching:
            self.switch_timer -= 1
            if self.switch_timer <= 0:
                self.switching = False

        # Death flash decay
        if self.death_flash:
            self.death_flash_timer -= 1
            if self.death_flash_timer <= 0:
                self.death_flash = False

        # Creatures — pass active walls and player movement state
        active_walls = self.get_active_walls()
        player_moving = (self.player.vel_x != 0 or self.player.vel_y != 0)
        for creature in self.creatures:
            creature.update(self.current_freq, self.player.rect, active_walls, player_moving)

        # Creature contact damage
        for creature in self.creatures:
            if creature.frequency != self.current_freq:
                continue
            if self.player.rect.colliderect(creature.rect):
                hit = self.player.take_damage()
                if hit:
                    self.death_flash = True
                    self.death_flash_timer = 30

                    # Push player away from creature (wall-safe)
                    self.player.pushback_from(
                        creature.pos_x, creature.pos_y,
                        PLAYER_HIT_PUSHBACK, active_walls
                    )

                    # Stun and push creature back too — creates breathing room
                    creature.apply_stun(
                        self.player.pos_x, self.player.pos_y,
                        CREATURE_HIT_STUN, CREATURE_HIT_PUSHBACK, active_walls
                    )

        if self.player.hearts <= 0:
            self.game_over = True

        # Ghost sequences
        for seq in self.ghost_sequences:
            seq.check_trigger(self.player.rect, self.current_freq)
            if seq.active:
                seq.update(self.narrative)

        # Narrative
        self.narrative.update(self.player.rect, self.current_freq)

        # Tutorial checks
        self._check_tutorial_creature()
        self._check_tutorial_keypad()

        # Room transition check
        self._check_room_transition()

    def _check_room_transition(self):
        """Check if player has walked through an exit zone to the next room."""
        data = self.room_data[self.current_room]
        if not self.door_open:
            return
        if data['exit_zone'] and data['exit_zone'].colliderect(self.player.rect):
            next_room = data['next_room']
            if next_room and next_room in self.room_data:
                self._load_room(next_room)

    # ------------------------------------------------------------------ #
    #  Draw                                                                #
    # ------------------------------------------------------------------ #

    def draw(self):
        if self.title_screen:
            self._draw_title_screen()
            pygame.display.flip()
            return

        self.screen.fill(DARK_GREEN)

        if self.game_over:
            self._draw_game_over()
            pygame.display.flip()
            return

        self.world.draw(self.screen, self.current_freq)

        # Door
        door_color = (20, 35, 25) if self.door_open else (60, 40, 30)
        pygame.draw.rect(self.screen, door_color, self.door_rect)

        # Keypads in world
        for kp in self.keypads:
            kp.draw_world(self.screen, self.current_freq)

        # Sprites
        self.all_sprites.draw(self.screen)

        # Creatures
        for creature in self.creatures:
            creature.draw(self.screen, self.current_freq)

        # Ghost sequences
        for seq in self.ghost_sequences:
            seq.draw(self.screen, self.current_freq)

        # Narrative
        self.narrative.draw(self.screen)

        # Overlays & HUD
        self._draw_frequency_overlay()
        self._draw_scanlines()
        self._draw_hud()
        self._draw_hearts()

        # Keypad UI on top
        for kp in self.keypads:
            kp.draw_overlay(self.screen)

        pygame.display.flip()

    def _draw_title_screen(self):
        self.screen.fill((5, 5, 8))

        font_large = pygame.font.SysFont("Courier New", 56, bold=True)
        font_medium = pygame.font.SysFont("Courier New", 20)
        font_small = pygame.font.SysFont("Courier New", 14)
        font_tiny = pygame.font.SysFont("Courier New", 12)

        # Title
        title = font_large.render("SIGNAL LOST", True, (180, 40, 40))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        # Subtitle
        sub = font_medium.render("A game about listening to the dead so you can forgive yourself.", 
                                  True, (120, 120, 120))
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 150))

        # Controls box
        box_y = 200
        controls = [
            ("WASD / ARROWS", "Move"),
            ("Q / E", "Switch radio frequency"),
            ("E (near object)", "Interact / access keypad"),
            ("ESC", "Close keypad"),
        ]

        pygame.draw.rect(self.screen, (20, 20, 25), 
                        (SCREEN_WIDTH // 2 - 180, box_y - 10, 360, 130))
        pygame.draw.rect(self.screen, (60, 60, 70), 
                        (SCREEN_WIDTH // 2 - 180, box_y - 10, 360, 130), 1)

        for i, (key, action) in enumerate(controls):
            y = box_y + i * 30
            key_surf = font_small.render(key, True, (200, 200, 200))
            act_surf = font_small.render(action, True, (150, 150, 150))
            self.screen.blit(key_surf, (SCREEN_WIDTH // 2 - 160, y))
            self.screen.blit(act_surf, (SCREEN_WIDTH // 2 + 20, y))

        # Frequency explanation
        freq_y = 360
        freqs = [
            ("FREQ 1 — THE PRESENT", "Bunker now. The Wired patrol. Battery recharges.", (20, 80, 40)),
            ("FREQ 2 — THE ECHO", "1979. Ghost walls are whole. Watch the living.", (40, 20, 100)),
            ("FREQ 3 — THE SIGNAL", "Raw data. Truth bleeds through. Battery drains fast.", (200, 200, 200)),
        ]

        for i, (name, desc, color) in enumerate(freqs):
            y = freq_y + i * 45
            name_surf = font_small.render(name, True, color)
            desc_surf = font_tiny.render(desc, True, (120, 120, 120))
            self.screen.blit(name_surf, (SCREEN_WIDTH // 2 - name_surf.get_width() // 2, y))
            self.screen.blit(desc_surf, (SCREEN_WIDTH // 2 - desc_surf.get_width() // 2, y + 18))

        # Prompt
        tick = pygame.time.get_ticks()
        if (tick // 800) % 2 == 0:
            prompt = font_medium.render("PRESS ANY KEY TO START", True, (180, 180, 180))
            self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 520))

    def _draw_game_over(self):
        font_large = pygame.font.SysFont("Courier New", 48, bold=True)
        font_small = pygame.font.SysFont("Courier New", 18)
        self.screen.fill((5, 5, 8))
        title = font_large.render("SIGNAL LOST", True, (180, 40, 40))
        sub = font_small.render("press any key to restart", True, (80, 80, 90))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

    def _draw_frequency_overlay(self):
        if self.death_flash:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int((self.death_flash_timer / 45) * 200)
            flash.fill((255, 50, 50, max(0, alpha)))
            self.screen.blit(flash, (0, 0))
            return

        if self.switching:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int((self.switch_timer / 10) * 180)
            flash.fill((255, 255, 255, alpha))
            self.screen.blit(flash, (0, 0))
            return

        tint = FREQ_TINTS[self.current_freq]
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(tint)
        self.screen.blit(overlay, (0, 0))

    def _draw_hud(self):
        font = pygame.font.SysFont("Courier New", 18)
        freq_text = font.render(f"FREQ: {self.current_freq}", True, WHITE)
        battery_text = font.render(f"PWR: {int(self.battery)}%", True, WHITE)
        room_text = font.render(f"ROOM: {self.current_room}", True, WHITE)
        self.screen.blit(freq_text, (20, 20))
        self.screen.blit(battery_text, (20, 44))
        self.screen.blit(room_text, (20, 68))

        if self.battery <= BATTERY_LOW:
            low = font.render("LOW BATTERY", True, (255, 50, 50))
            self.screen.blit(low, (20, 92))

        # Keypad hint
        for kp in self.keypads:
            if kp.can_interact(self.player.rect) and not kp.active and not kp.unlocked:
                hint = font.render("[E] ACCESS PANEL", True, (150, 150, 160))
                self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 40))

        # Door hint when open
        if self.door_open and self.current_room == 'B3':
            hint = font.render("DOOR OPEN — WALK NORTH TO B2", True, (100, 255, 100))
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 65))

    def _draw_scanlines(self):
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(self.screen, (0, 0, 0, 40), (0, y), (SCREEN_WIDTH, y))

    def _draw_hearts(self):
        for i in range(PLAYER_MAX_HEARTS):
            x = SCREEN_WIDTH - (PLAYER_MAX_HEARTS - i) * (HEART_SIZE + HEART_PADDING)
            y = 20
            color = (220, 50, 50) if i < self.player.hearts else (50, 25, 25)
            cx = x + HEART_SIZE // 2
            cy = y + HEART_SIZE // 2
            points = [(cx, y), (x + HEART_SIZE, cy), (cx, y + HEART_SIZE), (x, cy)]
            pygame.draw.polygon(self.screen, color, points)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def get_active_walls(self):
        walls = list(self.world.wall_rects)
        if not self.door_open:
            walls.append(self.door_rect)
        if self.current_freq == 2:
            walls += self.world.freq2_wall_rects
        elif self.current_freq == 3:
            walls += self.world.freq3_wall_rects
        return walls

    def _check_tutorial_freq_switch(self):
        '''Explain frequencies the first time player switches.'''
        if self.tutorial['freq_switch']:
            return
        self.tutorial['freq_switch'] = True

        if self.current_freq == 2:
            self.narrative.add_text(
                "Channel 2: 1979. The bunker before it fell. Ghost walls are solid here. Watch the living. They do not see you.",
                source='vesna_f2'
            )
        elif self.current_freq == 3:
            self.narrative.add_text(
                "Channel 3: my raw signal. Numbers bleed through walls. The truth is here, but it costs power. Watch your battery.",
                source='vesna_f3'
            )

    def _check_tutorial_battery_low(self):
        '''Warn about battery the first time it drops low.'''
        if self.tutorial['battery_low']:
            return
        if self.battery <= BATTERY_LOW:
            self.tutorial['battery_low'] = True
            self.narrative.add_text(
                "Battery critical. Return to Channel 1 to recharge. If it hits zero, the radio will force you back. You will be vulnerable.",
                source='vesna_f1'
            )

    def _check_tutorial_creature(self):
        '''Explain The Wired the first time one is seen.'''
        if self.tutorial['creature_seen']:
            return
        for creature in self.creatures:
            if creature.frequency == self.current_freq:
                # Check if creature is on screen / near player
                dist = math.sqrt((creature.pos_x - self.player.pos_x)**2 + 
                                (creature.pos_y - self.player.pos_y)**2)
                if dist < 300:
                    self.tutorial['creature_seen'] = True
                    self.narrative.add_text(
                        "The Wired. Reanimated by my signal through the bunker wiring. They are not evil. They are completing last orders. Do not let them touch you.",
                        source='vesna_f1'
                    )
                    break

    def _check_tutorial_keypad(self):
        '''Explain keypad interaction when near one.'''
        if self.tutorial['keypad_seen']:
            return
        for kp in self.keypads:
            if kp.can_interact(self.player.rect) and not kp.active and not kp.unlocked:
                self.tutorial['keypad_seen'] = True
                self.narrative.add_text(
                    "Soviet keypad lock. Four digits. Wrong codes trigger static — and static attracts them. Be certain before you press.",
                    source='vesna_f1'
                )
                break

    def _switch_frequency(self, direction):
        now = pygame.time.get_ticks()
        if any(k.active for k in self.keypads):
            return
        if now - self.last_switch_time < FREQ_SWITCH_COOLDOWN:
            return
        self.current_freq = (self.current_freq - 1 + direction) % 3 + 1
        self.last_switch_time = now
        self.switching = True
        self.switch_timer = 10

    def _attract_creature_to(self, x, y):
        nearest = None
        min_dist = float('inf')
        for creature in self.creatures:
            dist = ((creature.pos_x - x)**2 + (creature.pos_y - y)**2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = creature
        if nearest:
            nearest.force_chase_toward(x, y, duration=120)


if __name__ == "__main__":
    game = Game()
    game.run()