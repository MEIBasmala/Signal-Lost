import pygame
import math
import heapq
from settings import *


# =====================================================================
#  Simple A* pathfinding on tile grid
# =====================================================================

def astar_path(start, goal, walls, tile_size=TILE_SIZE):
    """Find path from start (x,y) to goal (x,y) avoiding walls.
    Returns list of (x,y) waypoints, or empty list if no path."""

    def to_grid(px, py):
        return int(px // tile_size), int(py // tile_size)

    def to_pixel(gx, gy):
        return gx * tile_size + tile_size // 2, gy * tile_size + tile_size // 2

    # Build wall grid set
    wall_set = set()
    for w in walls:
        # Mark all tiles this wall covers
        for cx in range(w.left // tile_size, (w.right + tile_size - 1) // tile_size):
            for cy in range(w.top // tile_size, (w.bottom + tile_size - 1) // tile_size):
                wall_set.add((cx, cy))

    start_g = to_grid(start[0], start[1])
    goal_g = to_grid(goal[0], goal[1])

    if start_g == goal_g:
        return [goal]

    if goal_g in wall_set:
        # Goal inside wall — find nearest free tile
        best = None
        best_dist = float('inf')
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                test = (goal_g[0] + dx, goal_g[1] + dy)
                if test not in wall_set:
                    d = math.sqrt((test[0]-goal_g[0])**2 + (test[1]-goal_g[1])**2)
                    if d < best_dist:
                        best_dist = d
                        best = test
        if best is None:
            return []
        goal_g = best

    # A*
    open_set = [(0, start_g)]
    came_from = {}
    g_score = {start_g: 0}
    f_score = {start_g: abs(start_g[0]-goal_g[0]) + abs(start_g[1]-goal_g[1])}

    neighbors = [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(-1,1),(1,-1),(1,1)]

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal_g:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(to_pixel(current[0], current[1]))
                current = came_from[current]
            path.reverse()
            return path

        for dx, dy in neighbors:
            neighbor = (current[0] + dx, current[1] + dy)

            # Diagonal movement blocked by corner walls
            if dx != 0 and dy != 0:
                if (current[0] + dx, current[1]) in wall_set and (current[0], current[1] + dy) in wall_set:
                    continue

            if neighbor in wall_set:
                continue

            move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
            tentative_g = g_score[current] + move_cost

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + abs(neighbor[0]-goal_g[0]) + abs(neighbor[1]-goal_g[1])
                f_score[neighbor] = f
                heapq.heappush(open_set, (f, neighbor))

    return []


# =====================================================================
#  Creature Types & Behaviors
# =====================================================================

class Creature(pygame.sprite.Sprite):
    """
    The Wired — reanimated soldiers completing last orders.

    Behaviors:
    - patrol: follow waypoints in order, loop or ping-pong
    - guard: stand at post, watch an arc, react to LOS
    - investigate: go to last known player position, then return
    - chase: A* pathfind to player, give up if lost for too long
    - forced_chase: attracted by sound (wrong keypad), temporary

    States: idle → patrol → alert → investigate → chase → return → patrol
    """

    def __init__(self, x, y, behavior='patrol', waypoints=None, 
                 frequency=1, name="Wired", detect_range=None,
                 chase_speed=None, patrol_speed=None, give_up_time=300):
        super().__init__()

        self.image = pygame.Surface((24, 32))
        self.image.fill((180, 40, 40))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos_x = float(x)
        self.pos_y = float(y)

        # Identity
        self.name = name
        self.frequency = frequency

        # Movement config
        self.patrol_speed = patrol_speed or CREATURE_SPEED_PATROL
        self.chase_speed = chase_speed or CREATURE_SPEED_CHASE
        self.detect_range = detect_range or CREATURE_DETECT_RANGE
        self.give_up_time = give_up_time  # frames before giving up chase

        # Behavior config
        self.behavior = behavior  # 'patrol', 'guard', 'wander'
        self.waypoints = waypoints or [(x, y)]
        self.waypoint_idx = 0
        self.waypoint_direction = 1  # 1 or -1 for ping-pong

        # State machine
        self.state = 'patrol'  # patrol, idle, alert, investigate, chase, return, forced_chase
        self.state_timer = 0

        # Investigation / chase memory
        self.last_seen_player = None
        self.last_seen_timer = 0
        self.investigate_target = None
        self.path = []  # A* path waypoints
        self.path_idx = 0

        # Forced chase (sound attraction)
        self.forced_target = None
        self.forced_timer = 0

        # Hit stun
        self.stun_timer = 0

        # Animation
        self.facing = 1  # 1 = right, -1 = left
        self.anim_frame = 0
        self.anim_timer = 0

        # Guard-specific
        self.guard_angle = 0
        self.guard_watch_speed = 0.02
        self.guard_arc = math.pi / 2  # 90 degree watch arc

        # Idle twitch
        self.twitch_timer = 0
        self.twitch_next = 120  # random twitch every ~2s

    # ------------------------------------------------------------------ #
    #  Core Movement (with wall collision)                               #
    # ------------------------------------------------------------------ #

    def _move(self, dx, dy, walls):
        """Move by (dx, dy) resolving wall collisions on each axis separately."""
        # X axis
        self.pos_x += dx
        self.rect.x = int(self.pos_x)
        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0:
                    self.rect.right = wall.left
                elif dx < 0:
                    self.rect.left = wall.right
                self.pos_x = float(self.rect.x)

        # Y axis
        self.pos_y += dy
        self.rect.y = int(self.pos_y)
        for wall in walls:
            if self.rect.colliderect(wall):
                if dy > 0:
                    self.rect.bottom = wall.top
                elif dy < 0:
                    self.rect.top = wall.bottom
                self.pos_y = float(self.rect.y)

    def _move_toward(self, target_x, target_y, speed, walls):
        """Move toward a point at given speed, with wall collision."""
        dx = target_x - self.pos_x
        dy = target_y - self.pos_y
        distance = math.sqrt(dx**2 + dy**2)

        if distance < 2:
            return True  # arrived

        move_x = (dx / distance) * speed
        move_y = (dy / distance) * speed
        self._move(move_x, move_y, walls)

        # Update facing
        if move_x > 0.1:
            self.facing = 1
        elif move_x < -0.1:
            self.facing = -1

        return False

    # ------------------------------------------------------------------ #
    #  State Behaviors                                                     #
    # ------------------------------------------------------------------ #

    def _do_patrol(self, walls):
        """Follow waypoints. Loop or ping-pong based on config."""
        if len(self.waypoints) <= 1:
            self.state = 'idle'
            return

        target = self.waypoints[self.waypoint_idx]
        arrived = self._move_toward(target[0], target[1], self.patrol_speed, walls)

        if arrived:
            self.waypoint_idx += self.waypoint_direction

            if self.waypoint_idx >= len(self.waypoints):
                self.waypoint_idx = len(self.waypoints) - 2
                self.waypoint_direction = -1
                if self.waypoint_idx < 0:
                    self.waypoint_idx = 0
                    self.waypoint_direction = 1
            elif self.waypoint_idx < 0:
                self.waypoint_idx = 1
                self.waypoint_direction = 1
                if self.waypoint_idx >= len(self.waypoints):
                    self.waypoint_idx = 0

    def _do_idle(self, walls):
        """Stand still, occasionally twitch."""
        self.twitch_timer += 1
        if self.twitch_timer >= self.twitch_next:
            self.twitch_timer = 0
            self.twitch_next = 60 + (pygame.time.get_ticks() % 120)  # 1-3s random
            # Small random jerk
            jerk_x = (pygame.time.get_ticks() % 3 - 1) * 2
            jerk_y = (pygame.time.get_ticks() % 5 - 2) * 1
            self._move(jerk_x, jerk_y, walls)

    def _do_guard(self, walls, player_rect):
        """Stand at post, sweep watch arc, react to LOS."""
        self.guard_angle += self.guard_watch_speed

        # Stay near guard post (first waypoint)
        post = self.waypoints[0] if self.waypoints else (self.pos_x, self.pos_y)
        dx = post[0] - self.pos_x
        dy = post[1] - self.pos_y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 20:
            self._move_toward(post[0], post[1], self.patrol_speed * 0.5, walls)

        # Check LOS in watch direction
        watch_x = math.cos(self.guard_angle) * self.detect_range
        watch_y = math.sin(self.guard_angle) * self.detect_range
        # Simplified: just use circular detection for now

    def _do_investigate(self, walls):
        """Go to investigate target, then return to patrol."""
        if self.investigate_target is None:
            self.state = 'return'
            return

        # Use A* path if we have one
        if self.path and self.path_idx < len(self.path):
            target = self.path[self.path_idx]
            arrived = self._move_toward(target[0], target[1], self.chase_speed * 0.8, walls)
            if arrived:
                self.path_idx += 1
        else:
            # Direct movement (may get stuck, but A* should handle most cases)
            arrived = self._move_toward(
                self.investigate_target[0], self.investigate_target[1],
                self.chase_speed * 0.8, walls
            )

        self.state_timer += 1
        if self.state_timer > self.give_up_time:
            self.state = 'return'
            self.path = []

    def _do_chase(self, player_rect, walls):
        """Chase player using A* pathfinding."""
        self.state_timer += 1

        # Update path periodically or if empty
        if not self.path or self.path_idx >= len(self.path) or self.state_timer % 30 == 0:
            self.path = astar_path(
                (self.pos_x, self.pos_y),
                (player_rect.centerx, player_rect.centery),
                walls
            )
            self.path_idx = 0

        if self.path and self.path_idx < len(self.path):
            target = self.path[self.path_idx]
            arrived = self._move_toward(target[0], target[1], self.chase_speed, walls)
            if arrived:
                self.path_idx += 1
        else:
            # Fallback: direct chase (will hug walls but better than nothing)
            self._move_toward(player_rect.centerx, player_rect.centery, self.chase_speed, walls)

        # Give up if chasing too long without seeing player
        if self.state_timer > self.give_up_time * 2:
            self.state = 'investigate'
            self.investigate_target = self.last_seen_player
            self.path = []

    def _do_return(self, walls):
        """Return to nearest patrol waypoint."""
        if not self.waypoints:
            self.state = 'idle'
            return

        # Find nearest waypoint
        nearest = min(self.waypoints, 
                     key=lambda w: (w[0]-self.pos_x)**2 + (w[1]-self.pos_y)**2)

        # A* path back
        if not self.path or self.path_idx >= len(self.path):
            self.path = astar_path((self.pos_x, self.pos_y), nearest, walls)
            self.path_idx = 0

        if self.path and self.path_idx < len(self.path):
            target = self.path[self.path_idx]
            arrived = self._move_toward(target[0], target[1], self.patrol_speed, walls)
            if arrived:
                self.path_idx += 1
        else:
            arrived = self._move_toward(nearest[0], nearest[1], self.patrol_speed, walls)

        if arrived or (abs(self.pos_x - nearest[0]) < 5 and abs(self.pos_y - nearest[1]) < 5):
            self.state = 'patrol'
            self.path = []
            # Set waypoint index to the one we returned to
            for i, w in enumerate(self.waypoints):
                if abs(w[0] - nearest[0]) < 5 and abs(w[1] - nearest[1]) < 5:
                    self.waypoint_idx = i
                    break

    def _do_forced_chase(self, walls):
        """Chase sound source (wrong keypad)."""
        self.forced_timer -= 1
        if self.forced_timer <= 0:
            self.state = 'investigate'
            self.investigate_target = self.forced_target
            self.forced_target = None
            self.path = []
            return

        # Direct chase toward sound — they rush recklessly
        self._move_toward(self.forced_target[0], self.forced_target[1], 
                         self.chase_speed * 1.2, walls)

    # ------------------------------------------------------------------ #
    #  Sensing                                                             #
    # ------------------------------------------------------------------ #

    def _can_see_player(self, player_rect, walls):
        """Line of sight check — raycast to player, blocked by walls."""
        dx = player_rect.centerx - self.pos_x
        dy = player_rect.centery - self.pos_y
        dist = math.sqrt(dx**2 + dy**2)

        if dist > self.detect_range:
            return False

        # Raycast from creature center to player center
        cx = self.pos_x + self.rect.width / 2
        cy = self.pos_y + self.rect.height / 2
        steps = int(dist / 8) + 1
        for i in range(1, steps):  # skip step 0 (creature's own position)
            t = i / steps
            rx = cx + dx * t
            ry = cy + dy * t
            test_rect = pygame.Rect(rx - 2, ry - 2, 4, 4)
            for wall in walls:
                if test_rect.colliderect(wall):
                    return False

        return True

    def _hear_player(self, player_rect, player_moving):
        """Can hear player if close enough and player is moving."""
        if not player_moving:
            return False
        dx = player_rect.centerx - self.pos_x
        dy = player_rect.centery - self.pos_y
        return math.sqrt(dx**2 + dy**2) < self.detect_range * 0.6

    # ------------------------------------------------------------------ #
    #  Update                                                              #
    # ------------------------------------------------------------------ #

    def update(self, current_freq, player_rect, walls=None, player_moving=False):
        if walls is None:
            walls = []

        # Not on our frequency — freeze in place (The Wired exist only on Freq 1)
        if current_freq != self.frequency:
            return

        # Stunned after hitting player — can't move or attack
        if self.stun_timer > 0:
            self.stun_timer -= 1
            # Still animate twitch while stunned
            self.anim_timer += 1
            if self.anim_timer > 10:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 4
            return

        # Forced chase takes absolute priority
        if self.forced_timer > 0 and self.forced_target:
            self.state = 'forced_chase'
        else:
            # Sensing
            can_see = self._can_see_player(player_rect, walls)
            can_hear = self._hear_player(player_rect, player_moving)

            if can_see:
                self.last_seen_player = (player_rect.centerx, player_rect.centery)
                self.last_seen_timer = 0
                if self.state not in ('chase', 'forced_chase'):
                    self.state = 'chase'
                    self.state_timer = 0
                    self.path = []
            elif can_hear and self.state not in ('chase', 'investigate', 'forced_chase'):
                self.state = 'investigate'
                self.investigate_target = (player_rect.centerx, player_rect.centery)
                self.state_timer = 0
                self.path = []
            elif self.state == 'chase' and not can_see:
                self.last_seen_timer += 1
                if self.last_seen_timer > 60:  # 1 second grace
                    self.state = 'investigate'
                    self.investigate_target = self.last_seen_player
                    self.state_timer = 0
                    self.path = []

        # Execute current state
        if self.state == 'patrol':
            self._do_patrol(walls)
        elif self.state == 'idle':
            self._do_idle(walls)
        elif self.state == 'guard':
            self._do_guard(walls, player_rect)
        elif self.state == 'investigate':
            self._do_investigate(walls)
        elif self.state == 'chase':
            self._do_chase(player_rect, walls)
        elif self.state == 'return':
            self._do_return(walls)
        elif self.state == 'forced_chase':
            self._do_forced_chase(walls)

        # Animation
        self.anim_timer += 1
        if self.anim_timer > 10:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4

    def force_chase_toward(self, x, y, duration):
        """Temporarily chase a specific point (sound attraction from wrong keypad)."""
        self.forced_target = (x, y)
        self.forced_timer = duration
        self.state = 'forced_chase'
        self.path = []

    def apply_stun(self, source_x, source_y, stun_duration, push_distance, walls):
        '''Stun creature and push it back from source.'''
        self.stun_timer = stun_duration
        self.state = 'idle'
        self.path = []

        # Push back
        dx = self.pos_x - source_x
        dy = self.pos_y - source_y
        dist = math.sqrt(dx**2 + dy**2) or 1
        push_x = (dx / dist) * push_distance
        push_y = (dy / dist) * push_distance

        # X axis with wall collision
        self.pos_x += push_x
        self.rect.x = int(self.pos_x)
        for wall in walls:
            if self.rect.colliderect(wall):
                if push_x > 0:
                    self.rect.right = wall.left
                elif push_x < 0:
                    self.rect.left = wall.right
                self.pos_x = float(self.rect.x)

        # Y axis with wall collision
        self.pos_y += push_y
        self.rect.y = int(self.pos_y)
        for wall in walls:
            if self.rect.colliderect(wall):
                if push_y > 0:
                    self.rect.bottom = wall.top
                elif push_y < 0:
                    self.rect.top = wall.bottom
                self.pos_y = float(self.rect.y)

    # ------------------------------------------------------------------ #
    #  Draw                                                                #
    # ------------------------------------------------------------------ #

    def draw(self, screen, current_freq):
        if current_freq != self.frequency:
            return

        tick = pygame.time.get_ticks()

        # State-based color
        if self.state == 'chase':
            base_color = (255, 60, 60)  # bright angry red
        elif self.state == 'investigate':
            base_color = (255, 120, 60)  # orange — suspicious
        elif self.state == 'forced_chase':
            base_color = (255, 200, 50)  # yellow — attracted by sound
        else:
            base_color = (180, 50, 50)  # dull red — patrol/idle

        # Electrical flicker
        flicker = (tick // 80) % 4 == 0
        if flicker:
            color = (min(255, base_color[0] + 40), min(255, base_color[1] + 30), base_color[2])
        else:
            color = base_color

        surf = pygame.Surface((28, 36), pygame.SRCALPHA)

        # Body — slightly hunched (The Wired are dead muscle)
        body_y = 10 if self.state in ('patrol', 'idle') else 8  # hunch when active
        pygame.draw.rect(surf, (*color, 220), (2, body_y, 20, 22))

        # Head
        head_y = 6 if self.state in ('patrol', 'idle') else 4
        pygame.draw.ellipse(surf, (*color, 220), (6, head_y, 12, 10))

        # Eyes — glow when chasing
        if self.state in ('chase', 'forced_chase'):
            eye_color = (255, 100, 100, 200)
            pygame.draw.circle(surf, eye_color, (10, head_y + 4), 2)
            pygame.draw.circle(surf, eye_color, (16, head_y + 4), 2)

        # Electrical sparks — more intense when active
        spark_intensity = 3 if self.state in ('chase', 'forced_chase') else 1
        if flicker:
            spark_color = (255, 255, 150, 180)
            for _ in range(spark_intensity):
                sx = 4 + (tick % 20)
                sy = 8 + (tick % 16)
                ex = sx + (tick % 6) - 3
                ey = sy + (tick % 6) - 3
                pygame.draw.line(surf, spark_color, (sx, sy), (ex, ey), 1)

        # State indicator (small icon above head)
        if self.stun_timer > 0:
            # Stunned — spiral/spark icon
            pygame.draw.circle(surf, (100, 100, 255, 180), (14, 2), 4)
            pygame.draw.circle(surf, (50, 50, 150, 180), (14, 2), 2)
        elif self.state == 'investigate':
            pygame.draw.circle(surf, (255, 200, 50, 150), (14, 2), 3)
        elif self.state == 'chase':
            pygame.draw.polygon(surf, (255, 50, 50, 150), 
                               [(14, 0), (18, 4), (10, 4)])

        # Flip if facing left
        if self.facing < 0:
            surf = pygame.transform.flip(surf, True, False)

        screen.blit(surf, (self.rect.x - 2, self.rect.y - 2))

        # Debug: draw path
        # if self.path and self.path_idx < len(self.path):
        #     for i in range(self.path_idx, len(self.path) - 1):
        #         pygame.draw.line(screen, (100, 100, 255), self.path[i], self.path[i+1], 1)