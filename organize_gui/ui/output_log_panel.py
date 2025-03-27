"""
Panel containing a scrollable text area for displaying logs or output,
with support for colored tags and saving content.
"""

import tkinter as tk
from tkinter import ttk, font, filedialog, messagebox
import datetime

class OutputLogPanel(ttk.Frame):
    """A frame containing a scrollable text area for output logs."""

    def __init__(self, parent, **text_options):
        """
        Initialize the OutputLogPanel.

        Args:
            parent: The parent widget.
            **text_options: Additional options for the tk.Text widget (e.g., height).
        """
        super().__init__(parent)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_widgets(**text_options)
        self._configure_tags()

    def _create_widgets(self, **text_options):
        """Create the text area and scrollbars."""
        y_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        x_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        x_scrollbar.grid(row=1, column=0, sticky='ew')

        default_font = font.nametofont("TkTextFont")
        # Sensible defaults, allow override
        options = {
            'wrap': tk.NONE,
            'height': 15,
            'font': default_font,
            'state': tk.DISABLED, # Start disabled
            'undo': True
        }
        options.update(text_options) # Apply overrides

        self.output_text = tk.Text(
            self,
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
            **options
        )
        self.output_text.grid(row=0, column=0, sticky='nsew')

        y_scrollbar.config(command=self.output_text.yview)
        x_scrollbar.config(command=self.output_text.xview)

    def _configure_tags(self):
        """Configure tags for colored output."""
        # Using standard color names for better theme compatibility
        self.output_text.tag_config("info", foreground="black") # Default/Info
        self.output_text.tag_config("success", foreground="green")
        self.output_text.tag_config("warning", foreground="orange")
        self.output_text.tag_config("error", foreground="red")
        self.output_text.tag_config("move", foreground="blue")
        self.output_text.tag_config("echo", foreground="grey") # Dimmed/Echo

        # Bold font for headings
        try:
            # Attempt to copy the default font and make it bold
            bold_font = font.nametofont("TkDefaultFont").copy()
            bold_font.configure(weight="bold")
            self.output_text.tag_config("heading", font=bold_font)
        except tk.TclError:
            # Fallback if font copying fails
            print("Warning: Could not create bold font for headings.")
            self.output_text.tag_config("heading", font=("", 0, "bold")) # Generic bold


    def add_output(self, text, tag="info", add_timestamp=True):
        """Add text to the output area with the specified tag."""
        original_state = self.output_text.cget("state")
        try:
            self.output_text.config(state=tk.NORMAL)
            if add_timestamp:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                self.output_text.insert(tk.END, f"[{timestamp}] ", "info") # Timestamp always info tag

            # Add the message with the specified tag
            self.output_text.insert(tk.END, f"{text}\n", tag)
            self.output_text.see(tk.END) # Scroll to the bottom
        finally:
            self.output_text.config(state=original_state) # Restore original state

    def clear_output(self):
        """Clear the output text."""
        original_state = self.output_text.cget("state")
        try:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
        finally:
            self.output_text.config(state=original_state)

    def save_output(self):
        """Save the output text to a file."""
        filetypes = [("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(
            title="Save Output Log",
            filetypes=filetypes,
            defaultextension=".log"
        )
        if filename:
            try:
                output_content = self.output_text.get("1.0", tk.END)
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(output_content)
                messagebox.showinfo("Save Output", f"Output saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save output: {str(e)}")

    def get_text(self):
         """Return the current text content of the editor."""
         return self.output_text.get("1.0", tk.END)

    def set_text(self, text):
         """Set the text content of the editor (clears existing)."""
         original_state = self.output_text.cget("state")
         try:
             self.output_text.config(state=tk.NORMAL)
             self.output_text.delete("1.0", tk.END)
             if text:
                 self.output_text.insert("1.0", text)
                 # Optionally re-highlight if syntax highlighting is complex
         finally:
             self.output_text.config(state=original_state)
         self.output_text.edit_reset() # Reset undo stack
