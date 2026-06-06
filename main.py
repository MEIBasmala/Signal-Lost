import pygame
import sys
import math

from settings import *
from src.player import Player
from src.keypad import Keypad

from src.world import World, ROOM_1
from src.creatures import Creature
from src.narrative import NarrativeManager, TriggerZone

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

        # World
        self.world = World(ROOM_1)

        # Player
        self.all_sprites = pygame.sprite.Group()
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.all_sprites.add(self.player)

        # Keypads
        self.keypads = []
        door_rect = pygame.Rect(12 * TILE_SIZE, 1 * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        keypad = Keypad(12 * TILE_SIZE, 2 * TILE_SIZE, 3427, door_rect)
        self.keypads.append(keypad)
        self.door_open = False
        
        # Door collision — starts as a wall
        self.door_wall = door_rect.copy()

        # Creatures
        self.creatures = pygame.sprite.Group()
        creature = Creature(
            x=7 * TILE_SIZE,
            y=8 * TILE_SIZE,
            patrol_start=(7 * TILE_SIZE, 8 * TILE_SIZE),
            patrol_end=(17 * TILE_SIZE, 8 * TILE_SIZE),
            frequency=1
        )
        self.creatures.add(creature)

                # Narrative system
        self.narrative = NarrativeManager()
        
        # B3 trigger zones
        self._setup_b3_triggers()
    
    def _setup_b3_triggers(self):
        """Set up all narrative triggers for Floor B3."""
        
        # Karim wakes — VESNA Freq 1
        self.narrative.add_trigger(TriggerZone(
            x=SCREEN_WIDTH//2 - 50, y=SCREEN_HEIGHT//2 - 50,
            width=100, height=100,
            text="...still here... still here... still—",
            source='vesna_f1',
            frequency=1
        ))
        
        # Yuri's log — under east bunk (approx x=500, y=250)
        self.narrative.add_trigger(TriggerZone(
            x=15 * TILE_SIZE, y=5 * TILE_SIZE,
            width=64, height=64,
            text='"VESNA said surface signal is fake. Said don\'t answer. I answered anyway. Static. Then they came."',
            source='yuri_log'
        ))
        
        # VESNA Freq 2 — morning greeting
        self.narrative.add_trigger(TriggerZone(
            x=SCREEN_WIDTH//2 - 100, y=SCREEN_HEIGHT//2 - 100,
            width=200, height=200,
            text="Good morning. Vitals normal. Surface temperature 34 degrees. It is a beautiful day.",
            source='vesna_f2',
            frequency=2
        ))
        
        # VESNA Freq 3 — scream
        self.narrative.add_trigger(TriggerZone(
            x=SCREEN_WIDTH//2 - 100, y=SCREEN_HEIGHT//2 - 100,
            width=200, height=200,
            text="KARIM I KNOW YOU CAN HEAR THIS WHY DIDN'T YOU—",
            source='vesna_f3',
            frequency=3
        ))
        
        # Hidden: Why Karim survived — Freq 3 near his bunk
        self.narrative.add_trigger(TriggerZone(
            x=3 * TILE_SIZE, y=10 * TILE_SIZE,
            width=64, height=64,
            text="Vitals: Messaoud, Karim. Critical. Sealing sector B3 ventilation. Unauthorized. I do not care.",
            source='vesna_f3',
            frequency=3
        ))
        
        # Freq 3 fragments — near where Yuri died
        self.narrative.add_trigger(TriggerZone(
            x=13 * TILE_SIZE, y=8 * TILE_SIZE,
            width=64, height=64,
            text="3 — NO — 4 — STOP — 2 — PLEASE — 7",
            source='vesna_f3',
            frequency=3
        ))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    for keypad in self.keypads:
                        if keypad.active:
                            keypad.deactivate()
                    continue

                keypad_handled = False
                for keypad in self.keypads:
                    if keypad.active:
                        result = keypad.handle_input(event)
                        if result == "wrong":
                            self.death_flash = True
                            self.death_flash_timer = 20
                            self.attract_creature_to(keypad.x, keypad.y)
                        elif result == "correct":
                            self.door_open = True
                        keypad_handled = True
                        break
                
                if keypad_handled:
                    continue

                if event.key == pygame.K_e:
                    near_keypad = False
                    for keypad in self.keypads:
                        if keypad.can_interact(self.player.rect):
                            keypad.activate()
                            near_keypad = True
                            break
                    
                    if near_keypad:
                        continue

                if not any(k.active for k in self.keypads):
                    if event.key == pygame.K_q:
                        self.switch_frequency(-1)
                    elif event.key == pygame.K_e:
                        self.switch_frequency(1)

    def switch_frequency(self, direction):
        now = pygame.time.get_ticks()
        if any(k.active for k in self.keypads):
            return
        if now - self.last_switch_time < FREQ_SWITCH_COOLDOWN:
            return
    
        self.current_freq = (self.current_freq - 1 + direction) % 3 + 1
        self.last_switch_time = now
        self.switching = True
        self.switch_timer = 10

    def attract_creature_to(self, x, y):
        nearest = None
        min_dist = float('inf')
        for creature in self.creatures:
            dist = ((creature.pos_x - x)**2 + (creature.pos_y - y)**2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest = creature
        if nearest:
            nearest.force_chase_toward(x, y, duration=120)

    def update(self):
        dt = self.clock.tick(FPS)
        
        for keypad in self.keypads:
            keypad.update(dt)
        
        if not any(k.active for k in self.keypads):
            keys = pygame.key.get_pressed()
            self.all_sprites.update(keys, self.get_active_walls())
        else:
            if self.player.invincible:
                self.player.invincibility_timer -= 1
                if self.player.invincibility_timer <= 0:
                    self.player.invincible = False
        
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

        if self.switching:
            self.switch_timer -= 1
            if self.switch_timer <= 0:
                self.switching = False
        
        for creature in self.creatures:
            creature.update(self.current_freq, self.player.rect)
        
        for creature in self.creatures:
            if creature.frequency != self.current_freq:
                continue
            if self.player.rect.colliderect(creature.rect):
                hit_landed = self.player.take_damage()
                if hit_landed:
                    self.death_flash = True
                    self.death_flash_timer = 30
                    dx = self.player.pos_x - creature.pos_x
                    dy = self.player.pos_y - creature.pos_y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist != 0:
                        self.player.pos_x += (dx / dist) * 60
                        self.player.pos_y += (dy / dist) * 60
        
        if self.player.hearts <= 0:
            self.running = False
        
        self.narrative.update(self.player.rect, self.current_freq)


    def draw(self):
        self.screen.fill(DARK_GREEN)
        self.world.draw(self.screen, self.current_freq)
        
        # Door
        if not self.door_open:
            for keypad in self.keypads:
                pygame.draw.rect(self.screen, (60, 40, 30), keypad.door_rect)
        else:
            for keypad in self.keypads:
                pygame.draw.rect(self.screen, (20, 35, 25), keypad.door_rect)
        
        # Keypads in world
        for keypad in self.keypads:
            keypad.draw_world(self.screen, self.current_freq)
        
        # Sprites and creatures
        self.all_sprites.draw(self.screen)
        for creature in self.creatures:
            creature.draw(self.screen, self.current_freq)
        
        # Narrative texts (before overlay effects so they get tinted)
        self.narrative.draw(self.screen)
        
        # Screen effects and HUD
        self.draw_frequency_overlay()
        self.draw_scanlines()
        self.draw_hud()
        self.draw_hearts()
        
        # Keypad overlay LAST (on top of everything)
        for keypad in self.keypads:
            keypad.draw_overlay(self.screen)
        
        pygame.display.flip()
    def draw_frequency_overlay(self):
        if self.death_flash:
            self.death_flash_timer -= 1
            if self.death_flash_timer <= 0:
                self.death_flash = False
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int((self.death_flash_timer / 45) * 255)
            flash.fill((255, 50, 50, alpha))
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

    def draw_hud(self):
        font = pygame.font.SysFont("Courier New", 18)
        freq_text = font.render(f"FREQ: {self.current_freq}", True, WHITE)
        battery_text = font.render(f"PWR: {int(self.battery)}%", True, WHITE)
        self.screen.blit(freq_text, (20, 20))
        self.screen.blit(battery_text, (20, 44))

        if self.battery <= BATTERY_LOW:
            low_battery_text = font.render("LOW BATTERY", True, (255, 50, 50))
            self.screen.blit(low_battery_text, (20, 68))

    def draw_scanlines(self):
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(self.screen, (0, 0, 0, 40), (0, y), (SCREEN_WIDTH, y))

    def draw_hearts(self):
        for i in range(PLAYER_MAX_HEARTS):
            x = SCREEN_WIDTH - (PLAYER_MAX_HEARTS - i) * (HEART_SIZE + HEART_PADDING)
            y = 20
            color = (220, 50, 50) if i < self.player.hearts else (60, 30, 30)
            cx = x + HEART_SIZE // 2
            cy = y + HEART_SIZE // 2
            points = [(cx, y), (x + HEART_SIZE, cy), (cx, y + HEART_SIZE), (x, cy)]
            pygame.draw.polygon(self.screen, color, points)

    def get_active_walls(self):
        walls = list(self.world.wall_rects)
        
        # Add door wall if still closed
        if not self.door_open:
            walls.append(self.door_wall)
        
        if self.current_freq == 2:
            walls += self.world.freq2_wall_rects
        elif self.current_freq == 3:
            walls += self.world.freq3_wall_rects
        
        return walls

if __name__ == "__main__":
    game = Game()
    game.run()