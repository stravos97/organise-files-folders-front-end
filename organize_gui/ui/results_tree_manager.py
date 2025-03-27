"""
Manages the Treeview component for displaying organization results,
including sorting, context menu, and file details dialog.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, font
import datetime

class ResultsTreeManager:
    """Manages the results Treeview and related interactions."""

    def __init__(self, parent_frame):
        """
        Initialize the ResultsTreeManager.

        Args:
            parent_frame: The ttk.Frame to build the Treeview UI within.
        """
        self.parent_frame = parent_frame
        self._create_widgets()

    def _create_widgets(self):
        """Create the Treeview and associated widgets."""
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)

        vscrollbar = ttk.Scrollbar(self.parent_frame, orient=tk.VERTICAL)
        vscrollbar.grid(row=0, column=1, sticky='ns')
        hscrollbar = ttk.Scrollbar(self.parent_frame, orient=tk.HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky='ew')

        self.tree = ttk.Treeview(
            self.parent_frame,
            columns=("source", "destination", "rule", "status"),
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set,
            selectmode="browse"
        )
        self.tree.grid(row=0, column=0, sticky='nsew')
        vscrollbar.config(command=self.tree.yview)
        hscrollbar.config(command=self.tree.xview)

        # Configure columns
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

        # Tag configurations
        style = ttk.Style()
        style.map("Treeview", foreground=self._fixed_map("foreground"))
        self.tree.tag_configure("moved", foreground="green")
        self.tree.tag_configure("skipped", foreground="orange")
        self.tree.tag_configure("error", foreground="red")
        self.tree.tag_configure("unknown", foreground="grey") # For items without status

        # Context menu
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Copy Source Path", command=self._copy_source_path)
        self.context_menu.add_command(label="Copy Destination Path", command=self._copy_destination_path)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open Source Location", command=self._open_source_location)
        self.context_menu.add_command(label="Open Destination Location", command=self._open_destination_location)

        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Button-2>", self._show_context_menu)
        self.tree.bind("<Double-1>", self._show_file_details)

    def _fixed_map(self, option):
        """Helper to fix ttk style mapping issue on theme change."""
        style = ttk.Style()
        return [elm for elm in style.map("Treeview", query_opt=option) if elm[:2] != ("!disabled", "!selected")]

    def clear_tree(self):
        """Remove all items from the tree."""
        self.tree.delete(*self.tree.get_children())

    def populate_tree(self, filtered_results):
        """Populate the tree with a list of result dictionaries."""
        self.clear_tree()
        for i, result in enumerate(filtered_results):
            status_text = result.get('status', '')
            tag = status_text.lower() if status_text else 'unknown'
            self.tree.insert(
                "", "end", text=str(i + 1),
                values=(
                    result.get('source', ''),
                    result.get('destination', ''),
                    result.get('rule', ''),
                    status_text
                ),
                tags=(tag,)
            )

    def _sort_column(self, column, reverse):
        """Sort tree contents when a column header is clicked."""
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        items.sort(reverse=reverse)
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
            self.tree.item(item, text=str(index + 1)) # Renumber
        self.tree.heading(column, command=lambda: self._sort_column(column, not reverse))

    def _show_context_menu(self, event):
        """Show the context menu on right click."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _get_selected_values(self):
        """Get the values tuple of the selected tree item."""
        selected_item = self.tree.selection()
        if not selected_item: return None
        return self.tree.item(selected_item[0], 'values')

    def _copy_source_path(self):
        values = self._get_selected_values()
        if values and len(values) > 0: self._copy_to_clipboard(values[0])

    def _copy_destination_path(self):
        values = self._get_selected_values()
        if values and len(values) > 1 and values[1]: self._copy_to_clipboard(values[1])

    def _open_source_location(self):
        values = self._get_selected_values()
        if values and len(values) > 0: self._open_file_location(values[0])

    def _open_destination_location(self):
        values = self._get_selected_values()
        if values and len(values) > 1 and values[1]: self._open_file_location(values[1])

    def _copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        try:
            # Use the widget's clipboard methods
            self.tree.clipboard_clear()
            self.tree.clipboard_append(text)
        except tk.TclError:
             messagebox.showwarning("Copy Failed", "Could not access clipboard.")

    def _open_file_location(self, path):
        """Open a file location in the system file explorer."""
        try:
            dir_path = os.path.dirname(path) if os.path.isfile(path) else path
            if not os.path.exists(dir_path):
                messagebox.showwarning("Open Location", "Path does not exist.")
                return
            if os.name == 'nt': os.startfile(dir_path)
            elif os.name == 'posix': os.system(f'open "{dir_path}"' if os.path.exists('/usr/bin/open') else f'xdg-open "{dir_path}"')
        except Exception as e: messagebox.showerror("Error", f"Failed to open location: {str(e)}")

    def _show_file_details(self, event):
        """Show detailed information about a file on double click."""
        item = self.tree.identify_row(event.y)
        if not item: return
        values = self.tree.item(item, 'values')
        if not values: return

        source, destination, rule, status = (values[0], values[1] if len(values) > 1 else "",
                                             values[2] if len(values) > 2 else "",
                                             values[3] if len(values) > 3 else "")

        details_dialog = tk.Toplevel(self.tree) # Parent is tree
        details_dialog.title("File Details")
        details_dialog.geometry("600x350")
        details_dialog.transient(self.tree)
        details_dialog.grab_set()

        main_frame = ttk.Frame(details_dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File name and status
        status_frame = ttk.Frame(main_frame); status_frame.pack(fill=tk.X, pady=5)
        file_name = os.path.basename(source)
        ttk.Label(status_frame, text=f"File: {file_name}", font=("", 12, "bold")).pack(side=tk.LEFT)
        status_label = ttk.Label(status_frame, text=f"Status: {status}")
        status_label.pack(side=tk.RIGHT)
        color = {"moved": "green", "skipped": "orange", "error": "red"}.get(status.lower(), "grey")
        status_label.config(foreground=color)

        # Paths
        path_frame = ttk.LabelFrame(main_frame, text="Paths", padding=5); path_frame.pack(fill=tk.X, pady=5)
        for label_text, path_val in [("Source:", source), ("Destination:", destination)]:
            if not path_val: continue
            row_frame = ttk.Frame(path_frame); row_frame.pack(fill=tk.X, pady=2)
            ttk.Label(row_frame, text=label_text, width=12).pack(side=tk.LEFT)
            path_var = tk.StringVar(value=path_val)
            entry = ttk.Entry(row_frame, textvariable=path_var, state='readonly'); entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            ttk.Button(row_frame, text="Copy", width=8, command=lambda p=path_val: self._copy_to_clipboard(p)).pack(side=tk.LEFT)

        # Rule
        if rule: ttk.Label(main_frame, text=f"Applied Rule: {rule}", font=("", 10, "italic")).pack(anchor=tk.W, pady=5)

        # File Info
        info_frame = ttk.LabelFrame(main_frame, text="File Information", padding=5); info_frame.pack(fill=tk.X, pady=5)
        try:
            file_to_stat = destination if status.lower() == "moved" and os.path.exists(destination) else source
            if os.path.exists(file_to_stat):
                stat = os.stat(file_to_stat)
                size_str = self._format_size(stat.st_size)
                created = datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                accessed = datetime.datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S")
                _, ext = os.path.splitext(file_to_stat)
                info_grid = ttk.Frame(info_frame); info_grid.pack(fill=tk.X)
                ttk.Label(info_grid, text="Size:").grid(row=0, column=0, sticky=tk.W, padx=5); ttk.Label(info_grid, text=size_str).grid(row=0, column=1, sticky=tk.W, padx=5)
                if ext: ttk.Label(info_grid, text="Type:").grid(row=0, column=2, sticky=tk.W, padx=5); ttk.Label(info_grid, text=ext[1:].upper()).grid(row=0, column=3, sticky=tk.W, padx=5)
                ttk.Label(info_grid, text="Created:").grid(row=1, column=0, sticky=tk.W, padx=5); ttk.Label(info_grid, text=created).grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5)
                ttk.Label(info_grid, text="Modified:").grid(row=2, column=0, sticky=tk.W, padx=5); ttk.Label(info_grid, text=modified).grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5)
                ttk.Label(info_grid, text="Accessed:").grid(row=3, column=0, sticky=tk.W, padx=5); ttk.Label(info_grid, text=accessed).grid(row=3, column=1, columnspan=3, sticky=tk.W, padx=5)
            else: ttk.Label(info_frame, text="File not found at source or destination.").pack(padx=5, pady=5)
        except Exception as e: ttk.Label(info_frame, text=f"Error retrieving file info: {e}").pack(padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(main_frame); button_frame.pack(fill=tk.X, pady=10)
        if os.path.exists(source): ttk.Button(button_frame, text="Open Source Location", command=lambda: self._open_file_location(source)).pack(side=tk.LEFT, padx=5)
        if destination and os.path.exists(destination): ttk.Button(button_frame, text="Open Dest Location", command=lambda: self._open_file_location(destination)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=details_dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _format_size(self, size_bytes):
        """Format size in bytes to human-readable string."""
        if size_bytes == 0: return "0 B"
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1: size_bytes /= 1024; i += 1
        return f"{size_bytes:.0f} {units[i]}" if i == 0 else f"{size_bytes:.2f} {units[i]}"
