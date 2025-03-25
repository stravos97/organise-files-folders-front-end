"""
Enhanced Organize Runner for the File Organization System.

This implementation provides a robust interface to run the organize-tool
command with proper error handling and result collection.
"""

import os
import subprocess
import tempfile
import re
import yaml
import threading
import time
import platform
from pathlib import Path

class OrganizeRunner:
    """Enhanced runner for the organize-tool."""
    
    def __init__(self):
        """Initialize the organize runner."""
        # Find paths to necessary tools
        self.organize_cmd = self._find_organize_command()
        self.script_path = self._find_organize_script()
        
        # Store run state
        self.is_running = False
        self.current_process = None
    
    def _find_organize_command(self):
        """Find the organize command."""
        try:
            # Check if organize is in PATH
            if os.name == 'nt':  # Windows
                # On Windows, check if the command exists
                result = subprocess.run(
                    ['where', 'organize'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    return 'organize'
            else:
                # On Unix-like systems, use 'which'
                result = subprocess.run(
                    ['which', 'organize'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    return 'organize'
            
            # If not found in PATH, try to find in common locations
            if os.name == 'nt':  # Windows
                python_path = os.path.dirname(sys.executable)
                candidate = os.path.join(python_path, 'Scripts', 'organize.exe')
                if os.path.exists(candidate):
                    return candidate
            
            # Default to just the command name and hope it works
            return 'organize'
            
        except Exception:
            # Default to just the command name
            return 'organize'
    
    def _find_organize_script(self):
        """Find the organize-files.sh or .bat script."""
        try:
            # Start from the current directory and go up
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Check common locations
            script_name = "organize-files.sh"
            if os.name == "nt":  # Windows
                script_name = "organize-files.bat"
            
            # Look for config directory
            paths_to_check = [
                os.path.join(current_dir, "config", script_name),
                os.path.join(current_dir, script_name),
                os.path.join(os.path.dirname(current_dir), "config", script_name),
                os.path.join(os.path.dirname(current_dir), script_name)
            ]
            
            for path in paths_to_check:
                if os.path.exists(path):
                    return path
            
            # If not found, search in potential locations
            for root, dirs, files in os.walk(current_dir):
                if script_name in files:
                    return os.path.join(root, script_name)
            
            # If not found, return a default path
            return os.path.join(current_dir, "config", script_name)
            
        except Exception:
            # Default to a reasonable path
            script_name = "organize-files.sh"
            if os.name == "nt":  # Windows
                script_name = "organize-files.bat"
            
            return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", script_name)
    
    def run(self, simulation=True, progress_callback=None, output_callback=None, config_path=None, verbose=False):
        """
        Run the organization process.
        
        Args:
            simulation (bool): If True, run in simulation mode (no actual changes)
            progress_callback (callable): Function to call with progress updates (value, status)
            output_callback (callable): Function to call with output text (text, tag)
            config_path (str): Path to a custom config file, or None to use the default
            verbose (bool): If True, enable verbose output
        
        Returns:
            dict: Result information
        """
        # Check if already running
        if self.is_running:
            if output_callback:
                output_callback("A process is already running. Please wait for it to complete.", "error")
            return {
                'success': False,
                'message': "A process is already running. Please wait for it to complete."
            }
        
        # Set running state
        self.is_running = True
        
        try:
            # Initialize progress
            if progress_callback:
                progress_callback(0, "Starting...")
            
            # Decide which method to use
            if os.path.exists(self.script_path):
                # Use the shell script if available
                result = self._run_with_script(
                    simulation,
                    progress_callback,
                    output_callback,
                    config_path,
                    verbose
                )
            else:
                # Use direct command otherwise
                result = self._run_with_command(
                    simulation,
                    progress_callback,
                    output_callback,
                    config_path,
                    verbose
                )
            
            return result
            
        except Exception as e:
            # Handle any exceptions
            if output_callback:
                output_callback(f"Error running organization process: {str(e)}", "error")
            
            # Reset running state
            self.is_running = False
            
            return {
                'success': False,
                'message': f"Error running organization process: {str(e)}"
            }
    
    def _run_with_script(self, simulation, progress_callback, output_callback, config_path, verbose):
        """Run the organization process using the shell script."""
        try:
            # Prepare command
            cmd = [self.script_path]
            
            if simulation:
                cmd.append("--simulate")
            else:
                cmd.append("--run")
            
            # Add config file if specified
            if config_path:
                cmd.extend(["--config", config_path])
            
            # Add verbose if specified
            if verbose:
                cmd.append("--verbose")
            
            # Log the command
            if output_callback:
                output_callback(f"Running command: {' '.join(cmd)}", "info")
            
            # Make sure script is executable
            if os.name != "nt":  # Not Windows
                try:
                    os.chmod(self.script_path, 0o755)  # Make executable
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
            
            # Store process for potential termination
            self.current_process = process
            
            # Process output and collect results
            results = self._process_output(
                process,
                progress_callback,
                output_callback,
                simulation
            )
            
            # Check return code
            if process.returncode == 0:
                message = "Simulation completed successfully." if simulation else "Organization completed successfully."
                if output_callback:
                    output_callback(message, "success")
                
                # Reset running state
                self.is_running = False
                self.current_process = None
                
                return {
                    'success': True,
                    'message': message,
                    'results': results
                }
            else:
                error_message = f"Process failed with return code {process.returncode}"
                if output_callback:
                    output_callback(error_message, "error")
                
                # Reset running state
                self.is_running = False
                self.current_process = None
                
                return {
                    'success': False,
                    'message': error_message,
                    'results': results
                }
            
        except Exception as e:
            # Handle exceptions
            if output_callback:
                output_callback(f"Error running with script: {str(e)}", "error")
            
            # Reset running state
            self.is_running = False
            self.current_process = None
            
            return {
                'success': False,
                'message': f"Error running with script: {str(e)}"
            }
    
    def _run_with_command(self, simulation, progress_callback, output_callback, config_path, verbose):
        """Run the organization process using the direct organize command."""
        try:
            # Create a temporary file for output if no config specified
            temp_file = None
            config_to_use = config_path
            
            if not config_to_use:
                # Try to get the default config
                config_paths = [
                    os.path.expanduser("~/.config/organize-tool/config.yaml"),
                    os.path.expanduser("~/Library/Application Support/organize-tool/config.yaml"),
                    os.path.join(os.getenv("APPDATA", ""), "organize-tool", "config.yaml")
                ]
                
                for path in config_paths:
                    if os.path.exists(path):
                        config_to_use = path
                        break
            
            # Prepare command
            cmd = [self.organize_cmd]
            
            # Add mode (sim or run)
            if simulation:
                cmd.append("sim")
            else:
                cmd.append("run")
            
            # Add config file if specified
            if config_to_use:
                cmd.append(config_to_use)
            
            # Add verbose flag if requested
            if verbose:
                cmd.append("--verbose")
            
            # Log the command
            if output_callback:
                output_callback(f"Running command: {' '.join(cmd)}", "info")
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
                bufsize=1
            )
            
            # Store process for potential termination
            self.current_process = process
            
            # Process output and collect results
            results = self._process_output(
                process,
                progress_callback,
                output_callback,
                simulation
            )
            
            # Check return code
            if process.returncode == 0:
                message = "Simulation completed successfully." if simulation else "Organization completed successfully."
                if output_callback:
                    output_callback(message, "success")
                
                # Reset running state
                self.is_running = False
                self.current_process = None
                
                return {
                    'success': True,
                    'message': message,
                    'results': results
                }
            else:
                error_message = f"Process failed with return code {process.returncode}"
                if output_callback:
                    output_callback(error_message, "error")
                
                # Reset running state
                self.is_running = False
                self.current_process = None
                
                return {
                    'success': False,
                    'message': error_message,
                    'results': results
                }
            
        except Exception as e:
            # Handle exceptions
            if output_callback:
                output_callback(f"Error running with command: {str(e)}", "error")
            
            # Reset running state
            self.is_running = False
            self.current_process = None
            
            return {
                'success': False,
                'message': f"Error running with command: {str(e)}"
            }
        finally:
            # Clean up temporary file if created
            if temp_file:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
    
    def _process_output(self, process, progress_callback, output_callback, simulation):
        """
        Process output from the organize process.
        
        Args:
            process: The subprocess.Popen object
            progress_callback: Function to call with progress updates
            output_callback: Function to call with output text
            simulation: Whether this is a simulation run
        
        Returns:
            list: Results from the process
        """
        results = []
        
        # Various regex patterns for parsing output
        file_pattern = re.compile(r'^\s*[✓✗]\s+(.*)')
        move_pattern = re.compile(r'.*Moving\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?')
        would_move_pattern = re.compile(r'.*Would move\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?')
        error_pattern = re.compile(r'^\s*Error:.*', re.IGNORECASE)
        rule_pattern = re.compile(r'^\s*Rule\s+"([^"]+)"')
        
        # Initialize processing variables
        total_lines = 0
        processed_files = 0
        current_rule = ""
        
        # Process stdout
        for line in iter(process.stdout.readline, ''):
            # Check if we've been asked to stop
            if not self.is_running:
                process.terminate()
                if output_callback:
                    output_callback("Process manually stopped.", "warning")
                break
            
            total_lines += 1
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for rule heading
            rule_match = rule_pattern.match(line)
            if rule_match:
                current_rule = rule_match.group(1)
                if output_callback:
                    output_callback(line, "heading")
                continue
            
            # Check for file being processed
            file_match = file_pattern.match(line)
            if file_match:
                processed_files += 1
                file_path = file_match.group(1)
                
                if output_callback:
                    output_callback(f"Processing: {file_path}", "info")
                
                # Update progress approximation
                if progress_callback:
                    progress = min(processed_files / max(1, processed_files + 100) * 100, 95)
                    progress_callback(progress, f"Processed {processed_files} files...")
                
                continue
            
            # Check for move/would move action
            move_match = move_pattern.match(line) if not simulation else None
            would_move_match = would_move_pattern.match(line) if simulation else None
            
            if move_match or would_move_match:
                match = move_match or would_move_match
                source = match.group(1)
                dest = match.group(2)
                
                # Add to results
                result = {
                    'source': source,
                    'destination': dest,
                    'status': "Moved" if not simulation else "Would move",
                    'rule': current_rule
                }
                results.append(result)
                
                # Log the move
                if output_callback:
                    output_callback(line, "move")
                
                continue
            
            # Check for error
            error_match = error_pattern.match(line)
            if error_match:
                if output_callback:
                    output_callback(line, "error")
                
                # Add to results if it looks like a file error
                if " file " in line.lower() or " path " in line.lower():
                    path_match = re.search(r'"([^"]+)"', line)
                    if path_match:
                        file_path = path_match.group(1)
                        result = {
                            'source': file_path,
                            'status': "Error",
                            'rule': current_rule
                        }
                        results.append(result)
                
                continue
            
            # Default output handling
            if output_callback:
                tag = "info"
                if "simulating" in line.lower() or "simulation" in line.lower():
                    tag = "heading"
                elif "echo:" in line.lower() or "found" in line.lower():
                    tag = "echo"
                
                output_callback(line, tag)
        
        # Process stderr
        for line in iter(process.stderr.readline, ''):
            line = line.strip()
            if line and output_callback:
                output_callback(line, "error")
        
        # Finalize progress
        if progress_callback:
            progress_callback(100, "Complete")
        
        return results
    
    def stop(self):
        """Stop the current process if running."""
        if not self.is_running or self.current_process is None:
            return False
        
        try:
            # Terminate the process
            self.current_process.terminate()
            
            # Wait a bit for it to terminate
            for _ in range(5):  # Wait up to 0.5 seconds
                if self.current_process.poll() is not None:
                    break
                time.sleep(0.1)
            
            # If still running, kill it
            if self.current_process.poll() is None:
                if os.name == 'nt':  # Windows
                    self.current_process.kill()
                else:
                    import signal
                    os.kill(self.current_process.pid, signal.SIGKILL)
            
            # Reset state
            self.is_running = False
            self.current_process = None
            
            return True
            
        except Exception:
            # Reset state
            self.is_running = False
            self.current_process = None
            
            return False
    
    def schedule(self, schedule_type, schedule_time, simulation=False, config_path=None):
        """
        Schedule the organization process to run automatically.
        
        Args:
            schedule_type (str): Type of schedule ('daily', 'weekly', 'monthly')
            schedule_time (str): Time to run (HH:MM)
            simulation (bool): If True, run in simulation mode
            config_path (str): Path to a custom config file, or None to use the default
        
        Returns:
            dict: Result information including the command to use for scheduling
        """
        try:
            # Parse time
            hour, minute = schedule_time.split(':')
            hour = int(hour)
            minute = int(minute)
            
            # Validate time
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                return {
                    'success': False,
                    'message': "Invalid time. Please use HH:MM format (24-hour)."
                }
            
            # Prepare command for scheduler
            if os.path.exists(self.script_path):
                # Use the shell script
                cmd = [self.script_path]
                
                if simulation:
                    cmd.append("--simulate")
                else:
                    cmd.append("--run")
                
                # Add config file if specified
                if config_path:
                    cmd.extend(["--config", config_path])
            else:
                # Use direct command
                cmd = [self.organize_cmd]
                
                # Add mode (sim or run)
                if simulation:
                    cmd.append("sim")
                else:
                    cmd.append("run")
                
                # Add config file if specified
                if config_path:
                    cmd.append(config_path)
            
            # Command string
            cmd_str = " ".join(cmd)
            
            # Generate scheduler command based on platform
            if os.name == 'nt':  # Windows
                # Windows Task Scheduler
                task_name = f"OrganizeTool_{schedule_type.capitalize()}"
                
                scheduler_info = {
                    'task_name': task_name,
                    'command': cmd_str,
                    'schedule_type': schedule_type,
                    'hour': hour,
                    'minute': minute,
                    'schtasks_cmd': f'schtasks /create /tn "{task_name}" /tr "{cmd_str}" /sc {schedule_type.upper()} /st {hour:02d}:{minute:02d} /f'
                }
                
                return {
                    'success': True,
                    'message': f"Generated Windows Task Scheduler command for {schedule_type} at {hour:02d}:{minute:02d}",
                    'scheduler_info': scheduler_info
                }
            else:
                # Unix cron
                # Convert schedule type to cron format
                if schedule_type == 'daily':
                    day_of_month = '*'
                    day_of_week = '*'
                    month = '*'
                elif schedule_type == 'weekly':
                    day_of_month = '*'
                    day_of_week = '0'  # Sunday
                    month = '*'
                elif schedule_type == 'monthly':
                    day_of_month = '1'  # 1st of month
                    day_of_week = '*'
                    month = '*'
                else:
                    return {
                        'success': False,
                        'message': f"Invalid schedule type: {schedule_type}"
                    }
                
                # Create cron line
                cron_line = f"{minute} {hour} {day_of_month} {month} {day_of_week} {cmd_str}"
                
                scheduler_info = {
                    'cron_line': cron_line
                }
                
                return {
                    'success': True,
                    'message': f"Generated cron entry for {schedule_type} at {hour:02d}:{minute:02d}",
                    'scheduler_info': scheduler_info
                }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error generating schedule: {str(e)}"
            }