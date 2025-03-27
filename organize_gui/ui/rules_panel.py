"""
Enhanced Rules panel for the File Organization System.

This panel uses RuleListManager to display the list and RuleEditorDialogs
for add/edit operations.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
import json
import yaml
import re
import copy # Added for deepcopy in duplicate

# Import the new dialog functions, list manager, and details panel
from .rule_editor_dialogs import show_selection_dialog, ask_filter_details, ask_action_details
from .rule_list_manager import RuleListManager
from .rule_details_panel import RuleDetailsPanel

class RulesPanel(ttk.Frame):
    """Enhanced panel for managing organization rules."""

    def __init__(self, parent):
        """Initialize the rules panel."""
        super().__init__(parent)

        # Current rules data
        self.rules = [] # This list holds the actual rule data
        self.current_rule_index = None # Store index instead of rule object

        # Create the UI components
        self._create_widgets()

    def _create_widgets(self):
        """Create the UI components for the rules panel using grid."""
        # Configure main frame grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main layout - split view with rules list on left and details on right
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # --- Left panel ---
        left_frame = ttk.Frame(self.paned_window, padding=5)
        self.paned_window.add(left_frame, weight=1)
        # Configure grid for left_frame to hold list manager and buttons below it
        left_frame.grid_rowconfigure(0, weight=1) # Rule list manager takes most space
        left_frame.grid_rowconfigure(1, weight=0) # Action buttons
        left_frame.grid_rowconfigure(2, weight=0) # State/Order buttons
        left_frame.grid_columnconfigure(0, weight=1)

        # Rules list LabelFrame (container for RuleListManager UI)
        rules_list_frame = ttk.LabelFrame(left_frame, text="Organization Rules", padding=(10, 5))
        rules_list_frame.grid(row=0, column=0, sticky='nsew')
        # Let RuleListManager configure its internal grid
        rules_list_frame.grid_columnconfigure(0, weight=1)
        rules_list_frame.grid_rowconfigure(0, weight=1) # Let RuleListManager manage its internal rows

        # --- Instantiate RuleListManager ---
        # Pass the frame where it should build its UI and a reference to the rules list
        self.rule_list_manager = RuleListManager(rules_list_frame, self.rules)
        # Bind the selection change event from the manager to our handler
        self.rule_list_manager.bind_selection_change(self._on_rule_selected)


        # Rule modification actions (Add, Edit, Delete, Duplicate)
        rule_actions_frame = ttk.Frame(left_frame) # Place below the list frame
        rule_actions_frame.grid(row=1, column=0, sticky='ew', pady=(5,0))
        add_button = ttk.Button(rule_actions_frame, text="Add", command=self._add_rule)
        add_button.pack(side=tk.LEFT, padx=(0, 5))
        edit_button = ttk.Button(rule_actions_frame, text="Edit", command=self._edit_rule)
        edit_button.pack(side=tk.LEFT, padx=5)
        delete_button = ttk.Button(rule_actions_frame, text="Delete", command=self._delete_rule)
        delete_button.pack(side=tk.LEFT, padx=5)
        duplicate_button = ttk.Button(rule_actions_frame, text="Duplicate", command=self._duplicate_rule)
        duplicate_button.pack(side=tk.LEFT, padx=5)

        # Rule state and order controls
        state_order_frame = ttk.Frame(left_frame) # Place below actions
        state_order_frame.grid(row=2, column=0, sticky='ew', pady=(5,0))
        enable_all_button = ttk.Button(state_order_frame, text="Enable All", command=self._enable_all_rules)
        enable_all_button.pack(side=tk.LEFT, padx=(0, 5))
        disable_all_button = ttk.Button(state_order_frame, text="Disable All", command=self._disable_all_rules)
        disable_all_button.pack(side=tk.LEFT, padx=5)
        move_up_button = ttk.Button(state_order_frame, text="Move Up", command=self._move_rule_up)
        move_up_button.pack(side=tk.LEFT, padx=(20, 5)) # Add space before move buttons
        move_down_button = ttk.Button(state_order_frame, text="Move Down", command=self._move_rule_down)
        move_down_button.pack(side=tk.LEFT, padx=5)


        # --- Right panel - Rule Details Panel ---
        right_frame = ttk.Frame(self.paned_window, padding=5)
        self.paned_window.add(right_frame, weight=2)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Instantiate RuleDetailsPanel
        self.details_panel = RuleDetailsPanel(right_frame, change_callback=self._notify_change)
        self.details_panel.grid(row=0, column=0, sticky='nsew')


    # _filter_rules and _get_rule_category are now handled by RuleListManager

    def _on_rule_selected(self, event):
        """Handle rule selection change event from RuleListManager."""
        selected_index = self.rule_list_manager.get_selected_rule_index()

        if selected_index is not None and 0 <= selected_index < len(self.rules):
            self.current_rule_index = selected_index
            rule_data = self.rules[self.current_rule_index]
            self.details_panel.display_details(rule_data) # Pass data to details panel
        else:
            # No valid selection or index out of bounds
            self.current_rule_index = None
            self.details_panel.clear_details() # Clear details panel

    # Remove _display_rule_details and _clear_rule_details as they are now in RuleDetailsPanel

    def _add_rule(self):
        """Add a new rule."""
        # Create a new rule with default values
        rule = {
            'name': 'New Rule',
            'enabled': True,
            'targets': 'files',
            'locations': [os.path.expanduser("~/Documents")], # Default as list
            'subfolders': True,
            'filter_mode': 'all',
            'filters': [
                {'extension': ['txt', 'pdf', 'doc', 'docx']}
            ],
            'actions': [
                {'move': {'dest': os.path.expanduser("~/Organized/Documents/"), 'on_conflict': 'rename_new'}}
            ]
        }

        # Add to rules list
        self.rules.append(rule)
        new_index = len(self.rules) - 1

        # Update the rule list display
        self.rule_list_manager.refresh_list()

        # Select the new rule in the list
        self.rule_list_manager.select_rule_by_index(new_index)
        # Selection change should trigger _on_rule_selected to display details

        # Notify about the change
        self._notify_change()

    def _edit_rule(self):
        """Focus the details panel for the selected rule."""
        selected_index = self.rule_list_manager.get_selected_rule_index()
        if selected_index is None:
            messagebox.showinfo("Edit Rule", "Please select a rule from the list first.")
            return

        # Ensure the details panel is showing the selected rule
        if self.current_rule_index != selected_index:
             self.current_rule_index = selected_index
             if 0 <= self.current_rule_index < len(self.rules):
                 self.details_panel.display_details(self.rules[self.current_rule_index])
             else: # Index out of bounds
                 self.details_panel.clear_details()
                 return

        # Focus the first editable element in the details panel
        # Assuming rule_name_entry exists in details_panel
        if hasattr(self.details_panel, 'rule_name_entry'):
            self.details_panel.rule_name_entry.focus_set()


    def _delete_rule(self):
        """Delete the selected rule."""
        selected_index = self.rule_list_manager.get_selected_rule_index()
        if selected_index is None:
            messagebox.showinfo("Delete Rule", "Please select a rule to delete.")
            return

        # Confirm deletion
        rule_name = self.rules[selected_index].get('name', f'Rule at index {selected_index}')
        if not messagebox.askyesno("Delete Rule", f"Are you sure you want to delete the rule '{rule_name}'?"):
            return

        # Delete the rule from the data list
        del self.rules[selected_index]

        # Refresh the list display
        self.rule_list_manager.refresh_list()

        # Clear the details panel as the selection is now invalid
        self.details_panel.clear_details()

        # Notify about the change
        self._notify_change()

    def _duplicate_rule(self):
        """Duplicate the selected rule."""
        selected_index = self.rule_list_manager.get_selected_rule_index()
        if selected_index is None:
            messagebox.showinfo("Duplicate Rule", "Please select a rule to duplicate.")
            return

        # Get the original rule
        original_rule = self.rules[selected_index]

        # Create a deep copy
        new_rule = copy.deepcopy(original_rule)

        # Update the name
        new_rule['name'] = f"{original_rule.get('name', 'Rule')} (Copy)"

        # Insert the new rule after the original one in the data list
        insert_pos = selected_index + 1
        self.rules.insert(insert_pos, new_rule)

        # Refresh the list display
        self.rule_list_manager.refresh_list()

        # Select the newly duplicated rule
        self.rule_list_manager.select_rule_by_index(insert_pos)
        # Selection change should trigger _on_rule_selected

        # Notify about the change
        self._notify_change()

    def _enable_all_rules(self):
        """Enable all rules in the data list."""
        changed = False
        for rule in self.rules:
            if not rule.get('enabled', True):
                rule['enabled'] = True
                changed = True

        if changed:
            # Refresh the list display
            self.rule_list_manager.refresh_list()

            # Update current rule display in details panel if it was affected
            if self.current_rule_index is not None and self.current_rule_index < len(self.rules):
                 current_rule_data = self.rules[self.current_rule_index]
                 if current_rule_data.get('enabled', True): # Check if it was actually changed
                      self.details_panel.display_details(current_rule_data)


            # Notify about the change
            self._notify_change()

    def _disable_all_rules(self):
        """Disable all rules in the data list."""
        changed = False
        for rule in self.rules:
             if rule.get('enabled', True):
                rule['enabled'] = False
                changed = True

        if changed:
            # Refresh the list display
            self.rule_list_manager.refresh_list()

            # Update current rule display in details panel if it was affected
            if self.current_rule_index is not None and self.current_rule_index < len(self.rules):
                 current_rule_data = self.rules[self.current_rule_index]
                 if not current_rule_data.get('enabled', True): # Check if it was actually changed
                      self.details_panel.display_details(current_rule_data)

            # Notify about the change
            self._notify_change()

    def _move_rule_up(self):
        """Move the selected rule up in the data list."""
        selected_index = self.rule_list_manager.get_selected_rule_index()
        if selected_index is None or selected_index == 0:
            return # Cannot move up if nothing selected or already at top

        # Swap rules in the data list
        self.rules[selected_index], self.rules[selected_index - 1] = \
            self.rules[selected_index - 1], self.rules[selected_index]

        new_index = selected_index - 1

        # Refresh the list display
        self.rule_list_manager.refresh_list()

        # Reselect the moved rule at its new position
        self.rule_list_manager.select_rule_by_index(new_index)
        # Selection change should trigger _on_rule_selected

        # Notify about the change
        self._notify_change()

    def _move_rule_down(self):
        """Move the selected rule down in the data list."""
        selected_index = self.rule_list_manager.get_selected_rule_index()
        if selected_index is None or selected_index >= len(self.rules) - 1:
            return # Cannot move down if nothing selected or already at bottom

        # Swap rules in the data list
        self.rules[selected_index], self.rules[selected_index + 1] = \
            self.rules[selected_index + 1], self.rules[selected_index]

        new_index = selected_index + 1

        # Refresh the list display
        self.rule_list_manager.refresh_list()

        # Reselect the moved rule at its new position
        self.rule_list_manager.select_rule_by_index(new_index)
        # Selection change should trigger _on_rule_selected

        # Notify about the change
        self._notify_change()

    # Remove methods now handled by RuleDetailsPanel:
    # _on_locations_changed, _update_current_rule_data,
    # _add_filter, _edit_filter, _remove_filter,
    # _add_action, _edit_action, _remove_action

    def _notify_change(self):
        """Callback for RuleDetailsPanel to notify of changes."""
        # Refresh list in case name/enabled changed
        self.rule_list_manager.refresh_list()
        # Ensure current selection is visually consistent
        if self.current_rule_index is not None:
            self.rule_list_manager.select_rule_by_index(self.current_rule_index)
        # Generate event for main window
        self.event_generate("<<RulesChanged>>", when="tail")


    # Public methods

    def update_rules(self, config):
        """Update the rules list from a configuration object."""
        if not config or 'rules' not in config or not isinstance(config['rules'], list):
            messagebox.showerror("Error", "Invalid configuration - 'rules' list not found or invalid.")
            self.rules = [] # Reset internal rules
        else:
             # Perform a basic check if rules seem valid (list of dicts)
             if not all(isinstance(r, dict) for r in config['rules']):
                  messagebox.showwarning("Warning", "Configuration contains non-dictionary items in 'rules' list. Skipping invalid items.")
                  self.rules = [r for r in config['rules'] if isinstance(r, dict)]
             else:
                  self.rules = config['rules'] # Assign the new list

        # Store the index of the currently selected rule if possible
        selected_index_before_update = self.rule_list_manager.get_selected_rule_index() if hasattr(self, 'rule_list_manager') else None

        # Refresh the list display using the new self.rules data
        if hasattr(self, 'rule_list_manager'):
            self.rule_list_manager.refresh_list()
        else:
             # Should not happen if _create_widgets was called, but handle defensively
             print("Warning: RuleListManager not initialized during update_rules.")
             self._create_widgets() # Attempt to create widgets if missing
             self.rule_list_manager.refresh_list()


        # Try to re-select the rule that was selected before the update
        if selected_index_before_update is not None and 0 <= selected_index_before_update < len(self.rules):
             self.rule_list_manager.select_rule_by_index(selected_index_before_update)
             # _on_rule_selected will handle updating the details panel
        else:
             # If previous selection is invalid or no selection, clear details panel
             self.details_panel.clear_details()

    def get_updated_config(self):
        """Get the updated configuration with current rules."""
        # Ensure any pending changes in the details panel are applied to the data
        if hasattr(self, 'details_panel'):
             self.details_panel.update_rule_data()

        # Create a configuration with the current rules list
        config = {'rules': self.rules}

        return config
