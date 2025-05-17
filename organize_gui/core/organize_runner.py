"""
Enhanced Organize Runner for the File Organization System.

Uses output_parser utility function for parsing process output.
"""

import os
import subprocess
import tempfile
import re
import yaml
import threading
import time
import platform
import sys
from pathlib import Path

# Import the parser function
from .output_parser import parse_organize_output

class OrganizeRunner:
    """Enhanced runner for the organize-tool."""

    # Pass config_manager in __init__ if needed, but not strictly required for this change
    def __init__(self, config_manager=None):
        """Initialize the organize runner."""
        self.organize_cmd = self._find_organize_command()
        self.script_path = self._find_organize_script()
        self.is_running = False
        self.current_process = None
        # Store config_manager if passed, might be useful elsewhere
        self.config_manager = config_manager

    def _find_organize_command(self):
        """Find the organize command."""
        try:
            if os.name == 'nt':
                result = subprocess.run(['where', 'organize'], capture_output=True, text=True, check=False)
                if result.returncode == 0: return 'organize'
                python_path = os.path.dirname(sys.executable)
                candidate = os.path.join(python_path, 'Scripts', 'organize.exe')
                if os.path.exists(candidate): return candidate
            else: # Unix-like
                result = subprocess.run(['which', 'organize'], capture_output=True, text=True, check=False)
                if result.returncode == 0: return 'organize'
                python_path = os.path.dirname(sys.executable)
                candidate = os.path.join(python_path, 'organize')
                if os.path.exists(candidate): return candidate
                candidate_sys = '/usr/local/bin/organize'
                if os.path.exists(candidate_sys): return candidate_sys
            return 'organize' # Default
        except Exception: return 'organize' # Fallback

    def _find_organize_script(self):
        """Find the organize-files.sh or .bat script."""
        try:
            # Assuming core/ is one level down from organize_gui/
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_name = "organize-files.bat" if os.name == "nt" else "organize-files.sh"
            # Check relative to organize_gui/ first, then parent
            paths_to_check = [
                os.path.join(base_dir, "config", script_name),
                os.path.join(base_dir, script_name),
                os.path.join(os.path.dirname(base_dir), "config", script_name),
                os.path.join(os.path.dirname(base_dir), script_name)
            ]
            for path in paths_to_check:
                if os.path.exists(path): return path
            # Fallback guess if not found
            return os.path.join(base_dir, "config", script_name)
        except Exception:
            script_name = "organize-files.bat" if os.name == "nt" else "organize-files.sh"
            # Fallback guess
            return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", script_name)

    # Modified run method signature
    def run(self, simulation=True, progress_callback=None, output_callback=None, config_path=None, config_data=None, verbose=False):
        """Runs the organization process, optionally using provided config data."""
        if self.is_running:
            if output_callback: output_callback("Process already running.", "error")
            return {'success': False, 'message': "Process already running."}

        self.is_running = True
        temp_config_path = None
        effective_config_path = config_path # Start with the explicitly passed path

        try:
            if progress_callback: progress_callback(0, "Starting...")

            # If config_data is provided, create a temporary file
            if config_data is not None:
                if not isinstance(config_data, dict) or 'rules' not in config_data:
                     raise ValueError("Invalid config_data provided.")
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as temp_file:
                        yaml.dump(config_data, temp_file, default_flow_style=False, sort_keys=False, indent=2)
                        temp_config_path = temp_file.name
                    effective_config_path = temp_config_path # Use the temp file path
                    if output_callback: output_callback(f"Using temporary config file: {temp_config_path}", "debug")
                except Exception as dump_err:
                    raise ValueError(f"Failed to write temporary config file: {dump_err}") from dump_err

            # Determine whether to use script or direct command
            # Note: Script might not support arbitrary config paths easily, prefer command if temp file used?
            # Let's assume script can take --config path for now.
            use_script = os.path.exists(self.script_path) and not temp_config_path # Prefer command if using temp file? Or modify script?
            # For now, let's try passing the temp path to the script too.

            runner_method = self._run_with_script if use_script else self._run_with_command

            # Pass the effective_config_path (could be original or temp)
            result = runner_method(
                simulation=simulation,
                output_stream=sys.stdout,  # Default to stdout
                output_callback=output_callback,
                config_path=effective_config_path,
                verbose=verbose
            )
            return result

        except Exception as e:
            if output_callback: output_callback(f"Error running process: {e}", "error")
            return {'success': False, 'message': f"Error: {e}"}
        finally:
            self.is_running = False
            # Clean up the temporary file if it was created
            if temp_config_path and os.path.exists(temp_config_path):
                try:
                    os.unlink(temp_config_path)
                    if output_callback: output_callback(f"Deleted temporary config file: {temp_config_path}", "debug")
                except OSError as unlink_err:
                    if output_callback: output_callback(f"Warning: Failed to delete temporary config file {temp_config_path}: {unlink_err}", "warning")

    # Modified to accept config_path with output_stream as optional
    def _run_with_script(self, simulation=None, output_stream=None, output_callback=None, config_path=None, verbose=False):
        """Runs the process using the shell script."""
        try:
            cmd = [self.script_path] + (["--simulate"] if simulation else ["--run"])
            # Use the config_path passed from run()
            if config_path: cmd.extend(["--config-file", config_path])
            # if verbose: cmd.append("--verbose") # Removed as organize run/sim does not support --verbose

            if output_callback: output_callback(f"Running script: {' '.join(cmd)}", "info")
            if os.name != "nt":
                try: os.chmod(self.script_path, 0o755)
                except Exception as e: output_callback(f"Warning: chmod failed: {e}", "warning")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.current_process = process
            # Call the external parser function using positional arguments, passing streams directly
            results = parse_organize_output(
                stdout_stream=process.stdout, # Pass stream directly
                stderr_stream=process.stderr, # Pass stream directly
                is_running_flag_func=lambda: self.is_running, # Pass running flag check
                output_callback=output_callback,
                progress_callback=None,  # Removed progress_callback
                simulation=simulation
            )
            process.wait() # Ensure process finishes after stream parsing
            success = process.returncode == 0
            message = f"Script {'simulation' if simulation else 'run'} {'completed' if success else 'failed'}."
            if not success: message += f" (Code: {process.returncode})"
            if output_callback: output_callback(message, "success" if success else "error")
            return {'success': success, 'message': message, 'results': results}
        except Exception as e:
            if output_callback: output_callback(f"Error with script: {e}", "error")
            return {'success': False, 'message': f"Script error: {e}"}
        finally:
             self.current_process = None

    # Modified to accept config_path with output_stream as optional
    def _run_with_command(self, simulation, output_callback=None, config_path=None, verbose=False, output_stream=None):
        """Runs the process using the direct organize command."""
        try:
            config_to_use = config_path # Use path passed from run()
            # Fallback to default only if no path was determined in run()
            if not config_to_use:
                 default_config = Path.home() / ".config" / "organize" / "config.yaml" # Standard organize default
                 if default_config.exists():
                     config_to_use = str(default_config)
                     if output_callback: output_callback(f"Using default config: {config_to_use}", "debug")
                 # Removed the Library/Application Support check as it's less standard for organize-tool CLI

            cmd = [self.organize_cmd]
            
            # Add subcommand first (sim or run)
            if simulation:
                cmd.append('sim')
            else:
                cmd.append('run')
            
            # Add config file as positional argument
            if config_to_use:
                cmd.append(config_to_use)
            else:
                # If no config_to_use, 'organize run' might expect --stdin or show help.
                # The original code didn't explicitly handle the case where config_to_use is None
                # and the command still proceeds. This might be okay if 'organize' handles it.
                if output_callback: output_callback("Warning: No configuration file specified or found. 'organize' might use default or expect --stdin.", "warning")

            if output_callback: output_callback(f"Running command: {' '.join(cmd)}", "info")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, # Always use PIPE for stdout to allow parsing
                stderr=subprocess.PIPE, # Use PIPE for stderr as well, to be parsed separately
                text=True
            )
            self.current_process = process
            # Call the external parser function using positional arguments, passing streams directly
            results = parse_organize_output(
                stdout_stream=process.stdout, 
                stderr_stream=process.stderr, # Pass the actual stderr stream
                is_running_flag_func=lambda: self.is_running, # Pass running flag check
                output_callback=output_callback,
                progress_callback=None, # Keep as None
                simulation=simulation
            )
            process.wait() # Ensure process finishes after stream parsing
            success = process.returncode == 0
            message = f"Command {'simulation' if simulation else 'run'} {'completed' if success else 'failed'}."
            if not success: message += f" (Code: {process.returncode})"
            if output_callback: output_callback(message, "success" if success else "error")
            return {'success': success, 'message': message, 'results': results}
        except Exception as e:
            if output_callback: output_callback(f"Error with command: {e}", "error")
            return {'success': False, 'message': f"Command error: {e}"}
        finally:
            self.current_process = None

    # Removed _parse_process_stream method body, now calls external function

    def kill(self):
        """Stop the current process if running."""
        if not self.is_running or not self.current_process: 
            return {"success": False, "message": "No process running to kill."}
        print("Attempting to stop process...")
        try:
            # Use platform specific termination
            if platform.system() == "Windows":
                # Send CTRL+C event on Windows
                # Note: This might not work reliably for all subprocesses
                # Using terminate/kill as fallback
                try:
                   # This requires the process to be created with creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                   # which we are not doing currently. Sticking to terminate/kill.
                   # os.kill(self.current_process.pid, signal.CTRL_C_EVENT)
                   self.current_process.terminate()
                except Exception:
                   self.current_process.kill() # Force kill if terminate fails
            else:
                # Send SIGINT (like Ctrl+C) on Unix-like systems
                self.current_process.send_signal(subprocess.signal.SIGINT)

            # Wait briefly for graceful shutdown
            try:
                self.current_process.wait(timeout=1.0)
                print("Process terminated gracefully.")
                message = "Process terminated gracefully."
            except subprocess.TimeoutExpired:
                 print("Process did not terminate gracefully, killing...")
                 self.current_process.kill() # Force kill if SIGINT didn't work
                 self.current_process.wait() # Wait for kill to complete
                 print("Process killed.")
                 message = "Process killed forcefully after timeout."
            return {"success": True, "message": message}
        except Exception as e:
            error_message = f"Error stopping process: {e}"
            print(error_message)
            # Ensure kill is attempted even if initial signal fails
            try:
                if self.current_process and self.current_process.poll() is None:
                    self.current_process.kill()
                    self.current_process.wait()
                    return {"success": True, "message": "Process killed after initial error."}
            except Exception as kill_e:
                print(f"Error during final kill attempt: {kill_e}")
            return {"success": False, "message": error_message}
        finally:
            self.is_running = False
            self.current_process = None

    def check_status(self):
        """Check if process is still running and update is_running flag accordingly"""
        if self.current_process:
            is_running = self.current_process.poll() is None
            # Update is_running flag if process has completed
            if not is_running:
                self.is_running = False
            return is_running
        return False

    def schedule(self, schedule_type, schedule_time, simulation=False, config_path=None, config_data=None):
        """Generates scheduler command/entry."""
        temp_config_path_sched = None
        effective_config_path_sched = config_path

        try:
            hour, minute = map(int, schedule_time.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59): raise ValueError("Invalid time")

            # Handle config_data for scheduling
            if config_data is not None:
                if not isinstance(config_data, dict) or 'rules' not in config_data:
                     raise ValueError("Invalid config_data provided for scheduling.")
                try:
                    # Need a persistent temp file for scheduler, or save it properly?
                    # For now, let's assume we need a *saved* config path for scheduling.
                    # Option 1: Save it somewhere specific?
                    # Option 2: Require user to save config before scheduling if changes made?
                    # Let's raise an error for now if config_data is passed, requiring a saved path.
                    raise ValueError("Scheduling with unsaved configuration changes (config_data) is not supported. Please save the configuration first.")
                    # If we were to support it, we'd need to save config_data to a known, persistent path.
                    # with tempfile.NamedTemporaryFile(...) as temp_file: ... (but need persistent path)
                    # effective_config_path_sched = persistent_temp_path
                except Exception as dump_err:
                    raise ValueError(f"Failed to handle config_data for scheduling: {dump_err}") from dump_err

            # Build command parts using the determined config path
            cmd_parts = [self.organize_cmd]
            # Add subcommand first (sim or run)
            cmd_parts.append('sim' if simulation else 'run')
            if effective_config_path_sched:
                 cmd_parts.append(effective_config_path_sched)
            # Note: Verbose is usually not desired for scheduled tasks
            cmd_str = " ".join(f'"{part}"' if " " in part else part for part in cmd_parts)

            scheduler_info = {}
            if platform.system() == 'Windows':
                task_name = f"OrganizeTool_{schedule_type.capitalize()}"
                # Ensure command path is properly quoted for schtasks
                tr_cmd_str = cmd_str.replace('"', '\\"') # Escape quotes for /tr argument
                scheduler_info['type'] = 'schtasks'
                # Use single quotes around the command for /tr if possible, or escaped double quotes
                scheduler_info['command'] = f'schtasks /create /tn "{task_name}" /tr "{tr_cmd_str}" /sc {schedule_type.upper()} /st {hour:02d}:{minute:02d} /f'
                message = f"Generated Windows Task Scheduler command."
            else: # Assume cron-like
                cron_minute, cron_hour = str(minute), str(hour)
                cron_day_month, cron_month, cron_day_week = '*', '*', '*'
                if schedule_type == 'weekly': cron_day_week = '0' # Sunday
                elif schedule_type == 'monthly': cron_day_month = '1' # 1st of month
                # Ensure command is suitable for cron (e.g., full paths if needed)
                cron_line = f"{cron_minute} {cron_hour} {cron_day_month} {cron_month} {cron_day_week} {cmd_str}"
                scheduler_info['type'] = 'cron'; scheduler_info['command'] = cron_line
                message = f"Generated cron entry."

            return {'success': True, 'message': message, 'scheduler_info': scheduler_info}
        except Exception as e:
            return {'success': False, 'message': f"Error generating schedule: {e}"}
