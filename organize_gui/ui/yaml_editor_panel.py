"""
Panel containing a text editor for viewing and editing YAML configuration,
with basic syntax highlighting and apply/revert functionality.
"""

import tkinter as tk
from tkinter import ttk, font, messagebox
import yaml
import re

class YamlEditorPanel(ttk.Frame):
    """A frame containing a YAML text editor with apply/revert buttons."""

    def __init__(self, parent, apply_callback=None, revert_callback=None):
        """
        Initialize the YamlEditorPanel.

        Args:
            parent: The parent widget.
            apply_callback: Function to call when 'Apply Changes' is clicked.
                            It should expect the current editor text as an argument.
            revert_callback: Function to call when 'Revert Changes' is clicked.
                             It should return the text to revert to.
        """
        super().__init__(parent, padding=(10, 5))
        self._apply_callback = apply_callback
        self._revert_callback = revert_callback

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_widgets()

    def _create_widgets(self):
        """Create the text editor and control buttons."""
        # Add a text editor for direct YAML editing
        yaml_editor_frame = ttk.Frame(self)
        yaml_editor_frame.grid(row=0, column=0, sticky='nsew')
        yaml_editor_frame.grid_rowconfigure(0, weight=1)
        yaml_editor_frame.grid_columnconfigure(0, weight=1)

        yaml_scroll_y = ttk.Scrollbar(yaml_editor_frame, orient=tk.VERTICAL)
        yaml_scroll_y.grid(row=0, column=1, sticky='ns')

        yaml_scroll_x = ttk.Scrollbar(yaml_editor_frame, orient=tk.HORIZONTAL)
        yaml_scroll_x.grid(row=1, column=0, sticky='ew')

        # Use default font from theme
        default_font = font.nametofont("TkTextFont")
        self.yaml_editor = tk.Text(
            yaml_editor_frame,
            wrap=tk.NONE,
            yscrollcommand=yaml_scroll_y.set,
            xscrollcommand=yaml_scroll_x.set,
            height=15, # Initial height, parent grid weight handles expansion
            font=default_font,
            undo=True # Enable undo/redo
        )
        self.yaml_editor.grid(row=0, column=0, sticky='nsew')

        yaml_scroll_y.config(command=self.yaml_editor.yview)
        yaml_scroll_x.config(command=self.yaml_editor.xview)

        # Configure syntax highlighting tags (adjust colors if needed for theme)
        self.yaml_editor.tag_configure("key", foreground="navy")
        self.yaml_editor.tag_configure("value", foreground="forest green")
        self.yaml_editor.tag_configure("comment", foreground="grey")
        self.yaml_editor.tag_configure("string", foreground="purple")
        self.yaml_editor.tag_configure("error", background="red", foreground="white")

        # Bind key release to re-highlight (can be optimized later)
        self.yaml_editor.bind("<KeyRelease>", self._on_key_release, add=True)

        # Editor buttons
        editor_buttons = ttk.Frame(self)
        editor_buttons.grid(row=1, column=0, sticky='ew', pady=(5,0))

        apply_button = ttk.Button(editor_buttons, text="Apply Changes", command=self._handle_apply)
        apply_button.pack(side=tk.LEFT, padx=(0, 5))

        revert_button = ttk.Button(editor_buttons, text="Revert Changes", command=self._handle_revert)
        revert_button.pack(side=tk.LEFT, padx=5)

    def get_text(self):
        """Return the current text content of the editor."""
        return self.yaml_editor.get("1.0", tk.END)

    def set_text(self, text):
        """Set the text content of the editor and apply highlighting."""
        # Store current scroll position
        # yview_pos = self.yaml_editor.yview()

        self.yaml_editor.delete("1.0", tk.END)
        if text:
            self.yaml_editor.insert("1.0", text)
            self._highlight_syntax()

        # Restore scroll position (optional, might be jarring)
        # self.yaml_editor.yview_moveto(yview_pos[0])

        # Reset undo stack after setting text externally
        self.yaml_editor.edit_reset()


    def _on_key_release(self, event=None):
        """Handle key release events for potential re-highlighting."""
        # Basic re-highlighting on any key release.
        # Can be optimized to only highlight the modified line or visible area.
        self._highlight_syntax()

    def _highlight_syntax(self):
        """Apply basic syntax highlighting to the YAML editor."""
        self.yaml_editor.mark_set("range_start", "1.0")
        data = self.get_text() # Use get_text method

        # Clear existing tags first
        tags_to_remove = ["key", "value", "comment", "string", "error"]
        for tag in tags_to_remove:
            self.yaml_editor.tag_remove(tag, "1.0", tk.END)

        # Basic YAML highlighting patterns
        key_pattern = r"^\s*([a-zA-Z0-9_.-]+)\s*:" # Allow dots and dashes in keys
        comment_pattern = r"(#.*)" # Capture comment including #
        string_pattern = r"(\".*?\"|\'.*?\')" # Basic strings
        # Simple value pattern (everything after ': ') - less precise
        # value_pattern = r":\s+(.*)"

        for i, line in enumerate(data.splitlines()):
            line_num = i + 1

            # Comments (highlight whole line after #)
            comment_match = re.search(comment_pattern, line)
            if comment_match:
                start, _ = comment_match.span(1)
                self.yaml_editor.tag_add("comment", f"{line_num}.{start}", f"{line_num}.end")
                # Don't necessarily skip other patterns if comment is mid-line

            # Keys
            key_match = re.search(key_pattern, line)
            if key_match:
                start, end = key_match.span(1)
                # Avoid highlighting if it's part of a comment
                is_commented = False
                if comment_match and start >= comment_match.start(1):
                    is_commented = True

                if not is_commented:
                    self.yaml_editor.tag_add("key", f"{line_num}.{start}", f"{line_num}.{end}")

                    # Highlight strings within the line (value part or key if quoted)
                    for str_match in re.finditer(string_pattern, line):
                         s_start, s_end = str_match.span(1)
                         # Avoid highlighting if it's part of a comment
                         is_str_commented = False
                         if comment_match and s_start >= comment_match.start(1):
                             is_str_commented = True
                         if not is_str_commented:
                             self.yaml_editor.tag_add("string", f"{line_num}.{s_start}", f"{line_num}.{s_end}")

            # Highlight strings even if not on a key line (e.g., list items)
            elif not comment_match: # Avoid highlighting strings within comments
                 for str_match in re.finditer(string_pattern, line):
                     s_start, s_end = str_match.span(1)
                     self.yaml_editor.tag_add("string", f"{line_num}.{s_start}", f"{line_num}.{s_end}")


    def _handle_apply(self):
        """Handle the Apply Changes button click."""
        current_text = self.get_text()
        try:
            # Validate YAML before calling callback
            parsed_config = yaml.safe_load(current_text)
            if not isinstance(parsed_config, dict):
                 # Allow empty or list-based configs if needed, adjust validation
                 if parsed_config is not None:
                      raise yaml.YAMLError("Root element must be a dictionary (mapping).")

            # YAML is valid (or empty), proceed with callback
            if self._apply_callback:
                self._apply_callback(current_text) # Pass the raw text
            else:
                messagebox.showinfo("Apply", "Apply action triggered (no callback registered).")

        except yaml.YAMLError as e:
            messagebox.showerror("YAML Error", f"Invalid YAML syntax:\n{e}")
            # Optionally highlight the error location if possible
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during apply: {e}")


    def _handle_revert(self):
        """Handle the Revert Changes button click."""
        if self._revert_callback:
            revert_text = self._revert_callback()
            if revert_text is not None:
                self.set_text(revert_text)
                messagebox.showinfo("Revert", "Changes reverted.")
            else:
                 messagebox.showwarning("Revert", "Could not get text to revert to.")
        else:
            messagebox.showinfo("Revert", "Revert action triggered (no callback registered).")
