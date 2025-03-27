"""
About Dialog for the File Organization System.
"""

import tkinter as tk
from tkinter import ttk

class AboutDialog(tk.Toplevel):
    """Displays the 'About' information for the application."""

    def __init__(self, parent):
        """Initialize the About dialog."""
        super().__init__(parent)
        self.title("About File Organization System")
        self.geometry("400x300")
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
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="File Organization System", font=("", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Version (Consider fetching from __init__.py or setup.py later)
        try:
            from organize_gui import __version__
            version_text = f"Version {__version__}"
        except ImportError:
            version_text = "Version 1.0.0" # Fallback
        version_label = ttk.Label(main_frame, text=version_text)
        version_label.pack(pady=(0, 20))

        # Description
        desc_text = "A graphical user interface for the powerful organize-tool file organization system.\n\n" \
                    "This application helps you automate the organization of your files based on sophisticated rules."
        desc_label = ttk.Label(main_frame, text=desc_text, wraplength=350, justify=tk.CENTER)
        desc_label.pack(pady=(0, 20))

        # Credits
        credits_label = ttk.Label(main_frame, text="Based on organize-tool by Thomas Feldmann")
        credits_label.pack()

        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=self.destroy)
        close_button.pack(pady=20)
