# 🎬 Desktop Animation Tool

A versatile desktop animation tool with multiple effects: 3D flip/ripple tile animations, eye movement animation, object hiding via inpainting, and clone/replace functionality.

![Demo](https://img.shields.io/badge/Platform-Linux-green) ![Python](https://img.shields.io/badge/Python-3.8+-blue)

## Project Structure

```
desktop_animation_tool/
├── __init__.py           # Package initialization
├── config.py             # Configuration and constants
├── main.py               # Main application class and entry point
├── utils/
│   ├── __init__.py       # Utils module exports
│   ├── system_stats.py   # CPU/GPU/Memory monitoring
│   ├── screenshot.py     # Desktop screenshot capture
│   └── desktop.py        # Wallpaper detection, window setup
└── effects/
    ├── __init__.py       # Effects module exports
    ├── flip_tile.py      # 3D flip tile animation
    ├── polygon_selector.py # Interactive region selector
    ├── eyes.py           # Eye detection and animation
    └── hidden.py         # Object hiding/inpainting

run_animation.py          # Standalone run script
```

## Features

- 🎴 **3D Flip Animation** — Tiles flip with realistic perspective scaling
- 🌊 **Two Animation Patterns** — Wave (center-out) or Ripple (concentric circles)
- 👁️ **Eyes Effect** — Detects and animates eyes in the image to look around
- 🫥 **Hidden Effect** — Remove objects (watches, jewelry) via inpainting
- 🔄 **Clone Effect** — Replace selected areas with content from another region
- 🖼️ **Desktop Capture** — Uses your actual current desktop/wallpaper
- 🖥️ **Desktop Mode** — Can run directly on your desktop background (X11)
- 🔄 **Auto-Restart** — Loops the animation at configurable intervals
- 📊 **System Stats** — Optional CPU, GPU, Memory usage display
- ✨ **Smooth Edges** — Hardware accelerated with soft blended tile edges
- ⚡ **Configurable** — Adjust tile size, speed, and timing

## Requirements

```bash
# Install Python dependencies
pip install pygame Pillow

# For system stats display (-u flag)
pip install psutil

# Install screenshot tool (for -c capture mode)
sudo apt install scrot

# Optional: for desktop mode (-d flag)
sudo apt install x11-utils xdotool

# Optional: for NVIDIA GPU stats
pip install GPUtil

# Optional: for AMD GPU stats
sudo apt install rocm-smi
```

## Quick Start

```bash
# Using the modular package:
python3 run_animation.py -c -e flip      # Flip effect
python3 run_animation.py -c -e ripple    # Ripple effect  

# Eyes effect - first time (select and save):
python3 run_animation.py -c -e eyes --select-eyes

# Eyes effect - subsequent runs (uses saved config):
python3 run_animation.py -c -e eyes

# Hidden effect - first time (select and save):
python3 run_animation.py -c -e hidden --select-objects

# Hidden effect - subsequent runs:
python3 run_animation.py -c -e hidden

# Clone effect - first time:
python3 run_animation.py -c -e clone --select-objects

# Clone effect - subsequent runs:
python3 run_animation.py -c -e clone

# Desktop mode with auto-restart every 5 seconds
python3 run_animation.py -c -d -r 5 -e eyes
```

## Saved Configurations

Polygon selections are saved to config files for reuse:
- **Eyes**: `~/.config/desktop_animation_tool/eyes.cfg`
- **Hidden/Clone**: `~/.config/desktop_animation_tool/hidden.cfg`

This allows you to select regions once and reuse them on subsequent runs.

## All Parameters

| Parameter | Short | Description | Default |
|-----------|-------|-------------|---------|
| `--size` | `-s` | Size of each square tile in pixels | 80 |
| `--windowed` | `-w` | Run in windowed mode instead of fullscreen | Off |
| `--desktop` | `-d` | Run directly on desktop background (X11 only) | Off |
| `--capture` | `-c` | Capture actual desktop screenshot | Off |
| `--restart` | `-r` | Auto-restart interval in seconds (0 = disabled) | 0 |
| `--usage` | `-u` | Show system stats (CPU, GPU, Memory) in corner | Off |
| `--stats-corner` | | Corner for stats box (top-right, top-left, bottom-right, bottom-left) | top-right |
| `--speed` | | Flip animation speed (degrees per frame) | 8 |
| `--no-smooth` | | Disable smooth edge blending (may improve performance) | Off |
| `--effect` | `-e` | Animation: flip, ripple, eyes, hidden, or clone | flip |
| `--eye-pos` | | Manual eye positions: "x1,y1,w1,h1;x2,y2,w2,h2" | |
| `--select-eyes` | | Interactive eye selection (saves to ~/.config/.../eyes.cfg) | Off |
| `--select-objects` | | Interactive object selection for hidden/clone (saves to ~/.config/.../hidden.cfg) | Off |
| `--reverse` | | Reverse animation: start from complete image, flip to scrambled | Off |
| `--help` | `-h` | Show help message | |

## Usage Examples

```bash
# Simple fullscreen with your wallpaper (wave pattern)
python3 desktop_flip_puzzle.py -c

# Ripple pattern (concentric circles)
python3 desktop_flip_puzzle.py -c -e ripple

# Eyes effect with auto-detection
python3 desktop_flip_puzzle.py -c -e eyes

# Eyes effect with interactive polygon selection (recommended!)
python3 desktop_flip_puzzle.py -c -e eyes --select-eyes

# Hidden effect - remove objects like watches, jewelry
python3 desktop_flip_puzzle.py -c -e hidden

# Clone effect - replace areas with content from another region
python3 desktop_flip_puzzle.py -c -e clone

# Reverse animation (original to scrambled)
python3 desktop_flip_puzzle.py -c --reverse

# Desktop mode (runs behind your windows on X11)
python3 desktop_flip_puzzle.py -c -d

# Auto-restart every 3 seconds (great for desktop mode)
python3 desktop_flip_puzzle.py -c -d -r 3

# With system stats display
python3 desktop_flip_puzzle.py -c -u -r 5

# Windowed mode for testing
python3 desktop_flip_puzzle.py -c -w

# Maximum chill: large tiles, slow animation, long pause
python3 desktop_flip_puzzle.py -c -s 150 --speed 4 -r 10
```

## Eyes Effect

The eyes effect detects faces and eyes in the captured image, then animates them to look around naturally.

**First time - Select and save eye regions:**
```bash
python3 desktop_flip_puzzle.py -c -e eyes --select-eyes
```
This opens an interactive tool where you can:
- **Left click** to add polygon points around each eye
- **Right click** to complete an eye and start the next
- **Backspace** to undo the last point
- **Enter** to save and start the animation
- **ESC** to cancel

Your selections are saved to `~/.config/desktop_animation_tool/eyes.cfg`

**Subsequent runs - Use saved config:**
```bash
python3 desktop_flip_puzzle.py -c -e eyes
```
This loads the previously saved eye regions automatically.

**Manual eye positions (if you know the coordinates):**
```bash
# Format: x,y,width,height for each eye separated by semicolon
python3 desktop_flip_puzzle.py -c -e eyes --eye-pos '120,120,100,70;330,96,120,80'
```

Requirements:
```bash
pip install opencv-python --break-system-packages
```

Features:
- **Saved configurations** - select once, use many times
- **Interactive polygon selection tool** for manual eye definition
- Color-based detection for distinctive eyes (red, bright, etc.)
- Manual eye position override when auto-detection fails
- Smooth sine-wave based pupil movement
- Edges of selection stay fixed - only inner pupil area moves
- Natural-looking gaze patterns

## Hidden Effect

The hidden effect removes objects from the image using OpenCV's inpainting algorithm. Perfect for making watches, jewelry, bracelets, and other accessories invisible.

**First time - Select and save regions:**
```bash
python3 desktop_flip_puzzle.py -c -e hidden --select-objects
```

This opens an interactive polygon selector where you can:
- **Left click** to add points around objects to hide
- **Right click** to complete a region and start the next
- **Backspace** to undo the last point
- **Enter** to apply inpainting and start the reveal animation
- **ESC** to cancel

Your selections are saved to `~/.config/desktop_animation_tool/hidden.cfg`

**Subsequent runs - Use saved config:**
```bash
python3 desktop_flip_puzzle.py -c -e hidden
```

**How it works:**
1. Select regions by drawing polygons around objects
2. OpenCV's inpainting fills selected areas with surrounding content
3. Smooth crossfade reveals the modified image

**Tips:**
- Draw tight polygons around objects for best results
- Works best on simple/uniform backgrounds
- Multiple regions can be selected before pressing Enter

## Clone Effect

The clone effect replaces selected areas with content from another region you specify. Perfect for replacing hair with skin, filling areas with specific textures, or removing objects when you know what should be behind them.

**First time - Select and save regions:**
```bash
python3 desktop_flip_puzzle.py -c -e clone --select-objects
```

Your selections are saved to `~/.config/desktop_animation_tool/hidden.cfg`

**Subsequent runs - Use saved config:**
```bash
python3 desktop_flip_puzzle.py -c -e clone
```

**How it works:**
1. Select the TARGET area (what to hide) - shown in RED
2. Right-click to complete, then select SOURCE area (what to clone from) - shown in GREEN  
3. Right-click to complete the source
4. Repeat for more regions, or press Enter to apply
5. The source content is scaled and copied to cover the target

**Tips:**
- Select a source area similar in size to the target for best results
- The source content will be scaled to fit the target area
- Works great for: replacing hair with skin, filling gaps with nearby texture

## Keyboard Controls

| Key | Action |
|-----|--------|
| `ESC` | Exit the program |
| `SPACE` | Manually restart animation |
| `UP` | Increase tile size |
| `DOWN` | Decrease tile size |

## How It Works

1. **Capture** — Takes a screenshot of your desktop (or reads wallpaper file)
2. **Divide** — Splits the image into a grid of square tiles
3. **Scramble** — Randomly flips each tile horizontally or vertically
4. **Animate** — Each tile flips back with a 3D effect, starting from the center
5. **Reveal** — Cut lines fade away to show the seamless original image
6. **Repeat** — Optionally auto-restarts after a delay

## Desktop Mode Notes (X11 Only)

The `-d` flag attempts to run the animation directly on your desktop background:

- **Works on:** X11 (most Linux distros with Xorg)
- **Does NOT work on:** Wayland (GNOME 40+, Fedora default, etc.)

To check your session type:
```bash
echo $XDG_SESSION_TYPE
```

If you're on Wayland, use regular fullscreen mode instead — it looks the same!

## Troubleshooting

**Black screen with `-c` flag:**
- Make sure `scrot` is installed: `sudo apt install scrot`

**Wrong wallpaper detected:**
- Use `-c` flag to capture actual desktop instead

**Desktop mode not working:**
- Only works on X11, not Wayland
- Install required tools: `sudo apt install x11-utils xdotool`

**Animation too fast/slow:**
- Adjust with `--speed` (lower = slower, higher = faster)

## Configuration

You can also edit the constants at the top of the script:

```python
SQUARE_SIZE = 80          # Default tile size in pixels
FLIP_SPEED = 8            # Animation speed (degrees per frame)
SETTLE_DELAY_RANGE = (0, 60)  # Random delay range for wave effect
LINE_FADE_SPEED = 5       # How fast cut lines disappear
FPS = 60                  # Frames per second
```

## Supported Desktop Environments

Wallpaper auto-detection works on:
- ✅ Cinnamon (Linux Mint)
- ✅ GNOME
- ✅ MATE
- ✅ KDE Plasma
- ✅ XFCE

For best results on any DE, use the `-c` capture flag.

## License

MIT License — Feel free to use, modify, and share!

---

**Enjoy the mesmerizing animation! 🎴✨**
