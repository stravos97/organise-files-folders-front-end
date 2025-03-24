"""
Rules management panel for the File Organization System.

This module defines the UI components for viewing, enabling/disabling,
and modifying organization rules.
"""

import tkinter as tk
from tkinter import ttk, messagebox

class RulesPanel(ttk.Frame):
    """Panel for managing organization rules."""
    
    def __init__(self, parent):
        """Initialize the rules panel."""
        super().__init__(parent)
        
        # Current rules data
        self.rules = []
        
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
        
        # Search box
        search_frame = ttk.Frame(rules_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_rules)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Category filter
        category_frame = ttk.Frame(rules_frame)
        category_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(category_frame, text="Category:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="All")
        categories = ["All", "Documents", "Media", "Development", "Archives", 
                      "Applications", "Fonts", "System", "Other", "Cleanup"]
        category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                     values=categories, state="readonly")
        category_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        category_combo.bind("<<ComboboxSelected>>", self._filter_rules)
        
        # Create scrollable frame for rules list
        rules_canvas = tk.Canvas(rules_frame)
        scrollbar = ttk.Scrollbar(rules_frame, orient="vertical", command=rules_canvas.yview)
        self.rules_list_frame = ttk.Frame(rules_canvas)
        
        self.rules_list_frame.bind(
            "<Configure>",
            lambda e: rules_canvas.configure(scrollregion=rules_canvas.bbox("all"))
        )
        
        rules_canvas.create_window((0, 0), window=self.rules_list_frame, anchor="nw")
        rules_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        rules_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Action buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        enable_all_button = ttk.Button(button_frame, text="Enable All", 
                                      command=self._enable_all_rules)
        enable_all_button.pack(side=tk.LEFT, padx=5)
        
        disable_all_button = ttk.Button(button_frame, text="Disable All", 
                                       command=self._disable_all_rules)
        disable_all_button.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Rule details
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=2)
        
        details_frame = ttk.LabelFrame(right_frame, text="Rule Details", padding=(10, 5))
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Rule name
        self.rule_name_var = tk.StringVar()
        rule_name_label = ttk.Label(details_frame, textvariable=self.rule_name_var, 
                                   font=("", 12, "bold"))
        rule_name_label.pack(fill=tk.X, pady=5)
        
        # Create notebook for rule details
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Locations tab
        locations_frame = ttk.Frame(self.details_notebook, padding=10)
        self.details_notebook.add(locations_frame, text="Locations")
        
        # Locations text
        ttk.Label(locations_frame, text="Source Locations:").pack(anchor=tk.W)
        self.locations_text = tk.Text(locations_frame, height=5, width=40, wrap=tk.WORD)
        self.locations_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.locations_text.config(state=tk.DISABLED)
        
        # Subfolders checkbox
        self.subfolders_var = tk.BooleanVar()
        subfolders_check = ttk.Checkbutton(
            locations_frame, 
            text="Include Subfolders",
            variable=self.subfolders_var,
            state=tk.DISABLED
        )
        subfolders_check.pack(anchor=tk.W)
        
        # Filters tab
        filters_frame = ttk.Frame(self.details_notebook, padding=10)
        self.details_notebook.add(filters_frame, text="Filters")
        
        # Filter mode
        filter_mode_frame = ttk.Frame(filters_frame)
        filter_mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_mode_frame, text="Filter Mode:").pack(side=tk.LEFT)
        self.filter_mode_var = tk.StringVar()
        filter_mode_label = ttk.Label(filter_mode_frame, textvariable=self.filter_mode_var,
                                     font=("", 10, "italic"))
        filter_mode_label.pack(side=tk.LEFT, padx=5)
        
        # Filters list
        ttk.Label(filters_frame, text="Filters:").pack(anchor=tk.W, pady=(10, 5))
        self.filters_text = tk.Text(filters_frame, height=10, width=40, wrap=tk.WORD)
        self.filters_text.pack(fill=tk.BOTH, expand=True)
        self.filters_text.config(state=tk.DISABLED)
        
        # Actions tab
        actions_frame = ttk.Frame(self.details_notebook, padding=10)
        self.details_notebook.add(actions_frame, text="Actions")
        
        # Actions list
        ttk.Label(actions_frame, text="Actions:").pack(anchor=tk.W)
        self.actions_text = tk.Text(actions_frame, height=10, width=40, wrap=tk.WORD)
        self.actions_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.actions_text.config(state=tk.DISABLED)
    
    def _create_rule_checkboxes(self):
        """Create checkboxes for all rules in the list."""
        # Clear existing checkboxes
        for widget in self.rules_list_frame.winfo_children():
            widget.destroy()
        
        # Add a checkbox for each rule
        self.rule_vars = {}
        
        for i, rule in enumerate(self.rules):
            frame = ttk.Frame(self.rules_list_frame)
            frame.pack(fill=tk.X, pady=1)
            
            # Rule enable/disable checkbox
            var = tk.BooleanVar(value=rule.get('enabled', True))
            self.rule_vars[rule['name']] = var
            
            # Tag the rule with a category for filtering
            category = self._get_rule_category(rule)
            
            check = ttk.Checkbutton(
                frame, 
                text=rule['name'],
                variable=var,
                command=lambda r=rule, v=var: self._toggle_rule(r, v)
            )
            check.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Add a category label
            category_label = ttk.Label(frame, text=category, width=12)
            category_label.pack(side=tk.RIGHT)
            
            # Make the whole row selectable
            frame.bind("<Button-1>", lambda e, r=rule: self._show_rule_details(r))
            check.bind("<Button-1>", lambda e, r=rule: self._show_rule_details(r), add="+")
            category_label.bind("<Button-1>", lambda e, r=rule: self._show_rule_details(r))
    
    def _get_rule_category(self, rule):
        """Determine the category of a rule based on its actions."""
        # This is a simplified categorization - in a real implementation,
        # you would analyze the rule's actions and filters more thoroughly
        
        # Check if this rule has actions
        if 'actions' not in rule:
            return "Unknown"
        
        # Look at the move action if present
        for action in rule['actions']:
            if isinstance(action, dict) and 'move' in action:
                dest = action['move']
                if isinstance(dest, dict) and 'dest' in dest:
                    dest = dest['dest']
                
                if '/Cleanup/' in dest or 'Temporary' in dest or 'Logs' in dest:
                    return "Cleanup"
                elif '/Documents/' in dest or 'Text' in dest or 'PDF' in dest:
                    return "Documents"
                elif '/Media/' in dest or 'Images' in dest or 'Audio' in dest or 'Video' in dest:
                    return "Media"
                elif '/Development/' in dest or 'Code' in dest or 'Web' in dest:
                    return "Development"
                elif '/Archives/' in dest:
                    return "Archives"
                elif '/Applications/' in dest:
                    return "Applications"
                elif '/Fonts/' in dest:
                    return "Fonts"
                elif '/System/' in dest:
                    return "System"
                elif '/Other/' in dest:
                    return "Other"
        
        return "Unknown"
    
    def _filter_rules(self, *args):
        """Filter the rules list by search text and category."""
        # Get current filter values
        search_text = self.search_var.get().lower()
        category = self.category_var.get()
        
        # Apply filters
        for widget in self.rules_list_frame.winfo_children():
            # Each widget is a frame containing a checkbox and category label
            checkbox = widget.winfo_children()[0]  # The checkbox is the first child
            rule_text = checkbox.cget("text").lower()
            
            # Get the rule category (from the label)
            rule_category = widget.winfo_children()[1].cget("text")  # The label is the second child
            
            # Check if rule matches filters
            matches_search = search_text in rule_text
            matches_category = category == "All" or category == rule_category
            
            # Show/hide based on filters
            if matches_search and matches_category:
                widget.pack(fill=tk.X, pady=1)
            else:
                widget.pack_forget()
    
    def _toggle_rule(self, rule, var):
        """Toggle a rule's enabled state."""
        rule['enabled'] = var.get()
        
        # Notify that rules have changed
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _enable_all_rules(self):
        """Enable all rules."""
        for rule in self.rules:
            rule['enabled'] = True
            
        # Update checkboxes
        for var in self.rule_vars.values():
            var.set(True)
        
        # Notify that rules have changed
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _disable_all_rules(self):
        """Disable all rules."""
        for rule in self.rules:
            rule['enabled'] = False
            
        # Update checkboxes
        for var in self.rule_vars.values():
            var.set(False)
        
        # Notify that rules have changed
        self.event_generate("<<RulesChanged>>", when="tail")
    
    def _show_rule_details(self, rule):
        """Show the details of a selected rule."""
        # Update rule name
        self.rule_name_var.set(rule['name'])
        
        # Update locations
        self.locations_text.config(state=tk.NORMAL)
        self.locations_text.delete(1.0, tk.END)
        
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
        
        self.locations_text.config(state=tk.DISABLED)
        
        # Update subfolders checkbox
        self.subfolders_var.set(rule.get('subfolders', False))
        
        # Update filter mode
        self.filter_mode_var.set(rule.get('filter_mode', 'all'))
        
        # Update filters
        self.filters_text.config(state=tk.NORMAL)
        self.filters_text.delete(1.0, tk.END)
        
        if 'filters' in rule:
            for filter_item in rule['filters']:
                if isinstance(filter_item, dict):
                    for filter_type, filter_value in filter_item.items():
                        self.filters_text.insert(tk.END, f"{filter_type}: ")
                        
                        # Handle different filter value types
                        if isinstance(filter_value, list):
                            self.filters_text.insert(tk.END, ", ".join(str(v) for v in filter_value))
                        elif isinstance(filter_value, dict):
                            self.filters_text.insert(tk.END, str(filter_value))
                        else:
                            self.filters_text.insert(tk.END, str(filter_value))
                        
                        self.filters_text.insert(tk.END, "\n")
                else:
                    self.filters_text.insert(tk.END, f"{filter_item}\n")
        
        self.filters_text.config(state=tk.DISABLED)
        
        # Update actions
        self.actions_text.config(state=tk.NORMAL)
        self.actions_text.delete(1.0, tk.END)
        
        if 'actions' in rule:
            for action in rule['actions']:
                if isinstance(action, dict):
                    for action_type, action_value in action.items():
                        self.actions_text.insert(tk.END, f"{action_type}: ")
                        
                        # Handle different action value types
                        if isinstance(action_value, dict):
                            self.actions_text.insert(tk.END, "\n")
                            for k, v in action_value.items():
                                self.actions_text.insert(tk.END, f"  {k}: {v}\n")
                        else:
                            self.actions_text.insert(tk.END, f"{action_value}\n")
                else:
                    self.actions_text.insert(tk.END, f"{action}\n")
        
        self.actions_text.config(state=tk.DISABLED)
    
    # Public methods
    
    def update_rules(self, config):
        """Update the rules list from a configuration object."""
        if not config or 'rules' not in config:
            messagebox.showerror("Error", "Invalid configuration - no rules found.")
            return
        
        self.rules = config['rules']
        
        # Recreate the checkboxes
        self._create_rule_checkboxes()
        
        # Select the first rule if available
        if self.rules:
            self._show_rule_details(self.rules[0])