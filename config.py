"""
Configuration and constants for Desktop Animation Tool.
"""

# Animation settings
FPS = 60
FLIP_SPEED = 5.0  # Can be modified at runtime

# Default tile settings
DEFAULT_SQUARE_SIZE = 80
MIN_SQUARE_SIZE = 20
MAX_SQUARE_SIZE = 200

# Animation timing
DEFAULT_RESTART_INTERVAL = 0  # 0 = no auto-restart

# Effect modes
EFFECT_FLIP = 'flip'
EFFECT_RIPPLE = 'ripple'
EFFECT_EYES = 'eyes'
EFFECT_HIDDEN = 'hidden'
EFFECT_CLONE = 'clone'

AVAILABLE_EFFECTS = [EFFECT_FLIP, EFFECT_RIPPLE, EFFECT_EYES, EFFECT_HIDDEN, EFFECT_CLONE]

# Stats display corners
STATS_CORNERS = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
DEFAULT_STATS_CORNER = 'bottom-right'

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (128, 128, 128)
COLOR_RED = (255, 100, 100)
COLOR_GREEN = (100, 255, 100)
COLOR_CYAN = (0, 200, 255)

# Eye detection settings
EYE_PUPIL_SCALE = 0.7  # Inner 70% of eye region moves
EYE_BLEND_START = 0.7  # Blending begins at 70% radius

# Hidden effect settings
INPAINT_RADIUS = 8
FEATHER_BLUR_SIZE = 15

# Polygon selector settings
SELECTOR_MAX_WIDTH = 1600
SELECTOR_MAX_HEIGHT = 900
