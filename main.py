#!/usr/bin/env python3
"""
Desktop Animation Tool
Entry point and main application class.
"""

import argparse
import json
import math
import os
import subprocess
import sys

import pygame

from config import FPS, FLIP_SPEED, DEFAULT_SQUARE_SIZE, MIN_SQUARE_SIZE, MAX_SQUARE_SIZE, DEFAULT_RESTART_INTERVAL, AVAILABLE_EFFECTS, STATS_CORNERS, DEFAULT_STATS_CORNER
from utils import SystemStats, capture_desktop_screenshot_to_file,load_wallpaper_or_fallback, setup_desktop_window_pygame
from effects import FlipTile, PolygonSelector, EyeEffect, HiddenEffect


# Global flip speed (can be modified)
_FLIP_SPEED = FLIP_SPEED

# Config file paths
EYES_CONFIG_FILE = os.path.expanduser("./eyes.cfg")
HIDDEN_CONFIG_FILE = os.path.expanduser("./hidden.cfg")


def save_polygon_config(filepath, polygon_data):
    """Save polygon data to a config file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(polygon_data, f, indent=2)
    print(f"Saved polygon configuration to: {filepath}")


def load_polygon_config(filepath):
    """Load polygon data from a config file."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            print(f"Loaded polygon configuration from: {filepath}")
            return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config file: {e}")
    return None


class DesktopAnimationTool:
    """Main application class for the desktop animation tool."""
    
    def __init__(self, square_size=DEFAULT_SQUARE_SIZE, fullscreen=True, desktop_mode=False, 
                 screenshot_path=None, restart_interval=DEFAULT_RESTART_INTERVAL, show_stats=False,
                 stats_corner=DEFAULT_STATS_CORNER, smooth_edges=True, effect_mode='flip',
                 reverse=False, eye_pos=None, polygon_data=None):
        
        self.square_size = square_size
        self.fullscreen = fullscreen
        self.desktop_mode = desktop_mode
        self.restart_interval = restart_interval
        self.smooth_edges = smooth_edges
        self.effect_mode = effect_mode
        self.reverse = reverse
        self.eye_pos = eye_pos
        self.polygon_data = polygon_data
        self.stats_corner = stats_corner
        
        # Initialize display
        if desktop_mode:
            self.screen, self.screen_width, self.screen_height = setup_desktop_window_pygame()
        else:
            pygame.init()
            info = pygame.display.Info()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            
            flags = pygame.DOUBLEBUF
            if fullscreen:
                flags |= pygame.FULLSCREEN
            
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height), flags
            )
        
        pygame.display.set_caption("Desktop Animation Tool")
        self.clock = pygame.time.Clock()
        
        # Load wallpaper/screenshot
        self.wallpaper = load_wallpaper_or_fallback(
            (self.screen_width, self.screen_height),
            screenshot_path
        )
        
        # Initialize effects
        self.eye_effect = None
        self.hidden_effect = None
        self.tiles = []
        
        self._init_effects(show_stats)
        
        self.running = True
        self.all_complete = False
        self.complete_time = None
    
    def _init_effects(self, show_stats):
        """Initialize the appropriate effect based on mode."""
        if self.effect_mode == 'eyes':
            self.eye_effect = EyeEffect(
                self.wallpaper, self.screen_width, self.screen_height,
                manual_eye_pos=self.eye_pos,
                polygon_data=self.polygon_data
            )
            if len(self.eye_effect.eyes) == 0:
                print("No eyes detected. Falling back to flip effect.")
                self.effect_mode = 'flip'
                self.eye_effect = None
        
        elif self.effect_mode == 'hidden':
            if self.polygon_data:
                self.hidden_effect = HiddenEffect(
                    self.wallpaper, self.screen_width, self.screen_height,
                    polygon_data=self.polygon_data
                )
            else:
                print("No regions selected. Falling back to flip effect.")
                self.effect_mode = 'flip'
        
        if self.effect_mode in ('flip', 'ripple'):
            self.tiles = self._create_tiles()
        
        self.system_stats = SystemStats(corner=self.stats_corner) if show_stats else None
    
    def _create_tiles(self):
        """Create flip tiles for the animation."""
        tiles = []
        
        cols = math.ceil(self.screen_width / self.square_size)
        rows = math.ceil(self.screen_height / self.square_size)
        
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        for row in range(rows):
            for col in range(cols):
                x = col * self.square_size
                y = row * self.square_size
                
                tile_center_x = x + self.square_size // 2
                tile_center_y = y + self.square_size // 2
                
                dist = math.sqrt(
                    (tile_center_x - center_x)**2 + 
                    (tile_center_y - center_y)**2
                )
                
                if self.effect_mode == 'ripple':
                    normalized_dist = dist / max_dist
                    ring = int(normalized_dist * 10)
                    delay = ring * 8 + (hash((col, row)) % 5)
                else:
                    normalized_dist = dist / max_dist
                    delay = int(normalized_dist * 60)
                
                if self.reverse:
                    max_delay = 60
                    delay = max_delay - delay
                    delay = max(0, delay)
                
                tile = FlipTile(
                    self.wallpaper, x, y, self.square_size, delay,
                    edge_softness=6 if self.smooth_edges else 0,
                    reverse=self.reverse
                )
                tiles.append(tile)
        
        return tiles
    
    def _restart_animation(self):
        """Restart the animation."""
        if self.effect_mode == 'eyes' and self.eye_effect:
            self.eye_effect.restart()
        elif self.effect_mode == 'hidden' and self.hidden_effect:
            self.hidden_effect.restart()
        else:
            self.tiles = self._create_tiles()
        self.all_complete = False
        self.complete_time = None
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self._restart_animation()
                elif event.key == pygame.K_UP:
                    self.square_size = min(MAX_SQUARE_SIZE, self.square_size + 10)
                    self._restart_animation()
                elif event.key == pygame.K_DOWN:
                    self.square_size = max(MIN_SQUARE_SIZE, self.square_size - 10)
                    self._restart_animation()
    
    def update(self):
        """Update the animation."""
        if self.effect_mode == 'eyes' and self.eye_effect:
            self.eye_effect.update()
            if self.eye_effect.is_complete and not self.all_complete:
                self.all_complete = True
                self.complete_time = pygame.time.get_ticks()
        
        elif self.effect_mode == 'hidden' and self.hidden_effect:
            self.hidden_effect.update()
            if self.hidden_effect.is_complete and not self.all_complete:
                self.all_complete = True
                self.complete_time = pygame.time.get_ticks()
        
        else:
            all_done = all(tile.is_complete for tile in self.tiles)
            all_lines_done = all(
                (tile.line_alpha >= 255 if self.reverse else tile.line_alpha <= 0)
                for tile in self.tiles
            )
            
            for tile in self.tiles:
                tile.update()
            
            if all_done and all_lines_done and not self.all_complete:
                self.all_complete = True
                self.complete_time = pygame.time.get_ticks()
        
        # Auto-restart
        if self.all_complete and self.restart_interval > 0 and self.complete_time:
            elapsed = (pygame.time.get_ticks() - self.complete_time) / 1000.0
            if elapsed >= self.restart_interval:
                self._restart_animation()
    
    def draw(self):
        """Draw the current frame."""
        self.screen.fill((0, 0, 0))
        
        if self.effect_mode == 'eyes' and self.eye_effect:
            self.eye_effect.draw(self.screen)
        elif self.effect_mode == 'hidden' and self.hidden_effect:
            self.hidden_effect.draw(self.screen)
        else:
            for tile in self.tiles:
                tile.draw(self.screen, use_soft_edges=self.smooth_edges)
            for tile in self.tiles:
                tile.draw_lines(self.screen)
        
        if self.system_stats:
            self.system_stats.update()
            self.system_stats.draw(self.screen)
        
        if not self.all_complete and not self.desktop_mode:
            font = pygame.font.Font(None, 24)
            if self.effect_mode in ('eyes', 'hidden'):
                instructions = "ESC: Exit | SPACE: Restart"
            else:
                instructions = "ESC: Exit | SPACE: Restart | UP/DOWN: Change tile size"
            text = font.render(instructions, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen_width // 2, 20))
            shadow = font.render(instructions, True, (0, 0, 0))
            self.screen.blit(shadow, (text_rect.x + 1, text_rect.y + 1))
            self.screen.blit(text, text_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Main loop."""
        print("\n" + "="*50)
        print("Desktop Animation Tool")
        print("="*50)
        print(f"Effect: {self.effect_mode.upper()}")
        print("Controls: ESC=Exit, SPACE=Restart")
        print("="*50 + "\n")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


def main():
    """Entry point."""
    global _FLIP_SPEED
    
    parser = argparse.ArgumentParser(description='Desktop Animation Tool')
    
    parser.add_argument('-s', '--size', type=int, default=DEFAULT_SQUARE_SIZE,
                        help=f'Size of tiles (default: {DEFAULT_SQUARE_SIZE})')
    parser.add_argument('-w', '--windowed', action='store_true',
                        help='Run in windowed mode')
    parser.add_argument('-d', '--desktop', action='store_true',
                        help='Run as desktop background (X11 only)')
    parser.add_argument('-c', '--capture', action='store_true',
                        help='Capture current desktop screenshot')
    parser.add_argument('-r', '--restart', type=float, default=DEFAULT_RESTART_INTERVAL,
                        help='Auto-restart interval in seconds (0=disabled)')
    parser.add_argument('-u', '--usage', action='store_true',
                        help='Show system stats')
    parser.add_argument('--stats-corner', type=str, default=DEFAULT_STATS_CORNER,
                        choices=STATS_CORNERS, help='Corner for stats display')
    parser.add_argument('--speed', type=float, default=FLIP_SPEED,
                        help=f'Flip animation speed (default: {FLIP_SPEED})')
    parser.add_argument('--no-smooth', action='store_true',
                        help='Disable smooth tile edges')
    parser.add_argument('-e', '--effect', type=str, default='flip',
                        choices=AVAILABLE_EFFECTS,
                        help='Animation effect to use')
    parser.add_argument('--eye-pos', type=str, default=None,
                        help='Manual eye positions: "x1,y1,w1,h1;x2,y2,w2,h2"')
    parser.add_argument('--select-eyes', action='store_true',
                        help='Interactive eye selection (saves to eyes.cfg)')
    parser.add_argument('--select-objects', action='store_true',
                        help='Interactive object selection for hidden/clone (saves to hidden.cfg)')
    parser.add_argument('--reverse', action='store_true',
                        help='Reverse animation direction')
    
    args = parser.parse_args()
    
    _FLIP_SPEED = args.speed
    
    # Capture screenshot before pygame starts
    screenshot_path = None
    if args.capture:
        print("Capturing desktop screenshot...")
        screenshot_path = capture_desktop_screenshot_to_file()
        if screenshot_path:
            print(f"Screenshot saved to: {screenshot_path}")
        else:
            print("Screenshot capture failed!")
    
    # Handle interactive selection modes
    polygon_data = None
    
    # EYES EFFECT
    if args.effect == 'eyes':
        if args.select_eyes:
            # Interactive selection mode - select and save
            print("\nStarting interactive eye selection...")
            try:
                selector = PolygonSelector(image_path=screenshot_path, mode='eyes')
                polygon_data = selector.run()
                
                if polygon_data is None or len(polygon_data) == 0:
                    print("No eyes selected. Exiting.")
                    if screenshot_path and os.path.exists(screenshot_path):
                        os.unlink(screenshot_path)
                    sys.exit(0)
                
                # Save to config file
                save_polygon_config(EYES_CONFIG_FILE, polygon_data)
                
            except Exception as e:
                print(f"Error in eye selection: {e}")
                if screenshot_path and os.path.exists(screenshot_path):
                    os.unlink(screenshot_path)
                sys.exit(1)
        else:
            # Try to load from config file
            polygon_data = load_polygon_config(EYES_CONFIG_FILE)
            if polygon_data is None:
                print(f"No saved eye configuration found at {EYES_CONFIG_FILE}")
                print("Use --select-eyes to select eye regions first.")
                if screenshot_path and os.path.exists(screenshot_path):
                    os.unlink(screenshot_path)
                sys.exit(1)
    
    # HIDDEN EFFECT
    if args.effect == 'hidden':
        if args.select_objects:
            # Interactive selection mode - select and save
            print("\nStarting hidden region selection...")
            try:
                selector = PolygonSelector(image_path=screenshot_path, mode='hidden')
                polygon_data = selector.run()
                
                if polygon_data is None or len(polygon_data) == 0:
                    print("No regions selected. Exiting.")
                    if screenshot_path and os.path.exists(screenshot_path):
                        os.unlink(screenshot_path)
                    sys.exit(0)
                
                # Save to config file
                save_polygon_config(HIDDEN_CONFIG_FILE, polygon_data)
                
            except Exception as e:
                print(f"Error in region selection: {e}")
                if screenshot_path and os.path.exists(screenshot_path):
                    os.unlink(screenshot_path)
                sys.exit(1)
        else:
            # Try to load from config file
            polygon_data = load_polygon_config(HIDDEN_CONFIG_FILE)
            if polygon_data is None:
                print(f"No saved hidden configuration found at {HIDDEN_CONFIG_FILE}")
                print("Use --select-objects to select regions first.")
                if screenshot_path and os.path.exists(screenshot_path):
                    os.unlink(screenshot_path)
                sys.exit(1)
    
    # CLONE EFFECT
    if args.effect == 'clone':
        if args.select_objects:
            # Interactive selection mode - select and save
            print("\nStarting clone region selection...")
            try:
                selector = PolygonSelector(image_path=screenshot_path, mode='hidden_clone')
                polygon_data = selector.run()
                
                if polygon_data is None or len(polygon_data) == 0:
                    print("No regions selected. Exiting.")
                    if screenshot_path and os.path.exists(screenshot_path):
                        os.unlink(screenshot_path)
                    sys.exit(0)
                
                # Save to config file (same as hidden)
                save_polygon_config(HIDDEN_CONFIG_FILE, polygon_data)
                
            except Exception as e:
                print(f"Error in region selection: {e}")
                if screenshot_path and os.path.exists(screenshot_path):
                    os.unlink(screenshot_path)
                sys.exit(1)
        else:
            # Try to load from config file
            polygon_data = load_polygon_config(HIDDEN_CONFIG_FILE)
            if polygon_data is None:
                print(f"No saved clone configuration found at {HIDDEN_CONFIG_FILE}")
                print("Use --select-objects to select regions first.")
                if screenshot_path and os.path.exists(screenshot_path):
                    os.unlink(screenshot_path)
                sys.exit(1)
        
        args.effect = 'hidden'  # Clone uses hidden effect internally
    
    try:
        app = DesktopAnimationTool(
            square_size=args.size,
            fullscreen=not args.windowed,
            desktop_mode=args.desktop,
            screenshot_path=screenshot_path,
            restart_interval=args.restart,
            show_stats=args.usage,
            stats_corner=args.stats_corner,
            smooth_edges=not args.no_smooth,
            effect_mode=args.effect,
            reverse=args.reverse,
            eye_pos=args.eye_pos,
            polygon_data=polygon_data
        )
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
    finally:
        if screenshot_path and os.path.exists(screenshot_path):
            os.unlink(screenshot_path)


if __name__ == "__main__":
    main()
