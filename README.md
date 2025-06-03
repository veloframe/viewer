# Photo Frame Application

A beautiful, full-screen photo frame application built with PySide6 that displays your photos with smooth transitions and optional metadata overlay.

## Features

- **Full-screen photo display** with support for both landscape and portrait orientations
- **Smart portrait photo handling**:
  - Automatically displays portrait photos side by side as pairs
  - Skips the next photo in the sequence when showing pairs to avoid duplicates
- **Configurable display time** per photo (seconds, minutes, hours, or days)
- **Smooth cross-fade transitions** between photos with customizable duration
- **Optional random photo order** for variety in your displays
- **Enhanced visual effects**:
  - Blurred, zoomed background effect for photos with aspect ratios different from the screen
  - Proper scaling and centering of all photos
- **Metadata overlay** showing capture date information
  - Customizable font, size, and opacity
  - Properly positioned for both single photos and photo pairs
- **Clock overlay** displaying current time
  - Configurable position (top-left, top-center, top-right, bottom-center)
  - Customizable font, size, opacity, and format
  - Uses Arrow library for flexible time/date display
- **Keyboard navigation**:
  - Left/Right arrows to navigate between photos
  - Space bar to advance to the next photo
  - Hold Shift while pressing navigation keys to skip transition effects
  - Escape key to quit the application

## Installation

1. Make sure you have Python 3.8 or later installed
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Configuration

Edit the `config.yaml` file to customize the photo frame settings:

```yaml
photos_directory: "~/Pictures"  # Path to directory containing photos
display_time: "5s"            # Time to display each photo (s=seconds, m=minutes, h=hours, d=days)
transition_time: "1s"        # Transition time between photos (s=seconds, m=minutes, h=hours)
random_order: true           # Whether to randomize photo order
blur_zoom_background: true   # Apply blurred zoom background for non-matching aspect ratios

# Metadata Overlay Settings
show_metadata: true         # Show photo metadata overlay
metadata_opacity: 30         # Opacity of metadata overlay (0-100)
metadata_font: "segoeui.ttf"  # Font for metadata overlay
metadata_point_size: 12     # Point size for metadata font

# Clock Overlay Settings
show_clock: true            # Show clock overlay
clock_position: "top-right"  # Clock position (top-left, top-center, top-right, bottom-center)
clock_opacity: 30           # Opacity of clock overlay (0-100)
clock_font: "segoeui.ttf"   # Font for clock overlay
clock_point_size: 16        # Point size for clock font
clock_format: "HH:mm"       # Clock format (Arrow format)
```

## Clock Format Options

The clock overlay uses the Arrow library for date formatting. Here are some common format codes you can use:

| Code | Description | Example |
|------|-------------|--------|
| `HH` | Hour (24-hour clock, 00-23) | 23 |
| `h` | Hour (12-hour clock, 1-12) | 11 |
| `hh` | Hour (12-hour clock, 01-12) | 11 |
| `mm` | Minute (00-59) | 19 |
| `ss` | Second (00-59) | 45 |
| `A` | AM/PM indicator | PM |
| `YYYY` | Year with century | 2025 |
| `MM` | Month (01-12) | 06 |
| `DD` | Day of month (01-31) | 01 |
| `ddd` | Abbreviated weekday name | Sun |
| `dddd` | Full weekday name | Sunday |
| `MMM` | Abbreviated month name | Jun |
| `MMMM` | Full month name | June |

Examples:
- `"HH:mm"` → 23:19 (24-hour time)
- `"hh:mm A"` → 11:19 PM (12-hour time with AM/PM)
- `"dddd, MMMM DD"` → Sunday, June 01 (weekday, month, day)
- `"YYYY-MM-DD HH:mm:ss"` → 2025-06-01 23:19:45 (ISO-like format)

## Usage

Run the application:

```bash
python photo_frame.py
```

### Keyboard Controls

- **Left Arrow**: Previous photo
- **Right Arrow** or **Space**: Next photo
- **Shift + Left/Right/Space**: Skip transition when changing photos
- **Escape**: Exit the application

## Architecture

The application has a modular architecture with the following components:

- **PhotoFrame** (`photo_frame.py`): Main application class that manages the window, user input, and slideshow timing
- **PhotoDisplay** (`photo_display.py`): Core class that orchestrates all display components
- **UIComponentManager** (`photo_ui_components.py`): Manages UI components like QGraphicsPixmapItems and opacity effects
- **PhotoPreparationManager** (`photo_preparation.py`): Handles photo loading, scaling, and position calculations
- **MetadataManager** (`metadata_overlay.py`): Manages metadata overlay creation and updates
- **ClockManager** (`clock_overlay.py`): Manages clock overlay with configurable format and position
- **TransitionManager** (`photo_transition_manager.py`): Handles transition animations and their lifecycle
- **PhotoFileSet** (`photo_file_set.py`): Manages the collection of photos, including navigation and portrait pair detection
- **Config** (`config_manager.py`): Handles loading and accessing configuration settings

This modular design improves maintainability, encapsulates responsibilities, and reduces fragile dependencies between components.

## Requirements

- Python 3.8 or later
- PySide6
- Pillow (PIL Fork)
- PyYAML
- NumPy

## License

This project is open source and available under the [MIT License](LICENSE).
