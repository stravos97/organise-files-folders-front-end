"""
Input Validation Functions for the File Organization System.

This module provides utility functions for validating user input
in the file organization system.
"""

import os
import re
import yaml

def is_valid_path(path):
    """
    Check if a path is syntactically valid.
    
    Args:
        path (str): Path to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Basic checks for invalid characters
    if not path or path.isspace():
        return False
    
    # Check for invalid characters based on platform
    if os.name == 'nt':  # Windows
        # Check for reserved characters and names
        invalid_chars = r'[<>:"|?*\0-\31]'
        reserved_names = r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)'
        
        if re.search(invalid_chars, path):
            return False
        
        # Check path components for reserved names
        for part in path.split('\\'):
            if re.match(reserved_names, part, re.IGNORECASE):
                return False
    else:  # Unix/Linux/macOS
        # Only null byte is invalid
        if '\0' in path:
            return False
    
    return True

def is_valid_yaml(content):
    """
    Check if a string is valid YAML.
    
    Args:
        content (str): YAML content to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Ensure input is a string
    if not isinstance(content, str):
        return False
        
    # Treat empty or whitespace-only strings as potentially valid
    # by yaml.safe_load (parses as None), but maybe semantically invalid
    # depending on use case. For basic validation, let safe_load decide.
    # If empty/whitespace should be strictly invalid, add:
    # if not content or content.isspace():
    #     return False

    try:
        yaml.safe_load(content)
        return True
    except yaml.YAMLError:
        return False
    
def is_valid_rule_name(name):
    """
    Check if a rule name is valid.
    
    Args:
        name (str): Rule name to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Rule names should not be empty
    if not name or name.isspace():
        return False
    
    # Rule names should not be too long
    if len(name) > 100:
        return False
    
    # Rule names should not contain special characters that might
    # cause issues in file names or yaml serialization
    invalid_chars = r'[<>:"|?*\0-\31\\/#]'
    if re.search(invalid_chars, name):
        return False
    
    return True

def is_valid_extension_list(extensions):
    """
    Validate a list of file extensions.
    
    Args:
        extensions (list): List of extensions to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(extensions, list):
        return False
    
    # Extensions should be strings
    for ext in extensions:
        if not isinstance(ext, str):
            return False
        
        # Extensions should not contain spaces or special characters
        if not ext or ext.isspace() or re.search(r'[<>:"|?*\0-\31\\/#\s]', ext):
            return False
        
        # Extensions should not start with a dot
        if ext.startswith('.'):
            return False
    
    return True

def is_valid_filter(filter_obj):
    """
    Validate a filter specification.
    
    Args:
        filter_obj (dict): Filter specification to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Basic filter types and their expected value types
    filter_types = {
        'extension': (list, str),
        'name': (str,),
        'regex': (dict,),
        'size': (dict,),
        'created': (str, dict),
        'lastmodified': (str, dict),
        'exif': (bool,),
        'duplicate': (dict, bool),
        'python': (str,)
    }
    
    if not isinstance(filter_obj, dict) or len(filter_obj) != 1:
        return False
    
    filter_type = list(filter_obj.keys())[0]
    filter_value = filter_obj[filter_type]
    
    # Check if filter type is known
    if filter_type not in filter_types:
        return False
    
    # Check if filter value has the expected type
    expected_types = filter_types[filter_type]
    if not any(isinstance(filter_value, t) for t in expected_types):
        return False
    
    # Specific validation for common filter types
    if filter_type == 'extension' and isinstance(filter_value, list):
        return is_valid_extension_list(filter_value)
    
    return True

def is_valid_action(action_obj):
    """
    Validate an action specification.
    
    Args:
        action_obj (dict): Action specification to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Basic action types and their expected value types
    action_types = {
        'move': (dict, str),
        'copy': (dict, str),
        'rename': (str,),
        'delete': (bool,),
        'trash': (bool,),
        'echo': (str,),
        'shell': (str,),
        'python': (str,),
        'confirm': (str,)
    }
    
    if not isinstance(action_obj, dict) or len(action_obj) != 1:
        return False
    
    action_type = list(action_obj.keys())[0]
    action_value = action_obj[action_type]
    
    # Check if action type is known
    if action_type not in action_types:
        return False
    
    # Check if action value has the expected type
    expected_types = action_types[action_type]
    if not any(isinstance(action_value, t) for t in expected_types):
        return False

    # Specific validation for move and copy actions (path validation)
    if action_type in ('move', 'copy'):
        dest_path = None
        if isinstance(action_value, dict):
            if 'dest' not in action_value:
                return False # Missing 'dest' key
            dest_path = action_value['dest']
        elif isinstance(action_value, str):
            dest_path = action_value

        # Validate the extracted destination path
        if not isinstance(dest_path, str) or not is_valid_path(dest_path):
            return False

    return True
