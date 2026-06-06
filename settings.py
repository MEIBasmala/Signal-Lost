# is where ALL your constants live — screen size, speeds, colors, frequency definitions.


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60 
TITLE = "My Game"

# Colors (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREEN = (10 ,25 ,15)



# Frequency tints (R, G, B, Alpha)
FREQ_TINTS = {
    1: (20,  80,  40,  55),   # cold green — normal world
    2: (40,  20,  100, 70),   # deep purple — ghost layer
    3: (200, 200, 200, 80),   # harsh white static — danger zone
}



# Signal / Battery
BATTERY_MAX        = 100.0
BATTERY_DRAIN_F2   = 0.08   # per frame on frequency 2
BATTERY_DRAIN_F3   = 0.20   # per frame on frequency 3
BATTERY_REGEN_F1   = 0.03   # slowly recharges on frequency 1
BATTERY_LOW        = 25.0   # threshold for warning effects



# Player
PLAYER_SPEED       = 3
PLAYER_SIZE        = (24, 32)   # width, height in pixels
FREQ_SWITCH_COOLDOWN = 400      # milliseconds between switches

# World
TILE_SIZE = 32


# Creatures
CREATURE_SPEED_PATROL = 1.2
CREATURE_SPEED_CHASE  = 2.8
CREATURE_DETECT_RANGE = 160    # pixels
CREATURE_HIT_DRAIN    = 35.0   # battery lost on contact


# Hearts / Health
PLAYER_MAX_HEARTS = 5
INVINCIBILITY_DURATION = 120  # frames (2 seconds at 60fps)
HEART_SIZE = 20               # pixel size of each heart icon
HEART_PADDING = 8             # space between hearts


# Keypad
KEYPAD_RANGE = 40          # px to interact
KEYPAD_DIGITS = 4
KEYPAD_LOCKOUT_TIME = 2000  # ms after wrong guess
KEYPAD_SHAKE_DURATION = 15  # frames
KEYPAD_SHAKE_INTENSITY = 5  # px

# Narrative text
NARRATIVE_TYPE_SPEED = 2      # chars per frame
NARRATIVE_HOLD_TIME = 180     # frames (3s)
NARRATIVE_FADE_TIME = 60      # frames (1s)
