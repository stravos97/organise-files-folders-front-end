"""
Schedule Dialog for the File Organization System.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

class ScheduleDialog(tk.Toplevel):
    """Dialog for setting up scheduled organization runs."""

    def __init__(self, parent, organize_runner, config_path=None):
        """
        Initialize the Schedule dialog.

        Args:
            parent: The parent window.
            organize_runner: An instance of OrganizeRunner to generate schedule commands.
            config_path (str, optional): The path to the current config file. Defaults to None.
        """
        super().__init__(parent)
        self.organize_runner = organize_runner
        self.config_path = config_path

        self.title("Schedule Organization")
        self.geometry("450x350") # Adjusted size slightly
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self._create_widgets()

        # Center the dialog
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Create the widgets for the dialog."""
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Schedule Type ---
        ttk.Label(main_frame, text="Schedule Type:", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))

        self.schedule_var = tk.StringVar(value="daily")
        schedule_frame = ttk.Frame(main_frame)
        schedule_frame.pack(anchor=tk.W, padx=10, pady=(0, 10))
        ttk.Radiobutton(schedule_frame, text="Daily", variable=self.schedule_var, value="daily").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(schedule_frame, text="Weekly", variable=self.schedule_var, value="weekly").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(schedule_frame, text="Monthly", variable=self.schedule_var, value="monthly").pack(side=tk.LEFT, padx=5)

        # --- Time ---
        ttk.Label(main_frame, text="Time:", font=("", 10, "bold")).pack(anchor=tk.W, pady=(5, 5))

        time_frame = ttk.Frame(main_frame)
        time_frame.pack(anchor=tk.W, padx=10, pady=(0, 15))

        self.hour_var = tk.StringVar(value="02")
        hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, width=3, textvariable=self.hour_var, format="%02.0f", wrap=True)
        hour_spin.pack(side=tk.LEFT)

        ttk.Label(time_frame, text=":", font=("", 12)).pack(side=tk.LEFT, padx=2)

        self.minute_var = tk.StringVar(value="00")
        minute_spin = ttk.Spinbox(time_frame, from_=0, to=59, width=3, textvariable=self.minute_var, format="%02.0f", wrap=True)
        minute_spin.pack(side=tk.LEFT)
        ttk.Label(time_frame, text="(HH:MM, 24-hour)").pack(side=tk.LEFT, padx=5)


        # --- Options ---
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)

        self.simulation_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Run in simulation mode (no changes)", variable=self.simulation_var).pack(anchor=tk.W)

        # --- Button Frame ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        button_frame.columnconfigure(0, weight=1) # Make buttons expand
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="Cancel", command=self.destroy, style="secondary.TButton").grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(button_frame, text="Generate Schedule Command", command=self._on_schedule).grid(row=0, column=1, padx=5, sticky="ew")

        # Add some style for secondary button if theme supports it
        style = ttk.Style()
        try:
            style.configure("secondary.TButton", foreground="grey")
        except tk.TclError:
            pass # Theme might not support custom styles

    def _on_schedule(self):
        """Handle the 'Schedule' button click."""
        try:
            schedule_type = self.schedule_var.get()
            time_str = f"{self.hour_var.get()}:{self.minute_var.get()}"
            simulation = self.simulation_var.get()

            # Use OrganizeRunner to get schedule info
            result = self.organize_runner.schedule(
                schedule_type=schedule_type,
                schedule_time=time_str,
                simulation=simulation,
                config_path=self.config_path
            )

            if result['success']:
                self._show_schedule_info(result['scheduler_info'])
                self.destroy() # Close the schedule dialog after showing info
            else:
                messagebox.showerror("Error", f"Failed to generate schedule: {result['message']}", parent=self)

        except ValueError:
             messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM format.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}", parent=self)

    def _show_schedule_info(self, scheduler_info):
        """Display the generated schedule command/info in a new window."""
        info_dialog = tk.Toplevel(self)
        info_dialog.title("Schedule Information")
        info_dialog.geometry("550x350") # Adjusted size
        info_dialog.transient(self)
        info_dialog.grab_set()

        main_frame = ttk.Frame(info_dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Add the following command/entry to your system scheduler:", wraplength=500).pack(anchor=tk.W, pady=(0, 10))

        text_area = tk.Text(main_frame, height=6, wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
        text_area.pack(fill=tk.X, pady=5)

        instructions_text = ""

        if os.name == 'nt':  # Windows
            info = scheduler_info.get('schtasks_cmd', 'N/A')
            text_area.insert("1.0", info)
            instructions_text = (
                "Instructions for Windows Task Scheduler:\n"
                "1. Open Command Prompt as Administrator.\n"
                "2. Paste and run the command above.\n"
                f"3. Verify the task '{scheduler_info.get('task_name', 'OrganizeTask')}' is created in Task Scheduler."
            )
        else:  # Unix-like (macOS, Linux)
            info = scheduler_info.get('cron_line', 'N/A')
            text_area.insert("1.0", info)
            instructions_text = (
                "Instructions for crontab:\n"
                "1. Open your terminal.\n"
                "2. Run the command: crontab -e\n"
                "3. Add the line shown above to the file.\n"
                "4. Save and close the editor."
            )

        text_area.config(state='disabled') # Make read-only

        ttk.Label(main_frame, text=instructions_text, justify=tk.LEFT, wraplength=500).pack(anchor=tk.W, pady=(10, 15))

        ttk.Button(main_frame, text="Close", command=info_dialog.destroy).pack(pady=5)

        # Center the info dialog relative to the schedule dialog
        info_dialog.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        dialog_width = info_dialog.winfo_width()
        dialog_height = info_dialog.winfo_height()
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        info_dialog.geometry(f"+{x}+{y}")
