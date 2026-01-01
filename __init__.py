"""
Desktop Animation Tool
A versatile desktop animation tool with multiple effects.

Effects:
- Flip: 3D flipping tile animation
- Ripple: Concentric circle tile animation  
- Eyes: Animated eye movement detection
- Hidden: Object removal via inpainting
- Clone: Replace regions with source content
"""

__version__ = "1.0.0"
__author__ = "Desktop Animation Tool"

from .main import DesktopAnimationTool, main
from .config import AVAILABLE_EFFECTS

__all__ = ['DesktopAnimationTool', 'main', 'AVAILABLE_EFFECTS']
