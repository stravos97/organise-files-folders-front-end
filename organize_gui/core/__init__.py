# __init__.py for ui package
"""
UI components for the File Organization System frontend.
"""

from .main_window import MainWindow
from .config_panel import ConfigPanel
from .rules_panel import RulesPanel
from .preview_panel import PreviewPanel
from .results_panel import ResultsPanel

# __init__.py for core package
"""
Core functionality for the File Organization System.
"""

from .config_manager import ConfigManager
from .organize_runner import OrganizeRunner

# __init__.py for utils package
"""
Utility functions for the File Organization System.
"""

from .path_helpers import (
    expand_path, format_path_for_display, is_path_writable,
    get_directory_size, format_size, open_directory,
    ensure_directory_exists, split_path_at_marker
)
from .validators import (
    is_valid_path, is_valid_yaml, is_valid_rule_name,
    is_valid_extension_list, is_valid_filter, is_valid_action
)

# __init__.py for main package
"""
File Organization System frontend application.

A graphical user interface for the organize-tool file organization system.
"""

__version__ = '1.0.0'