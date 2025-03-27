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

    def __init__(self):
        """Initialize the organize runner."""
        self.organize_cmd = self._find_organize_command()
        self.script_path = self._find_organize_script()
        self.is_running = False
        self.current_process = None

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
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_name = "organize-files.bat" if os.name == "nt" else "organize-files.sh"
            paths_to_check = [
                os.path.join(current_dir, "config", script_name), os.path.join(current_dir, script_name),
                os.path.join(os.path.dirname(current_dir), "config", script_name), os.path.join(os.path.dirname(current_dir), script_name)
            ]
            for path in paths_to_check:
                if os.path.exists(path): return path
            return os.path.join(current_dir, "config", script_name) # Default guess
        except Exception:
            script_name = "organize-files.bat" if os.name == "nt" else "organize-files.sh"
            return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", script_name)

    def run(self, simulation=True, progress_callback=None, output_callback=None, config_path=None, verbose=False):
        """Runs the organization process."""
        if self.is_running:
            if output_callback: output_callback("Process already running.", "error")
            return {'success': False, 'message': "Process already running."}
        self.is_running = True
        try:
            if progress_callback: progress_callback(0, "Starting...")
            use_script = os.path.exists(self.script_path)
            runner_method = self._run_with_script if use_script else self._run_with_command
            result = runner_method(simulation, progress_callback, output_callback, config_path, verbose)
            return result
        except Exception as e:
            if output_callback: output_callback(f"Error running process: {e}", "error")
            return {'success': False, 'message': f"Error: {e}"}
        finally:
            self.is_running = False

    def _run_with_script(self, simulation, progress_callback, output_callback, config_path, verbose):
        """Runs the process using the shell script."""
        try:
            cmd = [self.script_path] + (["--simulate"] if simulation else ["--run"])
            if config_path: cmd.extend(["--config", config_path])
            if verbose: cmd.append("--verbose")
            if output_callback: output_callback(f"Running script: {' '.join(cmd)}", "info")
            if os.name != "nt":
                try: os.chmod(self.script_path, 0o755)
                except Exception as e: output_callback(f"Warning: chmod failed: {e}", "warning")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True, bufsize=1, encoding='utf-8')
            self.current_process = process
            # Call the external parser function
            results = parse_organize_output(
                iter(process.stdout.readline, ''),
                iter(process.stderr.readline, ''),
                lambda: self.is_running, # Pass running flag check
                output_callback,
                progress_callback,
                simulation
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

    def _run_with_command(self, simulation, progress_callback, output_callback, config_path, verbose):
        """Runs the process using the direct organize command."""
        try:
            config_to_use = config_path
            if not config_to_use:
                 default_config = Path.home() / ".config" / "organize" / "config.yaml"
                 if default_config.exists(): config_to_use = str(default_config)

            cmd = [self.organize_cmd] + (['sim'] if simulation else ['run'])
            if config_to_use: cmd.append(config_to_use)
            if verbose: cmd.append("--verbose")
            if output_callback: output_callback(f"Running command: {' '.join(cmd)}", "info")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True, bufsize=1, encoding='utf-8')
            self.current_process = process
            # Call the external parser function
            results = parse_organize_output(
                iter(process.stdout.readline, ''),
                iter(process.stderr.readline, ''),
                lambda: self.is_running, # Pass running flag check
                output_callback,
                progress_callback,
                simulation
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

    def stop(self):
        """Stop the current process if running."""
        if not self.is_running or not self.current_process: return False
        print("Attempting to stop process...")
        try:
            self.current_process.terminate()
            try: self.current_process.wait(timeout=0.5); print("Process terminated.")
            except subprocess.TimeoutExpired:
                 print("Process did not terminate, killing..."); self.current_process.kill(); self.current_process.wait(); print("Process killed.")
            return True
        except Exception as e: print(f"Error stopping process: {e}"); return False
        finally: self.is_running = False; self.current_process = None

    def schedule(self, schedule_type, schedule_time, simulation=False, config_path=None):
        """Generates scheduler command/entry."""
        try:
            hour, minute = map(int, schedule_time.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59): raise ValueError("Invalid time")

            cmd_parts = [self.organize_cmd] + (['sim'] if simulation else ['run'])
            if config_path: cmd_parts.append(config_path)
            cmd_str = " ".join(f'"{part}"' if " " in part else part for part in cmd_parts)

            scheduler_info = {}
            if platform.system() == 'Windows':
                task_name = f"OrganizeTool_{schedule_type.capitalize()}"
                scheduler_info['type'] = 'schtasks'
                scheduler_info['command'] = f'schtasks /create /tn "{task_name}" /tr \'{cmd_str}\' /sc {schedule_type.upper()} /st {hour:02d}:{minute:02d} /f'
                message = f"Generated Windows Task Scheduler command."
            else: # Assume cron-like
                cron_minute, cron_hour = str(minute), str(hour)
                cron_day_month, cron_month, cron_day_week = '*', '*', '*'
                if schedule_type == 'weekly': cron_day_week = '0'
                elif schedule_type == 'monthly': cron_day_month = '1'
                cron_line = f"{cron_minute} {cron_hour} {cron_day_month} {cron_month} {cron_day_week} {cmd_str}"
                scheduler_info['type'] = 'cron'; scheduler_info['command'] = cron_line
                message = f"Generated cron entry."

            return {'success': True, 'message': message, 'scheduler_info': scheduler_info}
        except Exception as e:
            return {'success': False, 'message': f"Error generating schedule: {e}"}
