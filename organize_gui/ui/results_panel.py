"""
Enhanced Results panel for the File Organization System.

Uses ResultsTreeManager to display the results list.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import csv
import datetime
import json
import re

# Import the new manager
from .results_tree_manager import ResultsTreeManager

class ResultsPanel(ttk.Frame):
    """Enhanced panel for viewing organization results."""

    def __init__(self, parent):
        """Initialize the results panel."""
        super().__init__(parent)

        # Current results data
        self.results = []
        self.filtered_results = [] # Store currently displayed results

        # Create the UI components
        self._create_widgets()

    def _create_widgets(self):
        """Create the UI components for the results panel using grid."""
        self.grid_rowconfigure(3, weight=1) # Results frame should expand
        self.grid_columnconfigure(0, weight=1)

        row_index = 0

        # --- Summary frame ---
        summary_frame = ttk.LabelFrame(self, text="Summary", padding=(10, 5))
        summary_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_grid = ttk.Frame(summary_frame); summary_grid.grid(row=0, column=0, sticky='ew', pady=5)
        for i in range(6): summary_grid.grid_columnconfigure(i, weight=1)
        # Labels and Vars for summary
        self.total_files_var = tk.StringVar(value="0")
        self.files_moved_var = tk.StringVar(value="0")
        self.files_skipped_var = tk.StringVar(value="0")
        self.rules_applied_var = tk.StringVar(value="0")
        self.duplicates_var = tk.StringVar(value="0")
        self.errors_var = tk.StringVar(value="0")
        self.last_run_var = tk.StringVar(value="Never")
        # Grid layout for summary
        ttk.Label(summary_grid, text="Total Files:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, textvariable=self.total_files_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, text="Files Moved:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, textvariable=self.files_moved_var).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, text="Files Skipped:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, textvariable=self.files_skipped_var).grid(row=0, column=5, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, text="Rules Applied:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, textvariable=self.rules_applied_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, text="Duplicates Found:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, textvariable=self.duplicates_var).grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, text="Errors:").grid(row=1, column=4, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, textvariable=self.errors_var).grid(row=1, column=5, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, text="Last Run:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(summary_grid, textvariable=self.last_run_var).grid(row=2, column=1, columnspan=5, sticky=tk.W, padx=5, pady=2)
        row_index += 1

        # --- Category breakdown frame ---
        category_frame = ttk.LabelFrame(self, text="Category Breakdown", padding=(10, 5))
        category_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        category_frame.grid_columnconfigure(1, weight=1)
        self.category_vars = {}
        self.category_labels = {}
        self.categories = ["Documents", "Media", "Development", "Archives", "Applications", "Other", "Duplicates", "Temporary"]
        for i, category in enumerate(self.categories):
            ttk.Label(category_frame, text=f"{category}:", width=15).grid(row=i, column=0, sticky=tk.W, padx=5, pady=1)
            var = tk.IntVar(value=0)
            progress = ttk.Progressbar(category_frame, orient=tk.HORIZONTAL, mode='determinate', variable=var)
            progress.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=1)
            count_label = ttk.Label(category_frame, text="0", width=8, anchor=tk.E)
            count_label.grid(row=i, column=2, sticky=tk.E, padx=5, pady=1)
            self.category_vars[category] = var
            self.category_labels[category] = count_label
        row_index += 1

        # --- Filter frame ---
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(filter_frame, text="Filter:").grid(row=0, column=0, padx=(0, 5))
        self.filter_var = tk.StringVar(); self.filter_var.trace_add("write", self._apply_filters)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        filter_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        ttk.Label(filter_frame, text="Category:").grid(row=0, column=2, padx=(0, 5))
        self.category_filter_var = tk.StringVar(value="All")
        category_values = ["All"] + self.categories
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_filter_var, values=category_values, state="readonly", width=15)
        category_combo.grid(row=0, column=3, padx=(0, 10)); category_combo.bind("<<ComboboxSelected>>", self._apply_filters)
        ttk.Label(filter_frame, text="Status:").grid(row=0, column=4, padx=(0, 5))
        self.status_var = tk.StringVar(value="All")
        statuses = ["All", "Moved", "Skipped", "Error"]
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var, values=statuses, state="readonly", width=10)
        status_combo.grid(row=0, column=5); status_combo.bind("<<ComboboxSelected>>", self._apply_filters)
        row_index += 1

        # --- Results Treeview Frame ---
        results_outer_frame = ttk.LabelFrame(self, text="Results", padding=(10, 5))
        results_outer_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        results_outer_frame.grid_rowconfigure(0, weight=1)
        results_outer_frame.grid_columnconfigure(0, weight=1)

        # Instantiate ResultsTreeManager inside the LabelFrame
        self.results_tree_manager = ResultsTreeManager(results_outer_frame)
        # The manager handles its internal treeview, scrollbars, context menu, etc.

        row_index += 1

        # --- Action buttons (bottom) ---
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
        clear_button.grid(row=0, column=3, sticky='e')
        row_index += 1

    def _apply_filters(self, *args):
        """Filter the raw results and update the tree via ResultsTreeManager."""
        filter_text = self.filter_var.get().lower()
        category = self.category_filter_var.get()
        status = self.status_var.get()

        self.filtered_results = [] # Reset filtered list
        for result in self.results:
            source_lower = result.get('source', '').lower()
            dest_lower = result.get('destination', '').lower()
            rule_lower = result.get('rule', '').lower()
            status_lower = result.get('status', '').lower()

            # Apply filters
            text_match = not filter_text or any(filter_text in s for s in [source_lower, dest_lower, rule_lower])
            category_match = category == "All" or self._get_result_category(result) == category
            status_match = status == "All" or status_lower == status.lower()

            if text_match and category_match and status_match:
                self.filtered_results.append(result)

        # Update the tree view using the manager
        self.results_tree_manager.populate_tree(self.filtered_results)

    def _get_result_category(self, result):
        """Determine the category of a result based on its destination path."""
        dest = result.get('destination', '')
        status = result.get('status', '')
        if status == "Error": return "Other"
        if not dest: return "Other"
        dest_norm = dest.replace('\\', '/').lower()
        for category in self.categories:
            cat_lower = category.lower()
            if f'/{cat_lower}/' in dest_norm or f'/organized/{cat_lower}/' in dest_norm or f'/cleanup/{cat_lower}/' in dest_norm:
                 return category
        return "Other"

    # Removed methods now in ResultsTreeManager:
    # _sort_column, _show_context_menu, _copy_source_path, _copy_destination_path,
    # _open_source_location, _open_destination_location, _open_file_location,
    # _show_file_details, _copy_to_clipboard, _format_size, _fixed_map

    def _refresh_results(self):
        """Request results from the source (e.g., preview panel)."""
        try:
            parent = self.winfo_parent()
            parent_widget = self.nametowidget(parent)
            if isinstance(parent_widget, ttk.Notebook):
                for tab_id in parent_widget.tabs():
                    tab = parent_widget.nametowidget(tab_id)
                    # Check if the tab is the preview panel by name or attribute
                    if hasattr(tab, 'get_results') and "preview" in str(tab).lower():
                        results = tab.get_results()
                        if results is not None: # Allow empty list
                            self.set_results(results)
                            return
            # Fallback: Generate event if preview panel not found directly
            self.event_generate("<<RequestResults>>", when="tail")
        except Exception as e: messagebox.showerror("Error", f"Failed to refresh results: {str(e)}")

    def _export_results(self):
        """Export the currently displayed (filtered) results to a CSV file."""
        if not self.filtered_results:
            messagebox.showinfo("No Results", "There are no results currently displayed to export.")
            return
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(title="Export Displayed Results", filetypes=filetypes, defaultextension=".csv")
        if not filename: return
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Source Path", "Destination Path", "Rule Applied", "Status"])
                for result in self.filtered_results:
                     writer.writerow([result.get(k, '') for k in ['source', 'destination', 'rule', 'status']])
            messagebox.showinfo("Export Successful", f"Results exported to {filename}")
        except Exception as e: messagebox.showerror("Export Failed", f"Failed to export results: {str(e)}")

    def _visualize_results(self):
        """Visualize the results in a separate window."""
        if not self.results: messagebox.showinfo("No Results", "There are no results to visualize."); return
        viz_dialog = tk.Toplevel(self); viz_dialog.title("Results Visualization"); viz_dialog.geometry("800x600"); viz_dialog.transient(self)
        main_frame = ttk.Frame(viz_dialog, padding=10); main_frame.pack(fill=tk.BOTH, expand=True)
        viz_notebook = ttk.Notebook(main_frame); viz_notebook.pack(fill=tk.BOTH, expand=True)
        # Category Tab
        category_tab = ttk.Frame(viz_notebook, padding=10); viz_notebook.add(category_tab, text="Category Distribution")
        category_counts = {cat: 0 for cat in self.categories}
        for result in self.results: category_counts[self._get_result_category(result)] += 1
        canvas_frame = ttk.Frame(category_tab); canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        category_canvas = tk.Canvas(canvas_frame, bg="white", height=400); category_canvas.pack(fill=tk.BOTH, expand=True)
        # Use lambda to delay canvas update until after dialog is shown
        category_canvas.bind("<Map>", lambda e: self._draw_bar_chart(category_canvas, category_counts), add='+')
        # Status Tab
        status_tab = ttk.Frame(viz_notebook, padding=10); viz_notebook.add(status_tab, text="Status Distribution")
        status_counts = {}
        for result in self.results: status = result.get('status', ''); status_counts[status] = status_counts.get(status, 0) + 1
        status_canvas_frame = ttk.Frame(status_tab); status_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        status_canvas = tk.Canvas(status_canvas_frame, bg="white", height=400); status_canvas.pack(fill=tk.BOTH, expand=True)
        # Use lambda to delay canvas update
        status_canvas.bind("<Map>", lambda e: self._draw_pie_chart(status_canvas, status_counts), add='+')
        # Close Button
        ttk.Button(main_frame, text="Close", command=viz_dialog.destroy).pack(pady=10)

    def _draw_bar_chart(self, canvas, data):
        """Draw a simple bar chart on the canvas."""
        canvas.delete("all") # Clear previous drawing
        if not data: canvas.create_text(200, 200, text="No data", fill="gray"); return
        width = canvas.winfo_width(); height = canvas.winfo_height()
        if width <= 1 or height <= 1: return # Canvas not ready
        chart_width, chart_height = width - 100, height - 100
        x_start, y_start = 50, height - 50
        num_bars = len([c for c in data.values() if c > 0]) # Count non-zero bars
        if num_bars == 0: canvas.create_text(width/2, height/2, text="No data > 0", fill="gray"); return
        bar_width = max(10, min(60, chart_width / (num_bars * 1.5))); bar_spacing = bar_width / 2
        max_value = max(data.values()) if data else 1
        canvas.create_line(x_start, y_start, x_start + chart_width, y_start); canvas.create_line(x_start, y_start, x_start, y_start - chart_height)
        colors = {"Documents": "#4e89ae", "Media": "#43658b", "Development": "#ed6663", "Archives": "#ffa372", "Applications": "#a0c1b8", "Other": "#f39189", "Duplicates": "#ffbd69", "Temporary": "#b0a565"}
        x = x_start + bar_spacing
        for category, count in data.items():
            if count == 0: continue
            bar_height = max(1, (count / max_value) * chart_height) # Ensure min height 1
            color = colors.get(category, "#cccccc")
            canvas.create_rectangle(x, y_start - bar_height, x + bar_width, y_start, fill=color, outline="black")
            canvas.create_text(x + bar_width/2, y_start + 5, text=category, fill="black", anchor=tk.N, font=("Arial", 8), angle=45)
            canvas.create_text(x + bar_width/2, y_start - bar_height - 5, text=str(count), fill="black", anchor=tk.S, font=("Arial", 8, "bold"))
            x += bar_width + bar_spacing
        canvas.create_text(width / 2, 20, text="Files by Category", fill="black", font=("Arial", 12, "bold"))

    def _draw_pie_chart(self, canvas, data):
        """Draw a simple pie chart on the canvas."""
        canvas.delete("all")
        if not data or sum(data.values()) == 0: canvas.create_text(200, 200, text="No data", fill="gray"); return
        width = canvas.winfo_width(); height = canvas.winfo_height()
        if width <= 1 or height <= 1: return
        center_x, center_y = width / 2, height / 2; radius = min(width, height) / 3.5 # Smaller radius
        total = sum(data.values())
        colors = {"Moved": "#4CAF50", "Skipped": "#FFC107", "Error": "#F44336", "": "#9E9E9E"}
        start_angle, legend_y = 90, 50 # Start from top
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
        for status, count in sorted_data:
            if count == 0: continue
            angle = (count / total) * 360; end_angle = start_angle + angle
            color = colors.get(status, "#cccccc")
            canvas.create_arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius, start=start_angle, extent=angle, fill=color, outline="white", width=1)
            if angle > 10: # Label slightly larger slices
                mid_angle_rad = tk.radians(start_angle + angle / 2)
                text_radius = radius * 0.7
                text_x = center_x + text_radius * tk.cos(mid_angle_rad)
                text_y = center_y - text_radius * tk.sin(mid_angle_rad)
                percentage = (count / total) * 100
                canvas.create_text(text_x, text_y, text=f"{percentage:.0f}%", fill="white", font=("Arial", 9, "bold"))
            # Legend
            canvas.create_rectangle(width - 150, legend_y, width - 130, legend_y + 15, fill=color, outline="black")
            status_text = status if status else "Unknown"
            canvas.create_text(width - 125, legend_y + 7, text=f"{status_text} ({count})", fill="black", anchor=tk.W, font=("Arial", 9))
            legend_y += 25; start_angle = end_angle
        canvas.create_text(width / 2, 20, text="Files by Status", fill="black", font=("Arial", 12, "bold"))

    def _clear_results(self):
        """Clear all results data and UI."""
        if not self.results: return
        if messagebox.askyesno("Clear Results", "Are you sure you want to clear all results?"):
            self.results = []
            self.filtered_results = []
            self.results_tree_manager.clear_tree() # Use manager
            self._update_summary() # Update summary stats

    def _update_summary(self):
        """Update the summary labels and category breakdown."""
        total_files = len(self.results)
        files_moved = sum(1 for r in self.results if r.get('status') == "Moved")
        files_skipped = sum(1 for r in self.results if r.get('status') == "Skipped")
        errors = sum(1 for r in self.results if r.get('status') == "Error")
        rules = set(r.get('rule') for r in self.results if r.get('rule'))
        duplicates = sum(1 for r in self.results if "duplicate" in r.get('destination', '').lower())

        self.total_files_var.set(str(total_files))
        self.files_moved_var.set(str(files_moved))
        self.files_skipped_var.set(str(files_skipped))
        self.rules_applied_var.set(str(len(rules)))
        self.duplicates_var.set(str(duplicates))
        self.errors_var.set(str(errors))
        if self.results: self.last_run_var.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        else: self.last_run_var.set("Never")

        # Update category breakdown
        category_counts = {cat: 0 for cat in self.categories}
        for result in self.results: category_counts[self._get_result_category(result)] += 1
        for category, count in category_counts.items():
            if category in self.category_vars:
                percentage = (count / max(1, total_files)) * 100
                self.category_vars[category].set(percentage)
                self.category_labels[category].config(text=str(count))
        for category in self.category_vars: # Reset categories not present
            if category not in category_counts:
                self.category_vars[category].set(0)
                self.category_labels[category].config(text="0")

    # --- Public methods ---
    def add_result(self, source, destination, rule, status):
        """Add a single result to the internal list and update UI."""
        self.results.append({'source': source, 'destination': destination, 'rule': rule, 'status': status})
        self._apply_filters() # Re-filter and update tree
        self._update_summary()

    def set_results(self, results_list):
        """Set the results to a new list and update UI."""
        self.results = results_list if isinstance(results_list, list) else []
        self._apply_filters() # Filter and update tree
        self._update_summary()

    def clear(self):
        """Public method to clear results."""
        self._clear_results()

    def get_results(self):
        """Get the raw results list."""
        return self.results
