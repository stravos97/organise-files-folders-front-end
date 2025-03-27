#!/usr/bin/env python3
"""
File Organization System - Frontend Application

Main entry point for the file organization system GUI application.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, font

# Add project root to path to allow relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import application components
from ui.main_window import MainWindow

def main():
    """Main application entry point."""
    # Create the root Tk instance
    root = tk.Tk()
    root.title("File Organization System")

    # Set theme
    style = ttk.Style(root)
    try:
        # Try 'clam' theme first, fallback to others if not available
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        elif 'default' in available_themes:
            style.theme_use('default')
        # Add more fallbacks if needed
    except tk.TclError:
        print("Warning: Could not set a preferred ttk theme.")

    # Set initial window size (width x height)
    root.geometry("1000x700") # Increased default size slightly
    
    # Create the main application window
    app = MainWindow(root)
    
    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
