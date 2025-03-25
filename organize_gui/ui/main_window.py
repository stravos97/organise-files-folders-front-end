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
        self.presets_menu.add_command(label="Load Default Organization", command=self.on_load_default_organization)
        self.presets_menu.add_command(label="Load Photo Organization", command=self.on_load_photo_organization)
        self.presets_menu.add_command(label="Load Music Organization", command=self.on_load_music_organization)
        self.presets_menu.add_command(label="Load Document Organization", command=self.on_load_document_organization)
        self.presets_menu.add_command(label="Load Cleanup Rules", command=self.on_load_cleanup_rules)
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
        
        # Try to load default configuration if available
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    self.config_panel.load_configuration(config_path)
                    self.set_status(f"Loaded configuration from {config_path}")
                    return
                except Exception as e:
                    print(f"Error loading configuration: {str(e)}")
        
        # If no default config found, create a new one
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
        """Open the scheduling dialog."""
        # Create scheduling dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Schedule Organization")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Create dialog content
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Schedule Type:").pack(anchor=tk.W, pady=(5, 2))
        
        schedule_var = tk.StringVar(value="daily")
        
        ttk.Radiobutton(main_frame, text="Daily", variable=schedule_var, value="daily").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(main_frame, text="Weekly", variable=schedule_var, value="weekly").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(main_frame, text="Monthly", variable=schedule_var, value="monthly").pack(anchor=tk.W, padx=20)
        
        ttk.Label(main_frame, text="Time:").pack(anchor=tk.W, pady=(10, 2))
        
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(anchor=tk.W, padx=20, pady=5)
        
        hour_var = tk.StringVar(value="02")
        hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, width=2, textvariable=hour_var, format="%02.0f")
        hour_spin.pack(side=tk.LEFT)
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT, padx=2)
        
        minute_var = tk.StringVar(value="00")
        minute_spin = ttk.Spinbox(time_frame, from_=0, to=59, width=2, textvariable=minute_var, format="%02.0f")
        minute_spin.pack(side=tk.LEFT)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        simulation_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Run in simulation mode (no changes)", variable=simulation_var).pack(anchor=tk.W)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def on_schedule():
            try:
                # Get the selected schedule
                schedule_type = schedule_var.get()
                time_str = f"{hour_var.get()}:{minute_var.get()}"
                simulation = simulation_var.get()
                
                # Get command to add to crontab or scheduler
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                command = ""
                
                if os.name == "posix":  # Unix-like
                    organize_script = os.path.join(script_dir, "config", "organize-files.sh")
                    if not os.path.exists(organize_script):
                        organize_script = "organize"  # Use installed organize command
                    
                    command = f"{organize_script} "
                    if simulation:
                        command += "--simulate"
                    else:
                        command += "--run"
                else:  # Windows
                    organize_script = os.path.join(script_dir, "config", "organize-files.bat")
                    if not os.path.exists(organize_script):
                        organize_script = "organize"  # Use installed organize command
                    
                    command = f"{organize_script} "
                    if simulation:
                        command += "--simulate"
                    else:
                        command += "--run"
                
                # Display the command to add to scheduler
                result_dialog = tk.Toplevel(dialog)
                result_dialog.title("Schedule Information")
                result_dialog.geometry("500x300")
                result_dialog.transient(dialog)
                result_dialog.grab_set()
                
                result_frame = ttk.Frame(result_dialog, padding=10)
                result_frame.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(result_frame, text="Add the following to your scheduler:").pack(anchor=tk.W, pady=5)
                
                if os.name == "posix":  # Unix-like
                    cron_min = minute_var.get()
                    cron_hour = hour_var.get()
                    cron_dom = "*"
                    cron_month = "*"
                    cron_dow = "*"
                    
                    if schedule_type == "weekly":
                        cron_dow = "0"  # Sunday
                    elif schedule_type == "monthly":
                        cron_dom = "1"  # 1st of month
                    
                    cron_line = f"{cron_min} {cron_hour} {cron_dom} {cron_month} {cron_dow} {command}"
                    
                    ttk.Label(result_frame, text="For crontab:").pack(anchor=tk.W, pady=(10, 2))
                    
                    cron_text = tk.Text(result_frame, height=3, wrap=tk.WORD)
                    cron_text.pack(fill=tk.X, pady=5)
                    cron_text.insert("1.0", cron_line)
                    cron_text.config(state='disabled')
                    
                    ttk.Label(result_frame, text="To add to crontab:").pack(anchor=tk.W, pady=(10, 2))
                    ttk.Label(result_frame, text="1. Run 'crontab -e'").pack(anchor=tk.W, padx=20)
                    ttk.Label(result_frame, text="2. Add the above line").pack(anchor=tk.W, padx=20)
                    ttk.Label(result_frame, text="3. Save and exit").pack(anchor=tk.W, padx=20)
                    
                else:  # Windows
                    ttk.Label(result_frame, text="For Windows Task Scheduler:").pack(anchor=tk.W, pady=(10, 2))
                    ttk.Label(result_frame, text="1. Open Task Scheduler").pack(anchor=tk.W, padx=20)
                    ttk.Label(result_frame, text="2. Create Basic Task...").pack(anchor=tk.W, padx=20)
                    ttk.Label(result_frame, text=f"3. Set trigger: {schedule_type} at {time_str}").pack(anchor=tk.W, padx=20)
                    ttk.Label(result_frame, text="4. Set action: Start a program").pack(anchor=tk.W, padx=20)
                    ttk.Label(result_frame, text=f"5. Program/script: {command}").pack(anchor=tk.W, padx=20)
                
                ttk.Button(result_frame, text="Close", command=result_dialog.destroy).pack(pady=10)
                
                # Close the scheduling dialog
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create schedule: {str(e)}")
        
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Schedule", command=on_schedule).pack(side=tk.RIGHT, padx=5)
    
    def on_find_duplicates(self):
        """Create a configuration focused on finding duplicates."""
        if messagebox.askyesno("Find Duplicates", 
                              "This will create a configuration focused on finding duplicate files. Continue?"):
            # Create a new configuration
            config = {
                'rules': [
                    {
                        'name': "Find Duplicate Files",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Documents")],
                        'subfolders': True,
                        'filters': [
                            {'duplicate': {'detect_original_by': 'created'}}
                        ],
                        'actions': [
                            {'echo': "Found duplicate: {path} (Original: {duplicate.original})"},
                            {'move': {'dest': os.path.expanduser("~/Duplicates/{relative_path}/"), 'on_conflict': 'rename_new'}}
                        ]
                    }
                ]
            }
            
            self.config_panel.update_config(config)
            self.notebook.select(0)  # Switch to config tab
            self.set_status("Created duplicate finding configuration")
    
    def on_rename_photos(self):
        """Create a configuration focused on renaming photos with EXIF data."""
        if messagebox.askyesno("Rename Photos", 
                              "This will create a configuration focused on renaming photos using EXIF data. Continue?"):
            # Create a new configuration
            config = {
                'rules': [
                    {
                        'name': "Rename Photos with EXIF Data",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Pictures")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'heic', 'arw', 'nef', 'cr2', 'dng']},
                            {'exif': True}
                        ],
                        'actions': [
                            {'echo': "Renaming photo: {path}"},
                            {'rename': "{exif.image.make}_{exif.image.model}_{exif.image.datetime.year}-{exif.image.datetime.month}-{exif.image.datetime.day}_{exif.image.datetime.hour}-{exif.image.datetime.minute}-{exif.image.datetime.second}.{extension}"}
                        ]
                    },
                    {
                        'name': "Rename Photos without EXIF Data",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Pictures")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'heic', 'arw', 'nef', 'cr2', 'dng']},
                            {'not': 'exif'},
                            {'created': True}
                        ],
                        'actions': [
                            {'echo': "Renaming photo without EXIF: {path}"},
                            {'rename': "{parent_dir}_{created.year}-{created.month}-{created.day}_{name}.{extension}"}
                        ]
                    }
                ]
            }
            
            self.config_panel.update_config(config)
            self.notebook.select(0)  # Switch to config tab
            self.set_status("Created photo renaming configuration")
    
    def on_load_default_organization(self):
        """Load a full default organization configuration."""
        if messagebox.askyesno("Load Default Organization", 
                              "This will load a complete default organization configuration. Continue?"):
            # Try to find the default configuration
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "organize.yaml")
            
            if os.path.exists(config_path):
                self.config_panel.load_configuration(config_path)
                self.set_status("Loaded default organization configuration")
            else:
                messagebox.showwarning("Not Found", "Default configuration file not found.")
    
    def on_load_photo_organization(self):
        """Load a photo organization configuration."""
        if messagebox.askyesno("Load Photo Organization", 
                              "This will create a configuration for organizing photos. Continue?"):
            # Create a photo organization configuration
            config = {
                'rules': [
                    {
                        'name': "Organize Photos by Date",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Pictures")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'heic', 'arw', 'nef', 'cr2', 'dng']},
                            {'exif': True}
                        ],
                        'actions': [
                            {'move': {'dest': os.path.expanduser("~/Pictures/Organized/{exif.image.datetime.year}/{exif.image.datetime.month}/"), 'on_conflict': 'rename_new'}}
                        ]
                    },
                    {
                        'name': "Organize Photos without EXIF",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Pictures")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'heic', 'arw', 'nef', 'cr2', 'dng']},
                            {'not': 'exif'},
                            {'created': True}
                        ],
                        'actions': [
                            {'move': {'dest': os.path.expanduser("~/Pictures/Organized/{created.year}/{created.month}/"), 'on_conflict': 'rename_new'}}
                        ]
                    }
                ]
            }
            
            self.config_panel.update_config(config)
            self.notebook.select(0)  # Switch to config tab
            self.set_status("Created photo organization configuration")
    
    def on_load_music_organization(self):
        """Load a music organization configuration."""
        if messagebox.askyesno("Load Music Organization", 
                              "This will create a configuration for organizing music files. Continue?"):
            # Create a music organization configuration
            config = {
                'rules': [
                    {
                        'name': "Organize Music Files",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Music")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['mp3', 'wav', 'aac', 'flac', 'm4a', 'wma', 'opus', 'ogg']}
                        ],
                        'actions': [
                            {'move': {'dest': os.path.expanduser("~/Music/Organized/{extension.upper()}/"), 'on_conflict': 'rename_new'}}
                        ]
                    },
                    {
                        'name': "Handle Music Duplicates",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Music")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['mp3', 'wav', 'aac', 'flac', 'm4a', 'wma', 'opus', 'ogg']},
                            {'duplicate': {'detect_original_by': 'created'}}
                        ],
                        'actions': [
                            {'echo': "Found music duplicate: {path} (Original: {duplicate.original})"},
                            {'move': {'dest': os.path.expanduser("~/Music/Duplicates/{path.stem}_duplicate_{duplicate.count}.{extension}"), 'on_conflict': 'rename_new'}}
                        ]
                    }
                ]
            }
            
            self.config_panel.update_config(config)
            self.notebook.select(0)  # Switch to config tab
            self.set_status("Created music organization configuration")
    
    def on_load_document_organization(self):
        """Load a document organization configuration."""
        if messagebox.askyesno("Load Document Organization", 
                              "This will create a configuration for organizing documents. Continue?"):
            # Create a document organization configuration
            config = {
                'rules': [
                    {
                        'name': "Organize Text Documents",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Documents")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['txt', 'rtf', 'md', 'tex']}
                        ],
                        'actions': [
                            {'move': {'dest': os.path.expanduser("~/Documents/Organized/Text/"), 'on_conflict': 'rename_new'}}
                        ]
                    },
                    {
                        'name': "Organize Office Documents",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Documents")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp']}
                        ],
                        'actions': [
                            {'move': {'dest': os.path.expanduser("~/Documents/Organized/Office/"), 'on_conflict': 'rename_new'}}
                        ]
                    },
                    {
                        'name': "Organize PDF Documents",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Documents")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['pdf']}
                        ],
                        'actions': [
                            {'move': {'dest': os.path.expanduser("~/Documents/Organized/PDF/"), 'on_conflict': 'rename_new'}}
                        ]
                    }
                ]
            }
            
            self.config_panel.update_config(config)
            self.notebook.select(0)  # Switch to config tab
            self.set_status("Created document organization configuration")
    
    def on_load_cleanup_rules(self):
        """Load cleanup rules configuration."""
        if messagebox.askyesno("Load Cleanup Rules", 
                              "This will create a configuration for cleaning up temporary files. Continue?"):
            # Create a cleanup configuration
            config = {
                'rules': [
                    {
                        'name': "Clean Temporary Files",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Downloads")],
                        'subfolders': True,
                        'filters': [
                            {'extension': ['tmp', 'bak', 'cache', 'log']}
                        ],
                        'actions': [
                            {'move': {'dest': os.path.expanduser("~/Cleanup/Temporary/"), 'on_conflict': 'rename_new'}}
                        ]
                    },
                    {
                        'name': "Find Duplicate Files",
                        'enabled': True,
                        'targets': 'files',
                        'locations': [os.path.expanduser("~/Downloads")],
                        'subfolders': True,
                        'filters': [
                            {'duplicate': {'detect_original_by': 'created'}}
                        ],
                        'actions': [
                            {'echo': "Found duplicate: {path} (Original: {duplicate.original})"},
                            {'move': {'dest': os.path.expanduser("~/Cleanup/Duplicates/{path.stem}_duplicate_{duplicate.count}.{extension}"), 'on_conflict': 'rename_new'}}
                        ]
                    }
                ]
            }
            
            self.config_panel.update_config(config)
            self.notebook.select(0)  # Switch to config tab
            self.set_status("Created cleanup rules configuration")
    
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
        """Show the about dialog."""
        about_dialog = tk.Toplevel(self.parent)
        about_dialog.title("About File Organization System")
        about_dialog.geometry("400x300")
        about_dialog.transient(self.parent)
        about_dialog.grab_set()
        about_dialog.resizable(False, False)
        
        # Create dialog content
        main_frame = ttk.Frame(about_dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="File Organization System", font=("", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Version
        version_label = ttk.Label(main_frame, text="Version 1.0.0")
        version_label.pack(pady=(0, 20))
        
        # Description
        desc_text = "A graphical user interface for the powerful organize-tool file organization system.\n\n" \
                    "This application helps you automate the organization of your files based on sophisticated rules."
        desc_label = ttk.Label(main_frame, text=desc_text, wraplength=350, justify=tk.CENTER)
        desc_label.pack(pady=(0, 20))
        
        # Credits
        credits_label = ttk.Label(main_frame, text="Based on organize-tool by Thomas Feldmann")
        credits_label.pack()
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=about_dialog.destroy)
        close_button.pack(pady=20)
    
    def on_close(self):
        """Handle window close event."""
        # Check for unsaved changes
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.parent.destroy()