#!/usr/bin/env python3
"""
File Organization System - Frontend Application

Main entry point for the file organization system GUI application.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

# Add project root to path to allow relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import application components
from ui.main_window import MainWindow

def main():
    """Main application entry point."""
    # Create the root Tk instance
    root = tk.Tk()
    root.title("File Organization System")
    
    # Set initial window size (width x height)
    root.geometry("900x600")
    
    # Create the main application window
    app = MainWindow(root)
    
    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()