"""
Eye detection and animation effect.
Detects eyes in images and animates them to look around.
"""

import math
import os
import sys

import pygame

from config import FPS

# Try to import OpenCV
HAS_CV2 = False
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    pass


class EyeEffect:
    """Detects eyes in the image and animates them to look around."""
    
    def __init__(self, image, screen_width, screen_height, manual_eye_pos=None, polygon_data=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.original = image.copy()
        self.current_surface = image.copy()
        
        self.time = 0
        self.is_complete = False
        self.eyes = []
        
        self.look_speed = 0.5
        self.max_shift = 8
        self.animation_duration = 10.0
        
        if polygon_data:
            self._use_polygon_data(polygon_data)
        elif manual_eye_pos:
            self._use_manual_eyes(manual_eye_pos)
        else:
            self._detect_eyes()
    
    def _use_polygon_data(self, polygon_data):
        """Set eye positions from polygon selector data."""
        for eye_data in polygon_data:
            x, y, w, h = eye_data['x'], eye_data['y'], eye_data['w'], eye_data['h']
            
            eye_info = {
                'x': x, 'y': y, 'w': w, 'h': h,
                'center_x': eye_data.get('center_x', x + w // 2),
                'center_y': eye_data.get('center_y', y + h // 2),
                'polygon': eye_data.get('polygon', None)
            }
            
            pad = self.max_shift + 5
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(self.screen_width, x + w + pad)
            y2 = min(self.screen_height, y + h + pad)
            
            eye_info['padded_rect'] = (x1, y1, x2 - x1, y2 - y1)
            eye_info['original_pixels'] = self.original.subsurface(
                pygame.Rect(x1, y1, x2 - x1, y2 - y1)
            ).copy()
            eye_info['current_shift_x'] = 0
            eye_info['current_shift_y'] = 0
            
            self.eyes.append(eye_info)
            print(f"Polygon eye at ({x}, {y}) size {w}x{h}")
        
        print(f"Added {len(self.eyes)} polygon-defined eye(s)")
    
    def _use_manual_eyes(self, eye_pos_str):
        """Set eye positions manually from string 'x1,y1,w1,h1;x2,y2,w2,h2'"""
        try:
            eye_specs = eye_pos_str.split(';')
            for spec in eye_specs:
                parts = [int(p.strip()) for p in spec.split(',')]
                if len(parts) >= 4:
                    x, y, w, h = parts[:4]
                    eye_info = {
                        'x': x, 'y': y, 'w': w, 'h': h,
                        'center_x': x + w // 2,
                        'center_y': y + h // 2,
                    }
                    
                    pad = self.max_shift + 5
                    x1 = max(0, x - pad)
                    y1 = max(0, y - pad)
                    x2 = min(self.screen_width, x + w + pad)
                    y2 = min(self.screen_height, y + h + pad)
                    
                    eye_info['padded_rect'] = (x1, y1, x2 - x1, y2 - y1)
                    eye_info['original_pixels'] = self.original.subsurface(
                        pygame.Rect(x1, y1, x2 - x1, y2 - y1)
                    ).copy()
                    eye_info['current_shift_x'] = 0
                    eye_info['current_shift_y'] = 0
                    
                    self.eyes.append(eye_info)
                    print(f"Manual eye at ({x}, {y}) size {w}x{h}")
            
            print(f"Added {len(self.eyes)} manual eye(s)")
        except Exception as e:
            print(f"Error parsing manual eye positions: {e}")
    
    def _detect_eyes(self):
        """Detect eyes in the image using OpenCV."""
        global HAS_CV2
        
        if not HAS_CV2:
            print("OpenCV not available for eye detection. Installing...")
            os.system(f"{sys.executable} -m pip install opencv-python --break-system-packages")
            try:
                import cv2
                import numpy as np
                HAS_CV2 = True
            except:
                print("Failed to install OpenCV - eye detection disabled")
                return
        
        import cv2
        import numpy as np
        
        # Convert pygame surface to OpenCV format
        img_str = pygame.image.tostring(self.original, 'RGB')
        img_array = np.frombuffer(img_str, dtype=np.uint8)
        img_array = img_array.reshape((self.screen_height, self.screen_width, 3))
        
        cv_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        except Exception as e:
            print(f"Could not load Haar cascades: {e}")
            return
        
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(80, 80))
        
        if len(faces) == 0:
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.02, minNeighbors=2, minSize=(50, 50))
        
        print(f"Detected {len(faces)} face(s)")
        
        detected_eyes = []
        
        for (fx, fy, fw, fh) in faces:
            eye_region_top = fy + int(fh * 0.15)
            eye_region_bottom = fy + int(fh * 0.45)
            
            roi_gray = gray[eye_region_top:eye_region_bottom, fx:fx + fw]
            
            min_eye_size = max(15, int(fw * 0.12))
            max_eye_size = int(fw * 0.35)
            
            eyes = eye_cascade.detectMultiScale(
                roi_gray, scaleFactor=1.05, minNeighbors=5,
                minSize=(min_eye_size, min_eye_size),
                maxSize=(max_eye_size, max_eye_size)
            )
            
            valid_eyes = []
            for (ex, ey, ew, eh) in eyes:
                abs_x = fx + ex
                abs_y = eye_region_top + ey
                
                is_duplicate = False
                for ve in valid_eyes:
                    dist = math.sqrt((abs_x - ve[0])**2 + (abs_y - ve[1])**2)
                    if dist < ew:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    valid_eyes.append((abs_x, abs_y, ew, eh))
            
            if len(valid_eyes) >= 2:
                valid_eyes.sort(key=lambda e: e[0])
                for i in range(min(2, len(valid_eyes))):
                    ex, ey, ew, eh = valid_eyes[i]
                    detected_eyes.append({
                        'x': ex, 'y': ey, 'w': ew, 'h': eh,
                        'center_x': ex + ew // 2,
                        'center_y': ey + eh // 2,
                    })
        
        # Store eye data
        for eye_info in detected_eyes:
            pad = self.max_shift + 5
            x1 = max(0, eye_info['x'] - pad)
            y1 = max(0, eye_info['y'] - pad)
            x2 = min(self.screen_width, eye_info['x'] + eye_info['w'] + pad)
            y2 = min(self.screen_height, eye_info['y'] + eye_info['h'] + pad)
            
            eye_info['padded_rect'] = (x1, y1, x2 - x1, y2 - y1)
            eye_info['original_pixels'] = self.original.subsurface(
                pygame.Rect(x1, y1, x2 - x1, y2 - y1)
            ).copy()
            eye_info['current_shift_x'] = 0
            eye_info['current_shift_y'] = 0
            
            self.eyes.append(eye_info)
        
        print(f"Total eyes detected: {len(self.eyes)}")
    
    def _shift_eye_pixels(self, eye_info, shift_x, shift_y):
        """Shift only the inner pupil/iris area while keeping edges static."""
        if eye_info['original_pixels'] is None:
            return
        
        px, py, pw, ph = eye_info['padded_rect']
        
        inner_x = eye_info['x'] - px
        inner_y = eye_info['y'] - py
        inner_w = eye_info['w']
        inner_h = eye_info['h']
        
        pupil_scale = 0.7
        pupil_w = int(inner_w * pupil_scale)
        pupil_h = int(inner_h * pupil_scale)
        pupil_x = inner_x + (inner_w - pupil_w) // 2
        pupil_y = inner_y + (inner_h - pupil_h) // 2
        
        src_x = pupil_x - int(shift_x)
        src_y = pupil_y - int(shift_y)
        src_x = max(0, min(pw - pupil_w, src_x))
        src_y = max(0, min(ph - pupil_h, src_y))
        
        result = pygame.Surface((pw, ph))
        result.blit(eye_info['original_pixels'], (0, 0))
        
        pupil_surface = pygame.Surface((pupil_w, pupil_h))
        try:
            pupil_surface.blit(eye_info['original_pixels'], (0, 0),
                             (src_x, src_y, pupil_w, pupil_h))
        except:
            return
        
        center_x = pupil_w // 2
        center_y = pupil_h // 2
        blend_start = 0.7
        
        for y in range(pupil_h):
            for x in range(pupil_w):
                dx = (x - center_x) / (pupil_w / 2) if pupil_w > 0 else 0
                dy = (y - center_y) / (pupil_h / 2) if pupil_h > 0 else 0
                dist = math.sqrt(dx * dx + dy * dy)
                
                if dist >= 1.0:
                    continue
                
                dest_x = pupil_x + x
                dest_y = pupil_y + y
                
                try:
                    shifted_pixel = pupil_surface.get_at((x, y))
                    
                    if dist < blend_start:
                        result.set_at((dest_x, dest_y), (shifted_pixel[0], shifted_pixel[1], shifted_pixel[2]))
                    else:
                        blend = 1.0 - ((dist - blend_start) / (1.0 - blend_start))
                        blend = max(0.0, min(1.0, blend))
                        
                        orig_pixel = result.get_at((dest_x, dest_y))
                        
                        r = int(shifted_pixel[0] * blend + orig_pixel[0] * (1 - blend))
                        g = int(shifted_pixel[1] * blend + orig_pixel[1] * (1 - blend))
                        b = int(shifted_pixel[2] * blend + orig_pixel[2] * (1 - blend))
                        
                        result.set_at((dest_x, dest_y), (r, g, b))
                except:
                    pass
        
        self.current_surface.blit(result, (px, py))
    
    def update(self):
        """Update the eye animation."""
        if self.is_complete or len(self.eyes) == 0:
            return
        
        self.time += 1 / FPS
        
        if self.time >= self.animation_duration:
            self.is_complete = True
            self.current_surface = self.original.copy()
            return
        
        self.current_surface = self.original.copy()
        
        look_x = math.sin(self.time * self.look_speed * 2) * self.max_shift
        look_y = math.sin(self.time * self.look_speed * 1.5 + 1) * self.max_shift * 0.5
        look_x += math.sin(self.time * 3.7) * 2
        look_y += math.sin(self.time * 2.3) * 1
        
        for eye in self.eyes:
            self._shift_eye_pixels(eye, look_x, look_y)
    
    def draw(self, screen):
        """Draw the current frame."""
        screen.blit(self.current_surface, (0, 0))
    
    def restart(self):
        """Restart the animation."""
        self.time = 0
        self.is_complete = False
