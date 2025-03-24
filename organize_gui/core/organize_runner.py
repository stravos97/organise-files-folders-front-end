"""
Organize Runner for the File Organization System.

This module handles running the organize-tool with the provided configuration,
and collects the results for display.
"""

import os
import subprocess
import re
import shlex
import time
import threading

class OrganizeRunner:
    """Runner for the organize-tool."""
    
    def __init__(self):
        """Initialize the organize runner."""
        # Find paths to necessary tools
        self.organize_script = self._find_organize_script()
    
    def _find_organize_script(self):
        """Find the path to the organize-files.sh script."""
        # Start from the current directory and go up
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Check common locations
        script_name = "organize-files.sh"
        if os.name == "nt":  # Windows
            script_name = "organize-files.bat"
        
        # Look for config directory
        config_dir = os.path.join(current_dir, "config")
        script_path = os.path.join(config_dir, script_name)
        
        if os.path.exists(script_path):
            return script_path
        
        # If not found, search in potential locations
        for root, dirs, files in os.walk(current_dir):
            if script_name in files:
                return os.path.join(root, script_name)
        
        # If not found, return the default path anyway
        return script_path
    
    def run(self, simulation=True, progress_callback=None, output_callback=None):
        """
        Run the organization process.
        
        Args:
            simulation (bool): If True, run in simulation mode (no actual changes)
            progress_callback (callable): Function to call with progress updates
            output_callback (callable): Function to call with output text
        
        Returns:
            dict: Result information
        """
        # Prepare command
        if simulation:
            cmd = [self.organize_script, "--simulate"]
        else:
            cmd = [self.organize_script, "--run"]
        
        # Initialize progress
        if progress_callback:
            progress_callback(0, "Starting...")
        
        try:
            # Check if the script exists
            if not os.path.exists(self.organize_script):
                if output_callback:
                    output_callback(f"Error: organize script not found at {self.organize_script}", "error")
                return {
                    'success': False,
                    'message': f"organize script not found at {self.organize_script}"
                }
            
            # Make sure script is executable
            if os.name != "nt":  # Not Windows
                try:
                    os.chmod(self.organize_script, 0o755)  # Make executable
                except Exception as e:
                    if output_callback:
                        output_callback(f"Warning: Could not make script executable: {str(e)}", "warning")
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
                bufsize=1
            )
            
            # Process output in a separate thread to avoid blocking
            def process_output():
                total_lines = 0
                processed_files = 0
                error_count = 0
                
                # Regular expressions for parsing output
                file_pattern = re.compile(r'^\s*[✓✗]\s+(.*)')
                error_pattern = re.compile(r'^\s*Error:.*', re.IGNORECASE)
                move_pattern = re.compile(r'.*Moving\s+.*')
                
                for line in iter(process.stdout.readline, ''):
                    total_lines += 1
                    
                    # Extract information from the line
                    file_match = file_pattern.match(line)
                    error_match = error_pattern.match(line)
                    move_match = move_pattern.match(line)
                    
                    if file_match:
                        processed_files += 1
                        if output_callback:
                            output_callback(f"Processing: {file_match.group(1)}", "info")
                    elif error_match:
                        error_count += 1
                        if output_callback:
                            output_callback(line.strip(), "error")
                    elif move_match:
                        if output_callback:
                            output_callback(line.strip(), "success")
                    else:
                        if output_callback:
                            output_callback(line.strip(), "info")
                    
                    # Update progress (rough estimate)
                    if progress_callback and total_lines % 10 == 0:
                        # Since we don't know the total, we'll use a heuristic
                        progress = min(processed_files / max(1, processed_files + 100) * 100, 95)
                        progress_callback(progress, f"Processed {processed_files} files...")
                
                # Process any errors from stderr
                for line in iter(process.stderr.readline, ''):
                    if output_callback:
                        output_callback(line.strip(), "error")
                    error_count += 1
            
            # Start the output processing thread
            output_thread = threading.Thread(target=process_output, daemon=True)
            output_thread.start()
            
            # Wait for process to complete
            process.wait()
            output_thread.join(timeout=1.0)  # Join with timeout to avoid hanging
            
            # Final progress update
            if progress_callback:
                progress_callback(100, "Complete")
            
            # Check return code
            if process.returncode == 0:
                if output_callback:
                    if simulation:
                        output_callback("Simulation completed successfully.", "success")
                    else:
                        output_callback("Organization completed successfully.", "success")
                
                return {
                    'success': True,
                    'message': "Process completed successfully."
                }
            else:
                if output_callback:
                    output_callback(f"Process failed with return code {process.returncode}", "error")
                
                return {
                    'success': False,
                    'message': f"Process failed with return code {process.returncode}"
                }
        
        except Exception as e:
            if output_callback:
                output_callback(f"Error running organization process: {str(e)}", "error")
            
            return {
                'success': False,
                'message': f"Error running organization process: {str(e)}"
            }
    
    def schedule(self, schedule_type, time, simulation=False):
        """
        Schedule the organization process to run automatically.
        
        Args:
            schedule_type (str): Type of schedule ('daily', 'weekly', 'monthly')
            time (str): Time to run (HH:MM)
            simulation (bool): If True, run in simulation mode
        
        Returns:
            bool: True if scheduled successfully, False otherwise
        """
        # In a real implementation, this would create a scheduled task
        # using the system's scheduler (cron, Task Scheduler, etc.)
        return True