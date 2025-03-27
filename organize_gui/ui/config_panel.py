"""
Configuration panel for the File Organization System.

Uses YamlEditorPanel for the YAML editing part.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import yaml
import re
from pathlib import Path

# Import the new panel
from .yaml_editor_panel import YamlEditorPanel

class ConfigPanel(ttk.Frame):
    """Panel for editing configuration settings."""

    def __init__(self, parent, config_manager=None):
        """Initialize the configuration panel."""
        super().__init__(parent)

        # Initialize the config manager
        self.config_manager = config_manager

        # Current configuration path
        self.current_config_path = None
        self._config = None # Internal storage if no manager

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

        row_index = 0

        # Configuration file section
        config_frame = ttk.LabelFrame(self.scrollable_frame, text="Configuration File", padding=(10, 5))
        config_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        config_frame.grid_columnconfigure(0, weight=1)
        self.config_var = tk.StringVar()
        config_entry = ttk.Entry(config_frame, textvariable=self.config_var, state='readonly') # Readonly for display
        config_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        config_button = ttk.Button(config_frame, text="Browse...", command=self._browse_config)
        config_button.grid(row=0, column=1, sticky='e')
        row_index += 1

        # File operation buttons
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        load_button = ttk.Button(button_frame, text="Load Configuration", command=self._load_current_config)
        load_button.pack(side=tk.LEFT, padx=(0, 5))
        save_button = ttk.Button(button_frame, text="Save Configuration", command=self._save_current_config)
        save_button.pack(side=tk.LEFT, padx=5)
        save_as_button = ttk.Button(button_frame, text="Save As...", command=self.save_configuration_as)
        save_as_button.pack(side=tk.LEFT, padx=5)
        new_button = ttk.Button(button_frame, text="New Configuration", command=self.new_configuration)
        new_button.pack(side=tk.LEFT, padx=5)
        row_index += 1

        # Source directory section
        source_frame = ttk.LabelFrame(self.scrollable_frame, text="Source Directories", padding=(10, 5))
        source_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        source_frame.grid_columnconfigure(0, weight=1)
        self.source_frame_inner = ttk.Frame(source_frame)
        self.source_frame_inner.grid(row=0, column=0, sticky='nsew')
        self.source_frame_inner.grid_columnconfigure(0, weight=1)
        source_controls = ttk.Frame(source_frame)
        source_controls.grid(row=1, column=0, sticky='ew', pady=(5,0))
        add_source_button = ttk.Button(source_controls, text="Add Source Directory", command=self._add_source_directory)
        add_source_button.pack(side=tk.LEFT)
        row_index += 1

        # Destination directory section
        dest_frame = ttk.LabelFrame(self.scrollable_frame, text="Destination Base Directory", padding=(10, 5))
        dest_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        dest_frame.grid_columnconfigure(0, weight=1)
        self.dest_var = tk.StringVar()
        dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_var)
        dest_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        dest_button = ttk.Button(dest_frame, text="Browse...", command=self._browse_dest)
        dest_button.grid(row=0, column=1, sticky='e')
        self.dest_var.trace_add("write", lambda *args: self._update_tree_view())
        row_index += 1

        # Update paths button
        update_button = ttk.Button(self.scrollable_frame, text="Update Paths in YAML", command=self._update_paths)
        update_button.grid(row=row_index, column=0, sticky='w', padx=10, pady=5)
        row_index += 1

        # Subdirectory control
        subdir_frame = ttk.Frame(self.scrollable_frame)
        subdir_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        self.subfolders_var = tk.BooleanVar(value=True)
        subfolders_check = ttk.Checkbutton(subdir_frame, text="Include Subfolders (applies to rules)", variable=self.subfolders_var)
        subfolders_check.pack(side=tk.LEFT)
        row_index += 1

        # Directory structure preview
        preview_frame = ttk.LabelFrame(self.scrollable_frame, text="Destination Directory Structure Preview", padding=(10, 5))
        preview_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_rowconfigure(row_index, weight=1) # Expand vertically

        tree_frame = ttk.Frame(preview_frame)
        tree_frame.grid(row=0, column=0, sticky='nsew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_y.grid(row=0, column=1, sticky='ns')
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.grid(row=1, column=0, sticky='ew')
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        self.tree["columns"] = ("path",)
        self.tree.column("#0", width=200, minwidth=150, stretch=tk.NO)
        self.tree.column("path", width=400, minwidth=250, stretch=tk.YES)
        self.tree.heading("#0", text="Directory")
        self.tree.heading("path", text="Path")
        self._reset_tree_view()
        row_index += 1

        # --- YAML Editor Panel ---
        yaml_outer_frame = ttk.LabelFrame(self.scrollable_frame, text="YAML Configuration Editor", padding=(10, 5))
        yaml_outer_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        yaml_outer_frame.grid_rowconfigure(0, weight=1)
        yaml_outer_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_rowconfigure(row_index, weight=2) # Give editor space

        self.yaml_editor_panel = YamlEditorPanel(
            yaml_outer_frame, # Parent is the LabelFrame
            apply_callback=self._apply_yaml_changes_callback,
            revert_callback=self._revert_yaml_changes_callback
        )
        self.yaml_editor_panel.grid(row=0, column=0, sticky='nsew') # Grid inside LabelFrame
        row_index += 1

        # Initialize source directories list
        self.source_entries = []
        self._add_source_directory() # Add the first one

    def _reset_tree_view(self):
        """Reset the tree view with default structure."""
        for item in self.tree.get_children(): self.tree.delete(item)
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
        """Add a new source directory entry UI."""
        row_index = len(self.source_entries)
        entry_frame = ttk.Frame(self.source_frame_inner)
        entry_frame.grid(row=row_index, column=0, sticky='ew', pady=2)
        entry_frame.grid_columnconfigure(0, weight=1)
        source_var = tk.StringVar()
        source_entry = ttk.Entry(entry_frame, textvariable=source_var)
        source_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        browse_button = ttk.Button(entry_frame, text="Browse...", command=lambda v=source_var: self._browse_source(v))
        browse_button.grid(row=0, column=1, sticky='e', padx=(0, 5))
        remove_button = ttk.Button(entry_frame, text="Remove", command=lambda f=entry_frame, v=source_var: self._remove_source_directory(f, v))
        if self.source_entries: remove_button.grid(row=0, column=2, sticky='e')
        self.source_entries.append({'var': source_var, 'frame': entry_frame})

    def _remove_source_directory(self, frame_to_remove, var_to_remove):
        """Remove a source directory entry UI and data."""
        entry_to_remove = next((entry for entry in self.source_entries if entry['var'] == var_to_remove), None)
        if entry_to_remove:
            entry_to_remove['frame'].destroy()
            self.source_entries.remove(entry_to_remove)
        else: print("Warning: Could not find source directory entry to remove.")

    def _browse_source(self, string_var):
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory: string_var.set(directory)

    def _browse_dest(self):
        directory = filedialog.askdirectory(title="Select Destination Base Directory")
        if directory: self.dest_var.set(directory)

    def _browse_config(self):
        try:
            # Use space separation for macOS compatibility
            filetypes = [("YAML files", "*.yaml *.yml"), ("All files", "*")]
            filename = filedialog.askopenfilename(title="Select Configuration File", filetypes=filetypes)
            if filename:
                self.config_var.set(filename)
                self.current_config_path = filename
                self._load_current_config() # Auto-load after browse
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file dialog: {str(e)}")

    def _load_current_config(self):
        config_path = self.config_var.get()
        if not config_path: messagebox.showerror("Error", "No configuration file specified."); return
        if not os.path.exists(config_path): messagebox.showerror("Error", f"File not found:\n{config_path}"); return
        if self.load_configuration(config_path):
            messagebox.showinfo("Success", f"Configuration loaded from\n{config_path}")

    def _save_current_config(self):
        if self.save_configuration():
            messagebox.showinfo("Success", f"Configuration saved to\n{self.current_config_path}")

    def _update_paths(self):
        """Update source/dest paths in the config based on UI fields and update editor."""
        try:
            source_dirs = [entry['var'].get() for entry in self.source_entries if entry['var'].get()]
            if not source_dirs: raise ValueError("At least one source directory must be specified.")
            dest_dir = self.dest_var.get()
            if not dest_dir: raise ValueError("Destination directory must be specified.")

            config_text = self.yaml_editor_panel.get_text()
            config = yaml.safe_load(config_text)
            if not config or not isinstance(config, dict) or 'rules' not in config: raise ValueError("Invalid configuration in editor.")

            config_changed = False
            for rule in config.get('rules', []):
                new_locs = source_dirs[0] if len(source_dirs) == 1 else source_dirs
                if rule.get('locations') != new_locs: rule['locations'] = new_locs; config_changed = True
                new_subfolders = self.subfolders_var.get()
                if rule.get('subfolders') != new_subfolders: rule['subfolders'] = new_subfolders; config_changed = True

                for action in rule.get('actions', []):
                    action_type = next(iter(action)) if isinstance(action, dict) else None
                    if action_type in ('move', 'copy'):
                        action_value = action[action_type]
                        old_dest_path, is_dict_action = (action_value.get('dest'), True) if isinstance(action_value, dict) else (action_value, False)
                        if old_dest_path and isinstance(old_dest_path, str) and '{' not in old_dest_path:
                            rel_path = self._extract_relative_path(old_dest_path)
                            if rel_path:
                                new_dest_path = os.path.join(dest_dir, rel_path).replace('\\', '/')
                                if new_dest_path != old_dest_path:
                                    if is_dict_action: action[action_type]['dest'] = new_dest_path
                                    else: action[action_type] = new_dest_path
                                    config_changed = True
            if config_changed:
                 updated_yaml = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)
                 self.yaml_editor_panel.set_text(updated_yaml)
                 if self.config_manager: self.config_manager.config = config # Keep manager in sync
                 messagebox.showinfo("Success", "Paths updated in YAML editor. Review and Apply/Save.")
            else: messagebox.showinfo("Info", "Paths seem up-to-date based on current UI fields.")
        except Exception as e: messagebox.showerror("Error", f"Failed to update paths: {str(e)}")

    def _update_tree_view(self, *args):
        """Update the tree view based on the destination path and config."""
        for item in self.tree.get_children(): self.tree.delete(item)
        dest_base = self.dest_var.get()
        if not dest_base: self._reset_tree_view(); return

        dest_base_norm = dest_base.replace('\\', '/')
        organized_path = os.path.join(dest_base_norm, "Organized").replace('\\', '/')
        cleanup_path = os.path.join(dest_base_norm, "Cleanup").replace('\\', '/')
        organized = self.tree.insert("", "end", text="Organized", values=(organized_path + '/',), open=True, tags=("folder", "organized"))
        cleanup = self.tree.insert("", "end", text="Cleanup", values=(cleanup_path + '/',), open=True, tags=("folder", "cleanup"))
        for cat in ["Documents", "Media", "Development", "Archives", "Applications", "Other"]: self.tree.insert(organized, "end", text=cat, values=(os.path.join(organized_path, cat + '/'),), tags=("folder",))
        for cat in ["Temporary", "Duplicates"]: self.tree.insert(cleanup, "end", text=cat, values=(os.path.join(cleanup_path, cat + '/'),), tags=("folder",))

        try: # Add paths from editor config
            config_text = self.yaml_editor_panel.get_text()
            config = yaml.safe_load(config_text) if config_text else None
            if config and 'rules' in config:
                for rule in config.get('rules', []):
                    for action in rule.get('actions', []):
                        action_type = next(iter(action)) if isinstance(action, dict) else None
                        if action_type in ('move', 'copy'):
                            action_value = action[action_type]
                            dest_path = action_value.get('dest') if isinstance(action_value, dict) else action_value
                            if dest_path and isinstance(dest_path, str) and '{' not in dest_path: self._add_path_to_tree(dest_path)
        except Exception as e: print(f"Warning: Could not parse editor YAML for tree update: {e}")

    def _add_path_to_tree(self, path):
        """Add a potentially nested path relative to dest_base to the tree view."""
        path_norm = path.replace('\\', '/')
        dest_base_norm = self.dest_var.get().replace('\\', '/')
        if not dest_base_norm: return
        rel_path_parts, parent_node_id = (None, None)
        organized_prefix, cleanup_prefix = (dest_base_norm + '/Organized/', dest_base_norm + '/Cleanup/')
        if path_norm.startswith(organized_prefix): parent_node_id, rel_path_parts = self.tree.get_children()[0], path_norm[len(organized_prefix):].strip('/').split('/')
        elif path_norm.startswith(cleanup_prefix): parent_node_id, rel_path_parts = self.tree.get_children()[1], path_norm[len(cleanup_prefix):].strip('/').split('/')
        else: return
        if not rel_path_parts or not parent_node_id: return

        current_parent_id, current_path_prefix = parent_node_id, self.tree.item(parent_node_id, "values")[0]
        for part in rel_path_parts:
            if not part: continue
            found_child_id = next((cid for cid in self.tree.get_children(current_parent_id) if self.tree.item(cid, "text") == part), None)
            if found_child_id: current_parent_id, current_path_prefix = found_child_id, self.tree.item(found_child_id, "values")[0]
            else:
                new_path = os.path.join(current_path_prefix.rstrip('/'), part).replace('\\', '/') + '/'
                new_node_id = self.tree.insert(current_parent_id, "end", text=part, values=(new_path,), tags=("folder",))
                current_parent_id, current_path_prefix = new_node_id, new_path

    def _extract_relative_path(self, path):
        """Extract the relative part of a path after Organized/ or Cleanup/."""
        path_norm = path.replace('\\', '/')
        dest_base_norm = self.dest_var.get().replace('\\', '/')
        if not dest_base_norm: return None
        organized_prefix, cleanup_prefix = (dest_base_norm + '/Organized/', dest_base_norm + '/Cleanup/')
        if path_norm.startswith(organized_prefix): return 'Organized/' + path_norm[len(organized_prefix):]
        if path_norm.startswith(cleanup_prefix): return 'Cleanup/' + path_norm[len(cleanup_prefix):]
        markers = ['/Organized/', '/Cleanup/'] # Fallback check
        for marker in markers:
            if marker in path_norm:
                parts = path_norm.split(marker, 1); return marker.strip('/') + '/' + parts[1] if len(parts) > 1 else None
        print(f"Warning: Could not determine relative path structure for: {path}"); return None

    # --- Callbacks for YamlEditorPanel ---
    def _apply_yaml_changes_callback(self, yaml_text):
        """Callback from YamlEditorPanel when Apply is clicked."""
        try:
            config = yaml.safe_load(yaml_text)
            if not config or not isinstance(config, dict) or 'rules' not in config: raise ValueError("Invalid config: missing 'rules'")
            if self.config_manager: self.config_manager.config = config
            else: self._config = config # Store locally
            self._extract_paths_from_config(config)
            self._update_tree_view()
            self.event_generate("<<ConfigurationChanged>>", when="tail")
            messagebox.showinfo("Success", "YAML changes applied successfully.")
        except Exception as e: messagebox.showerror("Error", f"Failed to apply YAML changes: {str(e)}")

    def _revert_yaml_changes_callback(self):
        """Callback for YamlEditorPanel to get text to revert to."""
        config = self.config_manager.config if self.config_manager else self._config
        if config:
            try: return yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)
            except Exception as e: print(f"Error dumping config for revert: {e}")
        return None

    def _extract_paths_from_config(self, config):
        """Extract source/destination paths from config and update UI."""
        if not config or 'rules' not in config or not config['rules']:
            print("Warning: Cannot extract paths from empty or invalid config.")
            # Optionally reset UI fields here or leave them as is
            return

        # --- Extract Source Directories ---
        source_dirs = []
        subfolders_setting = True # Default
        first_rule = config['rules'][0] # Assume first rule is representative for UI

        if 'locations' in first_rule:
            locations = first_rule['locations']
            if isinstance(locations, list):
                source_dirs.extend(str(loc) for loc in locations)
            elif isinstance(locations, str):
                source_dirs.append(locations)
            # Handle more complex location dicts if necessary later

        if 'subfolders' in first_rule:
            subfolders_setting = bool(first_rule['subfolders'])

        # Update UI source entries
        # Remove existing entries beyond the first one
        while len(self.source_entries) > 1:
            entry = self.source_entries.pop()
            entry['frame'].destroy()
        # Clear or update the first entry
        if not self.source_entries: self._add_source_directory() # Ensure at least one exists
        self.source_entries[0]['var'].set(source_dirs[0] if source_dirs else "")
        # Add new entries if needed
        for i in range(1, len(source_dirs)):
            self._add_source_directory()
            self.source_entries[i]['var'].set(source_dirs[i])

        # Update subfolders checkbox
        self.subfolders_var.set(subfolders_setting)

        # --- Extract Destination Base Directory (Best Effort) ---
        dest_base = ""
        for rule in config.get('rules', []):
            for action in rule.get('actions', []):
                action_type = next(iter(action)) if isinstance(action, dict) else None
                if action_type in ('move', 'copy'):
                    action_value = action[action_type]
                    dest_path = action_value.get('dest') if isinstance(action_value, dict) else action_value
                    if dest_path and isinstance(dest_path, str):
                        # Try to find a common base path, e.g., up to 'Organized' or 'Cleanup'
                        path_norm = dest_path.replace('\\', '/')
                        markers = ['/Organized', '/Cleanup']
                        for marker in markers:
                            if marker in path_norm:
                                potential_base = path_norm.split(marker, 1)[0]
                                if potential_base:
                                    dest_base = potential_base
                                    break # Found a plausible base
                        if dest_base: break # Stop looking once found
            if dest_base: break # Stop looking once found

        if not dest_base and source_dirs:
             # Fallback: Use parent of first source dir? Or user's home?
             try: dest_base = str(Path(source_dirs[0]).parent)
             except: dest_base = os.path.expanduser("~")
             print(f"Warning: Could not determine destination base from actions, falling back to: {dest_base}")

        self.dest_var.set(dest_base)
        # Tree view will be updated by the caller or dest_var trace

    # --- Public Methods ---
    def get_current_config(self, from_editor=False):
        """Get the current configuration object, optionally prioritizing editor."""
        config = None
        print(f"ConfigPanel.get_current_config(from_editor={from_editor})")
        
        if from_editor and hasattr(self, 'yaml_editor_panel'):
            yaml_text = self.yaml_editor_panel.get_text().strip()
            print(f"YAML editor text length: {len(yaml_text)}")
            if yaml_text:
                try:
                    parsed_config = yaml.safe_load(yaml_text)
                    if parsed_config and isinstance(parsed_config, dict) and 'rules' in parsed_config:
                        config = parsed_config
                        print(f"Successfully parsed config from YAML editor with {len(config.get('rules', []))} rules")
                    else:
                        print(f"Warning: YAML editor content is invalid. Parsed result: {parsed_config}")
                except Exception as e:
                    print(f"Warning: Could not parse YAML editor content: {e}")
        
        if config is None:
            config = self.config_manager.config if self.config_manager else self._config
            print(f"Using config from {'config_manager' if self.config_manager else 'internal _config'}: {config is not None}")
            if config:
                print(f"Config has {len(config.get('rules', []))} rules")
        
        if config is None: # Final fallback
            print("Warning: No valid configuration found, returning default structure.")
            ui_source = self.source_entries[0]['var'].get() if self.source_entries else os.path.expanduser("~/Documents")
            ui_dest_base = self.dest_var.get() or os.path.expanduser("~/Documents")
            ui_dest_org = os.path.join(ui_dest_base, "Organized/").replace('\\','/')
            config = {'rules': [{'name': 'Example Rule', 'enabled': True, 'targets': 'files', 'locations': [ui_source], 'subfolders': self.subfolders_var.get(), 'filters': [{'extension': ['txt', 'pdf']}], 'actions': [{'move': {'dest': ui_dest_org, 'on_conflict': 'rename_new'}}]}]}
            print("Created default config with 1 example rule")
        
        return config

    def new_configuration(self):
        """Create a new empty configuration."""
        default_source = os.path.expanduser("~/Documents")
        default_dest_base = os.path.expanduser("~/Documents")
        default_dest_org = os.path.join(default_dest_base, "Organized/").replace('\\','/')
        config = {'rules': [{'name': 'Example Rule', 'enabled': True, 'targets': 'files', 'locations': [default_source], 'subfolders': self.subfolders_var.get(), 'filters': [{'extension': ['txt', 'pdf']}], 'actions': [{'move': {'dest': default_dest_org, 'on_conflict': 'rename_new'}}]}]}
        if self.config_manager: self.config_manager.config = config
        else: self._config = config
        self.current_config_path = None; self.config_var.set("")
        self._extract_paths_from_config(config)
        self._update_tree_view()
        if hasattr(self, 'yaml_editor_panel'):
             yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)
             self.yaml_editor_panel.set_text(yaml_str)
        self.event_generate("<<ConfigurationChanged>>", when="tail")

    def load_configuration(self, config_path):
        """Load a configuration from a file."""
        print(f"ConfigPanel.load_configuration: Loading from {config_path}")
        try:
            # Read the file content directly first for debugging
            with open(config_path, 'r') as file:
                file_content = file.read()
                print(f"File content length: {len(file_content)}")
                # Try to parse it
                raw_config = yaml.safe_load(file_content)
                print(f"Raw config parsed: {raw_config is not None}")
                if raw_config and 'rules' in raw_config:
                    print(f"Raw config contains {len(raw_config['rules'])} rules")
            
            # Now load it properly
            if self.config_manager:
                print("Using ConfigManager to load config")
                self.config_manager.load_config(config_path)
                config = self.config_manager.config
            else:
                print("Loading config directly")
                with open(config_path, 'r') as file:
                    config = yaml.safe_load(file)
                if not config or not isinstance(config, dict) or 'rules' not in config:
                    raise ValueError("Invalid format")
                self._config = config
            
            print(f"Config loaded with {len(config.get('rules', []))} rules")
            self.current_config_path = config_path
            self.config_var.set(config_path)
            
            # Extract paths and update UI
            self._extract_paths_from_config(config)
            self._update_tree_view()
            
            # Update YAML editor
            if hasattr(self, 'yaml_editor_panel'):
                yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)
                print(f"Setting YAML editor text (length: {len(yaml_str)})")
                self.yaml_editor_panel.set_text(yaml_str)
            else:
                print("Warning: yaml_editor_panel not available")
            
            # Generate event to notify other components
            print("Generating ConfigurationChanged event")
            self.event_generate("<<ConfigurationChanged>>", when="tail")
            return True
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            return False

    def open_configuration_dialog(self):
        """Open a file dialog to select and load a configuration."""
        try:
            # Use space separation for macOS compatibility
            filetypes = [("YAML files", "*.yaml *.yml"), ("All files", "*")]
            filename = filedialog.askopenfilename(title="Open Configuration File", filetypes=filetypes)
            if filename:
                return self.load_configuration(filename)
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file dialog: {str(e)}")
            return False

    def save_configuration(self):
        """Save the current configuration (from editor) to its file."""
        if not self.current_config_path: return self.save_configuration_as()
        try:
            config_text = self.yaml_editor_panel.get_text()
            config = yaml.safe_load(config_text)
            if not config or not isinstance(config, dict) or 'rules' not in config: raise ValueError("Invalid config in editor.")
            with open(self.current_config_path, 'w') as file: yaml.dump(config, file, default_flow_style=False, sort_keys=False, indent=2)
            if self.config_manager: self.config_manager.config = config
            else: self._config = config
            return True
        except Exception as e: messagebox.showerror("Error", f"Failed to save configuration: {str(e)}"); return False

    def save_configuration_as(self):
        """Save the current configuration (from editor) to a new file."""
        try:
            # Use space separation for macOS compatibility
            filetypes = [("YAML files", "*.yaml *.yml"), ("All files", "*")]
            filename = filedialog.asksaveasfilename(title="Save Configuration As", filetypes=filetypes, defaultextension=".yaml")
            if filename:
                config_text = self.yaml_editor_panel.get_text()
                config = yaml.safe_load(config_text)
                if not config or not isinstance(config, dict) or 'rules' not in config: raise ValueError("Invalid config in editor.")
                with open(filename, 'w') as file: yaml.dump(config, file, default_flow_style=False, sort_keys=False, indent=2)
                self.current_config_path = filename; self.config_var.set(filename)
                if self.config_manager: self.config_manager.config = config
                else: self._config = config
                return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
        return False

    def update_config(self, config):
        """Update the panel's state with an external configuration object."""
        print(f"ConfigPanel.update_config: Updating with config containing {len(config.get('rules', []))} rules")
        
        if self.config_manager:
            self.config_manager.config = config
            print("Updated config_manager.config")
        else:
            self._config = config
            print("Updated internal _config")
            
        self._extract_paths_from_config(config)
        self._update_tree_view()
        
        if hasattr(self, 'yaml_editor_panel'):
            yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2)
            print(f"Setting YAML editor text (length: {len(yaml_str)})")
            self.yaml_editor_panel.set_text(yaml_str)
        else:
            print("Warning: yaml_editor_panel not available")
        
        # Always generate the event to ensure rules panel is updated
        print("Generating ConfigurationChanged event from update_config")
        self.event_generate("<<ConfigurationChanged>>", when="tail")
