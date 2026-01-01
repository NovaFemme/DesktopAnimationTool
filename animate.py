#!/usr/bin/env python3
"""
Desktop Animation Tool - Run Script
Execute this file to run the animation tool.

Usage:
    python3 run_animation.py [options]
    
Examples:
    python3 run_animation.py -c -e flip          # Flip effect with desktop capture
    python3 run_animation.py -c -e ripple        # Ripple effect
    python3 run_animation.py -c -e eyes          # Eye animation
    python3 run_animation.py -c -e hidden        # Remove objects
    python3 run_animation.py -c -e clone         # Clone/replace regions
"""

import sys
import os

# Add the package directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()
