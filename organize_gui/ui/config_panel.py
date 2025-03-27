"""
Configuration panel for the File Organization System.

This implementation provides a complete interface for managing organize-tool
configurations, including source and destination directories.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import yaml
import re
from pathlib import Path

class ConfigPanel(ttk.Frame):
    """Panel for editing configuration settings."""
    
    def __init__(self, parent, config_manager=None):
        """Initialize the configuration panel."""
        super().__init__(parent)
        
        # Initialize the config manager
        self.config_manager = config_manager

        # Current configuration path
        self.current_config_path = None

        # Create the UI components
        self._create_widgets()
    def _create_widgets(self):
        """Create the UI components for the configuration panel using grid."""
        # Configure the main frame grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main layout container with scrolling
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        # Configure grid for the scrollable frame
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        # Define row weights later based on content

        # --- Widgets inside scrollable_frame ---
        row_index = 0

        # Configuration file section
        config_frame = ttk.LabelFrame(self.scrollable_frame, text="Configuration File", padding=(10, 5))
        config_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        config_frame.grid_columnconfigure(0, weight=1) # Make entry expand

        self.config_var = tk.StringVar()
        config_entry = ttk.Entry(config_frame, textvariable=self.config_var)
        config_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))

        config_button = ttk.Button(config_frame, text="Browse...", command=self._browse_config)
        config_button.grid(row=0, column=1, sticky='e')
        row_index += 1

        # File operation buttons
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)

        load_button = ttk.Button(button_frame, text="Load Configuration", command=self._load_current_config)
        load_button.pack(side=tk.LEFT, padx=(0, 5)) # Use pack for simple horizontal layout here

        save_button = ttk.Button(button_frame, text="Save Configuration", command=self._save_current_config)
        save_button.pack(side=tk.LEFT, padx=5) # Use pack for simple horizontal layout here
        row_index += 1

        # Source directory section
        source_frame = ttk.LabelFrame(self.scrollable_frame, text="Source Directories", padding=(10, 5))
        source_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        source_frame.grid_columnconfigure(0, weight=1) # Make inner frame expand

        # Create a dynamic list of source directories
        self.source_frame_inner = ttk.Frame(source_frame)
        self.source_frame_inner.grid(row=0, column=0, sticky='nsew')
        self.source_frame_inner.grid_columnconfigure(0, weight=1) # Make entries expand

        # Source directory controls
        source_controls = ttk.Frame(source_frame)
        source_controls.grid(row=1, column=0, sticky='ew', pady=(5,0))

        add_source_button = ttk.Button(source_controls, text="Add Source Directory", command=self._add_source_directory)
        add_source_button.pack(side=tk.LEFT) # Use pack for simple horizontal layout here
        row_index += 1

        # Default source directory (used for initial setup)
        self.source_var = tk.StringVar()

        # Destination directory section
        dest_frame = ttk.LabelFrame(self.scrollable_frame, text="Destination Base Directory", padding=(10, 5))
        dest_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        dest_frame.grid_columnconfigure(0, weight=1) # Make entry expand

        self.dest_var = tk.StringVar()
        dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_var)
        dest_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))

        dest_button = ttk.Button(dest_frame, text="Browse...", command=self._browse_dest)
        dest_button.grid(row=0, column=1, sticky='e')
        row_index += 1

        # Update paths button
        update_button = ttk.Button(self.scrollable_frame, text="Update All Paths", command=self._update_paths)
        update_button.grid(row=row_index, column=0, sticky='w', padx=10, pady=5)
        row_index += 1

        # Subdirectory control
        subdir_frame = ttk.Frame(self.scrollable_frame)
        subdir_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)

        self.subfolders_var = tk.BooleanVar(value=True)
        subfolders_check = ttk.Checkbutton(
            subdir_frame,
            text="Include Subfolders (applies to all new rules)",
            variable=self.subfolders_var
        )
        subfolders_check.pack(side=tk.LEFT) # Use pack for simple horizontal layout here
        row_index += 1

        # Directory structure preview
        preview_frame = ttk.LabelFrame(self.scrollable_frame, text="Destination Directory Structure", padding=(10, 5))
        preview_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_rowconfigure(row_index, weight=1) # Make this frame expand vertically

        # Add a tree view to show the directory structure
        tree_frame = ttk.Frame(preview_frame) # No need for extra frame?
        tree_frame.grid(row=0, column=0, sticky='nsew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_y.grid(row=0, column=1, sticky='ns')
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.grid(row=1, column=0, sticky='ew')

        self.tree = ttk.Treeview(tree_frame,
                                 yscrollcommand=tree_scroll_y.set,
                                 xscrollcommand=tree_scroll_x.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # Setup columns
        self.tree["columns"] = ("path",)
        self.tree.column("#0", width=200, minwidth=150, stretch=tk.NO) # Don't stretch name column
        self.tree.column("path", width=400, minwidth=250, stretch=tk.YES) # Stretch path column

        self.tree.heading("#0", text="Directory")
        self.tree.heading("path", text="Path")

        # Add the basic structure nodes
        self._reset_tree_view()
        row_index += 1

        # YAML Editor section
        yaml_frame = ttk.LabelFrame(self.scrollable_frame, text="YAML Configuration Editor", padding=(10, 5))
        yaml_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        yaml_frame.grid_rowconfigure(0, weight=1)
        yaml_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_rowconfigure(row_index, weight=2) # Give YAML editor more vertical space

        # Add a text editor for direct YAML editing
        yaml_editor_frame = ttk.Frame(yaml_frame) # No need for extra frame?
        yaml_editor_frame.grid(row=0, column=0, sticky='nsew')
        yaml_editor_frame.grid_rowconfigure(0, weight=1)
        yaml_editor_frame.grid_columnconfigure(0, weight=1)

        yaml_scroll_y = ttk.Scrollbar(yaml_editor_frame, orient=tk.VERTICAL)
        yaml_scroll_y.grid(row=0, column=1, sticky='ns')

        yaml_scroll_x = ttk.Scrollbar(yaml_editor_frame, orient=tk.HORIZONTAL)
        yaml_scroll_x.grid(row=1, column=0, sticky='ew')

        # Use default font from theme
        default_font = font.nametofont("TkTextFont")
        self.yaml_editor = tk.Text(
            yaml_editor_frame,
            wrap=tk.NONE,
            yscrollcommand=yaml_scroll_y.set,
            xscrollcommand=yaml_scroll_x.set,
            height=15, # Initial height, will expand
            font=default_font,
            # Remove hardcoded bg/fg, use theme defaults
            # bg="#2b2b2b",
            # fg="white",
            # insertbackground="white" # Use theme default
        )
        self.yaml_editor.grid(row=0, column=0, sticky='nsew')

        yaml_scroll_y.config(command=self.yaml_editor.yview)
        yaml_scroll_x.config(command=self.yaml_editor.xview)

        # Configure syntax highlighting tags (adjust colors if needed for theme)
        # These might need tweaking depending on the chosen theme's contrast
        self.yaml_editor.tag_configure("key", foreground="navy")
        self.yaml_editor.tag_configure("value", foreground="forest green")
        self.yaml_editor.tag_configure("comment", foreground="grey")
        # self.yaml_editor.tag_configure("brackets", foreground="#d4d4d4") # Use default
        self.yaml_editor.tag_configure("string", foreground="purple")

        # Editor buttons
        editor_buttons = ttk.Frame(yaml_frame)
        editor_buttons.grid(row=1, column=0, sticky='ew', pady=(5,0))

        apply_button = ttk.Button(editor_buttons, text="Apply Changes", command=self._apply_yaml_changes)
        apply_button.pack(side=tk.LEFT, padx=(0, 5)) # Use pack for simple horizontal layout here

        revert_button = ttk.Button(editor_buttons, text="Revert Changes", command=self._revert_yaml_changes)
        revert_button.pack(side=tk.LEFT, padx=5) # Use pack for simple horizontal layout here
        row_index += 1

        # Initialize source directories list
        self.source_entries = []
        self._add_source_directory() # Add the first one

        # Remove style setup calls
        # self._setup_styles()
        # self._style_buttons()
    
    def _reset_tree_view(self):
        """Reset the tree view with default structure."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add base structure
        organized = self.tree.insert("", "end", text="Organized", open=True, tags=("folder", "organized"))
        
        self.tree.insert(organized, "end", text="Documents", values=("Documents/",), tags=("folder",))
        self.tree.insert(organized, "end", text="Media", values=("Media/",), tags=("folder",))
        self.tree.insert(organized, "end", text="Development", values=("Development/",), tags=("folder",))
        self.tree.insert(organized, "end", text="Archives", values=("Archives/",), tags=("folder",))
        self.tree.insert(organized, "end", text="Applications", values=("Applications/",), tags=("folder",))
        self.tree.insert(organized, "end", text="Other", values=("Other/",), tags=("folder",))
        
        cleanup = self.tree.insert("", "end", text="Cleanup", open=True, tags=("folder", "cleanup"))
        
        self.tree.insert(cleanup, "end", text="Temporary", values=("Temporary/",), tags=("folder",))
        self.tree.insert(cleanup, "end", text="Duplicates", values=("Duplicates/",), tags=("folder",))
    
    def _add_source_directory(self):
        """Add a new source directory entry to the list."""
        """Add a new source directory entry to the list using grid."""
        row_index = len(self.source_entries)

        # Create a frame for this entry
        entry_frame = ttk.Frame(self.source_frame_inner)
        entry_frame.grid(row=row_index, column=0, sticky='ew', pady=2)
        entry_frame.grid_columnconfigure(0, weight=1) # Make entry expand

        # Create a StringVar for this entry
        source_var = tk.StringVar()

        # If this is the first entry and we have a default source, use it
        if not self.source_entries and self.source_var.get():
            source_var.set(self.source_var.get())

        # Create the entry widget
        source_entry = ttk.Entry(entry_frame, textvariable=source_var)
        source_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))

        # Create browse button
        browse_button = ttk.Button(
            entry_frame,
            text="Browse...",
            command=lambda v=source_var: self._browse_source(v)
        )
        browse_button.grid(row=0, column=1, sticky='e', padx=(0, 5))

        # Create remove button (except for the first entry)
        remove_button = ttk.Button(
            entry_frame,
            text="Remove",
            command=lambda f=entry_frame, v=source_var: self._remove_source_directory(f, v)
        )
        if self.source_entries:
            remove_button.grid(row=0, column=2, sticky='e')
        # else: # No need for spacer with grid

        # Store this entry in our list (store var and frame)
        self.source_entries.append({'var': source_var, 'frame': entry_frame})
    def _remove_source_directory(self, frame_to_remove, var_to_remove):
        """Remove a source directory entry from the list."""
        # Find the entry in the list
        entry_to_remove = None
        for entry in self.source_entries:
            if entry['var'] == var_to_remove:
                entry_to_remove = entry
                break

        if entry_to_remove:
            # Remove from UI
            entry_to_remove['frame'].destroy()
            # Remove from our list
            self.source_entries.remove(entry_to_remove)
            # Re-grid remaining entries to close the gap (optional, grid handles it)
            # for i, entry in enumerate(self.source_entries):
            #     entry['frame'].grid(row=i, column=0, sticky='ew', pady=2)
        else:
            print("Warning: Could not find source directory entry to remove.")
    
    def _browse_source(self, string_var):
        """Browse for source directory."""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            string_var.set(directory)
    
    def _browse_dest(self):
        """Browse for destination directory."""
        directory = filedialog.askdirectory(title="Select Destination Base Directory")
        if directory:
            self.dest_var.set(directory)
    
    def _browse_config(self):
        """Browse for configuration file."""
        filetypes = [("YAML files", "*.yaml"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(
            title="Select Configuration File", 
            filetypes=filetypes
        )
        if filename:
            self.config_var.set(filename)
            self.current_config_path = filename
    
    def _load_current_config(self):
        """Load the current configuration file."""
        config_path = self.config_var.get()
        if not config_path:
            messagebox.showerror("Error", "No configuration file specified.")
            return
        
        try:
            self.load_configuration(config_path)
            messagebox.showinfo("Success", f"Configuration loaded from {config_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def _save_current_config(self):
        """Save the current configuration."""
        if self.save_configuration():
            messagebox.showinfo("Success", "Configuration saved successfully.")
    
    def _update_paths(self):
        """Update source and destination paths in the configuration."""
        # Get all source directories
        source_dirs = [entry[0].get() for entry in self.source_entries if entry[0].get()]
        
        if not source_dirs:
            messagebox.showerror("Error", "At least one source directory must be specified.")
            return
        
        dest_dir = self.dest_var.get()
        if not dest_dir:
            messagebox.showerror("Error", "Destination directory must be specified.")
            return
        try:
            # Get all source directories from UI
            source_dirs = [entry['var'].get() for entry in self.source_entries if entry['var'].get()]

            if not source_dirs:
                messagebox.showerror("Error", "At least one source directory must be specified.")
                return

            dest_dir = self.dest_var.get()
            if not dest_dir:
                messagebox.showerror("Error", "Destination directory must be specified.")
                return

            # Get the current configuration from YAML editor or manager
            config = self.get_current_config(from_editor=True) # Prioritize editor content
            if not config:
                messagebox.showerror("Error", "Could not parse current configuration from editor.")
                return

            # --- Update the configuration dictionary ---
            config_changed = False
            for rule in config.get('rules', []):
                # Update locations
                current_locs = rule.get('locations')
                new_locs = source_dirs[0] if len(source_dirs) == 1 else source_dirs
                if current_locs != new_locs:
                    rule['locations'] = new_locs
                    config_changed = True

                # Update subfolders
                current_subfolders = rule.get('subfolders')
                new_subfolders = self.subfolders_var.get()
                if current_subfolders != new_subfolders:
                     rule['subfolders'] = new_subfolders
                     config_changed = True

                # Update 'move' actions destination base path
                if 'actions' in rule:
                    for action in rule.get('actions', []):
                        move_action = None
                        dest_key = None
                        if isinstance(action, dict):
                            if 'move' in action:
                                move_action = action['move']
                                dest_key = 'move'
                            # Add other actions like 'copy' if needed
                            # elif 'copy' in action:
                            #     move_action = action['copy']
                            #     dest_key = 'copy'

                        if move_action is not None and dest_key is not None:
                            old_dest_path = None
                            if isinstance(move_action, dict) and 'dest' in move_action:
                                old_dest_path = move_action['dest']
                            elif isinstance(move_action, str):
                                old_dest_path = move_action

                            if old_dest_path and isinstance(old_dest_path, str) and '{' not in old_dest_path:
                                # Try to extract relative path after common markers
                                rel_path = self._extract_relative_path(old_dest_path)

                                if rel_path:
                                    # Construct new absolute path
                                    new_dest_path = os.path.join(dest_dir, rel_path).replace('\\', '/') # Normalize slashes

                                    if new_dest_path != old_dest_path:
                                        # Update the action dictionary
                                        if isinstance(move_action, dict):
                                            action[dest_key]['dest'] = new_dest_path
                                        elif isinstance(move_action, str):
                                            action[dest_key] = new_dest_path
                                        config_changed = True

            # --- If changes were made, update manager and UI ---
            if config_changed:
                 # Update the configuration manager if available
                 if self.config_manager:
                    self.config_manager.config = config

                 # Update the YAML editor
                 self._display_yaml_config(config) # Pass updated config

                 # Update the tree view based on the new destination
                 self._update_tree_view()

                 messagebox.showinfo("Success", "Paths updated in configuration.")

                 # Notify about the change
                 self.event_generate("<<ConfigurationChanged>>", when="tail")
            else:
                 messagebox.showinfo("Info", "Paths are already up-to-date in the configuration.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update paths: {str(e)}")

    # Remove style setup methods
    # def _setup_styles(self): ...
    # def _style_buttons(self): ...

    def _update_tree_view(self):
        """Update the tree view with the current destination path."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get the destination base directory
        dest_base = self.dest_var.get()
        if not dest_base:
            # If no destination set, use default structure
            self._reset_tree_view()
            return

        # Normalize base path
        dest_base = dest_base.replace('\\', '/')

        # Create the main structure nodes with correct paths
        organized_path = os.path.join(dest_base, "Organized").replace('\\', '/')
        cleanup_path = os.path.join(dest_base, "Cleanup").replace('\\', '/')

        organized = self.tree.insert("", "end", text="Organized", values=(organized_path + '/',), open=True, tags=("folder", "organized"))
        cleanup = self.tree.insert("", "end", text="Cleanup", values=(cleanup_path + '/',), open=True, tags=("folder", "cleanup"))

        # Add organized subdirectories
        self.tree.insert(organized, "end", text="Documents",
                         values=(os.path.join(organized_path, "Documents/"),), tags=("folder",))
        self.tree.insert(organized, "end", text="Media",
                         values=(os.path.join(organized_path, "Media/"),), tags=("folder",))
        self.tree.insert(organized, "end", text="Development",
                         values=(os.path.join(organized_path, "Development/"),), tags=("folder",))
        self.tree.insert(organized, "end", text="Archives",
                         values=(os.path.join(organized_path, "Archives/"),), tags=("folder",))
        self.tree.insert(organized, "end", text="Applications",
                         values=(os.path.join(organized_path, "Applications/"),), tags=("folder",))
        self.tree.insert(organized, "end", text="Other",
                         values=(os.path.join(organized_path, "Other/"),), tags=("folder",))

        # Add cleanup subdirectories
        self.tree.insert(cleanup, "end", text="Temporary",
                         values=(os.path.join(cleanup_path, "Temporary/"),), tags=("folder",))
        self.tree.insert(cleanup, "end", text="Duplicates",
                         values=(os.path.join(cleanup_path, "Duplicates/"),), tags=("folder",))

        # If we have a configuration loaded, check for additional paths
        config = self.get_current_config() # Get config (might be from editor)
        if config and 'rules' in config:
            for rule in config.get('rules', []):
                if 'actions' in rule:
                    for action in rule.get('actions', []):
                        move_action = None
                        if isinstance(action, dict):
                            if 'move' in action:
                                move_action = action['move']
                            # Add other actions if needed

                        if move_action is not None:
                            dest_path = None
                            if isinstance(move_action, dict) and 'dest' in move_action:
                                dest_path = move_action['dest']
                            elif isinstance(move_action, str):
                                dest_path = move_action

                            if dest_path and isinstance(dest_path, str) and '{' not in dest_path: # Skip template paths
                                self._add_path_to_tree(dest_path)

    def _add_path_to_tree(self, path):
        """Add a path to the tree view if it's not already there."""
        # Normalize path separators
        path = path.replace('\\', '/')
        dest_base = self.dest_var.get().replace('\\', '/')

        # Determine if this is an Organized or Cleanup path relative to dest_base
        rel_path = None
        parent_id = None
        base_marker = None

        if path.startswith(dest_base + '/Organized/'):
            parent_id = self.tree.get_children()[0] # First item should be Organized
            rel_path = path[len(dest_base)+1:] # Get path relative to dest_base
            base_marker = 'Organized'
        elif path.startswith(dest_base + '/Cleanup/'):
            parent_id = self.tree.get_children()[1] # Second item should be Cleanup
            rel_path = path[len(dest_base)+1:] # Get path relative to dest_base
            base_marker = 'Cleanup'
        else:
            # Path doesn't seem to be under the current base destination
            return

        # Split the relative path into components
        components = rel_path.rstrip('/').split('/') # e.g., ['Organized', 'Subdir', 'File']

        # Navigate/build the tree structure starting from the base marker
        current_id = parent_id
        current_path_abs = os.path.join(dest_base, base_marker).replace('\\', '/')

        # Start from the component *after* the base marker ('Organized' or 'Cleanup')
        for component in components[1:]:
            # Look for existing node under current_id
            found = False
            for child_id in self.tree.get_children(current_id):
                if self.tree.item(child_id, "text") == component:
                    current_id = child_id
                    current_path_abs = self.tree.item(child_id, "values")[0].rstrip('/')
                    found = True
                    break

            if not found:
                # Create the node if it doesn't exist
                new_path_abs = os.path.join(current_path_abs, component).replace('\\', '/') + '/'
                current_id = self.tree.insert(current_id, "end", text=component, values=(new_path_abs,), tags=("folder",))
                current_path_abs = new_path_abs.rstrip('/')


    def _extract_relative_path(self, path):
        """Extract the relative part of a path after Organized/ or Cleanup/."""
        # Normalize path separators
        path = path.replace('\\', '/')
        dest_base = self.dest_var.get().replace('\\', '/')

        # Check if path starts with the destination base + marker
        organized_prefix = dest_base + '/Organized/'
        cleanup_prefix = dest_base + '/Cleanup/'

        if path.startswith(organized_prefix):
            return 'Organized/' + path[len(organized_prefix):]
        elif path.startswith(cleanup_prefix):
            return 'Cleanup/' + path[len(cleanup_prefix):]

        # Fallback: Check for markers anywhere (less reliable)
        markers = ['/Organized/', '/Cleanup/']
        for marker in markers:
            if marker in path:
                parts = path.split(marker, 1)
                if len(parts) > 1:
                    # Return marker + rest of path
                    return marker.strip('/') + '/' + parts[1]

        # No known structure found
        print(f"Warning: Could not determine relative path structure for: {path}")
        return None # Indicate failure to find relative path

    def _apply_yaml_changes(self):
        """Apply changes from the YAML editor to the configuration."""
        yaml_text = self.yaml_editor.get("1.0", tk.END)

        try:
            # Parse the YAML
            config = yaml.safe_load(yaml_text)

            # Validate minimum structure
            if not config or not isinstance(config, dict) or 'rules' not in config:
                raise ValueError("Invalid configuration: missing 'rules' section")

            # Update the configuration manager
            if self.config_manager:
                self.config_manager.config = config

            # Update the UI elements based on the new config
            self._extract_paths_from_config(config) # Update source/dest fields
            self._update_tree_view() # Update tree based on dest field and config

            # Re-highlight syntax (optional, could be done on text change)
            self._highlight_yaml_syntax()

            # Notify about the change
            self.event_generate("<<ConfigurationChanged>>", when="tail")

            messagebox.showinfo("Success", "YAML changes applied successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply YAML changes: {str(e)}")

    def _revert_yaml_changes(self):
        """Revert changes in the YAML editor to match config manager."""
        # Get the current configuration from the manager
        config = None
        if self.config_manager:
            config = self.config_manager.config

        # Update the YAML editor
        if config:
            self._display_yaml_config(config) # Pass config to display
            messagebox.showinfo("Success", "YAML changes reverted to last loaded/saved state.")
        else:
            messagebox.showerror("Error", "No configuration loaded in manager to revert to.")

    def _display_yaml_config(self, config_to_display=None):
        """Display the given configuration (or current) in the YAML editor."""
        # Get the configuration to display
        config = config_to_display if config_to_display else self.get_current_config()

        # Clear the editor
        self.yaml_editor.delete("1.0", tk.END)

        # If we have a configuration, display it
        if config:
            try:
                # Convert to YAML
                yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)

                # Insert into the editor
                self.yaml_editor.insert("1.0", yaml_str)

                # Apply basic syntax highlighting
                self._highlight_yaml_syntax()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to display configuration: {str(e)}")

    def _highlight_yaml_syntax(self):
        """Apply basic syntax highlighting to the YAML editor."""
        self.yaml_editor.mark_set("range_start", "1.0")
        data = self.yaml_editor.get("1.0", tk.END)

        # Clear existing tags
        for tag in self.yaml_editor.tag_names():
             if tag not in ("sel",): # Don't remove selection tag
                 self.yaml_editor.tag_remove(tag, "1.0", tk.END)

        # Basic YAML highlighting (can be improved)
        key_pattern = r"^\s*([a-zA-Z0-9_]+)\s*:"
        comment_pattern = r"^\s*(#.*)"
        string_pattern = r"(\".*?\"|\'.*?\')" # Basic strings
        value_pattern = r":\s*(.*)" # Everything after colon

        for i, line in enumerate(data.splitlines()):
            line_num = i + 1

            # Comments
            match = re.search(comment_pattern, line)
            if match:
                start, end = match.span(1)
                self.yaml_editor.tag_add("comment", f"{line_num}.{start}", f"{line_num}.{end}")
                continue # Skip other patterns if it's a comment line

            # Keys
            match = re.search(key_pattern, line)
            if match:
                start, end = match.span(1)
                self.yaml_editor.tag_add("key", f"{line_num}.{start}", f"{line_num}.{end}")

                # Values (simple approach)
                val_match = re.search(value_pattern, line)
                if val_match:
                     val_start, val_end = val_match.span(1)
                     # Avoid highlighting keys within values if possible (tricky)
                     if val_start > end: # Only highlight if value starts after key:
                         # Highlight strings within the value first
                         for str_match in re.finditer(string_pattern, val_match.group(1)):
                             s_start, s_end = str_match.span(1)
                             self.yaml_editor.tag_add("string", f"{line_num}.{val_start + s_start}", f"{line_num}.{val_start + s_end}")
                         # Highlight the rest as generic value (could refine for numbers, bools)
                         # This simple approach might over-highlight
                         # self.yaml_editor.tag_add("value", f"{line_num}.{val_start}", f"{line_num}.{val_end}")


    def _extract_paths_from_config(self, config):
        """Extract source and destination paths from the configuration."""
        if not config or 'rules' not in config:
            return [], None # Return empty list and None

        # Extract source directories
        source_dirs_set = set() # Use a set to avoid duplicates initially
        for rule in config.get('rules', []):
            locations = rule.get('locations', [])
            if isinstance(locations, str):
                locations = [locations] # Treat single string as a list

            if isinstance(locations, list):
                for loc in locations:
                    path = None
                    if isinstance(loc, dict) and 'path' in loc:
                        path = loc['path']
                    elif isinstance(loc, str):
                        path = loc

                    if path and isinstance(path, str): # Ensure it's a string
                         source_dirs_set.add(path.replace('\\', '/')) # Normalize slashes

        source_dirs = sorted(list(source_dirs_set)) # Convert back to sorted list

        # Extract destination directory (find first non-template base path)
        dest_dir = None
        for rule in config.get('rules', []):
            if dest_dir: break # Stop once found
            for action in rule.get('actions', []):
                if dest_dir: break
                move_action = None
                if isinstance(action, dict):
                    if 'move' in action:
                        move_action = action['move']
                    # Add other actions if needed

                if move_action is not None:
                    dest_path = None
                    if isinstance(move_action, dict) and 'dest' in move_action:
                        dest_path = move_action['dest']
                    elif isinstance(move_action, str):
                        dest_path = move_action

                    if dest_path and isinstance(dest_path, str) and '{' not in dest_path:
                        # Extract base destination by splitting at known markers
                        path_norm = dest_path.replace('\\', '/')
                        markers = ['/Organized/', '/Cleanup/']
                        for marker in markers:
                            if marker in path_norm:
                                dest_dir = path_norm.split(marker)[0]
                                break # Found base path

        # --- Update the UI ---
        # Clear existing source entries except the first one
        while len(self.source_entries) > 1:
            entry_to_remove = self.source_entries.pop()
            entry_to_remove['frame'].destroy()

        # Clear or set the first source entry
        if self.source_entries: # Should always be true after init
            if source_dirs:
                self.source_entries[0]['var'].set(source_dirs[0]) # Use correct access
            else:
                self.source_entries[0]['var'].set("") # Clear if no sources found

            # Add additional source entries if needed
            for i in range(1, len(source_dirs)):
                self._add_source_directory() # Adds a new row
                self.source_entries[-1]['var'].set(source_dirs[i]) # Set value for the new row

        # Set the destination entry
        self.dest_var.set(dest_dir if dest_dir else "") # Set to found dir or empty


    # Public methods

    def get_current_config(self, from_editor=False):
        """Get the current configuration object, optionally prioritizing editor."""
        config = None

        # Option 1: Get from YAML editor first
        if from_editor:
            yaml_text = self.yaml_editor.get("1.0", tk.END).strip()
            if yaml_text:
                try:
                    parsed_config = yaml.safe_load(yaml_text)
                    # Basic validation
                    if parsed_config and isinstance(parsed_config, dict) and 'rules' in parsed_config:
                        config = parsed_config
                    else:
                         print("Warning: YAML editor content is invalid.")
                except Exception as e:
                    print(f"Warning: Could not parse YAML editor content: {e}")
                    # Fall through to try manager or default

        # Option 2: Get from config manager (if not already loaded from editor)
        if config is None and self.config_manager and self.config_manager.config:
            config = self.config_manager.config

        # Option 3: Fallback to a default structure if nothing else worked
        if config is None:
            print("Warning: No valid configuration found, returning default structure.")
            # Get source/dest from UI to include in default if possible
            ui_source = self.source_entries[0]['var'].get() if self.source_entries and self.source_entries[0]['var'].get() else os.path.expanduser("~/Documents")
            ui_dest_base = self.dest_var.get() if self.dest_var.get() else os.path.expanduser("~/Documents")
            ui_dest_org = os.path.join(ui_dest_base, "Organized/").replace('\\','/')

            config = {
                'rules': [
                    {
                        'name': 'Example Rule',
                        'enabled': True,
                        'targets': 'files',
                        'locations': [ui_source],
                        'subfolders': self.subfolders_var.get(),
                        'filters': [
                            {'extension': ['txt', 'pdf', 'doc', 'docx']}
                        ],
                        'actions': [
                            {'move': {'dest': ui_dest_org, 'on_conflict': 'rename_new'}}
                        ]
                    }
                ]
            }

        return config

    def new_configuration(self):
        """Create a new empty configuration."""
        # Define default paths used in this method
        default_source = os.path.expanduser("~/Documents")
        default_dest_base = os.path.expanduser("~/Documents") # Or maybe just ~ ?
        default_dest_org = os.path.join(default_dest_base, "Organized/").replace('\\','/')

        # Define a basic configuration structure using these defaults
        config = {
            'rules': [
                {
                    'name': 'Example Rule',
                    'enabled': True,
                    'targets': 'files',
                    'locations': [default_source],
                    'subfolders': self.subfolders_var.get(), # Use current checkbox state
                    'filters': [
                        {'extension': ['txt', 'pdf', 'doc', 'docx']}
                    ],
                    'actions': [
                        {'move': {'dest': default_dest_org, 'on_conflict': 'rename_new'}}
                    ]
                }
            ]
        }

        # Update the configuration manager
        if self.config_manager:
            self.config_manager.config = config

        # Clear the configuration path UI field
        self.current_config_path = None
        self.config_var.set("")

        # Update source and destination UI fields
        self._extract_paths_from_config(config) # Use the extraction logic

        # Update the tree view based on the new destination
        self._update_tree_view()

        # Update the YAML editor
        self._display_yaml_config(config) # Pass the new config

        # Generate an event to notify other components
        self.event_generate("<<ConfigurationChanged>>", when="tail")

    def load_configuration(self, config_path):
        """Load a configuration from a file."""
        try:
            # Load the configuration using the manager if available
            if self.config_manager:
                self.config_manager.load_config(config_path)
                config = self.config_manager.config
            else:
                # Load manually if no manager
                with open(config_path, 'r') as file:
                    config = yaml.safe_load(file)
                # Basic validation
                if not config or not isinstance(config, dict) or 'rules' not in config:
                     raise ValueError("Invalid configuration file format.")

            # Update the UI
            self.current_config_path = config_path
            self.config_var.set(config_path)

            # Extract source and destination directories from loaded config
            self._extract_paths_from_config(config)

            # Update the tree view based on the new destination
            self._update_tree_view()

            # Update the YAML editor
            self._display_yaml_config(config) # Pass loaded config

            # Generate an event to notify other components
            self.event_generate("<<ConfigurationChanged>>", when="tail")

            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            return False

    def open_configuration_dialog(self):
        """Open a file dialog to select and load a configuration."""
        filetypes = [("YAML files", "*.yaml;*.yml"), ("All files", "*.*")] # Added .yml
        filename = filedialog.askopenfilename(
            title="Open Configuration File",
            filetypes=filetypes
        )
        if filename:
            return self.load_configuration(filename)
        return False

    def save_configuration(self):
        """Save the current configuration (from editor) to its file."""
        if not self.current_config_path:
            return self.save_configuration_as() # Prompt for path if none exists

        try:
            # Get the current configuration from the editor
            config = self.get_current_config(from_editor=True)
            if not config:
                 messagebox.showerror("Error", "Cannot save invalid configuration from editor.")
                 return False

            # Save the configuration
            with open(self.current_config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False, sort_keys=False, indent=2)

            # Update manager if needed (optional, should match editor)
            if self.config_manager:
                 self.config_manager.config = config

            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            return False

    def save_configuration_as(self):
        """Save the current configuration (from editor) to a new file."""
        filetypes = [("YAML files", "*.yaml;*.yml"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(
            title="Save Configuration As",
            filetypes=filetypes,
            defaultextension=".yaml"
        )
        if filename:
            try:
                # Get the current configuration from the editor
                config = self.get_current_config(from_editor=True)
                if not config:
                    messagebox.showerror("Error", "Cannot save invalid configuration from editor.")
                    return False

                # Save the configuration
                with open(filename, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False, sort_keys=False, indent=2)

                # Update the current path in UI and internal state
                self.current_config_path = filename
                self.config_var.set(filename)

                # Update manager if needed
                if self.config_manager:
                    self.config_manager.config = config

                return True

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

        return False

    def update_config(self, config):
        """Update the panel's state with an external configuration object."""
        # Update the configuration manager
        if self.config_manager:
            self.config_manager.config = config

        # Update UI elements based on the provided config
        self._extract_paths_from_config(config)
        self._update_tree_view()
        self._display_yaml_config(config) # Display the provided config

        # Generate an event to notify other components
        # self.event_generate("<<ConfigurationChanged>>", when="tail") # Avoid loop if called from event
    
    def _setup_styles(self):
        """Set up custom styles for the UI."""
        style = ttk.Style()
        
        # Configure the Treeview style
        style.configure("Treeview", 
                        background="#2b2b2b",
                        foreground="white",
                        fieldbackground="#2b2b2b",
                        font=('Arial', 10))
        
        # Configure Treeview heading style
        style.configure("Treeview.Heading", 
                        background="#3c3f41",
                        foreground="white",
                        font=('Arial', 10, 'bold'))
        
        # Configure tag styles for the tree
        self.tree.tag_configure("folder", foreground="#4e9bcd")
        self.tree.tag_configure("organized", foreground="#92d050")
        self.tree.tag_configure("cleanup", foreground="#ffcc00")
    
    def _style_buttons(self):
        """Style buttons with a modern look."""
        style = ttk.Style()
        
        # Configure button style
        style.configure("TButton", 
                        background="#3c3f41",
                        foreground="white",
                        font=('Arial', 10))
        
        # Configure label style
        style.configure("TLabel", 
                        background="#2b2b2b",
                        foreground="white",
                        font=('Arial', 10))
        
        # Configure entry style
        style.configure("TEntry", 
                        fieldbackground="#3c3f41",
                        foreground="white")
    
    def _update_tree_view(self):
        """Update the tree view with the current destination path."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get the destination base directory
        dest_base = self.dest_var.get()
        if not dest_base:
            # If no destination set, use default structure
            self._reset_tree_view()
            return
        
        # Create the main structure nodes with correct paths
        organized = self.tree.insert("", "end", text="Organized", open=True, tags=("folder", "organized"))
        cleanup = self.tree.insert("", "end", text="Cleanup", open=True, tags=("folder", "cleanup"))
        
        # Add organized subdirectories
        docs = self.tree.insert(organized, "end", text="Documents", 
                          values=(os.path.join(dest_base, "Organized/Documents/"),), tags=("folder",))
        
        self.tree.insert(organized, "end", text="Media", 
                   values=(os.path.join(dest_base, "Organized/Media/"),), tags=("folder",))
        
        self.tree.insert(organized, "end", text="Development", 
                   values=(os.path.join(dest_base, "Organized/Development/"),), tags=("folder",))
        
        self.tree.insert(organized, "end", text="Archives", 
                   values=(os.path.join(dest_base, "Organized/Archives/"),), tags=("folder",))
        
        self.tree.insert(organized, "end", text="Applications", 
                   values=(os.path.join(dest_base, "Organized/Applications/"),), tags=("folder",))
        
        self.tree.insert(organized, "end", text="Other", 
                   values=(os.path.join(dest_base, "Organized/Other/"),), tags=("folder",))
        
        # Add cleanup subdirectories
        self.tree.insert(cleanup, "end", text="Temporary", 
                   values=(os.path.join(dest_base, "Cleanup/Temporary/"),), tags=("folder",))
        
        self.tree.insert(cleanup, "end", text="Duplicates", 
                   values=(os.path.join(dest_base, "Cleanup/Duplicates/"),), tags=("folder",))
        
        # If we have a configuration loaded, check for additional paths
        config = self.get_current_config()
        if config and 'rules' in config:
            for rule in config.get('rules', []):
                if 'actions' in rule:
                    for action in rule['actions']:
                        if isinstance(action, dict) and 'move' in action:
                            dest_path = None
                            if isinstance(action['move'], dict) and 'dest' in action['move']:
                                dest_path = action['move']['dest']
                            elif isinstance(action['move'], str):
                                dest_path = action['move']
                            
                            if dest_path and '{' not in dest_path:  # Skip template paths
                                self._add_path_to_tree(dest_path)
    
    def _add_path_to_tree(self, path):
        """Add a path to the tree view if it's not already there."""
        # Normalize path separators
        path = path.replace('\\', '/')
        
        # Determine if this is an Organized or Cleanup path
        if '/Organized/' in path:
            parent_id = self.tree.get_children()[0]  # First item should be Organized
            base_path = path.split('/Organized/')[0]
            rel_path = 'Organized/' + path.split('/Organized/')[1]
        elif '/Cleanup/' in path:
            parent_id = self.tree.get_children()[1]  # Second item should be Cleanup
            base_path = path.split('/Cleanup/')[0]
            rel_path = 'Cleanup/' + path.split('/Cleanup/')[1]
        else:
            # Can't determine structure, don't add
            return
        
        # Split the relative path into components
        components = rel_path.rstrip('/').split('/')
        
        # Navigate/build the tree structure
        current_id = parent_id
        current_path = base_path
        
        # Skip the first component as it's already represented by parent_id
        for i, component in enumerate(components[1:], 1):
            # Update current path
            current_path = os.path.join(current_path, components[i-1])
            
            # Look for existing node
            found = False
            for child_id in self.tree.get_children(current_id):
                if self.tree.item(child_id, "text") == component:
                    current_id = child_id
                    found = True
                    break
            
            if not found:
                # Create the node if it doesn't exist
                full_path = os.path.join(current_path, component) + '/'
                current_id = self.tree.insert(current_id, "end", text=component, values=(full_path,), tags=("folder",))
    
    def _extract_relative_path(self, path):
        """Extract the relative part of a path after Organized/ or Cleanup/."""
        # Try to extract relative path after common markers
        markers = ['Organized/', 'Cleanup/', 'organized/', 'cleanup/']
        
        for marker in markers:
            if marker in path:
                # Get the part after the marker
                rel_path = path.split(marker, 1)[1]
                if rel_path:
                    # Get the parts
                    parts = path.split(marker)
                    if len(parts) > 1:
                        # Return with the marker
                        return marker + parts[1]
        
        # No marker found, return as is
        return path
    
    def _apply_yaml_changes(self):
        """Apply changes from the YAML editor to the configuration."""
        yaml_text = self.yaml_editor.get("1.0", tk.END)
        
        try:
            # Parse the YAML
            config = yaml.safe_load(yaml_text)
            
            # Validate minimum structure
            if not config or not isinstance(config, dict) or 'rules' not in config:
                raise ValueError("Invalid configuration: missing 'rules' section")
            
            # Update the configuration
            if self.config_manager:
                self.config_manager.config = config
            else:
                # Store locally
                self._config = config
            
            # Update the UI
            self._update_tree_view()
            
            # Notify about the change
            self.event_generate("<<ConfigurationChanged>>", when="tail")
            
            messagebox.showinfo("Success", "YAML changes applied successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply YAML changes: {str(e)}")
    
    def _revert_yaml_changes(self):
        """Revert changes in the YAML editor."""
        # Get the current configuration
        config = self.get_current_config()
        
        # Update the YAML editor
        if config:
            self._display_yaml_config()
            messagebox.showinfo("Success", "YAML changes reverted.")
        else:
            messagebox.showerror("Error", "No configuration to revert to.")
    
    def _display_yaml_config(self):
        """Display the current configuration in the YAML editor."""
        # Get the current configuration
        config = self.get_current_config()
        
        # Clear the editor
        self.yaml_editor.delete("1.0", tk.END)
        
        # If we have a configuration, display it
        if config:
            try:
                # Convert to YAML
                yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)
                
                # Insert into the editor
                self.yaml_editor.insert("1.0", yaml_str)
                
                # Apply basic syntax highlighting
                self._highlight_yaml_syntax()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to display configuration: {str(e)}")
    
    def _highlight_yaml_syntax(self):
        """Apply basic syntax highlighting to the YAML editor."""
        # Get all text
        text = self.yaml_editor.get("1.0", tk.END)
        
        # Clear existing tags
        for tag in ["key", "value", "comment"]:
            self.yaml_editor.tag_remove(tag, "1.0", tk.END)
        
        # Apply tags line by line
        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check for comments
            if line.strip().startswith("#"):
                self.yaml_editor.tag_add("comment", f"{line_num}.0", f"{line_num}.end")
                continue
            
            # Check for key-value pairs
            if ":" in line:
                key_end = line.find(":")
                self.yaml_editor.tag_add("key", f"{line_num}.0", f"{line_num}.{key_end+1}")
                
                # Check if there's a value after the colon
                if key_end < len(line) - 1:
                    self.yaml_editor.tag_add("value", f"{line_num}.{key_end+1}", f"{line_num}.end")
    
    def _extract_paths_from_config(self, config):
        """Extract source and destination paths from the configuration."""
        if not config or 'rules' not in config:
            return
        
        # Extract source directories
        source_dirs = []
        for rule in config['rules']:
            if 'locations' in rule:
                if isinstance(rule['locations'], list):
                    for loc in rule['locations']:
                        if isinstance(loc, dict) and 'path' in loc:
                            if loc['path'] not in source_dirs:
                                source_dirs.append(loc['path'])
                        elif isinstance(loc, str):
                            if loc not in source_dirs:
                                source_dirs.append(loc)
                elif isinstance(rule['locations'], str):
                    if rule['locations'] not in source_dirs:
                        source_dirs.append(rule['locations'])
        
        # Extract destination directory
        dest_dir = None
        for rule in config['rules']:
            if 'actions' in rule:
                for action in rule['actions']:
                    if isinstance(action, dict) and 'move' in action:
                        if isinstance(action['move'], dict) and 'dest' in action['move']:
                            dest = action['move']['dest']
                            if '{' not in dest:  # Skip template destinations
                                # Extract base destination
                                if '/Organized/' in dest:
                                    dest_dir = dest.split('/Organized/')[0]
                                    break
                                elif '/Cleanup/' in dest:
                                    dest_dir = dest.split('/Cleanup/')[0]
                                    break
                        elif isinstance(action['move'], str):
                            dest = action['move']
                            if '{' not in dest:  # Skip template destinations
                                # Extract base destination
                                if '/Organized/' in dest:
                                    dest_dir = dest.split('/Organized/')[0]
                                    break
                                elif '/Cleanup/' in dest:
                                    dest_dir = dest.split('/Cleanup/')[0]
                                    break
        
        # Update the UI
        # First, clear existing source entries except the first one
        while len(self.source_entries) > 1:
            entry = self.source_entries[-1]
            entry[3].destroy()
            self.source_entries.pop()
        
        # Set the first source entry
        if source_dirs:
            self.source_entries[0][0].set(source_dirs[0])
            
            # Add additional source entries if needed
            for i in range(1, len(source_dirs)):
                self._add_source_directory()
                self.source_entries[-1][0].set(source_dirs[i])
        
        # Set the destination entry
        if dest_dir:
            self.dest_var.set(dest_dir)

    # Public methods
    
    def get_current_config(self):
        """Get the current configuration object."""
        # First check if we have a config manager
        if self.config_manager and self.config_manager.config:
            return self.config_manager.config
        
        # Otherwise check if we have a local config
        if hasattr(self, '_config'):
            return self._config
        
        # Check the YAML editor content
        yaml_text = self.yaml_editor.get("1.0", tk.END).strip()
        if yaml_text:
            try:
                # Parse the YAML
                import yaml
                config = yaml.safe_load(yaml_text)
                
                # Validate minimum structure
                if config and isinstance(config, dict) and 'rules' in config:
                    return config
            except Exception:
                # If parsing fails, ignore
                pass
        
        # If no configuration is available, return a basic structure
        return {
            'rules': [
                {
                    'name': 'Example Rule',
                    'enabled': True,
                    'targets': 'files',
                    'locations': [os.path.expanduser("~/Documents")],
                    'subfolders': True,
                    'filters': [
                        {'extension': ['txt', 'pdf', 'doc', 'docx']}
                    ],
                    'actions': [
                        {'move': {'dest': os.path.expanduser("~/Documents/Organized/"), 'on_conflict': 'rename_new'}}
                    ]
                }
            ]
        }
    
    def new_configuration(self):
        """Create a new empty configuration."""
        # Create a basic configuration
        config = {
            'rules': [
                {
                    'name': 'Example Rule',
                    'enabled': True,
                    'targets': 'files',
                    'locations': [os.path.expanduser("~/Documents")],
                    'subfolders': self.subfolders_var.get(),
                    'filters': [
                        {'extension': ['txt', 'pdf', 'doc', 'docx']}
                    ],
                    'actions': [
                        {'move': {'dest': os.path.expanduser("~/Documents/Organized/"), 'on_conflict': 'rename_new'}}
                    ]
                }
            ]
        }
        
        # Update the configuration
        if self.config_manager:
            self.config_manager.config = config
        else:
            # Store the configuration directly
            self._config = config
        
        # Clear the configuration path
        self.current_config_path = None
        self.config_var.set("")

        # Update source and destination entries
        if self.source_entries: # Ensure list is not empty
            self.source_entries[0]['var'].set(default_source) # Use correct access
        self.dest_var.set(default_dest_base) # Use base path for dest field

        # Update the tree view
        self._update_tree_view()
        
        # Update the YAML editor
        self._display_yaml_config()
        
        # Generate an event to notify other components about the configuration change
        self.event_generate("<<ConfigurationChanged>>", when="tail")
    
    def load_configuration(self, config_path):
        """Load a configuration from a file."""
        try:
            # Load the configuration
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            # Update the configuration
            if self.config_manager:
                self.config_manager.load_config(config_path)
                config = self.config_manager.config
            else:
                # Store the configuration directly
                self._config = config
            
            # Update the UI
            self.current_config_path = config_path
            self.config_var.set(config_path)
            
            # Extract source and destination directories
            self._extract_paths_from_config(config)
            
            # Update the tree view
            self._update_tree_view()
            
            # Update the YAML editor
            self._display_yaml_config()
            
            # Generate an event to notify other components about the configuration change
            self.event_generate("<<ConfigurationChanged>>", when="tail")
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            return False
    
    def open_configuration_dialog(self):
        """Open a file dialog to select and load a configuration."""
        filetypes = [("YAML files", "*.yaml"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(
            title="Open Configuration File", 
            filetypes=filetypes
        )
        if filename:
            return self.load_configuration(filename)
        return False
    
    def save_configuration(self):
        """Save the current configuration to its file."""
        if not self.current_config_path:
            return self.save_configuration_as()
        
        try:
            # Get the current configuration
            config = self.get_current_config()
            
            # Save the configuration
            with open(self.current_config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False, sort_keys=False)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            return False
    
    def save_configuration_as(self):
        """Save the current configuration to a new file."""
        filetypes = [("YAML files", "*.yaml"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(
            title="Save Configuration As", 
            filetypes=filetypes,
            defaultextension=".yaml"
        )
        if filename:
            try:
                # Get the current configuration
                config = self.get_current_config()
                
                # Save the configuration
                with open(filename, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False, sort_keys=False)
                
                # Update the current path
                self.current_config_path = filename
                self.config_var.set(filename)
                
                return True
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
                
        return False
    
    def update_config(self, config):
        """Update the current configuration with a new one."""
        # Update the configuration
        if self.config_manager:
            self.config_manager.config = config
        else:
            # Store the configuration directly
            self._config = config
        
        # Update the YAML editor
        self._display_yaml_config()
        
        # Update the tree view
        self._update_tree_view()
        
        # Generate an event to notify other components about the configuration change
        self.event_generate("<<ConfigurationChanged>>", when="tail")
