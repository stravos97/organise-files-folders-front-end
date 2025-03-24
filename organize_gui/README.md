# File Organization System Frontend

A graphical user interface for the powerful [organize-tool](https://github.com/tfeldmann/organize) file organization system.

## Overview

This application provides a user-friendly interface to:

- Configure source and destination directories
- Enable/disable specific organization rules
- Run the organization process with visual feedback
- Preview changes before execution with simulation mode
- Schedule automatic organization runs
- View and analyze organization results

## Features

- **Configuration Management**: Easily update source and destination paths
- **Rule Management**: Enable/disable specific rules and view their details
- **Preview Mode**: See what will happen before making any changes
- **Detailed Results**: Track file movements and organization statistics
- **Scheduling**: Set up automatic organization runs

## Installation

### Prerequisites

- Python 3.6 or newer
- organize-tool installed (pip install -U organize-tool)
- Tkinter (usually included with Python)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/organize-gui.git
   cd organize-gui
   ```

2. Install with pip:
   ```bash
   pip install -e .
   ```

   Or simply run the application with the provided script:
   ```bash
   ./run.sh
   ```

## Usage

### Starting the Application

Launch the application by running:

```bash
organize-gui
```

Or use the provided script:

```bash
./run.sh
```

### Configuration Tab

1. Specify the source directory to scan for files
2. Specify the destination base directory for organized files
3. Load or save configurations
4. View the directory structure that will be created

### Rules Tab

1. Enable/disable specific organization rules
2. Filter rules by category or search text
3. View detailed information about each rule's:
   - Source locations
   - Filters
   - Actions

### Preview & Run Tab

1. Run the organization in simulation mode to preview changes
2. Run the actual organization process
3. Schedule automated organization runs
4. View real-time progress and output

### Results Tab

1. See statistics about the organization run
2. Filter and search through organized files
3. Export results to CSV format
4. View detailed information about each file movement

## Project Structure

The project follows a modular structure:

```
organize_gui/
├── app.py                  # Main application entry point
├── ui/                     # User interface components
│   ├── main_window.py      # Main application window
│   ├── config_panel.py     # Configuration panel
│   ├── rules_panel.py      # Rules management panel
│   ├── preview_panel.py    # Preview/simulation panel
│   └── results_panel.py    # Results display panel
├── core/                   # Core functionality
│   ├── config_manager.py   # YAML configuration handling
│   └── organize_runner.py  # Interface to organize-tool
└── utils/                  # Utility functions
    ├── path_helpers.py     # Path manipulation utilities
    └── validators.py       # Input validation functions
```

## Customization

The application is designed to be easily customizable:

- Add new tabs or panels by extending the UI components
- Add new validator functions for additional rules
- Modify the directory structure in the ConfigManager

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [organize-tool](https://github.com/tfeldmann/organize) - The underlying tool that powers this application