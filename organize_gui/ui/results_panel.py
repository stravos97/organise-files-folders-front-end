"""
Enhanced Results panel for the File Organization System.

This implementation provides a complete interface for viewing and analyzing the
results of the organization process, including filtering and statistics.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import csv
import datetime
import json
import re

class ResultsPanel(ttk.Frame):
    """Enhanced panel for viewing organization results."""
    
    def __init__(self, parent):
        """Initialize the results panel."""
        super().__init__(parent)
        
        # Current results data
        self.results = []
        
        # Create the UI components
        self._create_widgets()

    def _create_widgets(self):
        """Create the UI components for the results panel using grid."""
        # Configure main frame grid
        self.grid_rowconfigure(3, weight=1) # Results frame should expand
        self.grid_columnconfigure(0, weight=1)

        row_index = 0

        # Summary frame
        summary_frame = ttk.LabelFrame(self, text="Summary", padding=(10, 5))
        summary_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        summary_frame.grid_columnconfigure(0, weight=1) # Make inner grid expand

        # Create grid for summary information
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.grid(row=0, column=0, sticky='ew', pady=5)
        # Configure columns for even spacing (optional)
        for i in range(6):
            summary_grid.grid_columnconfigure(i, weight=1)

        # Row 1: Basic counts
        ttk.Label(summary_grid, text="Total Files:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.total_files_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.total_files_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Files Moved:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.files_moved_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.files_moved_var).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Files Skipped:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.files_skipped_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.files_skipped_var).grid(row=0, column=5, sticky=tk.W, padx=5, pady=2)

        # Row 2: Additional stats
        ttk.Label(summary_grid, text="Rules Applied:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.rules_applied_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.rules_applied_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Duplicates Found:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.duplicates_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.duplicates_var).grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Errors:").grid(row=1, column=4, sticky=tk.W, padx=5, pady=2)
        self.errors_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.errors_var).grid(row=1, column=5, sticky=tk.W, padx=5, pady=2)

        # Row 3: Last run information
        ttk.Label(summary_grid, text="Last Run:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.last_run_var = tk.StringVar(value="Never")
        ttk.Label(summary_grid, textvariable=self.last_run_var).grid(row=2, column=1, columnspan=5, sticky=tk.W, padx=5, pady=2)
        row_index += 1

        # Category breakdown frame
        category_frame = ttk.LabelFrame(self, text="Category Breakdown", padding=(10, 5))
        category_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        category_frame.grid_columnconfigure(1, weight=1) # Make progress bars expand

        # Horizontal progress bars for each category
        self.category_frames = {}
        self.category_vars = {}
        self.category_labels = {}
        self.category_progress = {}

        # Define categories (consider making this dynamic later)
        self.categories = [
            "Documents", "Media", "Development", "Archives",
            "Applications", "Other", "Duplicates", "Temporary"
        ]

        for i, category in enumerate(self.categories):
            # Create label and progress bar
            label = ttk.Label(category_frame, text=f"{category}:", width=15)
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=1)

            var = tk.IntVar(value=0)
            progress = ttk.Progressbar(
                category_frame,
                orient=tk.HORIZONTAL,
                mode='determinate',
                variable=var
            )
            progress.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=1)

            count_label = ttk.Label(category_frame, text="0", width=8, anchor=tk.E)
            count_label.grid(row=i, column=2, sticky=tk.E, padx=5, pady=1)

            # Store references
            self.category_vars[category] = var
            self.category_labels[category] = count_label
            self.category_progress[category] = progress
            # Note: Removed hardcoded color styling, rely on theme or add theme-aware styling later if needed
        row_index += 1

        # Filter frame
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1) # Make filter entry expand

        ttk.Label(filter_frame, text="Filter:").grid(row=0, column=0, padx=(0, 5))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self._apply_filters) # Use trace_add
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        filter_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))

        ttk.Label(filter_frame, text="Category:").grid(row=0, column=2, padx=(0, 5))
        self.category_filter_var = tk.StringVar(value="All")
        category_values = ["All"] + self.categories
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_filter_var,
                                     values=category_values, state="readonly", width=15)
        category_combo.grid(row=0, column=3, padx=(0, 10))
        category_combo.bind("<<ComboboxSelected>>", self._apply_filters)

        ttk.Label(filter_frame, text="Status:").grid(row=0, column=4, padx=(0, 5))
        self.status_var = tk.StringVar(value="All")
        statuses = ["All", "Moved", "Skipped", "Error"]
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var,
                                   values=statuses, state="readonly", width=10)
        status_combo.grid(row=0, column=5)
        status_combo.bind("<<ComboboxSelected>>", self._apply_filters)
        row_index += 1

        # Results frame with tree view
        results_frame = ttk.LabelFrame(self, text="Results", padding=(10, 5))
        results_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Create tree view with scrollbars
        tree_frame = ttk.Frame(results_frame)
        tree_frame.grid(row=0, column=0, sticky='nsew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        vscrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        vscrollbar.grid(row=0, column=1, sticky='ns')

        hscrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky='ew')

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("source", "destination", "rule", "status"),
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set,
            selectmode="browse" # Only allow single selection
        )
        self.tree.grid(row=0, column=0, sticky='nsew')

        vscrollbar.config(command=self.tree.yview)
        hscrollbar.config(command=self.tree.xview)

        # Configure tree columns
        self.tree.column("#0", width=50, minwidth=40, stretch=tk.NO, anchor=tk.E)
        self.tree.column("source", width=300, minwidth=150, stretch=tk.YES)
        self.tree.column("destination", width=300, minwidth=150, stretch=tk.YES)
        self.tree.column("rule", width=150, minwidth=100, stretch=tk.NO)
        self.tree.column("status", width=80, minwidth=70, stretch=tk.NO)

        self.tree.heading("#0", text="#", anchor=tk.E)
        self.tree.heading("source", text="Source Path", command=lambda: self._sort_column("source", False))
        self.tree.heading("destination", text="Destination Path", command=lambda: self._sort_column("destination", False))
        self.tree.heading("rule", text="Rule Applied", command=lambda: self._sort_column("rule", False))
        self.tree.heading("status", text="Status", command=lambda: self._sort_column("status", False))

        # Tag configurations for status colors (using theme-aware foreground)
        style = ttk.Style()
        style.map("Treeview", foreground=self._fixed_map("foreground")) # Fix for theme change issue
        self.tree.tag_configure("moved", foreground="green")
        self.tree.tag_configure("skipped", foreground="orange")
        self.tree.tag_configure("error", foreground="red")

        # Add context menu to tree
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Copy Source Path", command=self._copy_source_path)
        self.context_menu.add_command(label="Copy Destination Path", command=self._copy_destination_path)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open Source Location", command=self._open_source_location)
        self.context_menu.add_command(label="Open Destination Location", command=self._open_destination_location)

        self.tree.bind("<Button-3>", self._show_context_menu) # Standard right-click
        self.tree.bind("<Button-2>", self._show_context_menu) # macOS Control-click
        self.tree.bind("<Double-1>", self._show_file_details)
        row_index += 1

        # Action buttons (bottom)
        button_frame = ttk.Frame(self)
        button_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=(5, 10))
        button_frame.grid_columnconfigure(3, weight=1) # Push clear button right

        refresh_button = ttk.Button(button_frame, text="Refresh", command=self._refresh_results)
        refresh_button.grid(row=0, column=0, padx=(0, 5))

        export_button = ttk.Button(button_frame, text="Export Results...", command=self._export_results)
        export_button.grid(row=0, column=1, padx=5)

        visualize_button = ttk.Button(button_frame, text="Visualize Results", command=self._visualize_results)
        visualize_button.grid(row=0, column=2, padx=5)

        clear_button = ttk.Button(button_frame, text="Clear Results", command=self._clear_results)
        clear_button.grid(row=0, column=3, sticky='e') # Push to right
        row_index += 1
    # Helper function to fix ttk style mapping issue on theme change
    def _fixed_map(self, option):
        style = ttk.Style()
        return [elm for elm in style.map("Treeview", query_opt=option) if elm[:2] != ("!disabled", "!selected")]

    def _apply_filters(self, *args):
        """Apply filters to the results view."""
        filter_text = self.filter_var.get().lower()
        category = self.category_filter_var.get()
        status = self.status_var.get()

        # Clear the tree
        self.tree.delete(*self.tree.get_children())

        # Add filtered results
        count = 0
        for result in self.results:
            source_lower = result.get('source', '').lower()
            dest_lower = result.get('destination', '').lower()
            rule_lower = result.get('rule', '').lower()
            status_lower = result.get('status', '').lower()

            # Filter text match
            text_match = not filter_text or (
                filter_text in source_lower or
                filter_text in dest_lower or
                filter_text in rule_lower
            )
            if not text_match:
                continue

            # Category match
            if category != "All":
                result_category = self._get_result_category(result)
                if result_category != category:
                    continue

            # Status match
            if status != "All" and status_lower != status.lower():
                continue

            # Add the item to the tree
            count += 1
            status_text = result.get('status', '')
            rule_text = result.get('rule', '')

            # Determine tag based on status
            tag = status_text.lower() if status_text else 'unknown'

            self.tree.insert(
                "", "end", text=str(count), # Use count as item text
                values=(
                    result.get('source', ''),
                    result.get('destination', ''),
                    rule_text,
                    status_text
                ),
                tags=(tag,)
            )
    
    def _sort_column(self, column, reverse):
        """Sort tree contents when a column header is clicked."""
        # Get all items
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        
        # Sort items
        items.sort(reverse=reverse)
        
        # Rearrange items in sorted order
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
            
            # Update item text to maintain proper numbering
            self.tree.item(item, text=str(index + 1))
        
        # Switch the heading to display the opposite sort order
        self.tree.heading(column, command=lambda: self._sort_column(column, not reverse))
    def _get_result_category(self, result):
        """Determine the category of a result based on its destination path."""
        dest = result.get('destination', '')
        status = result.get('status', '')

        if status == "Error":
            return "Other" # Treat errors as 'Other' for categorization

        if not dest:
            return "Other"

        # Normalize path and check against defined categories
        dest_norm = dest.replace('\\', '/').lower()
        for category in self.categories:
            cat_lower = category.lower()
            # Check common patterns like /Category/ or /Organized/Category/ or /Cleanup/Category/
            if f'/{cat_lower}/' in dest_norm or f'/organized/{cat_lower}/' in dest_norm or f'/cleanup/{cat_lower}/' in dest_norm:
                 return category

        # Fallback
        return "Other"
    
    def _show_context_menu(self, event):
        """Show the context menu on right click."""
        item = self.tree.identify_row(event.y)
        if item:
            # Select the item
            self.tree.selection_set(item)
            # Show the context menu
            self.context_menu.post(event.x_root, event.y_root)
    def _copy_source_path(self):
        """Copy the source path of the selected item to the clipboard."""
        selected_item = self.tree.selection()
        if not selected_item: return
        values = self.tree.item(selected_item[0], 'values')
        if values and len(values) > 0:
            self._copy_to_clipboard(values[0]) # Use helper
    def _copy_destination_path(self):
        """Copy the destination path of the selected item to the clipboard."""
        selected_item = self.tree.selection()
        if not selected_item: return
        values = self.tree.item(selected_item[0], 'values')
        if values and len(values) > 1 and values[1]: # Check if destination exists
            self._copy_to_clipboard(values[1]) # Use helper
    def _open_source_location(self):
        """Open the source location in the file explorer."""
        selected_item = self.tree.selection()
        if not selected_item: return
        values = self.tree.item(selected_item[0], 'values')
        if values and len(values) > 0:
            path = values[0]
            self._open_file_location(path)
    def _open_destination_location(self):
        """Open the destination location in the file explorer."""
        selected_item = self.tree.selection()
        if not selected_item: return
        values = self.tree.item(selected_item[0], 'values')
        if values and len(values) > 1 and values[1]: # Check if destination exists
            path = values[1]
            self._open_file_location(path)
    
    def _open_file_location(self, path):
        """Open a file location in the system file explorer."""
        try:
            # Get the directory path
            if os.path.isfile(path):
                dir_path = os.path.dirname(path)
            else:
                dir_path = path
            
            # Make sure the path exists
            if not os.path.exists(dir_path):
                messagebox.showwarning("Open Location", "The specified path does not exist.")
                return
            
            # Open the location based on platform
            if os.name == 'nt':  # Windows
                os.startfile(dir_path)
            elif os.name == 'posix':  # macOS, Linux
                if os.path.exists('/usr/bin/open'):  # macOS
                    os.system(f'open "{dir_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{dir_path}"')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open location: {str(e)}")
    
    def _show_file_details(self, event):
        """Show detailed information about a file on double click."""
        item = self.tree.identify_row(event.y)
        if item:
            values = self.tree.item(item, 'values')
            if values:
                source = values[0]
                destination = values[1] if len(values) > 1 else ""
                rule = values[2] if len(values) > 2 else ""
                status = values[3] if len(values) > 3 else ""
                
                # Create a details dialog
                details_dialog = tk.Toplevel(self)
                details_dialog.title("File Details")
                details_dialog.geometry("600x350")
                details_dialog.transient(self)
                details_dialog.grab_set()
                
                # Create dialog content
                main_frame = ttk.Frame(details_dialog, padding=10)
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                # File name and status
                status_frame = ttk.Frame(main_frame)
                status_frame.pack(fill=tk.X, pady=5)
                
                file_name = os.path.basename(source)
                ttk.Label(status_frame, text=f"File: {file_name}", font=("", 12, "bold")).pack(side=tk.LEFT)
                
                status_label = ttk.Label(status_frame, text=f"Status: {status}")
                status_label.pack(side=tk.RIGHT)
                
                if status.lower() == "moved":
                    status_label.config(foreground="#008800")  # Green
                elif status.lower() == "skipped":
                    status_label.config(foreground="#FF8800")  # Orange
                elif status.lower() == "error":
                    status_label.config(foreground="#FF0000")  # Red
                
                # Source path
                path_frame = ttk.LabelFrame(main_frame, text="Paths", padding=5)
                path_frame.pack(fill=tk.X, pady=5)
                
                source_frame = ttk.Frame(path_frame)
                source_frame.pack(fill=tk.X, pady=2)
                
                ttk.Label(source_frame, text="Source:", width=10).pack(side=tk.LEFT)
                
                source_var = tk.StringVar(value=source)
                source_entry = ttk.Entry(source_frame, textvariable=source_var, width=50)
                source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
                source_entry.config(state="readonly")
                
                copy_source = ttk.Button(source_frame, text="Copy", width=8,
                                       command=lambda: self._copy_to_clipboard(source))
                copy_source.pack(side=tk.LEFT)
                
                # Destination path
                if destination:
                    dest_frame = ttk.Frame(path_frame)
                    dest_frame.pack(fill=tk.X, pady=2)
                    
                    ttk.Label(dest_frame, text="Destination:", width=10).pack(side=tk.LEFT)
                    
                    dest_var = tk.StringVar(value=destination)
                    dest_entry = ttk.Entry(dest_frame, textvariable=dest_var, width=50)
                    dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
                    dest_entry.config(state="readonly")
                    
                    copy_dest = ttk.Button(dest_frame, text="Copy", width=8,
                                         command=lambda: self._copy_to_clipboard(destination))
                    copy_dest.pack(side=tk.LEFT)
                
                # Rule info
                if rule:
                    ttk.Label(main_frame, text=f"Applied Rule: {rule}", font=("", 10, "italic")).pack(anchor=tk.W, pady=5)
                
                # File information
                file_info_frame = ttk.LabelFrame(main_frame, text="File Information", padding=5)
                file_info_frame.pack(fill=tk.X, pady=5)
                
                # Get file info if available
                try:
                    if os.path.exists(source):
                        file_stat = os.stat(source)
                        
                        # Format size
                        size = file_stat.st_size
                        size_str = self._format_size(size)
                        
                        # Format dates
                        created = datetime.datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                        modified = datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        accessed = datetime.datetime.fromtimestamp(file_stat.st_atime).strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Add info to grid
                        ttk.Label(file_info_frame, text="Size:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
                        ttk.Label(file_info_frame, text=size_str).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
                        
                        ttk.Label(file_info_frame, text="Created:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
                        ttk.Label(file_info_frame, text=created).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
                        
                        ttk.Label(file_info_frame, text="Modified:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
                        ttk.Label(file_info_frame, text=modified).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
                        
                        ttk.Label(file_info_frame, text="Accessed:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
                        ttk.Label(file_info_frame, text=accessed).grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
                        
                        # Get file type if possible
                        _, extension = os.path.splitext(source)
                        if extension:
                            ttk.Label(file_info_frame, text="Type:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
                            ttk.Label(file_info_frame, text=extension[1:].upper()).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
                    else:
                        ttk.Label(file_info_frame, text="File no longer exists at the source location.").pack(padx=5, pady=5)
                
                except Exception as e:
                    ttk.Label(file_info_frame, text=f"Error retrieving file information: {str(e)}").pack(padx=5, pady=5)
                
                # Action buttons
                button_frame = ttk.Frame(main_frame)
                button_frame.pack(fill=tk.X, pady=10)
                
                if os.path.exists(source):
                    open_source = ttk.Button(button_frame, text="Open Source Location", 
                                          command=lambda: self._open_file_location(source))
                    open_source.pack(side=tk.LEFT, padx=5)
                
                if destination and os.path.exists(destination):
                    open_dest = ttk.Button(button_frame, text="Open Destination Location", 
                                         command=lambda: self._open_file_location(destination))
                    open_dest.pack(side=tk.LEFT, padx=5)
                
                close_button = ttk.Button(button_frame, text="Close", 
                                        command=details_dialog.destroy)
                close_button.pack(side=tk.RIGHT, padx=5)
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            # Optionally show a brief status message without a dialog
            # print("Path copied to clipboard")
        except tk.TclError:
             messagebox.showwarning("Copy Failed", "Could not access clipboard.")
    
    def _format_size(self, size_bytes):
        """Format a size in bytes to a human-readable string."""
        # Define units and their thresholds
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        
        # Handle zero size
        if size_bytes == 0:
            return "0 B"
        
        # Calculate appropriate unit
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1
        
        # Format with appropriate precision
        if i == 0:  # Bytes
            return f"{size_bytes:.0f} {units[i]}"
        else:  # Larger units
            return f"{size_bytes:.2f} {units[i]}"
    
    def _refresh_results(self):
        """Refresh results from the preview panel."""
        # Try to get results from preview panel
        try:
            parent = self.winfo_parent()
            parent_widget = self.nametowidget(parent)
            
            # If parent is notebook, get the preview panel
            if isinstance(parent_widget, ttk.Notebook):
                # Try to find the preview panel
                for tab_id in parent_widget.tabs():
                    tab = parent_widget.nametowidget(tab_id)
                    if hasattr(tab, 'get_results'):
                        results = tab.get_results()
                        if results:
                            self.set_results(results)
                            return
            
            # If we got here, try to generate an event to request results
            self.event_generate("<<RequestResults>>", when="tail")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh results: {str(e)}")
    def _export_results(self):
        """Export the currently displayed (filtered) results to a CSV file."""
        # Get items currently displayed in the tree
        tree_items = self.tree.get_children()
        if not tree_items:
            messagebox.showinfo("No Results", "There are no results currently displayed to export.")
            return

        # Ask for file path
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(
            title="Export Displayed Results",
            filetypes=filetypes,
            defaultextension=".csv"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile: # Add encoding
                writer = csv.writer(csvfile)
                # Write header matching tree columns
                writer.writerow(["Source Path", "Destination Path", "Rule Applied", "Status"])
                # Write data from tree
                for item_id in tree_items:
                    values = self.tree.item(item_id, 'values')
                    writer.writerow(values)
            
            messagebox.showinfo("Export Successful", 
                              f"Results exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", 
                               f"Failed to export results: {str(e)}")
    
    def _visualize_results(self):
        """Visualize the results in a separate window."""
        if not self.results:
            messagebox.showinfo("No Results", "There are no results to visualize.")
            return
        
        # Create visualization dialog
        viz_dialog = tk.Toplevel(self)
        viz_dialog.title("Results Visualization")
        viz_dialog.geometry("800x600")
        viz_dialog.transient(self)
        
        # Create main frame
        main_frame = ttk.Frame(viz_dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for different visualizations
        viz_notebook = ttk.Notebook(main_frame)
        viz_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Category distribution tab
        category_tab = ttk.Frame(viz_notebook, padding=10)
        viz_notebook.add(category_tab, text="Category Distribution")
        
        # Calculate category counts
        category_counts = {}
        for result in self.results:
            category = self._get_result_category(result)
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Create canvas for category distribution
        canvas_frame = ttk.Frame(category_tab)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        category_canvas = tk.Canvas(canvas_frame, bg="white", height=400)
        category_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw simple bar chart
        self._draw_bar_chart(category_canvas, category_counts)
        
        # Status distribution tab
        status_tab = ttk.Frame(viz_notebook, padding=10)
        viz_notebook.add(status_tab, text="Status Distribution")
        
        # Calculate status counts
        status_counts = {}
        for result in self.results:
            status = result.get('status', '')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Create canvas for status distribution
        status_canvas_frame = ttk.Frame(status_tab)
        status_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        status_canvas = tk.Canvas(status_canvas_frame, bg="white", height=400)
        status_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw simple pie chart
        self._draw_pie_chart(status_canvas, status_counts)
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=viz_dialog.destroy)
        close_button.pack(pady=10)
    
    def _draw_bar_chart(self, canvas, data):
        """Draw a simple bar chart on the canvas."""
        if not data:
            canvas.create_text(canvas.winfo_width() / 2, canvas.winfo_height() / 2,
                              text="No data to display", fill="gray", font=("Arial", 14, "bold"))
            return
        
        # Get canvas dimensions
        canvas.update()
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Chart dimensions
        chart_width = width - 100
        chart_height = height - 100
        x_start = 50
        y_start = height - 50
        
        # Calculate bar width and spacing
        num_bars = len(data)
        bar_width = max(20, min(80, chart_width / (num_bars * 1.5)))
        bar_spacing = bar_width / 2
        
        # Find maximum value for scaling
        max_value = max(data.values()) if data else 1
        
        # Draw axes
        canvas.create_line(x_start, y_start, x_start + chart_width, y_start, fill="black", width=2)  # X-axis
        canvas.create_line(x_start, y_start, x_start, y_start - chart_height, fill="black", width=2)  # Y-axis
        
        # Bar colors
        colors = {
            "Documents": "#4e89ae",
            "Media": "#43658b",
            "Development": "#ed6663",
            "Archives": "#ffa372",
            "Applications": "#a0c1b8",
            "Other": "#f39189",
            "Duplicates": "#ffbd69",
            "Temporary": "#b0a565"
        }
        
        # Draw bars
        x = x_start + bar_spacing
        for category, count in data.items():
            # Calculate bar height
            bar_height = (count / max_value) * chart_height
            
            # Draw bar
            color = colors.get(category, "#cccccc")
            canvas.create_rectangle(
                x, y_start - bar_height,
                x + bar_width, y_start,
                fill=color, outline="black", width=1
            )
            
            # Draw label
            canvas.create_text(
                x + bar_width/2, y_start + 10,
                text=category, fill="black", anchor=tk.N,
                font=("Arial", 8), angle=45
            )
            
            # Draw value
            canvas.create_text(
                x + bar_width/2, y_start - bar_height - 10,
                text=str(count), fill="black", anchor=tk.S,
                font=("Arial", 8, "bold")
            )
            
            x += bar_width + bar_spacing
        
        # Draw title
        canvas.create_text(
            width / 2, 20,
            text="Files by Category",
            fill="black", font=("Arial", 12, "bold")
        )
    
    def _draw_pie_chart(self, canvas, data):
        """Draw a simple pie chart on the canvas."""
        if not data:
            canvas.create_text(canvas.winfo_width() / 2, canvas.winfo_height() / 2,
                              text="No data to display", fill="gray", font=("Arial", 14, "bold"))
            return
        
        # Get canvas dimensions
        canvas.update()
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Calculate center and radius
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 3
        
        # Calculate total
        total = sum(data.values())
        
        # Status colors
        colors = {
            "Moved": "#4CAF50",    # Green
            "Skipped": "#FFC107",  # Yellow
            "Error": "#F44336",    # Red
            "": "#9E9E9E"          # Gray (default)
        }
        
        # Draw pie slices
        start_angle = 0
        legend_y = 50
        
        # Sort data for consistent appearance
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
        
        for status, count in sorted_data:
            # Calculate angles
            angle = (count / total) * 360
            end_angle = start_angle + angle
            
            # Draw slice
            color = colors.get(status, "#cccccc")
            canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=start_angle, extent=angle,
                fill=color, outline="white", width=2
            )
            
            # Calculate midpoint for label
            mid_angle = start_angle + angle / 2
            text_radius = radius * 0.7
            text_x = center_x + text_radius * tk.cos(tk.rad(mid_angle))
            text_y = center_y - text_radius * tk.sin(tk.rad(mid_angle))
            
            # Only draw text for slices that are large enough
            if angle > 20:
                # Draw percentage label
                percentage = (count / total) * 100
                canvas.create_text(
                    text_x, text_y,
                    text=f"{percentage:.1f}%",
                    fill="white", font=("Arial", 10, "bold")
                )
            
            # Draw legend item
            canvas.create_rectangle(
                width - 150, legend_y,
                width - 130, legend_y + 15,
                fill=color, outline="black"
            )
            
            status_text = status if status else "Unknown"
            canvas.create_text(
                width - 125, legend_y + 7,
                text=f"{status_text} ({count})",
                fill="black", anchor=tk.W,
                font=("Arial", 9)
            )
            
            legend_y += 25
            start_angle = end_angle
        
        # Draw title
        canvas.create_text(
            width / 2, 20,
            text="Files by Status",
            fill="black", font=("Arial", 12, "bold")
        )
    
    def _clear_results(self):
        """Clear all results."""
        if not self.results:
            return
        
        if messagebox.askyesno("Clear Results", 
                              "Are you sure you want to clear all results?"):
            self.results = []
            self.tree.delete(*self.tree.get_children())
            self._update_summary()
    
    def _update_summary(self):
        """Update the summary information."""
        total_files = len(self.results)
        files_moved = sum(1 for r in self.results if r.get('status', '') == "Moved")
        files_skipped = sum(1 for r in self.results if r.get('status', '') == "Skipped")
        errors = sum(1 for r in self.results if r.get('status', '') == "Error")
        
        # Count unique rules
        rules = set(r.get('rule', '') for r in self.results if r.get('rule', ''))
        rules_applied = len(rules)
        
        # Count duplicates
        duplicates = sum(1 for r in self.results if "duplicate" in r.get('destination', '').lower())
        
        # Update the variables
        self.total_files_var.set(str(total_files))
        self.files_moved_var.set(str(files_moved))
        self.files_skipped_var.set(str(files_skipped))
        self.rules_applied_var.set(str(rules_applied))
        self.duplicates_var.set(str(duplicates))
        self.errors_var.set(str(errors))
        
        # Update last run timestamp
        self.last_run_var.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Update category breakdown
        category_counts = {}
        for result in self.results:
            category = self._get_result_category(result)
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate percentages and update progress bars
        for category, count in category_counts.items():
            if category in self.category_vars:
                percentage = (count / max(1, total_files)) * 100
                self.category_vars[category].set(percentage)
                self.category_labels[category].config(text=str(count))
            
        # Reset any categories not in the results
        for category in self.category_vars:
            if category not in category_counts:
                self.category_vars[category].set(0)
                self.category_labels[category].config(text="0")
    
    # Public methods
    
    def add_result(self, source, destination, rule, status):
        """Add a single result to the list."""
        self.results.append({
            'source': source,
            'destination': destination,
            'rule': rule,
            'status': status
        })
        
        # Update the tree and summary
        self._apply_filters()
        self._update_summary()
    
    def set_results(self, results):
        """Set the results to a new list."""
        self.results = results
        
        # Update the tree and summary
        self._apply_filters()
        self._update_summary()
    
    def clear(self):
        """Clear all results."""
        self.results = []
        self.tree.delete(*self.tree.get_children())
        self._update_summary()
    
    def get_results(self):
        """Get the current results."""
        return self.results
