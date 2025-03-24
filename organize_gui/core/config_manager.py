"""
Configuration Manager for the File Organization System.

This module handles loading, saving, and modifying the YAML configuration
for the file organization system.
"""

import os
import subprocess
import yaml
import tempfile
import shutil

class ConfigManager:
    """Manager for the file organization configuration."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        # The current configuration
        self.config = None
        
        # Path to the customize_config.py script
        self.customize_script = self._find_customize_script()
    
    def _find_customize_script(self):
        """Find the path to the customize_config.py script."""
        # Start from the current directory and go up
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Look for config directory
        config_dir = os.path.join(current_dir, "config")
        script_path = os.path.join(config_dir, "customize_config.py")
        
        if os.path.exists(script_path):
            return script_path
        
        # If not found, search in potential locations
        for root, dirs, files in os.walk(current_dir):
            if "customize_config.py" in files:
                return os.path.join(root, "customize_config.py")
        
        # If not found, return the default path anyway
        return script_path
    
    def create_new_config(self):
        """Create a new empty configuration."""
        self.config = {
            'rules': []
        }
    
    def load_config(self, config_path):
        """Load a configuration from a file."""
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
    
    def save_config(self, config_path):
        """Save the current configuration to a file."""
        if not self.config:
            raise ValueError("No configuration to save")
        
        with open(config_path, 'w') as file:
            yaml.dump(self.config, file, default_flow_style=False, sort_keys=False)
    
    def get_current_paths(self):
        """Get the current source and destination paths from the configuration."""
        if not self.config or 'rules' not in self.config or not self.config['rules']:
            return None, None
        
        # Get source path from the first rule
        source = None
        if 'locations' in self.config['rules'][0]:
            locations = self.config['rules'][0]['locations']
            if isinstance(locations, list) and locations:
                if isinstance(locations[0], dict) and 'path' in locations[0]:
                    source = locations[0]['path']
                else:
                    source = locations[0]
            elif isinstance(locations, str):
                source = locations
        
        # Get destination path by finding a common prefix
        dest = self._find_common_destination()
        
        return source, dest
    
    def _find_common_destination(self):
        """Find the common destination base path in the configuration."""
        if not self.config or 'rules' not in self.config:
            return None
        
        dest_paths = []
        
        # Extract all destination paths
        for rule in self.config['rules']:
            if 'actions' in rule:
                for action in rule['actions']:
                    if isinstance(action, dict) and 'move' in action:
                        if isinstance(action['move'], dict) and 'dest' in action['move']:
                            dest_paths.append(action['move']['dest'])
                        elif isinstance(action['move'], str):
                            dest_paths.append(action['move'])
        
        if not dest_paths:
            return None
        
        # Find common path using os.path.commonpath
        try:
            # Replace placeholders like {extension} with a dummy value
            # to make commonpath work
            cleaned_paths = []
            for path in dest_paths:
                cleaned = path
                if '{' in path:
                    # Replace placeholders with dummy values
                    cleaned = path.split('{')[0]
                    if cleaned.endswith('/'):
                        cleaned = cleaned[:-1]
                cleaned_paths.append(cleaned)
            
            common = os.path.commonpath(cleaned_paths)
            
            # Strip off Organized or Cleanup if present
            if '/Organized' in common:
                common = common.split('/Organized')[0]
            elif '/Cleanup' in common:
                common = common.split('/Cleanup')[0]
            
            return common
        except ValueError:
            # If the paths don't have a common prefix, return None
            return None
    
    def update_paths(self, source_dir, dest_dir):
        """Update the source and destination paths in the configuration."""
        if not self.config or 'rules' not in self.config:
            raise ValueError("No configuration loaded")
        
        # Use the customize_config.py script if available
        if os.path.exists(self.customize_script):
            self._update_with_script(source_dir, dest_dir)
        else:
            # Fallback to manual update
            self._update_manually(source_dir, dest_dir)
    
    def _update_with_script(self, source_dir, dest_dir):
        """Update paths using the customize_config.py script."""
        # Create a temporary file with the current configuration
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp_file:
            temp_path = temp_file.name
            yaml.dump(self.config, temp_file, default_flow_style=False, sort_keys=False)
        
        try:
            # Run the customize_config.py script
            result = subprocess.run(
                [
                    "python", self.customize_script,
                    "--config", temp_path,
                    "--source", source_dir,
                    "--dest-base", dest_dir
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to update paths: {result.stderr}")
            
            # Load the updated configuration
            with open(temp_path, 'r') as file:
                self.config = yaml.safe_load(file)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _update_manually(self, source_dir, dest_dir):
        """Update paths manually (fallback if script is not available)."""
        # Update source locations
        for rule in self.config['rules']:
            if 'locations' in rule:
                if isinstance(rule['locations'], list):
                    for i, location in enumerate(rule['locations']):
                        if isinstance(location, dict) and 'path' in location:
                            rule['locations'][i]['path'] = source_dir
                        else:
                            rule['locations'][i] = source_dir
                else:
                    rule['locations'] = source_dir
        
        # Update destination paths
        for rule in self.config['rules']:
            if 'actions' in rule:
                for action in rule['actions']:
                    if isinstance(action, dict) and 'move' in action:
                        if isinstance(action['move'], dict) and 'dest' in action['move']:
                            old_dest = action['move']['dest']
                            action['move']['dest'] = self._replace_dest_base(old_dest, dest_dir)
                        elif isinstance(action['move'], str):
                            old_dest = action['move']
                            action['move'] = self._replace_dest_base(old_dest, dest_dir)
    
    def _replace_dest_base(self, old_dest, new_base):
        """Replace the base directory in a destination path."""
        # Handle paths with placeholders like {extension}
        if '{' in old_dest:
            # Find where the relative path starts
            if '/Organized/' in old_dest:
                parts = old_dest.split('/Organized/')
                if len(parts) > 1:
                    return f"{new_base}/Organized/{parts[1]}"
            elif '/Cleanup/' in old_dest:
                parts = old_dest.split('/Cleanup/')
                if len(parts) > 1:
                    return f"{new_base}/Cleanup/{parts[1]}"
        
        # Handle direct paths
        if '/Organized/' in old_dest:
            parts = old_dest.split('/Organized/')
            if len(parts) > 1:
                return f"{new_base}/Organized/{parts[1]}"
        elif '/Cleanup/' in old_dest:
            parts = old_dest.split('/Cleanup/')
            if len(parts) > 1:
                return f"{new_base}/Cleanup/{parts[1]}"
        
        # If no pattern matches, just return the original
        return old_dest