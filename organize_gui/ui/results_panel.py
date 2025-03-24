"""
Results panel for the File Organization System.

This module defines the UI components for viewing the results of
organization runs and analyzing file movement.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import datetime

class ResultsPanel(ttk.Frame):
    """Panel for viewing organization results."""
    
    def __init__(self, parent):
        """Initialize the results panel."""
        super().__init__(parent)
        
        # Current results data
        self.results = []
        
        # Create the UI components
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI components for the results panel."""
        # Main layout container
        main_frame = ttk.Frame(self, padding=(10, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Summary frame
        summary_frame = ttk.LabelFrame(main_frame, text="Summary", padding=(10, 5))
        summary_frame.pack(fill=tk.X, pady=5)
        
        # Create grid for summary information
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, pady=5)
        
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
        
        # Last run information
        ttk.Label(summary_grid, text="Last Run:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.last_run_var = tk.StringVar(value="Never")
        ttk.Label(summary_grid, textvariable=self.last_run_var).grid(row=2, column=1, columnspan=5, sticky=tk.W, padx=5, pady=2)
        
        # Filter frame
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        # Search filter
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", self._apply_filters)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=30)
        filter_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Category filter
        ttk.Label(filter_frame, text="Category:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_var = tk.StringVar(value="All")
        categories = ["All", "Documents", "Media", "Development", "Archives", 
                      "Applications", "Fonts", "System", "Other", "Cleanup", "Error"]
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, 
                                     values=categories, state="readonly", width=15)
        category_combo.pack(side=tk.LEFT, padx=(0, 10))
        category_combo.bind("<<ComboboxSelected>>", self._apply_filters)
        
        # Status filter
        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_var = tk.StringVar(value="All")
        statuses = ["All", "Moved", "Skipped", "Error"]
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var, 
                                   values=statuses, state="readonly", width=10)
        status_combo.pack(side=tk.LEFT)
        status_combo.bind("<<ComboboxSelected>>", self._apply_filters)
        
        # Results frame with tree view
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=(10, 5))
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create tree view with scrollbars
        tree_frame = ttk.Frame(results_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar
        vscrollbar = ttk.Scrollbar(tree_frame)
        vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Horizontal scrollbar
        hscrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Tree view
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("source", "destination", "rule", "status"),
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set
        )
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        vscrollbar.config(command=self.tree.yview)
        hscrollbar.config(command=self.tree.xview)
        
        # Configure tree columns
        self.tree.column("#0", width=50, minwidth=50)
        self.tree.column("source", width=200, minwidth=100)
        self.tree.column("destination", width=200, minwidth=100)
        self.tree.column("rule", width=150, minwidth=100)
        self.tree.column("status", width=80, minwidth=80)
        
        self.tree.heading("#0", text="#")
        self.tree.heading("source", text="Source Path")
        self.tree.heading("destination", text="Destination Path")
        self.tree.heading("rule", text="Rule Applied")
        self.tree.heading("status", text="Status")
        
        # Tag configurations for status colors
        self.tree.tag_configure("moved", background="#e6ffe6")  # Light green
        self.tree.tag_configure("skipped", background="#ffffcc")  # Light yellow
        self.tree.tag_configure("error", background="#ffe6e6")  # Light red
        
        # Add context menu to tree
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Copy Source Path", command=self._copy_source_path)
        self.context_menu.add_command(label="Copy Destination Path", command=self._copy_destination_path)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Show in Explorer/Finder", command=self._show_in_explorer)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Double-1>", self._show_file_details)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        refresh_button = ttk.Button(button_frame, text="Refresh", command=self._refresh_results)
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        export_button = ttk.Button(button_frame, text="Export Results...", command=self._export_results)
        export_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(button_frame, text="Clear Results", command=self._clear_results)
        clear_button.pack(side=tk.RIGHT, padx=5)
    
    def _apply_filters(self, *args):
        """Apply filters to the results view."""
        filter_text = self.filter_var.get().lower()
        category = self.category_var.get()
        status = self.status_var.get()
        
        # Clear the tree
        self.tree.delete(*self.tree.get_children())
        
        # Add filtered results
        count = 0
        for result in self.results:
            # Skip items that don't match the filter
            if filter_text and not (
                filter_text in result['source'].lower() or 
                filter_text in result['destination'].lower() or 
                filter_text in result['rule'].lower()
            ):
                continue
            
            # Skip items that don't match the category
            if category != "All":
                result_category = self._get_result_category(result)
                if result_category != category:
                    continue
            
            # Skip items that don't match the status
            if status != "All" and result['status'] != status:
                continue
            
            # Add the item to the tree
            count += 1
            self.tree.insert(
                "", "end", text=str(count),
                values=(
                    result['source'],
                    result['destination'],
                    result['rule'],
                    result['status']
                ),
                tags=(result['status'].lower(),)
            )
    
    def _get_result_category(self, result):
        """Determine the category of a result based on its destination path."""
        dest = result['destination']
        
        if '/Documents/' in dest:
            return "Documents"
        elif '/Media/' in dest:
            return "Media"
        elif '/Development/' in dest:
            return "Development"
        elif '/Archives/' in dest:
            return "Archives"
        elif '/Applications/' in dest:
            return "Applications"
        elif '/Fonts/' in dest:
            return "Fonts"
        elif '/System/' in dest:
            return "System"
        elif '/Cleanup/' in dest:
            return "Cleanup"
        elif '/Other/' in dest:
            return "Other"
        elif result['status'] == "Error":
            return "Error"
        
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
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], 'values')
            if values:
                self.clipboard_clear()
                self.clipboard_append(values[0])
    
    def _copy_destination_path(self):
        """Copy the destination path of the selected item to the clipboard."""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], 'values')
            if values:
                self.clipboard_clear()
                self.clipboard_append(values[1])
    
    def _show_in_explorer(self):
        """Show the selected file in the file explorer/finder."""
        # In a real implementation, this would use platform-specific code
        # to open the file explorer/finder at the file's location
        messagebox.showinfo("Not Implemented", 
                          "This feature is not implemented in the skeleton code.")
    
    def _show_file_details(self, event):
        """Show detailed information about a file on double click."""
        item = self.tree.identify_row(event.y)
        if item:
            values = self.tree.item(item, 'values')
            if values:
                # In a real implementation, this would show a dialog with
                # detailed information about the file and its movement
                messagebox.showinfo("File Details", 
                                  f"Source: {values[0]}\n"
                                  f"Destination: {values[1]}\n"
                                  f"Rule: {values[2]}\n"
                                  f"Status: {values[3]}")
    
    def _refresh_results(self):
        """Refresh the results from the latest run."""
        # In a real implementation, this would reload results from storage
        messagebox.showinfo("Not Implemented", 
                          "This feature is not implemented in the skeleton code.")
    
    def _export_results(self):
        """Export the results to a CSV file."""
        if not self.results:
            messagebox.showinfo("No Results", "There are no results to export.")
            return
        
        # Ask for file path
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(
            title="Export Results", 
            filetypes=filetypes,
            defaultextension=".csv"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(["Source", "Destination", "Rule", "Status"])
                # Write data
                for result in self.results:
                    writer.writerow([
                        result['source'],
                        result['destination'],
                        result['rule'],
                        result['status']
                    ])
            
            messagebox.showinfo("Export Successful", 
                              f"Results exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", 
                               f"Failed to export results: {str(e)}")
    
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
        files_moved = sum(1 for r in self.results if r['status'] == "Moved")
        files_skipped = sum(1 for r in self.results if r['status'] == "Skipped")
        errors = sum(1 for r in self.results if r['status'] == "Error")
        
        # Count unique rules
        rules = set(r['rule'] for r in self.results)
        rules_applied = len(rules)
        
        # Count duplicates (in a real implementation, this would be more accurate)
        duplicates = sum(1 for r in self.results if "duplicate" in r['destination'].lower())
        
        # Update the variables
        self.total_files_var.set(str(total_files))
        self.files_moved_var.set(str(files_moved))
        self.files_skipped_var.set(str(files_skipped))
        self.rules_applied_var.set(str(rules_applied))
        self.duplicates_var.set(str(duplicates))
        self.errors_var.set(str(errors))
        
        # Update last run timestamp
        self.last_run_var.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
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