"""
Screenshot capture utilities.
"""

import os
import subprocess
import tempfile

import pygame
from PIL import Image


def capture_desktop_screenshot_to_file():
    """Capture the actual desktop to a temp file BEFORE pygame starts."""
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    # Method 1: Use scrot
    try:
        result = subprocess.run(
            ['scrot', '-o', temp_path],
            capture_output=True, timeout=5
        )
        if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            print("Captured desktop using scrot")
            return temp_path
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"scrot failed: {e}")
    
    # Method 2: Use import from ImageMagick
    try:
        result = subprocess.run(
            ['import', '-window', 'root', temp_path],
            capture_output=True, timeout=5
        )
        if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            print("Captured desktop using ImageMagick")
            return temp_path
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"ImageMagick failed: {e}")
    
    # Method 3: Use gnome-screenshot
    try:
        result = subprocess.run(
            ['gnome-screenshot', '-f', temp_path],
            capture_output=True, timeout=5
        )
        if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            print("Captured desktop using gnome-screenshot")
            return temp_path
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"gnome-screenshot failed: {e}")
    
    # Method 4: Use maim
    try:
        result = subprocess.run(
            ['maim', temp_path],
            capture_output=True, timeout=5
        )
        if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            print("Captured desktop using maim")
            return temp_path
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"maim failed: {e}")
    
    # Clean up if all failed
    if os.path.exists(temp_path):
        os.unlink(temp_path)
    
    return None


def load_wallpaper_from_file(filepath, screen_size):
    """Load wallpaper from a file path and convert to pygame surface."""
    img = Image.open(filepath)
    img = img.convert('RGB')
    img = img.resize(screen_size, Image.Resampling.LANCZOS)
    return pygame.image.fromstring(img.tobytes(), img.size, 'RGB')
