"""
Hidden/inpainting effect.
Removes objects from images using OpenCV inpainting and optional cloning.
"""

import os
import sys

import pygame

from config import FPS


class HiddenEffect:
    """Hides selected regions by inpainting them with surrounding content."""
    
    def __init__(self, image, screen_width, screen_height, polygon_data=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.original = image.copy()
        self.current_surface = image.copy()
        self.hidden_surface = None
        
        self.time = 0
        self.is_complete = False
        self.regions = []
        
        self.reveal_duration = 2.0
        self.hold_duration = 8.0
        self.animation_duration = self.reveal_duration + self.hold_duration
        
        if polygon_data:
            self._process_regions(polygon_data)
            self._apply_inpainting()
    
    def _process_regions(self, polygon_data):
        """Store the polygon regions to hide."""
        for region in polygon_data:
            self.regions.append({
                'polygon': region.get('polygon', []),
                'source_polygon': region.get('source_polygon', None),
                'x': region['x'],
                'y': region['y'],
                'w': region['w'],
                'h': region['h'],
                'source_x': region.get('source_x', 0),
                'source_y': region.get('source_y', 0),
                'source_w': region.get('source_w', 0),
                'source_h': region.get('source_h', 0),
            })
        print(f"Processing {len(self.regions)} region(s) to hide")
    
    def _apply_inpainting(self):
        """Use OpenCV inpainting to hide the selected regions."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            print("OpenCV required for hidden effect. Installing...")
            os.system(f"{sys.executable} -m pip install opencv-python --break-system-packages")
            try:
                import cv2
                import numpy as np
            except:
                print("Failed to install OpenCV")
                self.hidden_surface = self.original.copy()
                return
        
        # Convert pygame surface to OpenCV format
        img_str = pygame.image.tostring(self.original, 'RGB')
        img_array = np.frombuffer(img_str, dtype=np.uint8)
        img_array = img_array.reshape((self.screen_height, self.screen_width, 3))
        cv_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        original_image = cv_image.copy()
        result = cv_image.copy()
        
        # Create mask for all regions
        mask = np.zeros((self.screen_height, self.screen_width), dtype=np.uint8)
        
        for region in self.regions:
            polygon = region.get('polygon', [])
            if len(polygon) >= 3:
                pts = np.array(polygon, dtype=np.int32)
                cv2.fillPoly(mask, [pts], 255)
            else:
                x, y, w, h = region['x'], region['y'], region['w'], region['h']
                cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        
        # Process each region
        for region in self.regions:
            polygon = region.get('polygon', [])
            source_polygon = region.get('source_polygon', None)
            
            if len(polygon) < 3:
                continue
            
            region_mask = np.zeros((self.screen_height, self.screen_width), dtype=np.uint8)
            pts = np.array(polygon, dtype=np.int32)
            cv2.fillPoly(region_mask, [pts], 255)
            
            if source_polygon and len(source_polygon) >= 3:
                # Clone mode
                print("Cloning from source region...")
                
                target_x, target_y = region['x'], region['y']
                target_w, target_h = region['w'], region['h']
                source_x, source_y = region['source_x'], region['source_y']
                source_w, source_h = region['source_w'], region['source_h']
                
                if source_w > 0 and source_h > 0 and target_w > 0 and target_h > 0:
                    source_crop = original_image[source_y:source_y+source_h, source_x:source_x+source_w].copy()
                    source_resized = cv2.resize(source_crop, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
                    
                    source_pts = np.array(source_polygon, dtype=np.int32)
                    source_mask_full = np.zeros((self.screen_height, self.screen_width), dtype=np.uint8)
                    cv2.fillPoly(source_mask_full, [source_pts], 255)
                    source_mask_crop = source_mask_full[source_y:source_y+source_h, source_x:source_x+source_w]
                    source_mask_resized = cv2.resize(source_mask_crop, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
                    
                    for dy in range(target_h):
                        for dx in range(target_w):
                            ty, tx = target_y + dy, target_x + dx
                            if 0 <= ty < self.screen_height and 0 <= tx < self.screen_width:
                                if region_mask[ty, tx] > 0 and source_mask_resized[dy, dx] > 0:
                                    result[ty, tx] = source_resized[dy, dx]
            else:
                # Standard inpainting
                kernel_sample = np.ones((20, 20), np.uint8)
                mask_dilated = cv2.dilate(region_mask, kernel_sample, iterations=2)
                sample_band = cv2.subtract(mask_dilated, region_mask)
                
                if np.sum(sample_band) > 0:
                    surrounding_pixels = original_image[sample_band > 0]
                    if len(surrounding_pixels) > 0:
                        mean_color = np.mean(surrounding_pixels, axis=0)
                        region_coords = np.where(region_mask > 0)
                        for i in range(len(region_coords[0])):
                            py, px = region_coords[0][i], region_coords[1][i]
                            variation = np.random.normal(0, 3, 3)
                            new_color = np.clip(mean_color + variation, 0, 255).astype(np.uint8)
                            result[py, px] = new_color
        
        # Apply inpainting
        kernel = np.ones((3, 3), np.uint8)
        mask_inpaint = cv2.dilate(mask, kernel, iterations=1)
        result = cv2.inpaint(result, mask_inpaint, 8, cv2.INPAINT_TELEA)
        
        # Smooth and blend
        result_smooth = cv2.bilateralFilter(result, 5, 40, 40)
        mask_feather = cv2.GaussianBlur(mask.astype(float), (15, 15), 0) / 255.0
        mask_3ch = np.stack([mask_feather, mask_feather, mask_feather], axis=2)
        final_result = (result_smooth * mask_3ch + original_image * (1 - mask_3ch)).astype(np.uint8)
        
        # Convert back to pygame
        result_rgb = cv2.cvtColor(final_result, cv2.COLOR_BGR2RGB)
        self.hidden_surface = pygame.image.frombuffer(
            result_rgb.tobytes(), (self.screen_width, self.screen_height), 'RGB'
        ).convert()
        
        print("Inpainting complete - objects hidden")
    
    def update(self):
        """Update the reveal animation."""
        if self.is_complete or self.hidden_surface is None:
            return
        
        self.time += 1 / FPS
        
        if self.time >= self.animation_duration:
            self.is_complete = True
            self.current_surface = self.hidden_surface.copy()
            return
        
        if self.time < self.reveal_duration:
            progress = self.time / self.reveal_duration
            progress = progress * progress * (3 - 2 * progress)
            
            self.current_surface = self.original.copy()
            self.hidden_surface.set_alpha(int(255 * progress))
            self.current_surface.blit(self.hidden_surface, (0, 0))
            self.hidden_surface.set_alpha(255)
        else:
            self.current_surface = self.hidden_surface.copy()
    
    def draw(self, screen):
        """Draw the current frame."""
        screen.blit(self.current_surface, (0, 0))
    
    def restart(self):
        """Restart the animation."""
        self.time = 0
        self.is_complete = False
        self.current_surface = self.original.copy()
