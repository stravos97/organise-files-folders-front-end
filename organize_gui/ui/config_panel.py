"""
Configuration panel for the File Organization System.

This implementation provides a complete interface for managing organize-tool
configurations, including source and destination directories.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
        """Create the UI components for the configuration panel."""
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
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main container for all configuration elements
        main_frame = ttk.Frame(self.scrollable_frame, padding=(10, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configuration file section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration File", padding=(10, 5))
        config_frame.pack(fill=tk.X, pady=5)
        
        self.config_var = tk.StringVar()
        config_entry = ttk.Entry(config_frame, textvariable=self.config_var, width=50)
        config_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        config_button = ttk.Button(config_frame, text="Browse...", command=self._browse_config)
        config_button.pack(side=tk.RIGHT)
        
        # File operation buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        load_button = ttk.Button(button_frame, text="Load Configuration", 
                                command=self._load_current_config)
        load_button.pack(side=tk.LEFT, padx=5)
        
        save_button = ttk.Button(button_frame, text="Save Configuration", 
                                command=self._save_current_config)
        save_button.pack(side=tk.LEFT, padx=5)
        
        # Source directory section
        source_frame = ttk.LabelFrame(main_frame, text="Source Directories", padding=(10, 5))
        source_frame.pack(fill=tk.X, pady=5)
        
        # Create a dynamic list of source directories
        self.source_frame_inner = ttk.Frame(source_frame)
        self.source_frame_inner.pack(fill=tk.X, expand=True)
        
        # Source directory controls
        source_controls = ttk.Frame(source_frame)
        source_controls.pack(fill=tk.X, pady=5)
        
        add_source_button = ttk.Button(source_controls, text="Add Source Directory", 
                                      command=self._add_source_directory)
        add_source_button.pack(side=tk.LEFT, padx=5)
        
        # Default source directory (used for initial setup)
        self.source_var = tk.StringVar()
        
        # Destination directory section
        dest_frame = ttk.LabelFrame(main_frame, text="Destination Base Directory", padding=(10, 5))
        dest_frame.pack(fill=tk.X, pady=5)
        
        self.dest_var = tk.StringVar()
        dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_var, width=50)
        dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        dest_button = ttk.Button(dest_frame, text="Browse...", command=self._browse_dest)
        dest_button.pack(side=tk.RIGHT)
        
        # Update paths button
        update_button = ttk.Button(main_frame, text="Update All Paths", 
                                  command=self._update_paths)
        update_button.pack(anchor=tk.W, pady=5)
        
        # Subdirectory control
        subdir_frame = ttk.Frame(main_frame)
        subdir_frame.pack(fill=tk.X, pady=5)
        
        self.subfolders_var = tk.BooleanVar(value=True)
        subfolders_check = ttk.Checkbutton(
            subdir_frame, 
            text="Include Subfolders (applies to all new rules)",
            variable=self.subfolders_var
        )
        subfolders_check.pack(side=tk.LEFT)
        
        # Directory structure preview
        preview_frame = ttk.LabelFrame(main_frame, text="Destination Directory Structure", padding=(10, 5))
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add a tree view to show the directory structure
        tree_frame = ttk.Frame(preview_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        
        # Setup columns
        self.tree["columns"] = ("path",)
        self.tree.column("#0", width=200, minwidth=150)
        self.tree.column("path", width=300, minwidth=200)
        
        self.tree.heading("#0", text="Directory")
        self.tree.heading("path", text="Path")
        
        # Add the basic structure nodes
        self._reset_tree_view()
        
        # YAML Editor section
        yaml_frame = ttk.LabelFrame(main_frame, text="YAML Configuration Editor", padding=(10, 5))
        yaml_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add a text editor for direct YAML editing
        yaml_editor_frame = ttk.Frame(yaml_frame)
        yaml_editor_frame.pack(fill=tk.BOTH, expand=True)
        
        yaml_scroll_y = ttk.Scrollbar(yaml_editor_frame)
        yaml_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        yaml_scroll_x = ttk.Scrollbar(yaml_editor_frame, orient='horizontal')
        yaml_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.yaml_editor = tk.Text(
            yaml_editor_frame, 
            wrap=tk.NONE,
            yscrollcommand=yaml_scroll_y.set,
            xscrollcommand=yaml_scroll_x.set,
            height=15,
            font=("Courier", 10)
        )
        self.yaml_editor.pack(fill=tk.BOTH, expand=True)
        
        yaml_scroll_y.config(command=self.yaml_editor.yview)
        yaml_scroll_x.config(command=self.yaml_editor.xview)
        
        # Add syntax highlighting for YAML (basic)
        self.yaml_editor.tag_configure("key", foreground="blue")
        self.yaml_editor.tag_configure("value", foreground="green")
        self.yaml_editor.tag_configure("comment", foreground="gray")
        
        # Editor buttons
        editor_buttons = ttk.Frame(yaml_frame)
        editor_buttons.pack(fill=tk.X, pady=5)
        
        apply_button = ttk.Button(editor_buttons, text="Apply Changes", 
                                 command=self._apply_yaml_changes)
        apply_button.pack(side=tk.LEFT, padx=5)
        
        revert_button = ttk.Button(editor_buttons, text="Revert Changes", 
                                  command=self._revert_yaml_changes)
        revert_button.pack(side=tk.LEFT, padx=5)
        
        # Initialize source directories list
        self.source_entries = []
        self._add_source_directory()
    
    def _reset_tree_view(self):
        """Reset the tree view with default structure."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add base structure
        organized = self.tree.insert("", "end", text="Organized", open=True)
        
        self.tree.insert(organized, "end", text="Documents", values=("Documents/",))
        self.tree.insert(organized, "end", text="Media", values=("Media/",))
        self.tree.insert(organized, "end", text="Development", values=("Development/",))
        self.tree.insert(organized, "end", text="Archives", values=("Archives/",))
        self.tree.insert(organized, "end", text="Applications", values=("Applications/",))
        self.tree.insert(organized, "end", text="Other", values=("Other/",))
        
        cleanup = self.tree.insert("", "end", text="Cleanup", open=True)
        
        self.tree.insert(cleanup, "end", text="Temporary", values=("Temporary/",))
        self.tree.insert(cleanup, "end", text="Duplicates", values=("Duplicates/",))
    
    def _add_source_directory(self):
        """Add a new source directory entry to the list."""
        # Create a frame for this entry
        entry_frame = ttk.Frame(self.source_frame_inner)
        entry_frame.pack(fill=tk.X, pady=2)
        
        # Create a StringVar for this entry
        source_var = tk.StringVar()
        
        # If this is the first entry and we have a default source, use it
        if not self.source_entries and self.source_var.get():
            source_var.set(self.source_var.get())
        
        # Create the entry widget
        source_entry = ttk.Entry(entry_frame, textvariable=source_var, width=50)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Create browse button
        browse_button = ttk.Button(
            entry_frame, 
            text="Browse...", 
            command=lambda v=source_var: self._browse_source(v)
        )
        browse_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create remove button (except for the first entry)
        if self.source_entries:
            remove_button = ttk.Button(
                entry_frame, 
                text="Remove", 
                command=lambda f=entry_frame, e=(source_var, source_entry, browse_button): self._remove_source_directory(f, e)
            )
            remove_button.pack(side=tk.LEFT)
        else:
            # For the first entry, just add a spacer
            spacer = ttk.Frame(entry_frame, width=60)
            spacer.pack(side=tk.LEFT)
        
        # Store this entry in our list
        self.source_entries.append((source_var, source_entry, browse_button, entry_frame))
    
    def _remove_source_directory(self, frame, entry_tuple):
        """Remove a source directory entry from the list."""
        # Remove from UI
        frame.destroy()
        
        # Remove from our list
        self.source_entries.remove(entry_tuple)
    
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
            # Get the current configuration
            config = self.get_current_config()
            if not config:
                messagebox.showerror("Error", "No configuration loaded.")
                return
            
            # Update the configuration
            for rule in config.get('rules', []):
                # Update locations
                if 'locations' in rule:
                    if len(source_dirs) == 1:
                        rule['locations'] = source_dirs[0]
                    else:
                        rule['locations'] = source_dirs.copy()
                
                # Update subfolders
                rule['subfolders'] = self.subfolders_var.get()
                
                # Update actions
                if 'actions' in rule:
                    for action in rule['actions']:
                        if isinstance(action, dict) and 'move' in action:
                            if isinstance(action['move'], dict) and 'dest' in action['move']:
                                # Extract the path after Organized/ or Cleanup/
                                old_dest = action['move']['dest']
                                rel_path = None
                                
                                if '/Organized/' in old_dest:
                                    rel_path = 'Organized/' + old_dest.split('/Organized/')[1]
                                elif '/Cleanup/' in old_dest:
                                    rel_path = 'Cleanup/' + old_dest.split('/Cleanup/')[1]
                                elif 'Organized/' in old_dest:
                                    rel_path = old_dest
                                elif 'Cleanup/' in old_dest:
                                    rel_path = old_dest
                                
                                if rel_path:
                                    action['move']['dest'] = os.path.join(dest_dir, rel_path)
                            
                            elif isinstance(action['move'], str):
                                old_dest = action['move']
                                rel_path = None
                                
                                if '/Organized/' in old_dest:
                                    rel_path = 'Organized/' + old_dest.split('/Organized/')[1]
                                elif '/Cleanup/' in old_dest:
                                    rel_path = 'Cleanup/' + old_dest.split('/Cleanup/')[1]
                                elif 'Organized/' in old_dest:
                                    rel_path = old_dest
                                elif 'Cleanup/' in old_dest:
                                    rel_path = old_dest
                                
                                if rel_path:
                                    action['move'] = os.path.join(dest_dir, rel_path)
            
            # Update the configuration manager if available
            if self.config_manager:
                self.config_manager.config = config
            
            # Update the YAML editor
            self._display_yaml_config()
            
            # Update the tree view
            self._update_tree_view()
            
            messagebox.showinfo("Success", "Paths updated successfully.")
            
            # Notify about the change
            self.event_generate("<<ConfigurationChanged>>", when="tail")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update paths: {str(e)}")
    
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
        organized = self.tree.insert("", "end", text="Organized", open=True)
        cleanup = self.tree.insert("", "end", text="Cleanup", open=True)
        
        # Add organized subdirectories
        docs = self.tree.insert(organized, "end", text="Documents", 
                          values=(os.path.join(dest_base, "Organized/Documents/"),))
        
        self.tree.insert(organized, "end", text="Media", 
                   values=(os.path.join(dest_base, "Organized/Media/"),))
        
        self.tree.insert(organized, "end", text="Development", 
                   values=(os.path.join(dest_base, "Organized/Development/"),))
        
        self.tree.insert(organized, "end", text="Archives", 
                   values=(os.path.join(dest_base, "Organized/Archives/"),))
        
        self.tree.insert(organized, "end", text="Applications", 
                   values=(os.path.join(dest_base, "Organized/Applications/"),))
        
        self.tree.insert(organized, "end", text="Other", 
                   values=(os.path.join(dest_base, "Organized/Other/"),))
        
        # Add cleanup subdirectories
        self.tree.insert(cleanup, "end", text="Temporary", 
                   values=(os.path.join(dest_base, "Cleanup/Temporary/"),))
        
        self.tree.insert(cleanup, "end", text="Duplicates", 
                   values=(os.path.join(dest_base, "Cleanup/Duplicates/"),))
        
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
                current_id = self.tree.insert(current_id, "end", text=component, values=(full_path,))
    
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
        self.source_entries[0][0].set(os.path.expanduser("~/Documents"))
        self.dest_var.set(os.path.expanduser("~/Documents/Organized"))
        
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