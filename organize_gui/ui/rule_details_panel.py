"""
Panel for displaying and editing the details of a single organization rule.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
import json
import os # For expanduser

# Import dialog helpers
from .rule_editor_dialogs import show_selection_dialog, ask_filter_details, ask_action_details

class RuleDetailsPanel(ttk.Frame):
    """Frame for editing the details of a selected rule."""

    def __init__(self, parent, change_callback=None):
        """
        Initialize the Rule Details Panel.

        Args:
            parent: The parent widget.
            change_callback: A function to call when rule data is modified
                             by actions within this panel (e.g., adding/removing filters/actions).
        """
        super().__init__(parent, padding=5)
        self.current_rule_data = None # Reference to the specific rule dict being edited
        self._change_callback = change_callback

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_widgets()
        self.clear_details() # Start empty

    def _create_widgets(self):
        """Create the UI components for the rule details editor."""
        details_frame = ttk.LabelFrame(self, text="Rule Details", padding=(10, 5))
        details_frame.grid(row=0, column=0, sticky='nsew')
        details_frame.grid_rowconfigure(0, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)

        # Rule details scroll container
        canvas = tk.Canvas(details_frame)
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=canvas.yview)

        self.details_content = ttk.Frame(canvas, padding=5) # Add padding to content
        self.details_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.details_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        # Configure grid for details_content
        self.details_content.grid_columnconfigure(1, weight=1) # Make entries/text expand

        details_row = 0
        default_font = font.nametofont("TkTextFont")

        # --- Rule Name ---
        ttk.Label(self.details_content, text="Rule Name:").grid(row=details_row, column=0, sticky='w', pady=2)
        self.rule_name_var = tk.StringVar()
        self.rule_name_entry = ttk.Entry(self.details_content, textvariable=self.rule_name_var)
        self.rule_name_entry.grid(row=details_row, column=1, sticky='ew', pady=2)
        self.rule_name_var.trace_add("write", self._on_detail_changed)
        details_row += 1

        # --- Enabled Checkbox ---
        self.enabled_var = tk.BooleanVar(value=True)
        enabled_check = ttk.Checkbutton(
            self.details_content, text="Enabled", variable=self.enabled_var,
            command=self._on_detail_changed
        )
        enabled_check.grid(row=details_row, column=0, columnspan=2, sticky='w', pady=2)
        details_row += 1

        # --- Target Selector ---
        target_frame = ttk.Frame(self.details_content)
        target_frame.grid(row=details_row, column=0, columnspan=2, sticky='ew', pady=2)
        ttk.Label(target_frame, text="Target:").pack(side=tk.LEFT, padx=(0, 10))
        self.target_var = tk.StringVar(value="files")
        ttk.Radiobutton(target_frame, text="Files", variable=self.target_var, value="files",
                      command=self._on_detail_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(target_frame, text="Directories", variable=self.target_var, value="dirs",
                      command=self._on_detail_changed).pack(side=tk.LEFT, padx=5)
        details_row += 1

        # --- Subfolders Checkbox ---
        self.subfolders_var = tk.BooleanVar(value=True)
        subfolder_check = ttk.Checkbutton(
            self.details_content, text="Include Subfolders", variable=self.subfolders_var,
            command=self._on_detail_changed
        )
        subfolder_check.grid(row=details_row, column=0, columnspan=2, sticky='w', pady=2)
        details_row += 1

        # --- Locations ---
        locations_frame = ttk.LabelFrame(self.details_content, text="Locations", padding=(5, 5))
        locations_frame.grid(row=details_row, column=0, columnspan=2, sticky='nsew', pady=5)
        locations_frame.grid_columnconfigure(0, weight=1)
        locations_frame.grid_rowconfigure(0, weight=1)
        self.locations_text = tk.Text(locations_frame, height=3, width=40, wrap=tk.WORD, font=default_font)
        self.locations_text.grid(row=0, column=0, sticky='nsew', pady=(0, 5))
        self.locations_text.bind("<KeyRelease>", self._on_detail_changed) # Use generic change handler
        locations_note = ttk.Label(locations_frame,
                                text="(One path per line. Use absolute paths or ~/)",
                                style="secondary.TLabel")
        locations_note.grid(row=1, column=0, sticky='w')
        details_row += 1

        # --- Filter Mode ---
        filter_mode_frame = ttk.Frame(self.details_content)
        filter_mode_frame.grid(row=details_row, column=0, columnspan=2, sticky='ew', pady=2)
        ttk.Label(filter_mode_frame, text="Filter Mode:").pack(side=tk.LEFT, padx=(0, 10))
        self.filter_mode_var = tk.StringVar(value="all")
        ttk.Radiobutton(filter_mode_frame, text="All", variable=self.filter_mode_var, value="all",
                      command=self._on_detail_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_mode_frame, text="Any", variable=self.filter_mode_var, value="any",
                      command=self._on_detail_changed).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_mode_frame, text="None", variable=self.filter_mode_var, value="none",
                      command=self._on_detail_changed).pack(side=tk.LEFT, padx=5)
        details_row += 1

        # --- Filters ---
        filters_frame = ttk.LabelFrame(self.details_content, text="Filters", padding=(5, 5))
        filters_frame.grid(row=details_row, column=0, columnspan=2, sticky='nsew', pady=5)
        filters_frame.grid_columnconfigure(0, weight=1)
        filters_frame.grid_rowconfigure(0, weight=1)
        self.details_content.grid_rowconfigure(details_row, weight=1) # Give weight

        filter_list_frame = ttk.Frame(filters_frame)
        filter_list_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 5))
        filter_list_frame.grid_rowconfigure(0, weight=1)
        filter_list_frame.grid_columnconfigure(0, weight=1)
        filter_scrollbar = ttk.Scrollbar(filter_list_frame, orient=tk.VERTICAL)
        filter_scrollbar.grid(row=0, column=1, sticky='ns')
        self.filters_list = tk.Listbox(filter_list_frame, yscrollcommand=filter_scrollbar.set, height=6, font=default_font)
        self.filters_list.grid(row=0, column=0, sticky='nsew')
        filter_scrollbar.config(command=self.filters_list.yview)

        filter_buttons = ttk.Frame(filters_frame)
        filter_buttons.grid(row=1, column=0, sticky='ew')
        ttk.Button(filter_buttons, text="Add", command=self._add_filter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(filter_buttons, text="Edit", command=self._edit_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_buttons, text="Remove", command=self._remove_filter).pack(side=tk.LEFT, padx=5)
        details_row += 1

        # --- Actions ---
        actions_frame = ttk.LabelFrame(self.details_content, text="Actions", padding=(5, 5))
        actions_frame.grid(row=details_row, column=0, columnspan=2, sticky='nsew', pady=5)
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_rowconfigure(0, weight=1)
        self.details_content.grid_rowconfigure(details_row, weight=1) # Give weight

        action_list_frame = ttk.Frame(actions_frame)
        action_list_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 5))
        action_list_frame.grid_rowconfigure(0, weight=1)
        action_list_frame.grid_columnconfigure(0, weight=1)
        action_scrollbar = ttk.Scrollbar(action_list_frame, orient=tk.VERTICAL)
        action_scrollbar.grid(row=0, column=1, sticky='ns')
        self.actions_list = tk.Listbox(action_list_frame, yscrollcommand=action_scrollbar.set, height=6, font=default_font)
        self.actions_list.grid(row=0, column=0, sticky='nsew')
        action_scrollbar.config(command=self.actions_list.yview)

        action_buttons = ttk.Frame(actions_frame)
        action_buttons.grid(row=1, column=0, sticky='ew')
        ttk.Button(action_buttons, text="Add", command=self._add_action).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_buttons, text="Edit", command=self._edit_action).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons, text="Remove", command=self._remove_action).pack(side=tk.LEFT, padx=5)
        details_row += 1

        # Disable all widgets initially
        self._set_widgets_state(tk.DISABLED)


    def _set_widgets_state(self, state):
        """Enable or disable all interactive widgets in the details panel."""
        for child in self.details_content.winfo_children():
            # Check if it's a container frame (like locations_frame)
            if isinstance(child, (ttk.LabelFrame, ttk.Frame)):
                for widget in child.winfo_children():
                    try:
                        widget.configure(state=state)
                    except tk.TclError: # Widget might not support state (e.g., Label)
                        pass
            else: # Direct child widget
                 try:
                     child.configure(state=state)
                 except tk.TclError:
                     pass
        # Special handling for Text widget
        self.locations_text.configure(state=state)
        # Listboxes don't have a 'state' option in the same way,
        # but disabling buttons prevents interaction.


    def display_details(self, rule_data):
        """Populate the panel with details from the given rule dictionary."""
        self.current_rule_data = rule_data
        if not rule_data:
            self.clear_details()
            return

        self._set_widgets_state(tk.NORMAL) # Enable widgets

        # --- Populate fields ---
        # Disable trace while setting vars to prevent feedback loop
        if self.rule_name_var.trace_info():
            self.rule_name_var.trace_remove("write", self.rule_name_var.trace_info()[0][1])
        self.rule_name_var.set(rule_data.get('name', ''))
        self.rule_name_var.trace_add("write", self._on_detail_changed)

        self.enabled_var.set(rule_data.get('enabled', True))
        self.target_var.set(rule_data.get('targets', 'files'))
        self.subfolders_var.set(rule_data.get('subfolders', True))

        # Locations
        self.locations_text.delete('1.0', tk.END)
        locations = rule_data.get('locations', [])
        if not isinstance(locations, list):
            locations = [locations] if locations else []
        for loc in locations:
             loc_path = loc.get('path') if isinstance(loc, dict) else loc
             if loc_path:
                 self.locations_text.insert(tk.END, f"{loc_path}\n")

        self.filter_mode_var.set(rule_data.get('filter_mode', 'all'))

        # Filters List
        self.filters_list.delete(0, tk.END)
        for filter_item in rule_data.get('filters', []):
            self._insert_filter_display(filter_item)

        # Actions List
        self.actions_list.delete(0, tk.END)
        for action_item in rule_data.get('actions', []):
            self._insert_action_display(action_item)


    def clear_details(self):
        """Clear all fields and disable the panel."""
        self.current_rule_data = None

        # Disable trace while clearing
        if hasattr(self, 'rule_name_var') and self.rule_name_var.trace_info():
             self.rule_name_var.trace_remove("write", self.rule_name_var.trace_info()[0][1])
        self.rule_name_var.set("")
        # Don't re-add trace here, wait for display_details

        self.enabled_var.set(True)
        self.target_var.set("files")
        self.subfolders_var.set(True)
        self.locations_text.delete('1.0', tk.END)
        self.filter_mode_var.set("all")
        self.filters_list.delete(0, tk.END)
        self.actions_list.delete(0, tk.END)

        self._set_widgets_state(tk.DISABLED) # Disable widgets


    def _on_detail_changed(self, *args):
        """Callback when a simple detail (name, enabled, target, etc.) changes."""
        if self.current_rule_data:
            self.update_rule_data() # Apply changes to the bound rule dict
            if self._change_callback:
                self._change_callback() # Notify parent


    def update_rule_data(self):
        """Update the bound rule dictionary (self.current_rule_data) from UI fields."""
        if not self.current_rule_data:
            return

        self.current_rule_data['name'] = self.rule_name_var.get()
        self.current_rule_data['enabled'] = self.enabled_var.get()
        self.current_rule_data['targets'] = self.target_var.get()
        self.current_rule_data['subfolders'] = self.subfolders_var.get()
        self.current_rule_data['filter_mode'] = self.filter_mode_var.get()

        # Update locations
        location_text = self.locations_text.get('1.0', tk.END).strip()
        locations = [loc.strip() for loc in location_text.split('\n') if loc.strip()]
        self.current_rule_data['locations'] = locations[0] if len(locations) == 1 else locations

        # Filters and Actions are updated via their specific add/edit/remove methods


    # --- Filter/Action List Management ---

    def _insert_filter_display(self, filter_item):
        """Formats and inserts a filter item into the filters listbox."""
        if isinstance(filter_item, dict):
            filter_type = next(iter(filter_item))
            filter_value = filter_item[filter_type]
            if isinstance(filter_value, list):
                display = f"{filter_type}: {', '.join(str(v) for v in filter_value)}"
            elif isinstance(filter_value, dict):
                display = f"{filter_type}: {json.dumps(filter_value)}"
            else:
                display = f"{filter_type}: {filter_value}"
            self.filters_list.insert(tk.END, display)
        else:
            self.filters_list.insert(tk.END, str(filter_item))

    def _insert_action_display(self, action_item):
        """Formats and inserts an action item into the actions listbox."""
        if isinstance(action_item, dict):
            action_type = next(iter(action_item))
            action_value = action_item[action_type]
            if isinstance(action_value, dict):
                display = f"{action_type}: {json.dumps(action_value)}"
            else:
                display = f"{action_type}: {action_value}"
            self.actions_list.insert(tk.END, display)
        else:
            self.actions_list.insert(tk.END, str(action_item))

    def _add_filter(self):
        if not self.current_rule_data: return
        filter_types = ["extension", "name", "filename", "path", "created", "modified",
                        "accessed", "filecontent", "filesize", "exif", "duplicate",
                        "regex", "python"]
        filter_type = show_selection_dialog(self, "Select Filter Type", "Select filter type:", filter_types)
        if not filter_type: return

        new_filter = ask_filter_details(self, filter_type)
        if new_filter:
            if 'filters' not in self.current_rule_data:
                self.current_rule_data['filters'] = []
            self.current_rule_data['filters'].append(new_filter)
            self.filters_list.insert(tk.END, self._format_filter_display(new_filter)) # Update listbox
            if self._change_callback: self._change_callback()

    def _edit_filter(self):
        if not self.current_rule_data: return
        selection = self.filters_list.curselection()
        if not selection: return
        idx = selection[0]
        filters = self.current_rule_data.get('filters', [])
        if idx >= len(filters): return

        original_filter = filters[idx]
        if not isinstance(original_filter, dict) or not original_filter: return
        filter_type = next(iter(original_filter))

        updated_filter = ask_filter_details(self, filter_type, initial_data=original_filter)
        if updated_filter:
            filters[idx] = updated_filter
            # Update listbox display
            self.filters_list.delete(idx)
            self.filters_list.insert(idx, self._format_filter_display(updated_filter))
            self.filters_list.selection_set(idx)
            if self._change_callback: self._change_callback()

    def _remove_filter(self):
        if not self.current_rule_data: return
        selection = self.filters_list.curselection()
        if not selection: return
        idx = selection[0]
        filters = self.current_rule_data.get('filters', [])
        if idx >= len(filters): return

        del filters[idx]
        self.filters_list.delete(idx) # Update listbox
        if self._change_callback: self._change_callback()

    def _add_action(self):
        if not self.current_rule_data: return
        action_types = ["move", "copy", "rename", "delete", "trash", "echo", "shell", "python", "confirm"]
        action_type = show_selection_dialog(self, "Select Action Type", "Select action type:", action_types)
        if not action_type: return

        new_action = ask_action_details(self, action_type)
        if new_action:
            if 'actions' not in self.current_rule_data:
                self.current_rule_data['actions'] = []
            self.current_rule_data['actions'].append(new_action)
            self.actions_list.insert(tk.END, self._format_action_display(new_action)) # Update listbox
            if self._change_callback: self._change_callback()

    def _edit_action(self):
        if not self.current_rule_data: return
        selection = self.actions_list.curselection()
        if not selection: return
        idx = selection[0]
        actions = self.current_rule_data.get('actions', [])
        if idx >= len(actions): return

        original_action = actions[idx]
        if not isinstance(original_action, dict) or not original_action: return
        action_type = next(iter(original_action))

        updated_action = ask_action_details(self, action_type, initial_data=original_action)
        if updated_action:
            actions[idx] = updated_action
            # Update listbox display
            self.actions_list.delete(idx)
            self.actions_list.insert(idx, self._format_action_display(updated_action))
            self.actions_list.selection_set(idx)
            if self._change_callback: self._change_callback()

    def _remove_action(self):
        if not self.current_rule_data: return
        selection = self.actions_list.curselection()
        if not selection: return
        idx = selection[0]
        actions = self.current_rule_data.get('actions', [])
        if idx >= len(actions): return

        del actions[idx]
        self.actions_list.delete(idx) # Update listbox
        if self._change_callback: self._change_callback()

    # Helper methods to format display strings consistently
    def _format_filter_display(self, filter_item):
        if isinstance(filter_item, dict):
            filter_type = next(iter(filter_item))
            filter_value = filter_item[filter_type]
            if isinstance(filter_value, list): return f"{filter_type}: {', '.join(str(v) for v in filter_value)}"
            if isinstance(filter_value, dict): return f"{filter_type}: {json.dumps(filter_value)}"
            return f"{filter_type}: {filter_value}"
        return str(filter_item)

    def _format_action_display(self, action_item):
        if isinstance(action_item, dict):
            action_type = next(iter(action_item))
            action_value = action_item[action_type]
            if isinstance(action_value, dict): return f"{action_type}: {json.dumps(action_value)}"
            return f"{action_type}: {action_value}"
        return str(action_item)
