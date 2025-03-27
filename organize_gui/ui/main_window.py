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
        # Pass config_manager to OrganizeRunner if needed
        self.organize_runner = OrganizeRunner(config_manager=self.config_manager)

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
        # Pass config_panel reference to preview_panel
        self.preview_panel = PreviewPanel(self.notebook, self.organize_runner, self.config_panel)
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
        """Initialize the application state, prioritizing a specific config file."""
        loaded_successfully = False
        # Define the prioritized config file path relative to this file's location
        # main_window.py is in organize_gui/ui/
        # We want ../../organise_dirs/config/organize.yaml
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prioritized_config_path = os.path.abspath(os.path.join(script_dir, '..', '..', '..', 'organise_dirs', 'config', 'organize.yaml'))

        print(f"Looking for prioritized config file at: {prioritized_config_path}")
        if os.path.exists(prioritized_config_path):
            print(f"Found prioritized config file: {prioritized_config_path}")
            try:
                # Use the config_panel's load method which updates UI
                if self.config_panel.load_configuration(prioritized_config_path):
                    print("Successfully loaded prioritized config file")
                    self.set_status(f"Loaded default config: {os.path.basename(prioritized_config_path)}")
                    loaded_successfully = True
                    
                    # Force an update to the rules panel
                    config = self.config_panel.get_current_config(from_editor=True)
                    if config and 'rules' in config:
                        print(f"Explicitly updating rules panel with {len(config['rules'])} rules")
                        self.rules_panel.update_rules(config)
                else:
                    # load_configuration shows its own error message
                    print(f"Attempted to load {prioritized_config_path} but failed.")
            except Exception as e:
                print(f"Error loading prioritized configuration '{prioritized_config_path}': {str(e)}")
                messagebox.showerror("Config Load Error", f"Failed to load the default configuration file:\n{prioritized_config_path}\n\nError: {str(e)}")
        else:
            print(f"Prioritized config file not found: {prioritized_config_path}")

        # Fallback if prioritized config wasn't loaded
        if not loaded_successfully:
            print("Falling back to preset or new configuration.")
            # Try to load default configuration using PresetManager
            try:
                default_config = preset_manager.get_default_organization_config()
                if default_config and default_config.get('rules'): # Check if rules exist
                    print(f"Loading default preset with {len(default_config['rules'])} rules")
                    self.config_panel.update_config(default_config) # Update panel with preset data
                    self.set_status("Loaded default organization preset")
                    loaded_successfully = True
                    
                    # Force an update to the rules panel
                    print("Explicitly updating rules panel with default preset")
                    self.rules_panel.update_rules(default_config)
                else:
                     print("Default preset was empty or invalid.")
            except Exception as e:
                print(f"Error loading default configuration via preset manager: {str(e)}")

        # Final fallback: create a new empty configuration
        if not loaded_successfully:
            print("Falling back to creating a new configuration.")
            # Use the method that updates the UI
            self.config_panel.new_configuration()
            self.set_status("Created new configuration")
            
            # Force an update to the rules panel with the new configuration
            config = self.config_panel.get_current_config(from_editor=True)
            if config:
                print(f"Explicitly updating rules panel with new config containing {len(config.get('rules', []))} rules")
                self.rules_panel.update_rules(config)

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
            # Get config potentially from editor if that's the source of truth
            config = self.config_panel.get_current_config(from_editor=True)
            if config:
                print(f"Config changed event: Updating rules panel with config containing {len(config.get('rules', []))} rules")
                self.rules_panel.update_rules(config)
            else:
                print("Config changed event: No valid config found to update rules panel")

    def on_rules_changed(self, event):
        """Handle rules change events."""
        # Update config panel's editor when rules are enabled/disabled in RulesPanel
        config = self.rules_panel.get_updated_config()
        if config:
            # Update the config panel (which includes the YAML editor)
            self.config_panel.update_config(config)

    def on_process_complete(self, event):
        """Handle process completion events."""
        # Update the results panel with data from preview_panel
        results = self.preview_panel.get_results()
        self.results_panel.set_results(results) # <--- Changed from update_results
        self.notebook.select(3)  # Switch to results tab
        self.set_status("Process completed", show_progress=False)

    def on_new_config(self):
        """Create a new configuration."""
        if messagebox.askyesno("New Configuration",
                              "Are you sure you want to create a new configuration? Unsaved changes will be lost."):
            self.config_panel.new_configuration() # This method handles UI and config_manager
            self.set_status("Created new configuration")
            
            # Force an update to the rules panel
            config = self.config_panel.get_current_config(from_editor=True)
            if config and 'rules' in config:
                print(f"Explicitly updating rules panel after creating new config with {len(config['rules'])} rules")
                self.rules_panel.update_rules(config)

    def on_open_config(self):
        """Open an existing configuration."""
        if self.config_panel.open_configuration_dialog():
            print(f"Configuration loaded from {os.path.basename(self.config_panel.current_config_path)}")
            self.set_status(f"Configuration loaded from {os.path.basename(self.config_panel.current_config_path)}")
            
            # Force an update to the rules panel
            config = self.config_panel.get_current_config(from_editor=True)
            if config and 'rules' in config:
                print(f"Explicitly updating rules panel after opening config with {len(config['rules'])} rules")
                self.rules_panel.update_rules(config)

    def on_save_config(self):
        """Save the current configuration."""
        if self.config_panel.save_configuration():
            self.set_status(f"Configuration saved to {os.path.basename(self.config_panel.current_config_path)}")

    def on_save_config_as(self):
        """Save the current configuration to a new file."""
        if self.config_panel.save_configuration_as():
            self.set_status(f"Configuration saved to new file: {os.path.basename(self.config_panel.current_config_path)}")

    def on_run_simulation(self):
        """Run the organization in simulation mode."""
        # Switch to the preview tab
        self.notebook.select(2)  # Index 2 is the Preview & Run tab
        # Trigger simulation
        self.preview_panel.run_simulation()

    def on_run_organization(self):
        """Run the actual organization process."""
        # Confirmation is handled within preview_panel now
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
                              f"This will replace your current configuration with the {preset_name} preset. Unsaved changes will be lost. Continue?"):
            try:
                config = preset_func()
                if config and config.get('rules'):
                    print(f"Loading {preset_name} preset with {len(config['rules'])} rules")
                    
                    # Update config panel
                    self.config_panel.update_config(config)
                    
                    # Explicitly update rules panel
                    print(f"Explicitly updating rules panel with {preset_name} preset")
                    self.rules_panel.update_rules(config)
                    
                    # Switch to config tab
                    self.notebook.select(0)
                    self.set_status(f"Loaded {preset_name} configuration preset")
                else:
                    messagebox.showwarning("Preset Error", f"Could not generate or load the {preset_name} preset.")
            except Exception as e:
                print(f"Error loading {preset_name} preset: {str(e)}")
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
        # TODO: Check for unsaved changes in the YAML editor
        # if self.config_panel.has_unsaved_changes(): ...
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.parent.destroy()
