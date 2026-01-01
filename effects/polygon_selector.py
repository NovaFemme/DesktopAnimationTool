"""
Interactive polygon selector for defining regions.
Used for eye selection, hidden regions, and clone mode.
"""

import os

import pygame

from utils.screenshot import capture_desktop_screenshot_to_file
from config import SELECTOR_MAX_WIDTH, SELECTOR_MAX_HEIGHT


class PolygonSelector:
    """Interactive tool to select regions using polygon points."""
    
    def __init__(self, image_path=None, mode='eyes'):
        """
        Initialize the polygon selector.
        
        Args:
            image_path: Path to image file, or None to capture desktop
            mode: 'eyes', 'hidden', or 'hidden_clone'
        """
        pygame.init()
        
        self.mode = mode
        
        # Load the image
        if image_path and os.path.exists(image_path):
            self.original = pygame.image.load(image_path)
        else:
            print("Capturing desktop for selection...")
            screenshot_path = capture_desktop_screenshot_to_file()
            if screenshot_path:
                self.original = pygame.image.load(screenshot_path)
                os.unlink(screenshot_path)
            else:
                raise ValueError("No image provided and couldn't capture desktop")
        
        self.img_width = self.original.get_width()
        self.img_height = self.original.get_height()
        
        # Scale if too large
        self.scale = 1.0
        if self.img_width > SELECTOR_MAX_WIDTH or self.img_height > SELECTOR_MAX_HEIGHT:
            self.scale = min(SELECTOR_MAX_WIDTH / self.img_width, 
                           SELECTOR_MAX_HEIGHT / self.img_height)
            self.screen_width = int(self.img_width * self.scale)
            self.screen_height = int(self.img_height * self.scale)
            self.display_image = pygame.transform.smoothscale(
                self.original, (self.screen_width, self.screen_height)
            )
        else:
            self.screen_width = self.img_width
            self.screen_height = self.img_height
            self.display_image = self.original
        
        title = "Eye Polygon Selector" if mode == 'eyes' else "Hidden Region Selector"
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(title)
        
        # Polygon data
        self.polygons = []
        self.source_polygons = []
        self.current_polygon = []
        self.current_region = 1
        
        # Clone mode state
        self.selecting_source = False
        self.current_target_polygon = None
        
        # Colors
        if mode == 'eyes':
            self.colors = [(0, 255, 0), (0, 200, 255)]
        elif mode == 'hidden_clone':
            self.target_color = (255, 100, 100)
            self.source_color = (100, 255, 100)
            self.colors = [self.target_color]
        else:
            self.colors = [(255, 100, 100), (255, 150, 50), (255, 200, 100)]
        
        self.running = True
        self.saved = False
        self.clock = pygame.time.Clock()
    
    def run(self):
        """Run the polygon selector interface."""
        print("\n" + "="*60)
        if self.mode == 'eyes':
            print("EYE POLYGON SELECTOR")
        elif self.mode == 'hidden_clone':
            print("HIDDEN REGION SELECTOR (Clone Mode)")
            print("Select area to HIDE, then select SOURCE to clone from")
        else:
            print("HIDDEN REGION SELECTOR")
        print("="*60)
        print("Instructions:")
        print("  LEFT CLICK  - Add a point to current polygon")
        print("  RIGHT CLICK - Complete current region and start next")
        print("  BACKSPACE   - Remove last point")
        print("  ENTER       - Save polygons and start")
        print("  ESC         - Cancel and exit")
        if self.mode == 'hidden_clone':
            print("\nClone Mode: After completing target area (RED),")
            print("            select source area (GREEN) to sample from")
        print("="*60 + "\n")
        
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(60)
        
        pygame.quit()
        
        if self.saved and len(self.polygons) > 0:
            return self._get_polygon_data()
        return None
    
    def _handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                elif event.key == pygame.K_RETURN:
                    if len(self.current_polygon) >= 3:
                        if self.mode == 'hidden_clone' and self.selecting_source:
                            self.source_polygons.append(self.current_polygon.copy())
                            print("Source region completed")
                            self.selecting_source = False
                        else:
                            self.polygons.append(self.current_polygon.copy())
                    
                    if len(self.polygons) > 0:
                        if self.mode == 'hidden_clone' and len(self.source_polygons) < len(self.polygons):
                            print(f"Warning: {len(self.polygons)} targets but only {len(self.source_polygons)} sources")
                            print("Some regions will use standard inpainting")
                        self.saved = True
                        print(f"Saved {len(self.polygons)} region(s)")
                    else:
                        print("No regions defined!")
                    self.running = False
                
                elif event.key == pygame.K_BACKSPACE:
                    if len(self.current_polygon) > 0:
                        self.current_polygon.pop()
                        print(f"Removed point. {len(self.current_polygon)} points remaining.")
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                
                if event.button == 1:  # Left click
                    self.current_polygon.append((x, y))
                    if self.mode == 'hidden_clone':
                        if self.selecting_source:
                            print(f"Source: Added point ({x}, {y}) - {len(self.current_polygon)} points")
                        else:
                            print(f"Target {self.current_region}: Added point ({x}, {y}) - {len(self.current_polygon)} points")
                    else:
                        region_name = f"Eye {self.current_region}" if self.mode == 'eyes' else f"Region {self.current_region}"
                        print(f"{region_name}: Added point ({x}, {y}) - {len(self.current_polygon)} points")
                
                elif event.button == 3:  # Right click
                    if len(self.current_polygon) >= 3:
                        if self.mode == 'hidden_clone':
                            if self.selecting_source:
                                self.source_polygons.append(self.current_polygon.copy())
                                print("Source region completed. Now select next target or press ENTER.")
                                self.selecting_source = False
                                self.current_polygon = []
                                self.current_region += 1
                            else:
                                self.polygons.append(self.current_polygon.copy())
                                print(f"Target {self.current_region} completed. Now select SOURCE area to clone from.")
                                self.current_target_polygon = self.current_polygon.copy()
                                self.current_polygon = []
                                self.selecting_source = True
                        else:
                            self.polygons.append(self.current_polygon.copy())
                            region_name = f"Eye {self.current_region}" if self.mode == 'eyes' else f"Region {self.current_region}"
                            print(f"{region_name} completed with {len(self.current_polygon)} points")
                            self.current_polygon = []
                            self.current_region += 1
                            
                            if self.mode == 'eyes' and self.current_region > 2:
                                print("Both eyes defined! Press ENTER to save or continue adding more.")
                            elif self.mode == 'hidden':
                                print("Region complete! Add more regions or press ENTER to apply.")
                    else:
                        print("Need at least 3 points to complete a region")
    
    def _draw(self):
        """Draw the current state."""
        self.screen.blit(self.display_image, (0, 0))
        
        # Draw completed polygons
        if self.mode == 'hidden_clone':
            for polygon in self.polygons:
                color = self.target_color
                if len(polygon) >= 3:
                    poly_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
                    pygame.draw.polygon(poly_surface, (*color, 80), polygon)
                    self.screen.blit(poly_surface, (0, 0))
                    pygame.draw.polygon(self.screen, color, polygon, 2)
                for point in polygon:
                    pygame.draw.circle(self.screen, color, point, 4)
            
            for polygon in self.source_polygons:
                color = self.source_color
                if len(polygon) >= 3:
                    poly_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
                    pygame.draw.polygon(poly_surface, (*color, 80), polygon)
                    self.screen.blit(poly_surface, (0, 0))
                    pygame.draw.polygon(self.screen, color, polygon, 2)
                for point in polygon:
                    pygame.draw.circle(self.screen, color, point, 4)
        else:
            for i, polygon in enumerate(self.polygons):
                color = self.colors[i % len(self.colors)]
                if len(polygon) >= 3:
                    poly_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
                    pygame.draw.polygon(poly_surface, (*color, 80), polygon)
                    self.screen.blit(poly_surface, (0, 0))
                    pygame.draw.polygon(self.screen, color, polygon, 2)
                for point in polygon:
                    pygame.draw.circle(self.screen, color, point, 4)
        
        # Draw current polygon
        if len(self.current_polygon) > 0:
            if self.mode == 'hidden_clone':
                color = self.source_color if self.selecting_source else self.target_color
            else:
                color = self.colors[(self.current_region - 1) % len(self.colors)]
            
            if len(self.current_polygon) >= 2:
                pygame.draw.lines(self.screen, color, False, self.current_polygon, 2)
            
            mouse_pos = pygame.mouse.get_pos()
            pygame.draw.line(self.screen, color, self.current_polygon[-1], mouse_pos, 1)
            
            for point in self.current_polygon:
                pygame.draw.circle(self.screen, color, point, 5)
                pygame.draw.circle(self.screen, (255, 255, 255), point, 3)
        
        # Draw instructions
        font = pygame.font.Font(None, 28)
        if self.mode == 'eyes':
            region_label = f"Defining Eye {self.current_region}"
        elif self.mode == 'hidden_clone':
            if self.selecting_source:
                region_label = "Select SOURCE area (green) - what to clone"
            else:
                region_label = f"Select TARGET {self.current_region} (red) - what to hide"
        else:
            region_label = f"Defining Region {self.current_region} (to hide)"
        
        if self.current_polygon:
            region_label += f" ({len(self.current_polygon)} points)"
        
        instructions = [
            region_label,
            "LEFT CLICK: Add point | RIGHT CLICK: Complete | ENTER: Save | ESC: Cancel"
        ]
        
        for i, text in enumerate(instructions):
            shadow = font.render(text, True, (0, 0, 0))
            self.screen.blit(shadow, (11, 11 + i * 25))
            rendered = font.render(text, True, (255, 255, 255))
            self.screen.blit(rendered, (10, 10 + i * 25))
        
        if len(self.polygons) > 0:
            if self.mode == 'hidden_clone':
                status = f"Targets: {len(self.polygons)} | Sources: {len(self.source_polygons)}"
            else:
                label = "eye(s)" if self.mode == 'eyes' else "region(s) to hide"
                status = f"Completed: {len(self.polygons)} {label}"
            status_text = font.render(status, True, (0, 255, 0))
            self.screen.blit(status_text, (10, self.screen_height - 30))
        
        pygame.display.flip()
    
    def _get_polygon_data(self):
        """Convert polygons to data format with scaled coordinates."""
        polygon_data = []
        positions = []
        
        for i, polygon in enumerate(self.polygons):
            if len(polygon) >= 3:
                scaled_polygon = []
                for x, y in polygon:
                    orig_x = int(x / self.scale)
                    orig_y = int(y / self.scale)
                    scaled_polygon.append((orig_x, orig_y))
                
                xs = [p[0] for p in scaled_polygon]
                ys = [p[1] for p in scaled_polygon]
                x = min(xs)
                y = min(ys)
                w = max(xs) - x
                h = max(ys) - y
                
                positions.append(f"{x},{y},{w},{h}")
                
                data = {
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'polygon': scaled_polygon,
                    'center_x': x + w // 2,
                    'center_y': y + h // 2
                }
                
                if self.mode == 'hidden_clone' and i < len(self.source_polygons):
                    source_polygon = self.source_polygons[i]
                    scaled_source = []
                    for sx, sy in source_polygon:
                        scaled_source.append((int(sx / self.scale), int(sy / self.scale)))
                    data['source_polygon'] = scaled_source
                    
                    sxs = [p[0] for p in scaled_source]
                    sys_list = [p[1] for p in scaled_source]
                    data['source_x'] = min(sxs)
                    data['source_y'] = min(sys_list)
                    data['source_w'] = max(sxs) - min(sxs)
                    data['source_h'] = max(sys_list) - min(sys_list)
                
                polygon_data.append(data)
        
        if self.mode == 'eyes':
            pos_string = ';'.join(positions)
            print(f"\nEye positions: --eye-pos '{pos_string}'")
            print("(You can use this command next time to skip the selection step)")
        
        return polygon_data
