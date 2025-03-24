"""
Path Helper Functions for the File Organization System.

This module provides utility functions for working with file paths
and directories in a cross-platform way.
"""

import os
import platform
import subprocess
import re

def expand_path(path):
    """
    Expand a path string to an absolute path, handling ~ and environment variables.
    
    Args:
        path (str): Path to expand
    
    Returns:
        str: Expanded absolute path
    """
    # Expand ~ to user home directory
    expanded = os.path.expanduser(path)
    
    # Expand environment variables
    expanded = os.path.expandvars(expanded)
    
    # Normalize path separators
    expanded = os.path.normpath(expanded)
    
    # Get absolute path
    expanded = os.path.abspath(expanded)
    
    return expanded

def format_path_for_display(path, max_length=60):
    """
    Format a path for display, shortening if necessary.
    
    Args:
        path (str): Path to format
        max_length (int): Maximum length before shortening
    
    Returns:
        str: Formatted path
    """
    # Short enough, return as is
    if len(path) <= max_length:
        return path
    
    # Split into parts
    parts = path.split(os.sep)
    
    # If just a filename, truncate the middle
    if len(parts) <= 2:
        half = (max_length - 3) // 2
        return f"{path[:half]}...{path[-half:]}"
    
    # Get drive/root
    drive = parts[0] + os.sep if parts[0].endswith(':') else parts[0]
    
    # Get filename
    filename = parts[-1]
    
    # Calculate how many middle paths we can include
    middle_parts = parts[1:-1]
    remaining_length = max_length - len(drive) - len(filename) - 5  # 5 for '.../' and '/'
    
    if remaining_length <= 0:
        # Not enough space, just show root and filename
        return f"{drive}...{os.sep}{filename}"
    
    # Try to include some path components from the start and end
    start_count = min(len(middle_parts), 1)
    end_count = min(len(middle_parts) - start_count, 1)
    
    start_parts = middle_parts[:start_count]
    end_parts = middle_parts[-end_count:] if end_count > 0 else []
    
    formatted = drive + os.sep + os.sep.join(start_parts)
    if len(middle_parts) > (start_count + end_count):
        formatted += os.sep + '...'
    if end_parts:
        formatted += os.sep + os.sep.join(end_parts)
    formatted += os.sep + filename
    
    return formatted

def is_path_writable(path):
    """
    Check if a path is writable.
    
    Args:
        path (str): Path to check
    
    Returns:
        bool: True if writable, False otherwise
    """
    # If path doesn't exist, check if parent directory is writable
    if not os.path.exists(path):
        parent = os.path.dirname(path)
        if not parent:  # Empty string means current directory
            parent = '.'
        return os.access(parent, os.W_OK)
    
    # Path exists, check if it's writable
    return os.access(path, os.W_OK)

def get_directory_size(path):
    """
    Get the total size of a directory in bytes.
    
    Args:
        path (str): Directory path
    
    Returns:
        int: Size in bytes
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            # Skip symbolic links
            if not os.path.islink(file_path):
                total_size += os.path.getsize(file_path)
    
    return total_size

def format_size(size_bytes):
    """
    Format a size in bytes to a human-readable string.
    
    Args:
        size_bytes (int): Size in bytes
    
    Returns:
        str: Formatted size string
    """
    # Define units and their thresholds
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    
    # Handle zero size
    if size_bytes == 0:
        return "0 B"
    
    # Calculate appropriate unit
    unit_index = min(len(units) - 1, int(len(str(size_bytes)) / 3))
    unit = units[unit_index]
    
    # Convert to appropriate unit
    size_value = size_bytes / (1024 ** unit_index)
    
    # Format with appropriate precision
    if unit_index == 0:  # Bytes
        return f"{size_value:.0f} {unit}"
    elif size_value >= 100:  # Large values
        return f"{size_value:.1f} {unit}"
    else:  # Small values
        return f"{size_value:.2f} {unit}"

def open_directory(path):
    """
    Open a directory in the system file explorer/finder.
    
    Args:
        path (str): Directory path
    
    Returns:
        bool: True if opened successfully, False otherwise
    """
    try:
        path = os.path.abspath(path)
        
        # Make sure path exists
        if not os.path.exists(path):
            return False
        
        # Open directory based on platform
        if platform.system() == "Windows":
            # Windows
            os.startfile(path)
        elif platform.system() == "Darwin":
            # macOS
            subprocess.run(['open', path])
        else:
            # Linux
            subprocess.run(['xdg-open', path])
        
        return True
    except Exception:
        return False

def ensure_directory_exists(path):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path (str): Directory path
    
    Returns:
        bool: True if directory exists or was created, False otherwise
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return True
    except Exception:
        return False

def split_path_at_marker(path, marker):
    """
    Split a path at a marker directory.
    
    Args:
        path (str): Path to split
        marker (str): Marker directory name
    
    Returns:
        tuple: (base_path, relative_path) or (path, None) if marker not found
    """
    # Normalize path
    norm_path = os.path.normpath(path)
    
    # Regular expression to find the marker
    pattern = re.compile(f'(.*?{re.escape(os.sep)}{re.escape(marker)})(.*)')
    match = pattern.match(norm_path)
    
    if match:
        base_path = match.group(1)
        rel_path = match.group(2)
        
        # Remove leading separator from relative path
        if rel_path.startswith(os.sep):
            rel_path = rel_path[len(os.sep):]
        
        return (base_path, rel_path)
    
    return (path, None)