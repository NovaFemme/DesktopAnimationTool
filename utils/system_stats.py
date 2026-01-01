"""
System statistics display module.
Handles CPU, Memory, and GPU usage monitoring.
"""

import subprocess
import os
import math

import pygame


class SystemStats:
    """Handles gathering and displaying system statistics."""
    
    def __init__(self, corner='top-right', update_interval=1.0):
        self.corner = corner
        self.update_interval = update_interval
        self.last_update = 0
        
        # Current stats
        self.cpu_percent = 0
        self.memory_percent = 0
        self.gpu_percent = None
        self.gpu_name = None
        
        # Try to import psutil
        self.psutil = None
        try:
            import psutil
            self.psutil = psutil
            self.has_psutil = True
        except ImportError:
            self.has_psutil = False
            print("Warning: psutil not installed. Install with: pip install psutil --break-system-packages")
        
        # Try to import GPUtil
        self.gputil = None
        try:
            import GPUtil
            self.gputil = GPUtil
        except ImportError:
            pass
        
        # Check GPU availability
        self.has_nvidia = self._check_nvidia_smi()
        self.has_amd = self._check_amd_gpu()
        self.has_gpu = self.gputil is not None or self.has_nvidia or self.has_amd
        
        # Initial update
        if self.has_psutil:
            self._update_stats()
    
    def _check_nvidia_smi(self):
        """Check if nvidia-smi is available."""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=2)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _check_amd_gpu(self):
        """Check if AMD GPU is available via sysfs or rocm-smi."""
        try:
            import glob
            gpu_busy_files = glob.glob('/sys/class/drm/card*/device/gpu_busy_percent')
            if gpu_busy_files:
                return True
        except:
            pass
        
        try:
            result = subprocess.run(['rocm-smi'], capture_output=True, timeout=2)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return False
    
    def _get_amd_gpu_stats(self):
        """Get AMD GPU stats using sysfs or rocm-smi."""
        # Method 1: Use sysfs
        try:
            import glob
            gpu_busy_files = glob.glob('/sys/class/drm/card*/device/gpu_busy_percent')
            for gpu_file in gpu_busy_files:
                with open(gpu_file, 'r') as f:
                    gpu_percent = float(f.read().strip())
                
                gpu_name = "AMD GPU"
                device_dir = gpu_file.replace('/gpu_busy_percent', '')
                name_file = f"{device_dir}/product_name"
                if os.path.exists(name_file):
                    with open(name_file, 'r') as f:
                        gpu_name = f.read().strip()
                else:
                    uevent_file = f"{device_dir}/uevent"
                    if os.path.exists(uevent_file):
                        with open(uevent_file, 'r') as f:
                            for line in f:
                                if 'PCI_ID=' in line:
                                    gpu_name = "AMD Radeon"
                                    break
                
                hwmon_dirs = glob.glob(f"{device_dir}/hwmon/hwmon*/name")
                for hwmon_name in hwmon_dirs:
                    with open(hwmon_name, 'r') as f:
                        name = f.read().strip()
                        if 'amdgpu' in name.lower():
                            gpu_name = "AMD Radeon"
                
                return gpu_percent, gpu_name
        except (FileNotFoundError, ValueError, PermissionError):
            pass
        
        # Method 2: Use rocm-smi
        try:
            result = subprocess.run(
                ['rocm-smi', '--showuse'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                import re
                match = re.search(r'GPU\s*\[?\d*\]?\s*.*?(\d+(?:\.\d+)?)\s*%', result.stdout)
                if match:
                    return float(match.group(1)), "AMD Radeon"
                match = re.search(r'(\d+(?:\.\d+)?)\s*%', result.stdout)
                if match:
                    return float(match.group(1)), "AMD Radeon"
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        
        # Method 3: rocm-smi with -u flag
        try:
            result = subprocess.run(
                ['rocm-smi', '-u'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                import re
                match = re.search(r'(\d+(?:\.\d+)?)\s*%', result.stdout)
                if match:
                    return float(match.group(1)), "AMD Radeon"
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return None, None
    
    def _get_gpu_stats_nvidia_smi(self):
        """Get GPU stats using nvidia-smi."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,name', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split(', ')
                    if len(parts) >= 2:
                        return float(parts[0].strip()), parts[1].strip()
                    elif len(parts) == 1:
                        return float(parts[0].strip()), "NVIDIA GPU"
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                output = result.stdout
                import re
                util_match = re.search(r'(\d+)\s*%\s*Default', output)
                if util_match:
                    gpu_util = float(util_match.group(1))
                    name_match = re.search(r'NVIDIA\s+([^\|]+)', output)
                    gpu_name = name_match.group(1).strip() if name_match else "NVIDIA GPU"
                    return gpu_util, gpu_name
                
                util_match = re.search(r'\|\s*(\d+)%\s+\w+', output)
                if util_match:
                    return float(util_match.group(1)), "NVIDIA GPU"
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return None, None
    
    def _update_stats(self):
        """Update all system statistics."""
        if not self.has_psutil:
            return
            
        self.cpu_percent = self.psutil.cpu_percent(interval=None)
        self.memory_percent = self.psutil.virtual_memory().percent
        
        if self.gputil:
            try:
                gpus = self.gputil.getGPUs()
                if gpus:
                    self.gpu_percent = gpus[0].load * 100
                    self.gpu_name = gpus[0].name
                    return
            except:
                pass
        
        if self.has_nvidia:
            gpu_pct, gpu_name = self._get_gpu_stats_nvidia_smi()
            if gpu_pct is not None:
                self.gpu_percent = gpu_pct
                self.gpu_name = gpu_name
                return
        
        if self.has_amd:
            gpu_pct, gpu_name = self._get_amd_gpu_stats()
            if gpu_pct is not None:
                self.gpu_percent = gpu_pct
                self.gpu_name = gpu_name
                return
    
    def update(self):
        """Update stats if enough time has passed."""
        if not self.has_psutil:
            return
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.last_update >= self.update_interval:
            self._update_stats()
            self.last_update = current_time
    
    def draw(self, screen):
        """Draw the stats box on the screen."""
        if not self.has_psutil:
            return
        
        padding = 15
        line_height = 24
        num_lines = 3 if self.gpu_percent is not None else 2
        box_width = 200
        box_height = padding * 2 + line_height * num_lines + 10
        corner_radius = 15
        
        screen_width, screen_height = screen.get_size()
        margin = 20
        
        if self.corner == 'top-right':
            box_x = screen_width - box_width - margin
            box_y = margin
        elif self.corner == 'top-left':
            box_x = margin
            box_y = margin
        elif self.corner == 'bottom-right':
            box_x = screen_width - box_width - margin
            box_y = screen_height - box_height - margin
        elif self.corner == 'bottom-left':
            box_x = margin
            box_y = screen_height - box_height - margin
        else:
            box_x = screen_width - box_width - margin
            box_y = margin
        
        box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        
        self._draw_rounded_rect(box_surface, (30, 30, 30, 200), 
                               (0, 0, box_width, box_height), corner_radius)
        self._draw_rounded_rect_border(box_surface, (100, 100, 100, 150),
                                       (0, 0, box_width, box_height), corner_radius, 2)
        
        font = pygame.font.Font(None, 22)
        y_offset = padding
        
        cpu_color = self._get_color_for_percent(self.cpu_percent)
        self._draw_stat_line(box_surface, font, "CPU", self.cpu_percent, 
                            cpu_color, padding, y_offset, box_width)
        y_offset += line_height
        
        mem_color = self._get_color_for_percent(self.memory_percent)
        self._draw_stat_line(box_surface, font, "MEM", self.memory_percent,
                            mem_color, padding, y_offset, box_width)
        y_offset += line_height
        
        if self.gpu_percent is not None:
            gpu_color = self._get_color_for_percent(self.gpu_percent)
            self._draw_stat_line(box_surface, font, "GPU", self.gpu_percent,
                                gpu_color, padding, y_offset, box_width)
        
        screen.blit(box_surface, (box_x, box_y))
    
    def _draw_stat_line(self, surface, font, label, percent, color, x, y, box_width):
        """Draw a single stat line with label, bar, and percentage."""
        bar_width = 80
        bar_height = 12
        
        label_surface = font.render(f"{label}:", True, (200, 200, 200))
        surface.blit(label_surface, (x, y + 2))
        
        bar_x = x + 50
        bar_y = y + 4
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=6)
        
        fill_width = int((percent / 100) * bar_width)
        if fill_width > 0:
            pygame.draw.rect(surface, color, (bar_x, bar_y, fill_width, bar_height), border_radius=6)
        
        percent_text = font.render(f"{percent:.0f}%", True, (220, 220, 220))
        surface.blit(percent_text, (bar_x + bar_width + 8, y + 2))
    
    def _get_color_for_percent(self, percent):
        """Get color based on usage percentage (green -> yellow -> red)."""
        if percent < 50:
            ratio = percent / 50
            return (int(100 + 155 * ratio), int(200 - 50 * ratio), 100)
        else:
            ratio = (percent - 50) / 50
            return (255, int(150 - 150 * ratio), int(100 - 100 * ratio))
    
    def _draw_rounded_rect(self, surface, color, rect, radius):
        """Draw a filled rounded rectangle."""
        x, y, width, height = rect
        pygame.draw.rect(surface, color, (x + radius, y, width - 2 * radius, height))
        pygame.draw.rect(surface, color, (x, y + radius, width, height - 2 * radius))
        pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
        pygame.draw.circle(surface, color, (x + width - radius, y + radius), radius)
        pygame.draw.circle(surface, color, (x + radius, y + height - radius), radius)
        pygame.draw.circle(surface, color, (x + width - radius, y + height - radius), radius)
    
    def _draw_rounded_rect_border(self, surface, color, rect, radius, width):
        """Draw a rounded rectangle border."""
        x, y, w, h = rect
        pygame.draw.line(surface, color, (x + radius, y), (x + w - radius, y), width)
        pygame.draw.line(surface, color, (x + radius, y + h - 1), (x + w - radius, y + h - 1), width)
        pygame.draw.line(surface, color, (x, y + radius), (x, y + h - radius), width)
        pygame.draw.line(surface, color, (x + w - 1, y + radius), (x + w - 1, y + h - radius), width)
        pygame.draw.arc(surface, color, (x, y, radius * 2, radius * 2), 
                       math.pi / 2, math.pi, width)
        pygame.draw.arc(surface, color, (x + w - radius * 2, y, radius * 2, radius * 2),
                       0, math.pi / 2, width)
        pygame.draw.arc(surface, color, (x, y + h - radius * 2, radius * 2, radius * 2),
                       math.pi, 3 * math.pi / 2, width)
        pygame.draw.arc(surface, color, (x + w - radius * 2, y + h - radius * 2, radius * 2, radius * 2),
                       3 * math.pi / 2, 2 * math.pi, width)
