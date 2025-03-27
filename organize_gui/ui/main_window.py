"""
Enhanced Main Window for the File Organization System.

This implementation provides a complete GUI equivalent to organize-files-folders
with all the functionality of the command-line version.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import yaml
import re
from pathlib import Path

from ui.config_panel import ConfigPanel
from ui.rules_panel import RulesPanel
from ui.preview_panel import PreviewPanel
from ui.results_panel import ResultsPanel
from core.config_manager import ConfigManager
from core.organize_runner import OrganizeRunner
from core import preset_manager # Import the new preset manager
from ui.dialogs.about_dialog import AboutDialog # Import the new AboutDialog
from ui.dialogs.schedule_dialog import ScheduleDialog # Import the new ScheduleDialog

class MainWindow:
    """Enhanced main application window class."""
    
    def __init__(self, parent):
        """Initialize the main window."""
        self.parent = parent
        
        # Configure the parent window
        self.parent.title("File Organization System")
        self.parent.geometry("1000x700")
        self.parent.minsize(800, 600)
        self.parent.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set application icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.parent.iconbitmap(icon_path)
        except Exception:
            pass  # Ignore icon errors
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.organize_runner = OrganizeRunner()
        
        # Create the main menu
        self._create_menu()
        
        # Create the main container
        self.main_container = ttk.Frame(self.parent)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tab panels
        self.config_panel = ConfigPanel(self.notebook, self.config_manager)
        self.rules_panel = RulesPanel(self.notebook)
        self.preview_panel = PreviewPanel(self.notebook, self.organize_runner)
        self.results_panel = ResultsPanel(self.notebook)
        
        # Add tabs to the notebook
        self.notebook.add(self.config_panel, text="Configuration")
        self.notebook.add(self.rules_panel, text="Rules")
        self.notebook.add(self.preview_panel, text="Preview & Run")
        self.notebook.add(self.results_panel, text="Results")
        
        # Create status bar
        self._create_status_bar()
        
        # Set up event handlers
        self._setup_events()
        
        # Initialize application state
        self._initialize_state()
    
    def _create_menu(self):
        """Create the main application menu."""
        # Main menu bar
        self.menu_bar = tk.Menu(self.parent)
        self.parent.config(menu=self.menu_bar)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Configuration", command=self.on_new_config)
        self.file_menu.add_command(label="Open Configuration...", command=self.on_open_config)
        self.file_menu.add_command(label="Save Configuration", command=self.on_save_config)
        self.file_menu.add_command(label="Save Configuration As...", command=self.on_save_config_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_close)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Tools menu
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.tools_menu.add_command(label="Run Simulation", command=self.on_run_simulation)
        self.tools_menu.add_command(label="Run Organization", command=self.on_run_organization)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="Schedule Organization...", command=self.on_schedule_organization)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="Find Duplicates", command=self.on_find_duplicates)
        self.tools_menu.add_command(label="Rename Photos with EXIF", command=self.on_rename_photos)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        
        # Presets menu
        self.presets_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.presets_menu.add_command(label="Load Default Organization", command=lambda: self._load_preset(preset_manager.get_default_organization_config, "Default Organization"))
        self.presets_menu.add_command(label="Load Photo Organization", command=lambda: self._load_preset(preset_manager.get_photo_organization_config, "Photo Organization"))
        self.presets_menu.add_command(label="Load Music Organization", command=lambda: self._load_preset(preset_manager.get_music_organization_config, "Music Organization"))
        self.presets_menu.add_command(label="Load Document Organization", command=lambda: self._load_preset(preset_manager.get_document_organization_config, "Document Organization"))
        self.presets_menu.add_command(label="Load Cleanup Rules", command=lambda: self._load_preset(preset_manager.get_cleanup_rules_config, "Cleanup Rules"))
        self.menu_bar.add_cascade(label="Presets", menu=self.presets_menu)

        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Documentation", command=self.on_documentation)
        self.help_menu.add_command(label="About", command=self.on_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
    
    def _create_status_bar(self):
        """Create the status bar at the bottom of the window."""
        self.status_frame = ttk.Frame(self.parent, relief=tk.SUNKEN, padding=(2, 2))
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Add progress indicator for background operations
        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(
            self.status_frame, 
            orient=tk.HORIZONTAL, 
            length=200, 
            mode='determinate',
            variable=self.progress_var
        )
        self.progress.pack(side=tk.RIGHT, padx=5)
        self.progress.pack_forget()  # Hide initially
    
    def _setup_events(self):
        """Set up event handlers for communication between panels."""
        # Listen for configuration change events
        self.parent.bind("<<ConfigurationChanged>>", self.on_config_changed)
        
        # Listen for rule change events
        self.parent.bind("<<RulesChanged>>", self.on_rules_changed)
        
        # Listen for process completion events
        self.parent.bind("<<ProcessComplete>>", self.on_process_complete)
    
    def _initialize_state(self):
        """Initialize the application state."""
        # Try to find config file locations
        config_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "organize.yaml"),
            os.path.expanduser("~/.config/organize-tool/config.yaml"),
            os.path.expanduser("~/Library/Application Support/organize-tool/config.yaml"),
            os.path.join(os.getenv("APPDATA", ""), "organize-tool", "config.yaml")
        ]
        
        # Try to load default configuration using PresetManager
        default_config = preset_manager.get_default_organization_config()
        if default_config and default_config.get('rules'): # Check if rules exist
            try:
                self.config_panel.update_config(default_config)
                self.set_status("Loaded default organization configuration")
            except Exception as e:
                print(f"Error loading default configuration via preset manager: {str(e)}")
                # Fallback to new config if loading default fails
                self.on_new_config()
        else:
            # If no default config found or it's empty, create a new one
            self.on_new_config()
    
    def set_status(self, message, show_progress=False, progress_value=0):
        """Update the status bar with a message and optional progress."""
        self.status_label.config(text=message)
        
        if show_progress:
            self.progress.pack(side=tk.RIGHT, padx=5)
            self.progress_var.set(progress_value)
        else:
            self.progress.pack_forget()
        
        # Update UI
        self.parent.update_idletasks()
    
    # Event handlers
    
    def on_config_changed(self, event):
        """Handle configuration change events."""
        # Update the rules panel with the new configuration
        if hasattr(self, 'config_panel') and hasattr(self, 'rules_panel'):
            config = self.config_panel.get_current_config()
            if config:
                self.rules_panel.update_rules(config)
    
    def on_rules_changed(self, event):
        """Handle rules change events."""
        # Update config when rules are enabled/disabled
        config = self.rules_panel.get_updated_config()
        if config:
            self.config_panel.update_config(config)
    
    def on_process_complete(self, event):
        """Handle process completion events."""
        # Update the results panel
        self.notebook.select(3)  # Switch to results tab
        self.set_status("Process completed", show_progress=False)
    
    def on_new_config(self):
        """Create a new configuration."""
        if messagebox.askyesno("New Configuration", 
                              "Are you sure you want to create a new configuration? Unsaved changes will be lost."):
            self.config_panel.new_configuration()
            self.set_status("Created new configuration")
    
    def on_open_config(self):
        """Open an existing configuration."""
        if self.config_panel.open_configuration_dialog():
            self.set_status("Configuration loaded")
    
    def on_save_config(self):
        """Save the current configuration."""
        if self.config_panel.save_configuration():
            self.set_status("Configuration saved")
    
    def on_save_config_as(self):
        """Save the current configuration to a new file."""
        if self.config_panel.save_configuration_as():
            self.set_status("Configuration saved to new file")
    
    def on_run_simulation(self):
        """Run the organization in simulation mode."""
        # Switch to the preview tab
        self.notebook.select(2)  # Index 2 is the Preview & Run tab
        # Trigger simulation
        self.preview_panel.run_simulation()
    
    def on_run_organization(self):
        """Run the actual organization process."""
        if messagebox.askyesno("Run Organization", 
                              "Are you sure you want to run the file organization process? Files will be moved according to the configuration."):
            # Switch to the preview tab
            self.notebook.select(2)  # Index 2 is the Preview & Run tab
            # Trigger actual run
            self.preview_panel.run_organization()
    
    def on_schedule_organization(self):
        """Open the scheduling dialog using the dedicated class."""
        # Get the path of the currently saved config file, if any
        current_config_path = self.config_panel.current_config_path
        ScheduleDialog(self.parent, self.organize_runner, config_path=current_config_path)

    def on_find_duplicates(self):
        """Create a configuration focused on finding duplicates."""
        if messagebox.askyesno("Find Duplicates", 
                               "This will create a configuration focused on finding duplicate files. Continue?"):
            self._load_preset(preset_manager.get_find_duplicates_config, "Duplicate Finding")
    
    def on_rename_photos(self):
        """Create a configuration focused on renaming photos with EXIF data."""
        if messagebox.askyesno("Rename Photos", 
                               "This will create a configuration focused on renaming photos using EXIF data. Continue?"):
            self._load_preset(preset_manager.get_rename_photos_config, "Photo Renaming")
    
    def _load_preset(self, preset_func, preset_name):
        """Helper function to load a preset configuration."""
        if messagebox.askyesno(f"Load {preset_name} Preset",
                              f"This will replace your current configuration with the {preset_name} preset. Continue?"):
            try:
                config = preset_func()
                if config and config.get('rules'):
                    self.config_panel.update_config(config)
                    self.notebook.select(0)  # Switch to config tab
                    self.set_status(f"Loaded {preset_name} configuration preset")
                else:
                    messagebox.showwarning("Preset Error", f"Could not generate or load the {preset_name} preset.")
            except Exception as e:
                messagebox.showerror("Error Loading Preset", f"Failed to load {preset_name} preset: {str(e)}")

    # Remove the individual on_load_* methods as they are replaced by _load_preset calls in the menu

    def on_documentation(self):
        """Show the documentation."""
        try:
            # Try to open the online documentation
            subprocess.run(["organize", "docs"], check=False)
        except Exception:
            # Fallback to showing a message
            messagebox.showinfo("Documentation", 
                               "Please refer to the organize-tool documentation:\n\n"
                               "https://organize.readthedocs.io/")
    
    def on_about(self):
        """Show the about dialog using the dedicated class."""
        AboutDialog(self.parent) # Instantiate the dialog

    def on_close(self):
        """Handle window close event."""
        # Check for unsaved changes
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.parent.destroy()
