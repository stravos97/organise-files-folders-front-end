"""
Dialog helpers for the Rule Editor panel.
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox


def show_selection_dialog(parent, title, message, options, default=None):
    """Show a dialog to select from options."""
    # Create dialog
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("400x300")
    dialog.transient(parent)
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


def ask_filter_details(parent, filter_type, initial_data=None):
    """Ask user for filter details based on type."""
    filter_item = None
    initial_value = initial_data.get(filter_type) if initial_data and isinstance(initial_data, dict) else None

    if filter_type == "extension":
        initial_str = ""
        if initial_value:
            initial_str = ", ".join(initial_value) if isinstance(initial_value, list) else str(initial_value)

        extensions = simpledialog.askstring(
            "Extension Filter",
            "Enter extensions (comma-separated):",
            initialvalue=initial_str,
            parent=parent
        )
        if extensions is not None: # Check for cancel
            extensions_list = [ext.strip() for ext in extensions.split(',') if ext.strip()]
            if extensions_list:
                filter_item = {filter_type: extensions_list}
            else: # Handle empty input case - maybe remove filter or keep as is? Ask user? For now, treat as cancel.
                filter_item = None # Or maybe keep initial_data?

    elif filter_type in ["name", "filename", "path"]:
        pattern = simpledialog.askstring(
            f"{filter_type.title()} Filter",
            f"Enter {filter_type} pattern:",
            initialvalue=initial_value if initial_value else "",
            parent=parent
        )
        if pattern is not None: # Check for cancel
             if pattern: # Only add if not empty
                 filter_item = {filter_type: pattern}
             else: # Treat empty as cancel for now
                 filter_item = None

    elif filter_type in ["created", "modified", "accessed"]:
        # Ask if user wants to filter by specific date or just use for date properties
        use_date = messagebox.askyesno(
            f"{filter_type.title()} Filter",
            f"Do you want to filter by a specific {filter_type} date?\n\n"
            f"Yes: Filter by specific date\n"
            f"No: Just use for date properties in actions",
            parent=parent
        )

        if use_date:
            date_format = simpledialog.askstring(
                f"{filter_type.title()} Filter",
                f"Enter {filter_type} date (YYYY-MM-DD or relative like '-7d'):",
                 initialvalue=initial_value if isinstance(initial_value, str) else "",
                parent=parent
            )
            if date_format is not None: # Check for cancel
                if date_format:
                    filter_item = {filter_type: date_format}
                else: # Treat empty as cancel
                    filter_item = None
        else:
            # User selected 'No', just use the filter type as a flag
            filter_item = {filter_type: True}


    elif filter_type == "filesize":
        size = simpledialog.askstring(
            "Filesize Filter",
            "Enter size value (e.g., 10MB, <5GB, >1KB):",
            initialvalue=initial_value if initial_value else "",
            parent=parent
        )
        if size is not None: # Check for cancel
            if size:
                filter_item = {filter_type: size}
            else: # Treat empty as cancel
                filter_item = None

    elif filter_type == "exif":
        # Simple flag filter, maybe allow editing specific EXIF tags later?
        # For now, just confirm if they want to add/keep it.
        if initial_data is None: # Adding new
             confirm = messagebox.askyesno("EXIF Filter", "Add EXIF filter?\n(This enables using EXIF data in actions)", parent=parent)
             if confirm:
                 filter_item = {filter_type: True}
        else: # Editing existing
             confirm = messagebox.askyesno("EXIF Filter", "Keep EXIF filter?\n(This enables using EXIF data in actions)", parent=parent)
             if confirm:
                 filter_item = {filter_type: True} # Keep it
             else:
                 filter_item = None # Remove it


    elif filter_type == "duplicate":
        current_detect_by = "created" # Default
        if isinstance(initial_value, dict) and "detect_original_by" in initial_value:
            current_detect_by = initial_value["detect_original_by"]
        elif initial_value is True and initial_data is not None: # Editing a simple 'duplicate: true'
             pass # Keep default
        elif initial_data is None: # Adding new
             pass # Keep default
        else: # Unexpected initial_value format
             current_detect_by = "created"


        detect_by = show_selection_dialog(
            parent,
            "Duplicate Filter",
            "How to detect the original file:",
            ["created", "modified", "first_seen", "filename"],
            current_detect_by
        )
        if detect_by:
            filter_item = {filter_type: {"detect_original_by": detect_by}}
        # If cancelled, keep original or None if adding new


    elif filter_type == "regex":
        initial_expr = ""
        if isinstance(initial_value, dict) and "expr" in initial_value:
            initial_expr = initial_value["expr"]
        elif isinstance(initial_value, str): # Handle old format?
             initial_expr = initial_value

        pattern = simpledialog.askstring(
            "Regex Filter",
            "Enter regex pattern:",
            initialvalue=initial_expr,
            parent=parent
        )
        if pattern is not None: # Check for cancel
            if pattern:
                filter_item = {filter_type: {"expr": pattern}}
            else: # Treat empty as cancel
                filter_item = None


    elif filter_type == "python":
        initial_code = ('# Use this Python filter to implement custom logic\n'
                        '# Available variables: path, filename, tags\n'
                        '# Return True to include the file, False to exclude\n\n'
                        'return "important" in filename.lower()')
        if initial_value:
            initial_code = initial_value

        # Open a text editor for Python code
        code_dialog = tk.Toplevel(parent)
        code_dialog.title("Python Filter")
        code_dialog.geometry("600x400")
        code_dialog.transient(parent)
        code_dialog.grab_set()

        code_frame = ttk.Frame(code_dialog, padding=10)
        code_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(code_frame, text="Enter Python code:").pack(anchor=tk.W)

        code_scroll = ttk.Scrollbar(code_frame)
        code_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        code_text = tk.Text(code_frame, yscrollcommand=code_scroll.set, width=70, height=20)
        code_text.pack(fill=tk.BOTH, expand=True)
        code_scroll.config(command=code_text.yview)

        code_text.insert(tk.END, initial_code)

        # Buttons
        button_frame = ttk.Frame(code_dialog)
        button_frame.pack(fill=tk.X, pady=10)

        saved_code = [None] # Use list to modify in nested function

        def on_cancel():
            code_dialog.destroy()

        def on_save():
            saved_code[0] = code_text.get("1.0", tk.END).strip()
            code_dialog.destroy()

        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.RIGHT, padx=5)

        parent.wait_window(code_dialog)

        if saved_code[0] is not None: # Check if saved
             if saved_code[0]: # Only add if not empty
                 filter_item = {filter_type: saved_code[0]}
             else: # Treat empty as cancel
                 filter_item = None

    # Add more filter types here as needed
    # ...

    # If filter_item is still None, it means either the type wasn't handled
    # or the user cancelled/entered empty value where not allowed.
    # If editing, we might want to return initial_data in case of cancel.
    # For now, returning None signifies cancellation or invalid input.
    if filter_item is None and initial_data is not None:
         # Optionally, ask user if they want to keep the original filter on cancel
         # keep_original = messagebox.askyesno("Keep Original?", "Keep the original filter settings?", parent=parent)
         # if keep_original:
         #     return initial_data
         return None # Treat cancel as removal intent for now when editing

    return filter_item


def ask_action_details(parent, action_type, initial_data=None):
    """Ask user for action details based on type."""
    action_item = None
    initial_value = initial_data.get(action_type) if initial_data and isinstance(initial_data, dict) else None

    if action_type in ["move", "copy"]:
        initial_dest = ""
        initial_conflict = "rename_new"
        if isinstance(initial_value, dict):
            initial_dest = initial_value.get("dest", "")
            initial_conflict = initial_value.get("on_conflict", "rename_new")
        elif isinstance(initial_value, str): # Old format
            initial_dest = initial_value

        dest = simpledialog.askstring(
            f"{action_type.title()} Action",
            "Enter destination path:",
            initialvalue=initial_dest,
            parent=parent
        )

        if dest is not None: # Check for cancel
            if dest:
                conflict_types = ["rename_new", "skip", "overwrite"]
                conflict = show_selection_dialog(
                    parent,
                    "Conflict Resolution",
                    "Select how to handle conflicts:",
                    conflict_types,
                    initial_conflict
                )

                if conflict: # If conflict selection is not cancelled
                    action_item = {action_type: {"dest": dest, "on_conflict": conflict}}
                # else: Treat conflict cancel as overall cancel? Or default? Defaulting for now.
                #     action_item = {action_type: {"dest": dest, "on_conflict": "rename_new"}}
            else: # Treat empty dest as cancel
                action_item = None


    elif action_type == "rename":
        pattern = simpledialog.askstring(
            "Rename Action",
            "Enter rename pattern (e.g., '{name}_{created.year}.{extension}'):",
            initialvalue=initial_value if initial_value else "",
            parent=parent
        )
        if pattern is not None: # Check for cancel
            if pattern:
                action_item = {action_type: pattern}
            else: # Treat empty as cancel
                action_item = None

    elif action_type in ["delete", "trash"]:
        # Simple flag action, confirm add/keep
        if initial_data is None: # Adding new
             confirm = messagebox.askyesno(f"{action_type.title()} Action", f"Add '{action_type}' action?", parent=parent)
             if confirm:
                 action_item = {action_type: True}
        else: # Editing existing
             confirm = messagebox.askyesno(f"{action_type.title()} Action", f"Keep '{action_type}' action?", parent=parent)
             if confirm:
                 action_item = {action_type: True} # Keep it
             else:
                 action_item = None # Remove it


    elif action_type in ["echo", "confirm"]:
        message = simpledialog.askstring(
            f"{action_type.title()} Action",
            "Enter message:",
            initialvalue=initial_value if initial_value else "",
            parent=parent
        )
        if message is not None: # Check for cancel
            if message:
                action_item = {action_type: message}
            else: # Treat empty as cancel
                action_item = None

    elif action_type == "shell":
        command = simpledialog.askstring(
            "Shell Action",
            "Enter shell command:",
            initialvalue=initial_value if initial_value else "",
            parent=parent
        )
        if command is not None: # Check for cancel
            if command:
                action_item = {action_type: command}
            else: # Treat empty as cancel
                action_item = None

    elif action_type == "python":
        initial_code = ('# Use this Python action to implement custom logic\n'
                        '# Available variables: path, filename, tags\n'
                        '# Return a dictionary to store information\n\n'
                        'print(f"Processing file: {path}")\n'
                        'return {"processed": True}')
        if initial_value:
            initial_code = initial_value

        # Open a text editor for Python code
        code_dialog = tk.Toplevel(parent)
        code_dialog.title("Python Action")
        code_dialog.geometry("600x400")
        code_dialog.transient(parent)
        code_dialog.grab_set()

        code_frame = ttk.Frame(code_dialog, padding=10)
        code_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(code_frame, text="Enter Python code:").pack(anchor=tk.W)

        code_scroll = ttk.Scrollbar(code_frame)
        code_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        code_text = tk.Text(code_frame, yscrollcommand=code_scroll.set, width=70, height=20)
        code_text.pack(fill=tk.BOTH, expand=True)
        code_scroll.config(command=code_text.yview)

        code_text.insert(tk.END, initial_code)

        # Buttons
        button_frame = ttk.Frame(code_dialog)
        button_frame.pack(fill=tk.X, pady=10)

        saved_code = [None] # Use list to modify in nested function

        def on_cancel():
            code_dialog.destroy()

        def on_save():
            saved_code[0] = code_text.get("1.0", tk.END).strip()
            code_dialog.destroy()

        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.RIGHT, padx=5)

        parent.wait_window(code_dialog)

        if saved_code[0] is not None: # Check if saved
            if saved_code[0]: # Only add if not empty
                action_item = {action_type: saved_code[0]}
            else: # Treat empty as cancel
                action_item = None

    # Add more action types here as needed
    # ...

    # Handle cancellation/invalid input similar to ask_filter_details
    if action_item is None and initial_data is not None:
        # Optionally ask user if they want to keep the original action on cancel
        # keep_original = messagebox.askyesno("Keep Original?", "Keep the original action settings?", parent=parent)
        # if keep_original:
        #     return initial_data
        return None # Treat cancel as removal intent for now when editing

    return action_item
