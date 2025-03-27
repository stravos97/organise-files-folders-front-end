"""
Manages the rule list Treeview, filtering, and selection
for the RulesPanel.
"""

import tkinter as tk
from tkinter import ttk

class RuleListManager:
    """Manages the rule list Treeview and associated controls."""

    def __init__(self, parent_frame, rules_data_ref):
        """
        Initialize the RuleListManager.

        Args:
            parent_frame: The ttk.Frame to build the UI within.
            rules_data_ref: A reference to the list containing the rule dictionaries.
                            This manager reads this list but does not modify it directly.
        """
        self.parent_frame = parent_frame
        self.rules_data_ref = rules_data_ref # Reference to the external rules list
        self._selection_change_callback = None

        self._create_widgets()
        self.refresh_list() # Initial population

    def _create_widgets(self):
        """Create the UI components for the rule list."""
        self.parent_frame.grid_columnconfigure(0, weight=1)
        self.parent_frame.grid_rowconfigure(1, weight=1) # Make list_frame expand

        # Search and filter controls
        filter_frame = ttk.Frame(self.parent_frame)
        filter_frame.grid(row=0, column=0, sticky='ew', pady=(0, 5))
        filter_frame.grid_columnconfigure(1, weight=1) # Make search entry expand

        search_label = ttk.Label(filter_frame, text="Search:")
        search_label.grid(row=0, column=0, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_rules_ui_event)
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))

        category_label = ttk.Label(filter_frame, text="Category:")
        category_label.grid(row=0, column=2, padx=(0, 5))

        self.category_var = tk.StringVar(value="All")
        categories = ["All", "Documents", "Media", "Development", "Archives",
                      "Applications", "Fonts", "System", "Other", "Cleanup"]
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var,
                                     values=categories, state="readonly", width=15)
        category_combo.grid(row=0, column=3)
        category_combo.bind("<<ComboboxSelected>>", self._filter_rules_ui_event)

        # Rules list with scrollbar
        list_frame = ttk.Frame(self.parent_frame)
        list_frame.grid(row=1, column=0, sticky='nsew', pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.grid(row=0, column=1, sticky='ns')

        self.rules_tree = ttk.Treeview(
            list_frame,
            columns=("enabled", "category"),
            yscrollcommand=scrollbar.set,
            selectmode="browse" # Only allow single selection
        )
        self.rules_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.config(command=self.rules_tree.yview)

        # Configure columns
        self.rules_tree.column("#0", width=220, minwidth=180, stretch=tk.YES) # Name column
        self.rules_tree.column("enabled", width=60, minwidth=60, anchor=tk.CENTER, stretch=tk.NO)
        self.rules_tree.column("category", width=100, minwidth=80, anchor=tk.W, stretch=tk.NO)

        self.rules_tree.heading("#0", text="Rule Name")
        self.rules_tree.heading("enabled", text="Enabled")
        self.rules_tree.heading("category", text="Category")

        # Bind selection event to internal handler
        self.rules_tree.bind("<<TreeviewSelect>>", self._on_selection_changed)

    def _get_rule_category(self, rule):
        """Determine the category of a rule based on its actions/filters."""
        # Default category
        category = "Other"
        actions = rule.get('actions', [])
        filters = rule.get('filters', [])

        # Check move/copy actions for destination hints
        for action in actions:
            if isinstance(action, dict):
                action_type = next(iter(action))
                if action_type in ('move', 'copy'):
                    dest_info = action[action_type]
                    dest = dest_info.get('dest') if isinstance(dest_info, dict) else dest_info
                    if isinstance(dest, str):
                        dest_lower = dest.lower()
                        # Simple category matching based on path segments
                        if any(f'/{cat.lower()}/' in dest_lower or f'organized/{cat.lower()}' in dest_lower for cat in ["Documents", "Media", "Development", "Archives", "Applications", "Fonts", "System", "Other"]):
                            for cat in ["Documents", "Media", "Development", "Archives", "Applications", "Fonts", "System", "Other"]:
                                if f'/{cat.lower()}/' in dest_lower or f'organized/{cat.lower()}' in dest_lower:
                                    return cat
                        if '/cleanup/' in dest_lower or 'cleanup/' in dest_lower or '/duplicates/' in dest_lower or 'duplicates/' in dest_lower:
                            return "Cleanup"

        # Check filters for hints (e.g., extension)
        for filter_item in filters:
            if isinstance(filter_item, dict) and 'extension' in filter_item:
                extensions = filter_item['extension']
                if isinstance(extensions, list):
                    ext_set = {ext.lower().strip('.') for ext in extensions}
                    doc_exts = {'txt', 'pdf', 'doc', 'docx', 'rtf', 'odt', 'pages', 'key', 'ppt', 'pptx', 'xls', 'xlsx'}
                    media_exts = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'mp3', 'wav', 'aac', 'flac', 'mp4', 'avi', 'mov', 'mkv', 'wmv'}
                    dev_exts = {'py', 'js', 'html', 'css', 'java', 'c', 'cpp', 'h', 'hpp', 'cs', 'rb', 'php', 'swift', 'kt', 'go'}
                    archive_exts = {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'}

                    if ext_set.intersection(doc_exts): return "Documents"
                    if ext_set.intersection(media_exts): return "Media"
                    if ext_set.intersection(dev_exts): return "Development"
                    if ext_set.intersection(archive_exts): return "Archives"

        return category

    def _filter_rules_ui_event(self, *args):
        """Callback for UI events that trigger filtering."""
        self.refresh_list()

    def refresh_list(self):
        """Clear and re-populate the Treeview based on current filters."""
        search_text = self.search_var.get().lower()
        category = self.category_var.get()

        # Clear the tree
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)

        # Add filtered rules from the referenced list
        for i, rule in enumerate(self.rules_data_ref):
            # Ensure rule is a dictionary
            if not isinstance(rule, dict):
                print(f"Warning: Skipping non-dictionary rule at index {i}")
                continue

            rule_name = rule.get('name', f'Unnamed Rule {i+1}')
            rule_name_lower = rule_name.lower()
            rule_category = self._get_rule_category(rule)

            # Check if rule matches filters
            name_match = not search_text or search_text in rule_name_lower
            category_match = category == "All" or category == rule_category

            if name_match and category_match:
                enabled_text = "✓" if rule.get('enabled', True) else "✗"
                # Use index 'i' as the item ID (iid) for stable reference
                item_id = str(i)
                self.rules_tree.insert("", "end", iid=item_id, text=rule_name,
                                       values=(enabled_text, rule_category))
                # We don't need tags anymore as iid stores the index

    def get_selected_rule_index(self):
        """Return the index (from rules_data_ref) of the selected rule."""
        selection = self.rules_tree.selection()
        if not selection:
            return None
        item_id = selection[0]
        try:
            # The item_id is the original index as a string
            return int(item_id)
        except (ValueError, IndexError):
            return None

    def select_rule_by_index(self, index):
        """Selects a rule in the Treeview based on its original index."""
        item_id = str(index)
        if self.rules_tree.exists(item_id):
            self.rules_tree.selection_set(item_id)
            self.rules_tree.focus(item_id) # Set focus
            self.rules_tree.see(item_id) # Ensure visible
        else:
            # If the item might be filtered out, clear selection
            current_selection = self.rules_tree.selection()
            if current_selection:
                self.rules_tree.selection_remove(current_selection)


    def bind_selection_change(self, callback):
        """Register a callback function for when the selection changes."""
        self._selection_change_callback = callback

    def _on_selection_changed(self, event):
        """Internal handler for Treeview selection change."""
        if self._selection_change_callback:
            # Pass the event object to the callback, similar to how Tkinter bindings work
            self._selection_change_callback(event)
