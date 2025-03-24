"""
Configuration panel for the File Organization System.

This module defines the UI components for configuring sources, destinations,
and other settings for the file organization system.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.config_manager import ConfigManager

class ConfigPanel(ttk.Frame):
    """Panel for editing configuration settings."""
    
    def __init__(self, parent):
        """Initialize the configuration panel."""
        super().__init__(parent)
        
        # Initialize the config manager
        self.config_manager = ConfigManager()
        
        # Current configuration path
        self.current_config_path = None
        
        # Create the UI components
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI components for the configuration panel."""
        # Main layout container
        main_frame = ttk.Frame(self, padding=(10, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Source directory selection
        source_frame = ttk.LabelFrame(main_frame, text="Source Directory", padding=(10, 5))
        source_frame.pack(fill=tk.X, pady=5)
        
        self.source_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=50)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        source_button = ttk.Button(source_frame, text="Browse...", command=self._browse_source)
        source_button.pack(side=tk.RIGHT)
        
        # Destination base directory selection
        dest_frame = ttk.LabelFrame(main_frame, text="Destination Base Directory", padding=(10, 5))
        dest_frame.pack(fill=tk.X, pady=5)
        
        self.dest_var = tk.StringVar()
        dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_var, width=50)
        dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        dest_button = ttk.Button(dest_frame, text="Browse...", command=self._browse_dest)
        dest_button.pack(side=tk.RIGHT)
        
        # Configuration file selection
        config_frame = ttk.LabelFrame(main_frame, text="Configuration File", padding=(10, 5))
        config_frame.pack(fill=tk.X, pady=5)
        
        self.config_var = tk.StringVar()
        config_entry = ttk.Entry(config_frame, textvariable=self.config_var, width=50)
        config_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        config_button = ttk.Button(config_frame, text="Browse...", command=self._browse_config)
        config_button.pack(side=tk.RIGHT)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        load_button = ttk.Button(button_frame, text="Load Configuration", 
                                command=self._load_current_config)
        load_button.pack(side=tk.LEFT, padx=5)
        
        save_button = ttk.Button(button_frame, text="Save Configuration", 
                                command=self._save_current_config)
        save_button.pack(side=tk.LEFT, padx=5)
        
        update_button = ttk.Button(button_frame, text="Update Paths", 
                                  command=self._update_paths)
        update_button.pack(side=tk.LEFT, padx=5)
        
        # Directory structure preview
        preview_frame = ttk.LabelFrame(main_frame, text="Directory Structure Preview", padding=(10, 5))
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add a tree view to show the directory structure
        self.tree = ttk.Treeview(preview_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Add the basic structure nodes
        organized_node = self.tree.insert("", "end", text="Organized", open=True)
        self.tree.insert(organized_node, "end", text="Documents")
        self.tree.insert(organized_node, "end", text="Media")
        self.tree.insert(organized_node, "end", text="Development")
        self.tree.insert(organized_node, "end", text="Archives")
        self.tree.insert(organized_node, "end", text="Applications")
        self.tree.insert(organized_node, "end", text="Fonts")
        self.tree.insert(organized_node, "end", text="System/Config")
        self.tree.insert(organized_node, "end", text="Other")
        
        cleanup_node = self.tree.insert("", "end", text="Cleanup", open=True)
        self.tree.insert(cleanup_node, "end", text="Temporary")
        self.tree.insert(cleanup_node, "end", text="Logs")
        self.tree.insert(cleanup_node, "end", text="System")
        self.tree.insert(cleanup_node, "end", text="ErrorReports")
        self.tree.insert(cleanup_node, "end", text="Duplicates")
        self.tree.insert(cleanup_node, "end", text="URLFragments")
        self.tree.insert(cleanup_node, "end", text="Unknown")
    
    def _browse_source(self):
        """Browse for source directory."""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_var.set(directory)
    
    def _browse_dest(self):
        """Browse for destination directory."""
        directory = filedialog.askdirectory(title="Select Destination Base Directory")
        if directory:
            self.dest_var.set(directory)
    
    def _browse_config(self):
        """Browse for configuration file."""
        filetypes = [("YAML files", "*.yaml"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(
            title="Select Configuration File", 
            filetypes=filetypes
        )
        if filename:
            self.config_var.set(filename)
            self.current_config_path = filename
    
    def _load_current_config(self):
        """Load the current configuration file."""
        config_path = self.config_var.get()
        if not config_path:
            messagebox.showerror("Error", "No configuration file specified.")
            return
        
        try:
            self.load_configuration(config_path)
            messagebox.showinfo("Success", f"Configuration loaded from {config_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def _save_current_config(self):
        """Save the current configuration."""
        if self.save_configuration():
            messagebox.showinfo("Success", "Configuration saved successfully.")
    
    def _update_paths(self):
        """Update source and destination paths in the configuration."""
        source_dir = self.source_var.get()
        dest_dir = self.dest_var.get()
        
        if not source_dir or not dest_dir:
            messagebox.showerror("Error", "Source and destination directories must be specified.")
            return
        
        try:
            self.config_manager.update_paths(source_dir, dest_dir)
            messagebox.showinfo("Success", "Paths updated successfully.")
            
            # Update the tree view to reflect the new paths
            self._update_tree_view()
            
            # Generate an event to notify other components about the configuration change
            self.event_generate("<<ConfigurationChanged>>", when="tail")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update paths: {str(e)}")
    
    def _update_tree_view(self):
        """Update the tree view with the current configuration structure."""
        # In a real implementation, this would parse the configuration and
        # update the tree view to show the actual directory structure
        pass
    
    # Public methods
    
    def new_configuration(self):
        """Create a new empty configuration."""
        self.config_manager.create_new_config()
        self.current_config_path = None
        self.config_var.set("")
        self.source_var.set("")
        self.dest_var.set("")
        
        # Generate an event to notify other components about the configuration change
        self.event_generate("<<ConfigurationChanged>>", when="tail")
    
    def load_configuration(self, config_path):
        """Load a configuration from a file."""
        self.config_manager.load_config(config_path)
        self.current_config_path = config_path
        self.config_var.set(config_path)
        
        # Update source and destination paths from the loaded configuration
        source, dest = self.config_manager.get_current_paths()
        if source:
            self.source_var.set(source)
        if dest:
            self.dest_var.set(dest)
        
        # Update the tree view to reflect the loaded configuration
        self._update_tree_view()
        
        # Generate an event to notify other components about the configuration change
        self.event_generate("<<ConfigurationChanged>>", when="tail")
    
    def open_configuration_dialog(self):
        """Open a file dialog to select and load a configuration."""
        filetypes = [("YAML files", "*.yaml"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(
            title="Open Configuration File", 
            filetypes=filetypes
        )
        if filename:
            try:
                self.load_configuration(filename)
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
        return False
    
    def save_configuration(self):
        """Save the current configuration to its file."""
        if not self.current_config_path:
            return self.save_configuration_as()
        
        try:
            self.config_manager.save_config(self.current_config_path)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            return False
    
    def save_configuration_as(self):
        """Save the current configuration to a new file."""
        filetypes = [("YAML files", "*.yaml"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(
            title="Save Configuration As", 
            filetypes=filetypes,
            defaultextension=".yaml"
        )
        if filename:
            try:
                self.config_manager.save_config(filename)
                self.current_config_path = filename
                self.config_var.set(filename)
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
        return False
    
    def get_current_config(self):
        """Get the current configuration object."""
        return self.config_manager.config