"""
Enhanced Rules panel for the File Organization System.

This implementation provides a complete interface for managing and editing
organization rules, including filters and actions.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import yaml
import re

class RulesPanel(ttk.Frame):
    """Enhanced panel for managing organization rules."""
    
    def __init__(self, parent):
        """Initialize the rules panel."""
        super().__init__(parent)
        
        # Current rules data
        self.rules = []
        self.current_rule = None
        
        # Create the UI components
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI components for the rules panel."""
        # Main layout - split view with rules list on left and details on right
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Rules list
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=1)
        
        # Rules list with enable/disable checkboxes
        rules_frame = ttk.LabelFrame(left_frame, text="Organization Rules", padding=(10, 5))
        rules_frame.pack(fill=tk.BOTH, expand=True)
        
        # Search and filter controls
        filter_frame = ttk.Frame(rules_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        # Search box
        search_label = ttk.Label(filter_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_rules)
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Category filter
        category_label = ttk.Label(filter_frame, text="Category:")
        category_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.category_var = tk.StringVar(value="All")
        categories = ["All", "Documents", "Media", "Development", "Archives", 
                      "Applications", "Fonts", "System", "Other", "Cleanup"]
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, 
                                     values=categories, state="readonly", width=15)
        category_combo.pack(side=tk.LEFT)
        category_combo.bind("<<ComboboxSelected>>", self._filter_rules)
        
        # Rules list with scrollbar
        list_frame = ttk.Frame(rules_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Use a Treeview for better presentation of rules
        self.rules_tree = ttk.Treeview(
            list_frame,
            columns=("enabled", "category"),
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.rules_tree.yview)
        
        # Configure columns
        self.rules_tree.column("#0", width=220, minwidth=200)  # Name column
        self.rules_tree.column("enabled", width=60, minwidth=60, anchor=tk.CENTER)
        self.rules_tree.column("category", width=100, minwidth=80, anchor=tk.CENTER)
        
        self.rules_tree.heading("#0", text="Rule Name")
        self.rules_tree.heading("enabled", text="Enabled")
        self.rules_tree.heading("category", text="Category")
        
        # Bind selection event
        self.rules_tree.bind("<<TreeviewSelect>>", self._on_rule_selected)
        
        # Rule actions
        action_frame = ttk.Frame(rules_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        # Create button icons with descriptive text
        add_button = ttk.Button(action_frame, text="Add Rule", 
                               command=self._add_rule)
        add_button.pack(side=tk.LEFT, padx=5)
        
        edit_button = ttk.Button(action_frame, text="Edit Rule", 
                                command=self._edit_rule)
        edit_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = ttk.Button(action_frame, text="Delete Rule", 
                                  command=self._delete_rule)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        duplicate_button = ttk.Button(action_frame, text="Duplicate", 
                                     command=self._duplicate_rule)
        duplicate_button.pack(side=tk.LEFT, padx=5)
        
        # Rule state controls
        state_frame = ttk.Frame(rules_frame)
        state_frame.pack(fill=tk.X, pady=5)
        
        enable_all_button = ttk.Button(state_frame, text="Enable All", 
                                      command=self._enable_all_rules)
        enable_all_button.pack(side=tk.LEFT, padx=5)
        
        disable_all_button = ttk.Button(state_frame, text="Disable All", 
                                       command=self._disable_all_rules)
        disable_all_button.pack(side=tk.LEFT, padx=5)
        
        # Move up/down buttons
        move_frame = ttk.Frame(rules_frame)
        move_frame.pack(fill=tk.X, pady=5)
        
        move_up_button = ttk.Button(move_frame, text="Move Up", 
                                   command=self._move_rule_up)
        move_up_button.pack(side=tk.LEFT, padx=5)
        
        move_down_button = ttk.Button(move_frame, text="Move Down", 
                                     command=self._move_rule_down)
        move_down_button.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Rule details
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=2)
        
        details_frame = ttk.LabelFrame(right_frame, text="Rule Details", padding=(10, 5))
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Rule details scroll container
        canvas = tk.Canvas(details_frame)
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=canvas.yview)
        
        self.details_content = ttk.Frame(canvas)
        self.details_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.details_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Rule name
        name_frame = ttk.Frame(self.details_content)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Rule Name:", width=12).pack(side=tk.LEFT)
        
        self.rule_name_var = tk.StringVar()
        self.rule_name_entry = ttk.Entry(name_frame, textvariable=self.rule_name_var, width=40)
        self.rule_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Enabled checkbox
        enabled_frame = ttk.Frame(self.details_content)
        enabled_frame.pack(fill=tk.X, pady=5)
        
        self.enabled_var = tk.BooleanVar(value=True)
        enabled_check = ttk.Checkbutton(
            enabled_frame, 
            text="Enabled", 
            variable=self.enabled_var,
            command=self._update_current_rule
        )
        enabled_check.pack(side=tk.LEFT)
        
        # Target selector
        target_frame = ttk.Frame(self.details_content)
        target_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(target_frame, text="Target:", width=12).pack(side=tk.LEFT)
        
        self.target_var = tk.StringVar(value="files")
        ttk.Radiobutton(target_frame, text="Files", variable=self.target_var, value="files",
                      command=self._update_current_rule).pack(side=tk.LEFT)
        ttk.Radiobutton(target_frame, text="Directories", variable=self.target_var, value="dirs",
                      command=self._update_current_rule).pack(side=tk.LEFT)
        
        # Subfolders checkbox
        subfolder_frame = ttk.Frame(self.details_content)
        subfolder_frame.pack(fill=tk.X, pady=5)
        
        self.subfolders_var = tk.BooleanVar(value=True)
        subfolder_check = ttk.Checkbutton(
            subfolder_frame, 
            text="Include Subfolders", 
            variable=self.subfolders_var,
            command=self._update_current_rule
        )
        subfolder_check.pack(side=tk.LEFT)
        
        # Locations
        locations_frame = ttk.LabelFrame(self.details_content, text="Locations", padding=(5, 5))
        locations_frame.pack(fill=tk.X, pady=5)
        
        self.locations_text = tk.Text(locations_frame, height=3, width=40, wrap=tk.WORD)
        self.locations_text.pack(fill=tk.X, expand=True, pady=5)
        self.locations_text.bind("<KeyRelease>", self._on_locations_changed)
        
        locations_note = ttk.Label(locations_frame, 
                                text="(One path per line. Use absolute paths like /home/user/Documents or ~/Documents)")
        locations_note.pack(anchor=tk.W)
        
        # Filter mode
        filter_mode_frame = ttk.Frame(self.details_content)
        filter_mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_mode_frame, text="Filter Mode:", width=12).pack(side=tk.LEFT)
        
        self.filter_mode_var = tk.StringVar(value="all")
        ttk.Radiobutton(filter_mode_frame, text="All", variable=self.filter_mode_var, value="all",
                      command=self._update_current_rule).pack(side=tk.LEFT)
        ttk.Radiobutton(filter_mode_frame, text="Any", variable=self.filter_mode_var, value="any",
                      command=self._update_current_rule).pack(side=tk.LEFT)
        ttk.Radiobutton(filter_mode_frame, text="None", variable=self.filter_mode_var, value="none",
                      command=self._update_current_rule).pack(side=tk.LEFT)
        
        # Filters
        filters_frame = ttk.LabelFrame(self.details_content, text="Filters", padding=(5, 5))
        filters_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Filter list with scrollbar
        filter_list_frame = ttk.Frame(filters_frame)
        filter_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        filter_scrollbar = ttk.Scrollbar(filter_list_frame)
        filter_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.filters_list = tk.Listbox(filter_list_frame, yscrollcommand=filter_scrollbar.set, height=6)
        self.filters_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        filter_scrollbar.config(command=self.filters_list.yview)
        
        # Filter buttons
        filter_buttons = ttk.Frame(filters_frame)
        filter_buttons.pack(fill=tk.X)
        
        self.add_filter_button = ttk.Button(filter_buttons, text="Add Filter", 
                                           command=self._add_filter)
        self.add_filter_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_filter_button = ttk.Button(filter_buttons, text="Edit Filter", 
                                           command=self._edit_filter)
        self.edit_filter_button.pack(side=tk.LEFT, padx=5)
        
        self.remove_filter_button = ttk.Button(filter_buttons, text="Remove Filter", 
                                             command=self._remove_filter)
        self.remove_filter_button.pack(side=tk.LEFT, padx=5)
        
        # Actions
        actions_frame = ttk.LabelFrame(self.details_content, text="Actions", padding=(5, 5))
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Action list with scrollbar
        action_list_frame = ttk.Frame(actions_frame)
        action_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        action_scrollbar = ttk.Scrollbar(action_list_frame)
        action_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.actions_list = tk.Listbox(action_list_frame, yscrollcommand=action_scrollbar.set, height=6)
        self.actions_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        action_scrollbar.config(command=self.actions_list.yview)
        
        # Action buttons
        action_buttons = ttk.Frame(actions_frame)
        action_buttons.pack(fill=tk.X)
        
        self.add_action_button = ttk.Button(action_buttons, text="Add Action", 
                                           command=self._add_action)
        self.add_action_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_action_button = ttk.Button(action_buttons, text="Edit Action", 
                                           command=self._edit_action)
        self.edit_action_button.pack(side=tk.LEFT, padx=5)
        
        self.remove_action_button = ttk.Button(action_buttons, text="Remove Action", 
                                             command=self._remove_action)
        self.remove_action_button.pack(side=tk.LEFT, padx=5)
        
        # Save button
        save_frame = ttk.Frame(self.details_content)
        save_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(save_frame, text="Save Rule", 
                                command=self._save_rule_details)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Initialize the details panel
        self._clear_rule_details()
    
    def _filter_rules(self, *args):
        """Filter the rules list by search text and category."""
        search_text = self.search_var.get().lower()
        category = self.category_var.get()
        
        # Clear the tree
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # Add filtered rules
        for i, rule in enumerate(self.rules):
            rule_name = rule.get('name', '').lower()
            rule_category = self._get_rule_category(rule)
            
            # Check if rule matches filters
            name_match = not search_text or search_text in rule_name
            category_match = category == "All" or category == rule_category
            
            if name_match and category_match:
                # Add the rule to the tree
                enabled_text = "✓" if rule.get('enabled', True) else "✗"
                item_id = self.rules_tree.insert("", "end", text=rule.get('name', ''), 
                                              values=(enabled_text, rule_category))
                
                # Store the rule index for reference
                self.rules_tree.item(item_id, tags=(str(i),))
    
    def _get_rule_category(self, rule):
        """Determine the category of a rule based on its actions."""
        # Default category
        category = "Other"
        
        # This is a simplified categorization - in a real implementation,
        # you would analyze the rule's actions and filters more thoroughly
        
        # Check if this rule has actions
        if 'actions' not in rule:
            return category
        
        # Look at the move action if present
        for action in rule['actions']:
            if isinstance(action, dict) and 'move' in action:
                dest = action['move']
                if isinstance(dest, dict) and 'dest' in dest:
                    dest = dest['dest']
                elif not isinstance(dest, str):
                    continue
                
                # Check for category in path
                dest_lower = dest.lower()
                
                if '/documents/' in dest_lower or 'organized/documents' in dest_lower:
                    return "Documents"
                elif '/media/' in dest_lower or 'organized/media' in dest_lower:
                    return "Media"
                elif '/development/' in dest_lower or 'organized/development' in dest_lower:
                    return "Development"
                elif '/archives/' in dest_lower or 'organized/archives' in dest_lower:
                    return "Archives"
                elif '/applications/' in dest_lower or 'organized/applications' in dest_lower:
                    return "Applications"
                elif '/fonts/' in dest_lower or 'organized/fonts' in dest_lower:
                    return "Fonts"
                elif '/system/' in dest_lower or 'organized/system' in dest_lower:
                    return "System"
                elif '/other/' in dest_lower or 'organized/other' in dest_lower:
                    return "Other"
                elif '/cleanup/' in dest_lower or 'cleanup/' in dest_lower:
                    return "Cleanup"
                elif '/duplicates/' in dest_lower or 'duplicates/' in dest_lower:
                    return "Cleanup"
        
        # Check filters for category hints
        if 'filters' in rule:
            for filter_item in rule['filters']:
                if isinstance(filter_item, dict):
                    if 'extension' in filter_item:
                        extensions = filter_item['extension']
                        if isinstance(extensions, list):
                            # Check extension groups
                            doc_exts = ['txt', 'pdf', 'doc', 'docx', 'rtf', 'odt']
                            media_exts = ['jpg', 'jpeg', 'mp3', 'mp4', 'avi', 'mov', 'png']
                            dev_exts = ['py', 'js', 'html', 'css', 'java', 'c', 'cpp']
                            
                            if any(ext in extensions for ext in doc_exts):
                                return "Documents"
                            elif any(ext in extensions for ext in media_exts):
                                return "Media"
                            elif any(ext in extensions for ext in dev_exts):
                                return "Development"
        
        # If we're here, use the default
        return category
    
    def _on_rule_selected(self, event):
        """Handle rule selection in the tree."""
        # Get the selected item
        selection = self.rules_tree.selection()
        if not selection:
            return
        
        # Get the rule index
        item_id = selection[0]
        tags = self.rules_tree.item(item_id, "tags")
        if not tags:
            return
        
        rule_idx = int(tags[0])
        if rule_idx < 0 or rule_idx >= len(self.rules):
            return
        
        # Get the rule
        rule = self.rules[rule_idx]
        
        # Save the current rule index
        self.current_rule = rule_idx
        
        # Display rule details
        self._display_rule_details(rule)
    
    def _display_rule_details(self, rule):
        """Display the details of a rule in the details panel."""
        # Update rule name
        self.rule_name_var.set(rule.get('name', ''))
        
        # Update enabled state
        self.enabled_var.set(rule.get('enabled', True))
        
        # Update target
        self.target_var.set(rule.get('targets', 'files'))
        
        # Update subfolders
        self.subfolders_var.set(rule.get('subfolders', True))
        
        # Update locations
        self.locations_text.delete('1.0', tk.END)
        if 'locations' in rule:
            locations = rule['locations']
            if isinstance(locations, list):
                for loc in locations:
                    if isinstance(loc, dict) and 'path' in loc:
                        self.locations_text.insert(tk.END, f"{loc['path']}\n")
                    else:
                        self.locations_text.insert(tk.END, f"{loc}\n")
            else:
                self.locations_text.insert(tk.END, f"{locations}\n")
        
        # Update filter mode
        self.filter_mode_var.set(rule.get('filter_mode', 'all'))
        
        # Update filters list
        self.filters_list.delete(0, tk.END)
        if 'filters' in rule:
            for filter_item in rule['filters']:
                if isinstance(filter_item, dict):
                    for filter_type, filter_value in filter_item.items():
                        # Format the filter for display
                        if isinstance(filter_value, list):
                            filter_display = f"{filter_type}: {', '.join(str(v) for v in filter_value)}"
                        elif isinstance(filter_value, dict):
                            filter_display = f"{filter_type}: {json.dumps(filter_value)}"
                        else:
                            filter_display = f"{filter_type}: {filter_value}"
                        self.filters_list.insert(tk.END, filter_display)
                else:
                    self.filters_list.insert(tk.END, str(filter_item))
        
        # Update actions list
        self.actions_list.delete(0, tk.END)
        if 'actions' in rule:
            for action in rule['actions']:
                if isinstance(action, dict):
                    for action_type, action_value in action.items():
                        # Format the action for display
                        if isinstance(action_value, dict):
                            action_display = f"{action_type}: {json.dumps(action_value)}"
                        else:
                            action_display = f"{action_type}: {action_value}"
                        self.actions_list.insert(tk.END, action_display)
                else:
                    self.actions_list.insert(tk.END, str(action))
    
    def _clear_rule_details(self):
        """Clear the details panel."""
        # Clear rule name
        self.rule_name_var.set("")
        
        # Reset enabled state
        self.enabled_var.set(True)
        
        # Reset target
        self.target_var.set("files")
        
        # Reset subfolders
        self.subfolders_var.set(True)
        
        # Clear locations
        self.locations_text.delete('1.0', tk.END)
        
        # Reset filter mode
        self.filter_mode_var.set("all")
        
        # Clear filters list
        self.filters_list.delete(0, tk.END)
        
        # Clear actions list
        self.actions_list.delete(0, tk.END)
        
        # Clear current rule
        self.current_rule = None
    
    def _add_rule(self):
        """Add a new rule."""
        # Create a new rule with default values
        rule = {
            'name': 'New Rule',
            'enabled': True,
            'targets': 'files',
            'locations': [os.path.expanduser("~/Documents")],
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
        
        # Update the rule list
        self._filter_rules()
        
        # Set as current rule and display details
        self.current_rule = len(self.rules) - 1
        self._display_rule_details(rule)
        
        # Select the new rule in the tree
        for item in self.rules_tree.get_children():
            if self.rules_tree.item(item, "tags")[0] == str(self.current_rule):
                self.rules_tree.selection_set(item)
                self.rules_tree.see(item)
                break
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _edit_rule(self):
        """Edit the selected rule."""
        # Get the selected rule
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showinfo("Edit Rule", "Please select a rule to edit.")
            return
        
        # Display rule details
        item_id = selection[0]
        tags = self.rules_tree.item(item_id, "tags")
        if not tags:
            return
        
        rule_idx = int(tags[0])
        if rule_idx < 0 or rule_idx >= len(self.rules):
            return
        
        # Get the rule
        rule = self.rules[rule_idx]
        
        # Save the current rule index
        self.current_rule = rule_idx
        
        # Display rule details
        self._display_rule_details(rule)
    
    def _delete_rule(self):
        """Delete the selected rule."""
        # Get the selected rule
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showinfo("Delete Rule", "Please select a rule to delete.")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Delete Rule", "Are you sure you want to delete this rule?"):
            return
        
        # Get the rule index
        item_id = selection[0]
        tags = self.rules_tree.item(item_id, "tags")
        if not tags:
            return
        
        rule_idx = int(tags[0])
        if rule_idx < 0 or rule_idx >= len(self.rules):
            return
        
        # Delete the rule
        del self.rules[rule_idx]
        
        # Update the rule list
        self._filter_rules()
        
        # Clear the details panel
        self._clear_rule_details()
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _duplicate_rule(self):
        """Duplicate the selected rule."""
        # Get the selected rule
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showinfo("Duplicate Rule", "Please select a rule to duplicate.")
            return
        
        # Get the rule index
        item_id = selection[0]
        tags = self.rules_tree.item(item_id, "tags")
        if not tags:
            return
        
        rule_idx = int(tags[0])
        if rule_idx < 0 or rule_idx >= len(self.rules):
            return
        
        # Get the rule
        rule = self.rules[rule_idx]
        
        # Create a deep copy of the rule
        import copy
        new_rule = copy.deepcopy(rule)
        
        # Update the name
        new_rule['name'] = f"{rule['name']} (Copy)"
        
        # Add to rules list
        self.rules.append(new_rule)
        
        # Update the rule list
        self._filter_rules()
        
        # Set as current rule and display details
        self.current_rule = len(self.rules) - 1
        self._display_rule_details(new_rule)
        
        # Select the new rule in the tree
        for item in self.rules_tree.get_children():
            if self.rules_tree.item(item, "tags")[0] == str(self.current_rule):
                self.rules_tree.selection_set(item)
                self.rules_tree.see(item)
                break
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _enable_all_rules(self):
        """Enable all rules."""
        for rule in self.rules:
            rule['enabled'] = True
        
        # Update the rule list
        self._filter_rules()
        
        # Update current rule display if there is one
        if self.current_rule is not None:
            self._display_rule_details(self.rules[self.current_rule])
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _disable_all_rules(self):
        """Disable all rules."""
        for rule in self.rules:
            rule['enabled'] = False
        
        # Update the rule list
        self._filter_rules()
        
        # Update current rule display if there is one
        if self.current_rule is not None:
            self._display_rule_details(self.rules[self.current_rule])
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _move_rule_up(self):
        """Move the selected rule up in the list."""
        # Get the selected rule
        selection = self.rules_tree.selection()
        if not selection:
            return
        
        # Get the rule index
        item_id = selection[0]
        tags = self.rules_tree.item(item_id, "tags")
        if not tags:
            return
        
        rule_idx = int(tags[0])
        if rule_idx <= 0 or rule_idx >= len(self.rules):
            return
        
        # Swap rules
        self.rules[rule_idx], self.rules[rule_idx-1] = self.rules[rule_idx-1], self.rules[rule_idx]
        
        # Update the rule list
        self._filter_rules()
        
        # Update current rule index
        self.current_rule = rule_idx - 1
        
        # Select the moved rule in the tree
        for item in self.rules_tree.get_children():
            if self.rules_tree.item(item, "tags")[0] == str(self.current_rule):
                self.rules_tree.selection_set(item)
                self.rules_tree.see(item)
                break
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _move_rule_down(self):
        """Move the selected rule down in the list."""
        # Get the selected rule
        selection = self.rules_tree.selection()
        if not selection:
            return
        
        # Get the rule index
        item_id = selection[0]
        tags = self.rules_tree.item(item_id, "tags")
        if not tags:
            return
        
        rule_idx = int(tags[0])
        if rule_idx < 0 or rule_idx >= len(self.rules) - 1:
            return
        
        # Swap rules
        self.rules[rule_idx], self.rules[rule_idx+1] = self.rules[rule_idx+1], self.rules[rule_idx]
        
        # Update the rule list
        self._filter_rules()
        
        # Update current rule index
        self.current_rule = rule_idx + 1
        
        # Select the moved rule in the tree
        for item in self.rules_tree.get_children():
            if self.rules_tree.item(item, "tags")[0] == str(self.current_rule):
                self.rules_tree.selection_set(item)
                self.rules_tree.see(item)
                break
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _on_locations_changed(self, event):
        """Handle changes to the locations text."""
        if self.current_rule is not None:
            self._update_current_rule()
    
    def _update_current_rule(self):
        """Update the current rule from the UI state."""
        if self.current_rule is None:
            return
        
        # Get the current rule
        rule = self.rules[self.current_rule]
        
        # Update from UI state
        rule['name'] = self.rule_name_var.get()
        rule['enabled'] = self.enabled_var.get()
        rule['targets'] = self.target_var.get()
        rule['subfolders'] = self.subfolders_var.get()
        rule['filter_mode'] = self.filter_mode_var.get()
        
        # Update locations
        location_text = self.locations_text.get('1.0', tk.END).strip()
        locations = [loc for loc in location_text.split('\n') if loc.strip()]
        
        if len(locations) == 1:
            rule['locations'] = locations[0]
        else:
            rule['locations'] = locations
        
        # Update the rule list display for the enabled state
        self._filter_rules()
        
        # Make sure the rule is still selected
        for item in self.rules_tree.get_children():
            if self.rules_tree.item(item, "tags")[0] == str(self.current_rule):
                self.rules_tree.selection_set(item)
                break
    
    def _save_rule_details(self):
        """Save the current rule details."""
        if self.current_rule is None:
            return
        
        # Update the rule from the UI
        self._update_current_rule()
        
        # Show success message
        messagebox.showinfo("Save Rule", "Rule details saved successfully.")
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _add_filter(self):
        """Add a new filter to the current rule."""
        if self.current_rule is None:
            messagebox.showinfo("Add Filter", "Please select a rule first.")
            return
        
        # Create a dialog to select filter type
        filter_types = [
            "extension", "name", "filename", "path", "created", "modified", 
            "accessed", "filecontent", "filesize", "exif", "duplicate", 
            "regex", "python"
        ]
        
        # Ask the user for the filter type
        filter_type = self._show_selection_dialog(
            "Select Filter Type", 
            "Select the type of filter to add:", 
            filter_types
        )
        
        if not filter_type:
            return
        
        # Create the filter based on the type
        filter_item = None
        
        if filter_type == "extension":
            # Ask for extensions
            extensions = simpledialog.askstring(
                "Extension Filter",
                "Enter extensions (comma-separated):",
                parent=self
            )
            if extensions:
                extensions = [ext.strip() for ext in extensions.split(',')]
                filter_item = {filter_type: extensions}
        
        elif filter_type == "name" or filter_type == "filename" or filter_type == "path":
            # Ask for pattern
            pattern = simpledialog.askstring(
                f"{filter_type.title()} Filter",
                f"Enter {filter_type} pattern:",
                parent=self
            )
            if pattern:
                filter_item = {filter_type: pattern}
        
        elif filter_type == "created" or filter_type == "modified" or filter_type == "accessed":
            # Ask if user wants to filter by specific date or just use for date properties
            use_date = messagebox.askyesno(
                f"{filter_type.title()} Filter",
                f"Do you want to filter by a specific {filter_type} date?\n\n"
                f"Yes: Filter by specific date\n"
                f"No: Just use for date properties in actions"
            )
            
            if use_date:
                # Ask for date format
                date_format = simpledialog.askstring(
                    f"{filter_type.title()} Filter",
                    f"Enter {filter_type} date (YYYY-MM-DD):",
                    parent=self
                )
                if date_format:
                    filter_item = {filter_type: date_format}
            else:
                filter_item = {filter_type: True}
        
        elif filter_type == "filesize":
            # Ask for size and unit
            size = simpledialog.askstring(
                "Filesize Filter",
                "Enter size value (e.g., 10MB, <5GB, >1KB):",
                parent=self
            )
            if size:
                filter_item = {filter_type: size}
        
        elif filter_type == "exif":
            # Just use the basic exif filter
            filter_item = {filter_type: True}
        
        elif filter_type == "duplicate":
            # Ask for detect_original_by
            detect_by = self._show_selection_dialog(
                "Duplicate Filter",
                "How to detect the original file:",
                ["created", "modified", "first_seen", "filename"]
            )
            if detect_by:
                filter_item = {filter_type: {"detect_original_by": detect_by}}
            else:
                filter_item = {filter_type: True}
        
        elif filter_type == "regex":
            # Ask for regex pattern
            pattern = simpledialog.askstring(
                "Regex Filter",
                "Enter regex pattern:",
                parent=self
            )
            if pattern:
                filter_item = {filter_type: {"expr": pattern}}
        
        elif filter_type == "python":
            # Open a text editor for Python code
            code_dialog = tk.Toplevel(self)
            code_dialog.title("Python Filter")
            code_dialog.geometry("600x400")
            code_dialog.transient(self)
            code_dialog.grab_set()
            
            code_frame = ttk.Frame(code_dialog, padding=10)
            code_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(code_frame, text="Enter Python code:").pack(anchor=tk.W)
            
            code_scroll = ttk.Scrollbar(code_frame)
            code_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            code_text = tk.Text(code_frame, yscrollcommand=code_scroll.set, width=70, height=20)
            code_text.pack(fill=tk.BOTH, expand=True)
            code_scroll.config(command=code_text.yview)
            
            # Add sample code
            sample_code = '# Use this Python filter to implement custom logic\n' \
                          '# Available variables: path, filename, tags\n' \
                          '# Return True to include the file, False to exclude\n\n' \
                          'return "important" in filename.lower()'
            code_text.insert(tk.END, sample_code)
            
            # Buttons
            button_frame = ttk.Frame(code_dialog)
            button_frame.pack(fill=tk.X, pady=10)
            
            def on_cancel():
                code_dialog.destroy()
            
            def on_save():
                code = code_text.get("1.0", tk.END).strip()
                nonlocal filter_item
                filter_item = {filter_type: code}
                code_dialog.destroy()
            
            ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.RIGHT, padx=5)
            
            # Wait for dialog to close
            self.wait_window(code_dialog)
        
        # Add the filter if created
        if filter_item:
            # Get the current rule
            rule = self.rules[self.current_rule]
            
            # Make sure filters list exists
            if 'filters' not in rule:
                rule['filters'] = []
            
            # Add the filter
            rule['filters'].append(filter_item)
            
            # Update the filters list
            self._display_rule_details(rule)
            
            # Notify about the change
            self.event_generate("<<RulesChanged>>", when="tail")
    
    def _edit_filter(self):
        """Edit the selected filter."""
        if self.current_rule is None:
            messagebox.showinfo("Edit Filter", "Please select a rule first.")
            return
        
        # Get the selected filter
        selection = self.filters_list.curselection()
        if not selection:
            messagebox.showinfo("Edit Filter", "Please select a filter to edit.")
            return
        
        # Get the filter index
        filter_idx = selection[0]
        
        # Get the current rule
        rule = self.rules[self.current_rule]
        
        # Make sure filters list exists
        if 'filters' not in rule or filter_idx >= len(rule['filters']):
            return
        
        # Get the filter
        filter_item = rule['filters'][filter_idx]
        
        # Edit based on filter type
        if isinstance(filter_item, dict):
            filter_type = list(filter_item.keys())[0]
            filter_value = filter_item[filter_type]
            
            # Handle different filter types
            if filter_type == "extension":
                # Edit extensions
                extensions = filter_value
                if isinstance(extensions, list):
                    extensions_str = ", ".join(extensions)
                else:
                    extensions_str = str(extensions)
                
                new_extensions = simpledialog.askstring(
                    "Edit Extension Filter",
                    "Edit extensions (comma-separated):",
                    initialvalue=extensions_str,
                    parent=self
                )
                
                if new_extensions:
                    new_extensions = [ext.strip() for ext in new_extensions.split(',')]
                    filter_item[filter_type] = new_extensions
            
            elif filter_type == "name" or filter_type == "filename" or filter_type == "path":
                # Edit pattern
                pattern = filter_value
                
                new_pattern = simpledialog.askstring(
                    f"Edit {filter_type.title()} Filter",
                    f"Edit {filter_type} pattern:",
                    initialvalue=pattern,
                    parent=self
                )
                
                if new_pattern:
                    filter_item[filter_type] = new_pattern
            
            elif filter_type == "filesize":
                # Edit size
                size = filter_value
                
                new_size = simpledialog.askstring(
                    "Edit Filesize Filter",
                    "Edit size value (e.g., 10MB, <5GB, >1KB):",
                    initialvalue=size,
                    parent=self
                )
                
                if new_size:
                    filter_item[filter_type] = new_size
            
            elif filter_type == "duplicate":
                # Edit duplicate settings
                if isinstance(filter_value, dict) and "detect_original_by" in filter_value:
                    current = filter_value["detect_original_by"]
                    
                    new_detect_by = self._show_selection_dialog(
                        "Edit Duplicate Filter",
                        "How to detect the original file:",
                        ["created", "modified", "first_seen", "filename"],
                        current
                    )
                    
                    if new_detect_by:
                        filter_item[filter_type] = {"detect_original_by": new_detect_by}
                else:
                    # Ask if user wants to add detect_original_by
                    add_detect = messagebox.askyesno(
                        "Edit Duplicate Filter",
                        "Do you want to specify how to detect the original file?"
                    )
                    
                    if add_detect:
                        detect_by = self._show_selection_dialog(
                            "Duplicate Filter",
                            "How to detect the original file:",
                            ["created", "modified", "first_seen", "filename"]
                        )
                        
                        if detect_by:
                            filter_item[filter_type] = {"detect_original_by": detect_by}
            
            elif filter_type == "regex":
                # Edit regex pattern
                if isinstance(filter_value, dict) and "expr" in filter_value:
                    pattern = filter_value["expr"]
                    
                    new_pattern = simpledialog.askstring(
                        "Edit Regex Filter",
                        "Edit regex pattern:",
                        initialvalue=pattern,
                        parent=self
                    )
                    
                    if new_pattern:
                        filter_item[filter_type] = {"expr": new_pattern}
            
            elif filter_type == "python":
                # Edit Python code
                code = filter_value
                
                # Open a text editor for Python code
                code_dialog = tk.Toplevel(self)
                code_dialog.title("Edit Python Filter")
                code_dialog.geometry("600x400")
                code_dialog.transient(self)
                code_dialog.grab_set()
                
                code_frame = ttk.Frame(code_dialog, padding=10)
                code_frame.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(code_frame, text="Edit Python code:").pack(anchor=tk.W)
                
                code_scroll = ttk.Scrollbar(code_frame)
                code_scroll.pack(side=tk.RIGHT, fill=tk.Y)
                
                code_text = tk.Text(code_frame, yscrollcommand=code_scroll.set, width=70, height=20)
                code_text.pack(fill=tk.BOTH, expand=True)
                code_scroll.config(command=code_text.yview)
                
                # Insert existing code
                code_text.insert(tk.END, code)
                
                # Buttons
                button_frame = ttk.Frame(code_dialog)
                button_frame.pack(fill=tk.X, pady=10)
                
                def on_cancel():
                    code_dialog.destroy()
                
                def on_save():
                    new_code = code_text.get("1.0", tk.END).strip()
                    filter_item[filter_type] = new_code
                    code_dialog.destroy()
                
                ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
                ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.RIGHT, padx=5)
                
                # Wait for dialog to close
                self.wait_window(code_dialog)
        
        # Update the filters list
        self._display_rule_details(rule)
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _remove_filter(self):
        """Remove the selected filter."""
        if self.current_rule is None:
            messagebox.showinfo("Remove Filter", "Please select a rule first.")
            return
        
        # Get the selected filter
        selection = self.filters_list.curselection()
        if not selection:
            messagebox.showinfo("Remove Filter", "Please select a filter to remove.")
            return
        
        # Get the filter index
        filter_idx = selection[0]
        
        # Get the current rule
        rule = self.rules[self.current_rule]
        
        # Make sure filters list exists
        if 'filters' not in rule or filter_idx >= len(rule['filters']):
            return
        
        # Remove the filter
        del rule['filters'][filter_idx]
        
        # Update the filters list
        self._display_rule_details(rule)
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _add_action(self):
        """Add a new action to the current rule."""
        if self.current_rule is None:
            messagebox.showinfo("Add Action", "Please select a rule first.")
            return
        
        # Create a dialog to select action type
        action_types = [
            "move", "copy", "rename", "delete", "trash", 
            "echo", "shell", "python", "confirm"
        ]
        
        # Ask the user for the action type
        action_type = self._show_selection_dialog(
            "Select Action Type", 
            "Select the type of action to add:", 
            action_types
        )
        
        if not action_type:
            return
        
        # Create the action based on the type
        action_item = None
        
        if action_type == "move" or action_type == "copy":
            # Ask for destination
            dest = simpledialog.askstring(
                f"{action_type.title()} Action",
                "Enter destination path:",
                parent=self
            )
            
            if dest:
                # Ask for conflict resolution
                conflict_types = ["rename_new", "skip", "overwrite"]
                conflict = self._show_selection_dialog(
                    "Conflict Resolution",
                    "Select how to handle conflicts:",
                    conflict_types,
                    "rename_new"
                )
                
                if conflict:
                    action_item = {action_type: {"dest": dest, "on_conflict": conflict}}
                else:
                    action_item = {action_type: dest}
        
        elif action_type == "rename":
            # Ask for rename pattern
            pattern = simpledialog.askstring(
                "Rename Action",
                "Enter rename pattern (e.g., '{name}_{created.year}.{extension}'):",
                parent=self
            )
            
            if pattern:
                action_item = {action_type: pattern}
        
        elif action_type == "delete" or action_type == "trash":
            # Just use the basic action
            action_item = {action_type: True}
        
        elif action_type == "echo" or action_type == "confirm":
            # Ask for message
            message = simpledialog.askstring(
                f"{action_type.title()} Action",
                "Enter message:",
                parent=self
            )
            
            if message:
                action_item = {action_type: message}
        
        elif action_type == "shell":
            # Ask for shell command
            command = simpledialog.askstring(
                "Shell Action",
                "Enter shell command:",
                parent=self
            )
            
            if command:
                action_item = {action_type: command}
        
        elif action_type == "python":
            # Open a text editor for Python code
            code_dialog = tk.Toplevel(self)
            code_dialog.title("Python Action")
            code_dialog.geometry("600x400")
            code_dialog.transient(self)
            code_dialog.grab_set()
            
            code_frame = ttk.Frame(code_dialog, padding=10)
            code_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(code_frame, text="Enter Python code:").pack(anchor=tk.W)
            
            code_scroll = ttk.Scrollbar(code_frame)
            code_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            code_text = tk.Text(code_frame, yscrollcommand=code_scroll.set, width=70, height=20)
            code_text.pack(fill=tk.BOTH, expand=True)
            code_scroll.config(command=code_text.yview)
            
            # Add sample code
            sample_code = '# Use this Python action to implement custom logic\n' \
                          '# Available variables: path, filename, tags\n' \
                          '# Return a dictionary to store information\n\n' \
                          'print(f"Processing file: {path}")\n' \
                          'return {"processed": True}'
            code_text.insert(tk.END, sample_code)
            
            # Buttons
            button_frame = ttk.Frame(code_dialog)
            button_frame.pack(fill=tk.X, pady=10)
            
            def on_cancel():
                code_dialog.destroy()
            
            def on_save():
                code = code_text.get("1.0", tk.END).strip()
                nonlocal action_item
                action_item = {action_type: code}
                code_dialog.destroy()
            
            ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.RIGHT, padx=5)
            
            # Wait for dialog to close
            self.wait_window(code_dialog)
        
        # Add the action if created
        if action_item:
            # Get the current rule
            rule = self.rules[self.current_rule]
            
            # Make sure actions list exists
            if 'actions' not in rule:
                rule['actions'] = []
            
            # Add the action
            rule['actions'].append(action_item)
            
            # Update the actions list
            self._display_rule_details(rule)
            
            # Notify about the change
            self.event_generate("<<RulesChanged>>", when="tail")
    
    def _edit_action(self):
        """Edit the selected action."""
        if self.current_rule is None:
            messagebox.showinfo("Edit Action", "Please select a rule first.")
            return
        
        # Get the selected action
        selection = self.actions_list.curselection()
        if not selection:
            messagebox.showinfo("Edit Action", "Please select an action to edit.")
            return
        
        # Get the action index
        action_idx = selection[0]
        
        # Get the current rule
        rule = self.rules[self.current_rule]
        
        # Make sure actions list exists
        if 'actions' not in rule or action_idx >= len(rule['actions']):
            return
        
        # Get the action
        action_item = rule['actions'][action_idx]
        
        # Edit based on action type
        if isinstance(action_item, dict):
            action_type = list(action_item.keys())[0]
            action_value = action_item[action_type]
            
            # Handle different action types
            if action_type == "move" or action_type == "copy":
                if isinstance(action_value, dict) and "dest" in action_value:
                    # Edit destination
                    dest = action_value["dest"]
                    
                    new_dest = simpledialog.askstring(
                        f"Edit {action_type.title()} Action",
                        "Edit destination path:",
                        initialvalue=dest,
                        parent=self
                    )
                    
                    if new_dest:
                        action_value["dest"] = new_dest
                        
                        # Edit conflict resolution
                        if "on_conflict" in action_value:
                            current_conflict = action_value["on_conflict"]
                        else:
                            current_conflict = "rename_new"
                        
                        conflict_types = ["rename_new", "skip", "overwrite"]
                        conflict = self._show_selection_dialog(
                            "Conflict Resolution",
                            "Select how to handle conflicts:",
                            conflict_types,
                            current_conflict
                        )
                        
                        if conflict:
                            action_value["on_conflict"] = conflict
                
                else:
                    # Edit simple destination
                    dest = action_value
                    
                    new_dest = simpledialog.askstring(
                        f"Edit {action_type.title()} Action",
                        "Edit destination path:",
                        initialvalue=dest,
                        parent=self
                    )
                    
                    if new_dest:
                        # Ask if user wants to add conflict resolution
                        add_conflict = messagebox.askyesno(
                            "Edit Action",
                            "Do you want to specify conflict resolution?"
                        )
                        
                        if add_conflict:
                            conflict_types = ["rename_new", "skip", "overwrite"]
                            conflict = self._show_selection_dialog(
                                "Conflict Resolution",
                                "Select how to handle conflicts:",
                                conflict_types,
                                "rename_new"
                            )
                            
                            if conflict:
                                action_item[action_type] = {"dest": new_dest, "on_conflict": conflict}
                            else:
                                action_item[action_type] = new_dest
                        else:
                            action_item[action_type] = new_dest
            
            elif action_type == "rename":
                # Edit rename pattern
                pattern = action_value
                
                new_pattern = simpledialog.askstring(
                    "Edit Rename Action",
                    "Edit rename pattern (e.g., '{name}_{created.year}.{extension}'):",
                    initialvalue=pattern,
                    parent=self
                )
                
                if new_pattern:
                    action_item[action_type] = new_pattern
            
            elif action_type == "echo" or action_type == "confirm":
                # Edit message
                message = action_value
                
                new_message = simpledialog.askstring(
                    f"Edit {action_type.title()} Action",
                    "Edit message:",
                    initialvalue=message,
                    parent=self
                )
                
                if new_message:
                    action_item[action_type] = new_message
            
            elif action_type == "shell":
                # Edit shell command
                command = action_value
                
                new_command = simpledialog.askstring(
                    "Edit Shell Action",
                    "Edit shell command:",
                    initialvalue=command,
                    parent=self
                )
                
                if new_command:
                    action_item[action_type] = new_command
            
            elif action_type == "python":
                # Edit Python code
                code = action_value
                
                # Open a text editor for Python code
                code_dialog = tk.Toplevel(self)
                code_dialog.title("Edit Python Action")
                code_dialog.geometry("600x400")
                code_dialog.transient(self)
                code_dialog.grab_set()
                
                code_frame = ttk.Frame(code_dialog, padding=10)
                code_frame.pack(fill=tk.BOTH, expand=True)
                
                ttk.Label(code_frame, text="Edit Python code:").pack(anchor=tk.W)
                
                code_scroll = ttk.Scrollbar(code_frame)
                code_scroll.pack(side=tk.RIGHT, fill=tk.Y)
                
                code_text = tk.Text(code_frame, yscrollcommand=code_scroll.set, width=70, height=20)
                code_text.pack(fill=tk.BOTH, expand=True)
                code_scroll.config(command=code_text.yview)
                
                # Insert existing code
                code_text.insert(tk.END, code)
                
                # Buttons
                button_frame = ttk.Frame(code_dialog)
                button_frame.pack(fill=tk.X, pady=10)
                
                def on_cancel():
                    code_dialog.destroy()
                
                def on_save():
                    new_code = code_text.get("1.0", tk.END).strip()
                    action_item[action_type] = new_code
                    code_dialog.destroy()
                
                ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
                ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.RIGHT, padx=5)
                
                # Wait for dialog to close
                self.wait_window(code_dialog)
        
        # Update the actions list
        self._display_rule_details(rule)
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _remove_action(self):
        """Remove the selected action."""
        if self.current_rule is None:
            messagebox.showinfo("Remove Action", "Please select a rule first.")
            return
        
        # Get the selected action
        selection = self.actions_list.curselection()
        if not selection:
            messagebox.showinfo("Remove Action", "Please select an action to remove.")
            return
        
        # Get the action index
        action_idx = selection[0]
        
        # Get the current rule
        rule = self.rules[self.current_rule]
        
        # Make sure actions list exists
        if 'actions' not in rule or action_idx >= len(rule['actions']):
            return
        
        # Remove the action
        del rule['actions'][action_idx]
        
        # Update the actions list
        self._display_rule_details(rule)
        
        # Notify about the change
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _show_selection_dialog(self, title, message, options, default=None):
        """Show a dialog to select from options."""
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Create dialog content
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=message).pack(pady=10)
        
        # Create listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Add options
        for option in options:
            listbox.insert(tk.END, option)
        
        # Select default
        if default and default in options:
            index = options.index(default)
            listbox.selection_set(index)
            listbox.see(index)
        
        # Variables
        result = [None]  # Use list to be modifiable in nested function
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def on_cancel():
            dialog.destroy()
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                result[0] = options[selection[0]]
            dialog.destroy()
        
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Select", command=on_select).pack(side=tk.RIGHT, padx=5)
        
        # Double-click selects
        listbox.bind("<Double-1>", lambda e: on_select())
        
        # Wait for dialog to close
        dialog.wait_window()
        
        return result[0]
    
    # Public methods
    
    def update_rules(self, config):
        """Update the rules list from a configuration object."""
        if not config or 'rules' not in config:
            messagebox.showerror("Error", "Invalid configuration - no rules found.")
            return
        
        # Save current rule selection
        current_rule_name = None
        if self.current_rule is not None and self.current_rule < len(self.rules):
            current_rule_name = self.rules[self.current_rule].get('name')
        
        # Update rules
        self.rules = config['rules']
        
        # Update the rule list
        self._filter_rules()
        
        # Try to reselect the current rule
        if current_rule_name:
            for i, rule in enumerate(self.rules):
                if rule.get('name') == current_rule_name:
                    self.current_rule = i
                    self._display_rule_details(rule)
                    
                    # Select in the tree
                    for item in self.rules_tree.get_children():
                        if self.rules_tree.item(item, "tags")[0] == str(i):
                            self.rules_tree.selection_set(item)
                            self.rules_tree.see(item)
                            break
                    
                    break
        else:
            # Clear rule details
            self._clear_rule_details()
    
    def get_updated_config(self):
        """Get the updated configuration with current rules."""
        # Create a configuration with the current rules
        config = {'rules': self.rules}
        
        return config