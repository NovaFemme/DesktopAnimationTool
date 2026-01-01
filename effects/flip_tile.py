"""
Flip tile animation effect.
Creates 3D flipping tile animations.
"""

import math
import random

import pygame

from config import FLIP_SPEED, FPS


# Line fade speed (how fast cut lines fade out)
LINE_FADE_SPEED = 5


class FlipTile:
    """Represents a single flipping tile of the puzzle with smooth edges."""
    
    def __init__(self, original_image, x, y, size, delay, edge_softness=6, reverse=False):
        self.x = x
        self.y = y
        self.size = size
        self.delay = delay
        self.edge_softness = edge_softness
        self.reverse = reverse
        
        # Extract this tile's portion of the image with alpha support
        self.original_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        self.original_surface.blit(original_image, (0, 0), (x, y, size, size))
        
        # Create soft-edged version for smooth blending
        self.original_soft = self._create_soft_edge_surface(self.original_surface)
        
        # Animation state
        self.flip_angle = 0
        self.target_flips = random.randint(1, 4)
        self.total_rotation = self.target_flips * 180
        self.flip_direction = random.choice(['horizontal', 'vertical'])
        self.flip_speed = FLIP_SPEED + random.uniform(-2, 2)
        
        self.is_animating = False
        self.is_complete = False
        self.current_delay = delay
        
        self.line_alpha = 255 if not reverse else 0
        
        self._precompute_flip_states()
    
    def _create_soft_edge_surface(self, surface):
        """Create a surface with soft, feathered edges for smooth blending."""
        size = surface.get_width()
        soft_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        soft_surface.blit(surface, (0, 0))
        
        edge = self.edge_softness
        if edge <= 0:
            return soft_surface
        
        alpha_mask = pygame.Surface((size, size), pygame.SRCALPHA)
        alpha_mask.fill((255, 255, 255, 255))
        
        for i in range(edge):
            alpha = int(255 * ((i + 1) / edge) ** 0.6)
            rect = pygame.Rect(i, i, size - 2*i, size - 2*i)
            if rect.width > 0 and rect.height > 0:
                pygame.draw.rect(alpha_mask, (255, 255, 255, alpha), rect, 1)
        
        for y in range(size):
            for x in range(size):
                dist_from_edge = min(x, y, size - 1 - x, size - 1 - y)
                if dist_from_edge < edge:
                    pixel = soft_surface.get_at((x, y))
                    edge_alpha = int(255 * (dist_from_edge / edge) ** 0.6)
                    new_alpha = min(pixel[3], edge_alpha)
                    soft_surface.set_at((x, y), (pixel[0], pixel[1], pixel[2], new_alpha))
        
        return soft_surface
    
    def _precompute_flip_states(self):
        """Pre-compute all the surfaces needed for the flip animation."""
        self.flip_surfaces = []
        self.flip_surfaces_soft = []
        
        current = self.original_surface.copy()
        current_soft = self.original_soft.copy()
        
        # Apply random flips to create scrambled state
        if random.choice([True, False]):
            current = pygame.transform.flip(current, True, False)
            current_soft = pygame.transform.flip(current_soft, True, False)
        if random.choice([True, False]):
            current = pygame.transform.flip(current, False, True)
            current_soft = pygame.transform.flip(current_soft, False, True)
        
        self.flip_surfaces.append(current)
        self.flip_surfaces_soft.append(current_soft)
        
        for i in range(self.target_flips):
            if self.flip_direction == 'horizontal':
                current = pygame.transform.flip(current, True, False)
                current_soft = pygame.transform.flip(current_soft, True, False)
            else:
                current = pygame.transform.flip(current, False, True)
                current_soft = pygame.transform.flip(current_soft, False, True)
            self.flip_surfaces.append(current)
            self.flip_surfaces_soft.append(current_soft)
        
        self.flip_surfaces[-1] = self.original_surface
        self.flip_surfaces_soft[-1] = self.original_soft
        
        if self.reverse:
            self.flip_surfaces = self.flip_surfaces[::-1]
            self.flip_surfaces_soft = self.flip_surfaces_soft[::-1]
        
        self.final_surface = self.flip_surfaces[-1]
        self.final_surface_soft = self.flip_surfaces_soft[-1]
    
    def start_animation(self):
        """Begin the flip animation."""
        self.is_animating = True
    
    def update(self):
        """Update the tile's animation state."""
        if self.is_complete:
            if self.reverse:
                if self.line_alpha < 255:
                    self.line_alpha = min(255, self.line_alpha + LINE_FADE_SPEED * 2)
            else:
                if self.line_alpha > 0:
                    self.line_alpha = max(0, self.line_alpha - LINE_FADE_SPEED)
            return
        
        if self.reverse and self.is_animating and self.line_alpha < 255:
            self.line_alpha = min(255, self.line_alpha + LINE_FADE_SPEED)
        
        if self.current_delay > 0:
            self.current_delay -= 1
            return
        
        if not self.is_animating:
            self.start_animation()
        
        self.flip_angle += self.flip_speed
        
        if self.flip_angle >= self.total_rotation:
            self.flip_angle = self.total_rotation
            self.is_complete = True
    
    def draw(self, screen, use_soft_edges=True):
        """Draw the tile to the screen with optional soft edges."""
        if self.is_complete:
            screen.blit(self.final_surface, (self.x, self.y))
            return
        
        if not self.is_animating:
            surfaces = self.flip_surfaces_soft if use_soft_edges else self.flip_surfaces
            screen.blit(surfaces[0], (self.x, self.y))
            return
        
        flip_index = int(self.flip_angle / 180)
        angle_in_flip = self.flip_angle % 180
        flip_index = min(flip_index, len(self.flip_surfaces) - 2)
        
        scale = abs(math.cos(math.radians(angle_in_flip)))
        scale = max(0.02, scale)
        
        surfaces = self.flip_surfaces_soft if use_soft_edges else self.flip_surfaces
        if angle_in_flip < 90:
            base_surface = surfaces[flip_index]
        else:
            base_surface = surfaces[flip_index + 1]
        
        if self.flip_direction == 'horizontal':
            new_width = max(1, int(self.size * scale))
            scaled = pygame.transform.smoothscale(base_surface, (new_width, self.size))
            offset_x = (self.size - new_width) // 2
            screen.blit(scaled, (self.x + offset_x, self.y))
        else:
            new_height = max(1, int(self.size * scale))
            scaled = pygame.transform.smoothscale(base_surface, (self.size, new_height))
            offset_y = (self.size - new_height) // 2
            screen.blit(scaled, (self.x, self.y + offset_y))
    
    def draw_lines(self, screen):
        """Draw subtle cut lines around this tile."""
        if self.line_alpha <= 0:
            return
        
        alpha = int(self.line_alpha * 0.4)
        color = (0, 0, 0, alpha)
        
        line_surface = pygame.Surface((self.size + 1, self.size + 1), pygame.SRCALPHA)
        pygame.draw.rect(line_surface, color, (0, 0, self.size, self.size), 1)
        screen.blit(line_surface, (self.x, self.y))
