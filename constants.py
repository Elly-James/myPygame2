# constants.py
# Screen dimensions
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_CX = SCREEN_WIDTH // 2
SCREEN_CY = SCREEN_HEIGHT // 2

# Game states
STATE_INIT = 1
STATE_RESTART = 2
STATE_PLAY = 3
STATE_GAMEOVER = 4
STATE_WON = 5
STATE_PAUSED = 6

# Colors
COLORS = {
    'LIGHT': {'road': (136, 136, 136), 'grass': (66, 147, 82), 'rumble': (184, 49, 46)},
    'DARK': {'road': (102, 102, 102), 'grass': (57, 125, 70), 'rumble': (221, 221, 221), 'lane': (255, 255, 255)}
}

# Road parameters
SEGMENT_LENGTH = 100
ROAD_WIDTH = 1000
RUMBLE_SEGMENTS = 5
ROAD_LANES = 3
VISIBLE_SEGMENTS = 200

# Object types
OBJ_CAR = 0
OBJ_TRUCK = 1
OBJ_BILLBOARD = 2
OBJ_TREE = 3
OBJ_SIGN = 4