"""
Utility modules for Desktop Animation Tool.
"""

from .system_stats import SystemStats
from .screenshot import capture_desktop_screenshot_to_file, load_wallpaper_from_file
from .desktop import (
    is_wayland, is_x11, set_desktop_window_x11, 
    setup_desktop_window_pygame, get_desktop_wallpaper,
    load_wallpaper_or_fallback
)

__all__ = [
    'SystemStats',
    'capture_desktop_screenshot_to_file',
    'load_wallpaper_from_file',
    'is_wayland',
    'is_x11',
    'set_desktop_window_x11',
    'setup_desktop_window_pygame',
    'get_desktop_wallpaper',
    'load_wallpaper_or_fallback'
]
