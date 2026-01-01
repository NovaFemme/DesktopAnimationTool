"""
Desktop and wallpaper utilities.
Handles wallpaper detection, desktop mode window setup, etc.
"""

import os
import platform
import subprocess
from pathlib import Path

import pygame
from PIL import Image

from .screenshot import load_wallpaper_from_file


def is_wayland():
    """Check if running under Wayland."""
    return os.environ.get('XDG_SESSION_TYPE') == 'wayland' or \
           os.environ.get('WAYLAND_DISPLAY') is not None


def is_x11():
    """Check if running under X11."""
    return os.environ.get('XDG_SESSION_TYPE') == 'x11' or \
           (os.environ.get('DISPLAY') is not None and not is_wayland())


def set_desktop_window_x11(window_id):
    """Set window type to desktop using xprop."""
    try:
        subprocess.run([
            'xprop', '-id', str(window_id),
            '-f', '_NET_WM_WINDOW_TYPE', '32a',
            '-set', '_NET_WM_WINDOW_TYPE', '_NET_WM_WINDOW_TYPE_DESKTOP'
        ], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return False


def setup_desktop_window_pygame():
    """Configure pygame window to act as desktop background."""
    os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '0'
    
    pygame.init()
    
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h
    
    screen = pygame.display.set_mode(
        (screen_width, screen_height),
        pygame.NOFRAME | pygame.DOUBLEBUF
    )
    
    pygame.display.set_caption("Desktop Animation Tool")
    
    try:
        window_info = pygame.display.get_wm_info()
        window_id = window_info.get('window')
        
        if window_id:
            set_desktop_window_x11(window_id)
            
            try:
                subprocess.run([
                    'xdotool', 'windowlower', str(window_id)
                ], capture_output=True)
            except FileNotFoundError:
                pass
            
            try:
                subprocess.run([
                    'xdotool', 'windowmove', str(window_id), '0', '0'
                ], capture_output=True)
            except FileNotFoundError:
                pass
    except Exception as e:
        print(f"Warning: Could not set desktop window properties: {e}")
    
    return screen, screen_width, screen_height


def get_desktop_wallpaper():
    """Get the current desktop wallpaper path based on OS."""
    system = platform.system()
    
    if system == "Windows":
        return get_windows_wallpaper()
    elif system == "Darwin":
        return get_macos_wallpaper()
    elif system == "Linux":
        return get_linux_wallpaper()
    else:
        raise OSError(f"Unsupported operating system: {system}")


def get_windows_wallpaper():
    """Get wallpaper path on Windows."""
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Control Panel\Desktop"
        )
        wallpaper_path, _ = winreg.QueryValueEx(key, "WallPaper")
        winreg.CloseKey(key)
        if wallpaper_path and os.path.exists(wallpaper_path):
            return wallpaper_path
    except:
        pass
    
    appdata = os.environ.get('APPDATA', '')
    wallpaper_path = os.path.join(
        appdata, 
        r"Microsoft\Windows\Themes\TranscodedWallpaper"
    )
    if os.path.exists(wallpaper_path):
        return wallpaper_path
    
    raise FileNotFoundError("Could not find Windows wallpaper")


def get_macos_wallpaper():
    """Get wallpaper path on macOS."""
    try:
        script = '''
        tell application "Finder"
            get POSIX path of (get desktop picture as alias)
        end tell
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True
        )
        path = result.stdout.strip()
        if path and os.path.exists(path):
            return path
    except:
        pass
    
    home = Path.home()
    possible_paths = [
        home / "Library/Application Support/Dock/desktoppicture.db",
        "/System/Library/Desktop Pictures/Sonoma.heic",
        "/System/Library/Desktop Pictures/Ventura.heic",
    ]
    
    for p in possible_paths:
        if p.exists():
            return str(p)
    
    raise FileNotFoundError("Could not find macOS wallpaper")


def get_linux_wallpaper():
    """Get wallpaper path on Linux (supports GNOME, Cinnamon, KDE, XFCE, etc.)."""
    # Try Cinnamon (Linux Mint)
    try:
        result = subprocess.run(
            ['gsettings', 'get', 'org.cinnamon.desktop.background', 'picture-uri'],
            capture_output=True, text=True
        )
        path = result.stdout.strip().strip("'\"")
        if path.startswith('file://'):
            path = path[7:]
        if path and os.path.exists(path):
            return path
    except:
        pass
    
    # Try MATE
    try:
        result = subprocess.run(
            ['gsettings', 'get', 'org.mate.background', 'picture-filename'],
            capture_output=True, text=True
        )
        path = result.stdout.strip().strip("'\"")
        if path and os.path.exists(path):
            return path
    except:
        pass
    
    # Try GNOME
    try:
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri'],
            capture_output=True, text=True
        )
        path = result.stdout.strip().strip("'\"")
        if path.startswith('file://'):
            path = path[7:]
        if path and os.path.exists(path):
            return path
    except:
        pass
    
    # Try GNOME dark variant
    try:
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri-dark'],
            capture_output=True, text=True
        )
        path = result.stdout.strip().strip("'\"")
        if path.startswith('file://'):
            path = path[7:]
        if path and os.path.exists(path):
            return path
    except:
        pass
    
    # Try KDE Plasma
    try:
        kde_config = Path.home() / ".config/plasma-org.kde.plasma.desktop-appletsrc"
        if kde_config.exists():
            with open(kde_config, 'r') as f:
                for line in f:
                    if 'Image=' in line:
                        path = line.split('=')[1].strip()
                        if path.startswith('file://'):
                            path = path[7:]
                        if os.path.exists(path):
                            return path
    except:
        pass
    
    # Try XFCE
    try:
        result = subprocess.run(
            ['xfconf-query', '-c', 'xfce4-desktop', '-p', 
             '/backdrop/screen0/monitor0/workspace0/last-image'],
            capture_output=True, text=True
        )
        path = result.stdout.strip()
        if path and os.path.exists(path):
            return path
    except:
        pass
    
    # Fallback: check common wallpaper directories
    home = Path.home()
    common_paths = [
        home / ".local/share/backgrounds",
        home / "Pictures/Wallpapers",
        Path("/usr/share/backgrounds"),
        Path("/usr/share/wallpapers"),
    ]
    
    for dir_path in common_paths:
        if dir_path.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                files = list(dir_path.glob(ext))
                if files:
                    return str(files[0])
    
    raise FileNotFoundError("Could not find Linux wallpaper")


def load_wallpaper_or_fallback(screen_size, screenshot_path=None):
    """Try to load wallpaper, create a gradient fallback if not found."""
    
    if screenshot_path and os.path.exists(screenshot_path):
        try:
            surface = load_wallpaper_from_file(screenshot_path, screen_size)
            os.unlink(screenshot_path)
            return surface
        except Exception as e:
            print(f"Failed to load screenshot: {e}")
    
    try:
        wallpaper_path = get_desktop_wallpaper()
        print(f"Found wallpaper: {wallpaper_path}")
        
        img = Image.open(wallpaper_path)
        img = img.convert('RGB')
        img = img.resize(screen_size, Image.Resampling.LANCZOS)
        
        return pygame.image.fromstring(img.tobytes(), img.size, 'RGB')
    
    except (FileNotFoundError, OSError, Exception) as e:
        print(f"Could not load wallpaper: {e}")
        print("Using gradient fallback...")
        
        surface = pygame.Surface(screen_size)
        for y in range(screen_size[1]):
            ratio = y / screen_size[1]
            r = int(25 + 50 * ratio)
            g = int(50 + 100 * (1 - ratio))
            b = int(100 + 155 * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (screen_size[0], y))
        
        return surface
