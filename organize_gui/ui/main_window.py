"""
Main application window for the File Organization System.

This module defines the main window and overall UI structure of the application.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

from ui.config_panel import ConfigPanel
from ui.rules_panel import RulesPanel
from ui.preview_panel import PreviewPanel
from ui.results_panel import ResultsPanel

class MainWindow:
    """Main application window class."""
    
    def __init__(self, parent):
        """Initialize the main window."""
        self.parent = parent
        
        # Configure the parent window
        self.parent.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create the main menu
        self._create_menu()
        
        # Create the main container
        self.main_container = ttk.Frame(self.parent)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tab panels
        self.config_panel = ConfigPanel(self.notebook)
        self.rules_panel = RulesPanel(self.notebook)
        self.preview_panel = PreviewPanel(self.notebook)
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
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        
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
    
    def _setup_events(self):
        """Set up event handlers for communication between panels."""
        # Example: Listen for configuration change events
        self.parent.bind("<<ConfigurationChanged>>", self.on_config_changed)
        
        # Example: Listen for rule change events
        self.parent.bind("<<RulesChanged>>", self.on_rules_changed)
    
    def _initialize_state(self):
        """Initialize the application state."""
        # Try to load default configuration if available
        default_config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "organize.yaml"
        )
        
        if os.path.exists(default_config_path):
            # If default config exists, try to load it
            try:
                self.config_panel.load_configuration(default_config_path)
                self.set_status(f"Loaded default configuration from {default_config_path}")
            except Exception as e:
                self.set_status(f"Error loading default configuration: {str(e)}")
        else:
            self.set_status("Ready - No configuration loaded")
    
    def set_status(self, message):
        """Update the status bar with a message."""
        self.status_label.config(text=message)
    
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
        # Handle rule changes (e.g., enable/disable)
        pass
    
    def on_new_config(self):
        """Create a new configuration."""
        if messagebox.askyesno("New Configuration", 
                              "Are you sure you want to create a new configuration? Unsaved changes will be lost."):
            self.config_panel.new_configuration()
            self.set_status("Created new configuration")
    
    def on_open_config(self):
        """Open an existing configuration."""
        self.config_panel.open_configuration_dialog()
    
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
        """Open the scheduling dialog."""
        # Implement scheduling dialog
        messagebox.showinfo("Schedule Organization", 
                           "Scheduling functionality not implemented yet.")
    
    def on_documentation(self):
        """Show the documentation."""
        messagebox.showinfo("Documentation", 
                           "Please refer to the README.md file for documentation.")
    
    def on_about(self):
        """Show the about dialog."""
        messagebox.showinfo("About File Organization System", 
                           "File Organization System\nVersion 1.0\n\nA GUI frontend for organize-tool.")
    
    def on_close(self):
        """Handle window close event."""
        # Check for unsaved changes before closing
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.parent.destroy()