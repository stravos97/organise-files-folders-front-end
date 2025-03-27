"""
Enhanced Preview and Run panel for the File Organization System.

Uses OutputLogPanel for displaying process output.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import threading
import queue
import datetime
import subprocess
import tempfile
import yaml
import re

# Import the new panel
from .output_log_panel import OutputLogPanel

class PreviewPanel(ttk.Frame):
    """Enhanced panel for previewing and running the organization process."""

    def __init__(self, parent, organize_runner=None):
        """Initialize the preview panel."""
        super().__init__(parent)

        self.organize_runner = organize_runner
        self.is_running = False
        self.queue = queue.Queue()
        self.current_results = []

        self._create_widgets()

    def _create_widgets(self):
        """Create the UI components for the preview panel using grid."""
        self.grid_rowconfigure(3, weight=1) # Output frame should expand
        self.grid_columnconfigure(0, weight=1)

        row_index = 0

        # --- Actions frame ---
        actions_frame = ttk.LabelFrame(self, text="Actions", padding=(10, 5))
        actions_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        sim_button = ttk.Button(actions_frame, text="Run Simulation", command=self.run_simulation)
        sim_button.pack(side=tk.LEFT, padx=(0, 5), pady=5)
        run_button = ttk.Button(actions_frame, text="Run Organization", command=self.run_organization)
        run_button.pack(side=tk.LEFT, padx=5, pady=5)
        row_index += 1

        # --- Options frame ---
        options_frame = ttk.LabelFrame(self, text="Options", padding=(10, 5))
        options_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        options_frame.grid_columnconfigure(2, weight=1)
        # Verbose output
        self.verbose_var = tk.BooleanVar(value=True)
        verbose_check = ttk.Checkbutton(options_frame, text="Verbose Output", variable=self.verbose_var)
        verbose_check.grid(row=0, column=0, sticky='w', padx=(0, 10), pady=5)
        # Custom config checkbox
        self.use_custom_config_var = tk.BooleanVar(value=False)
        custom_config_check = ttk.Checkbutton(options_frame, text="Use Custom Config File", variable=self.use_custom_config_var, command=self._toggle_custom_config)
        custom_config_check.grid(row=0, column=1, sticky='w', padx=(0, 10), pady=5)
        # Custom config path frame
        self.custom_config_frame = ttk.Frame(options_frame)
        self.custom_config_frame.grid(row=0, column=2, sticky='ew', padx=5, pady=5)
        self.custom_config_frame.grid_columnconfigure(0, weight=1)
        self.custom_config_path_var = tk.StringVar()
        self.custom_config_entry = ttk.Entry(self.custom_config_frame, textvariable=self.custom_config_path_var)
        self.custom_config_entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.custom_config_button = ttk.Button(self.custom_config_frame, text="Browse...", command=self._browse_config)
        self.custom_config_button.grid(row=0, column=1, sticky='e')
        self.custom_config_frame.grid_remove() # Hide initially
        row_index += 1

        # --- Progress frame ---
        progress_frame = ttk.LabelFrame(self, text="Progress", padding=(10, 5))
        progress_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=5)
        progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate', variable=self.progress_var)
        self.progress_bar.grid(row=0, column=0, sticky='ew', pady=(0, 5))
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky='w')
        row_index += 1

        # --- Output Log Panel ---
        output_outer_frame = ttk.LabelFrame(self, text="Output", padding=(10, 5))
        output_outer_frame.grid(row=row_index, column=0, sticky='nsew', padx=10, pady=5)
        output_outer_frame.grid_rowconfigure(0, weight=1)
        output_outer_frame.grid_columnconfigure(0, weight=1)

        # Instantiate OutputLogPanel
        self.output_log_panel = OutputLogPanel(output_outer_frame, height=15) # Pass parent frame
        self.output_log_panel.grid(row=0, column=0, sticky='nsew') # Grid the panel itself

        row_index += 1

        # --- Button frame (bottom) ---
        button_frame = ttk.Frame(self)
        button_frame.grid(row=row_index, column=0, sticky='ew', padx=10, pady=(5, 10))
        button_frame.grid_columnconfigure(1, weight=1) # Push save button right
        clear_button = ttk.Button(button_frame, text="Clear Output", command=self._clear_output)
        clear_button.grid(row=0, column=0, sticky='w', padx=(0, 5))
        stop_button = ttk.Button(button_frame, text="Stop Process", command=self._stop_process)
        stop_button.grid(row=0, column=1, sticky='w', padx=5)
        save_output_button = ttk.Button(button_frame, text="Save Output", command=self._save_output)
        save_output_button.grid(row=0, column=2, sticky='e')
        row_index += 1

    def _toggle_custom_config(self):
        """Toggle the custom config file entry visibility."""
        if self.use_custom_config_var.get(): self.custom_config_frame.grid()
        else: self.custom_config_frame.grid_remove()

    def _browse_config(self):
        """Browse for a custom config file."""
        filetypes = [("YAML files", "*.yaml;*.yml"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Configuration File", filetypes=filetypes)
        if filename: self.custom_config_path_var.set(filename)

    def _clear_output(self):
        """Clear the output log panel."""
        self.output_log_panel.clear_output()
        self.progress_var.set(0)
        self.status_var.set("Ready")

    def _stop_process(self):
        """Stop the current process."""
        if not self.is_running: return
        if not messagebox.askyesno("Stop Process", "Are you sure you want to stop the current process?"): return
        self.is_running = False
        self.status_var.set("Stopping...")
        self._add_output("Process manually stopped by user.", "warning")

    def _save_output(self):
        """Save the output log content."""
        self.output_log_panel.save_output()

    def _update_progress(self, value, status_text=None):
        """Update the progress bar and status text."""
        self.progress_var.set(value)
        if status_text: self.status_var.set(status_text)
        self.update_idletasks()

    def _add_output(self, text, tag="info"):
        """Add text to the output log panel."""
        self.output_log_panel.add_output(text, tag)
        self.update_idletasks() # Ensure UI updates

    def _process_queue(self):
        """Process messages from the thread queue."""
        try:
            while True:
                message = self.queue.get_nowait()
                msg_type = message.get('type')
                if msg_type == 'progress':
                    self._update_progress(message['value'], message.get('status'))
                elif msg_type == 'output':
                    self._add_output(message['text'], message.get('tag', 'info'))
                elif msg_type == 'complete':
                    self._process_complete(message.get('success', True), message.get('message'), message.get('results', []))
                self.queue.task_done()
        except queue.Empty:
            if self.is_running: self.after(100, self._process_queue) # Check again later

    def _process_complete(self, success, message=None, results=None):
        """Handle process completion."""
        self.is_running = False
        status_msg = "Complete" if success else "Failed"
        status_tag = "success" if success else "error"
        self._update_progress(100 if success else 0, status_msg)
        self._add_output(message or f"Process {status_msg.lower()}.", status_tag)
        self.current_results = results if results is not None else []
        self.event_generate("<<ProcessComplete>>", when="tail") # Notify listeners

    def _run_process(self, simulation=True):
        """Start the organization process in a separate thread."""
        self._clear_output() # Clear previous output
        self._update_progress(0, "Starting...")
        self.is_running = True
        self.after(100, self._process_queue) # Start queue polling
        thread = threading.Thread(target=self._thread_process, args=(simulation,), daemon=True)
        thread.start()

    def _thread_process(self, simulation):
        """The actual process run in the thread."""
        try:
            action_text = "simulation" if simulation else "organization process"
            self.queue.put({'type': 'output', 'text': f"Starting {action_text}...", 'tag': 'heading'})

            config_path_to_use = None
            if self.use_custom_config_var.get():
                config_path_to_use = self.custom_config_path_var.get()
                if not config_path_to_use or not os.path.exists(config_path_to_use):
                    raise ValueError("Custom config file path is invalid or file does not exist.")

            if self.organize_runner:
                # Use the provided runner (preferred)
                result = self.organize_runner.run(
                    simulation=simulation,
                    progress_callback=self._thread_progress_callback,
                    output_callback=self._thread_output_callback,
                    config_path=config_path_to_use,
                    verbose=self.verbose_var.get()
                )
                self.queue.put({'type': 'complete', **result}) # Pass runner result directly
            else:
                # Fallback to subprocess (less detailed feedback)
                self._run_organize_command(simulation)

        except Exception as e:
            self.queue.put({'type': 'output', 'text': f"Error during process: {str(e)}", 'tag': 'error'})
            self.queue.put({'type': 'complete', 'success': False, 'message': "Process failed due to an error."})

    def _run_organize_command(self, simulation):
        """Fallback: Run the organize command using subprocess."""
        # This method remains largely the same, but uses self.queue.put for output/progress
        try:
            config = self._get_current_config()
            if not config: raise ValueError("No configuration available.")

            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
                temp_path = temp_file.name
                yaml.dump(config, temp_file, default_flow_style=False, sort_keys=False, indent=2)

            try:
                cmd = ['organize'] + (['sim'] if simulation else ['run']) + [temp_path]
                if self.verbose_var.get(): cmd.append('--verbose')
                self.queue.put({'type': 'output', 'text': f"Running command: {' '.join(cmd)}", 'tag': 'info'})

                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True, bufsize=1, encoding='utf-8')

                results = []
                # Simplified output processing for subprocess fallback
                for line in iter(process.stdout.readline, ''):
                    if not self.is_running: process.terminate(); break
                    line_strip = line.strip()
                    if line_strip:
                        tag = 'info'
                        if line_strip.startswith("Moving"): tag = 'move'
                        elif line_strip.startswith("Error"): tag = 'error'
                        elif line_strip.startswith("Rule") or "Simulation mode" in line_strip: tag = 'heading'
                        self.queue.put({'type': 'output', 'text': line_strip, 'tag': tag})
                        # Basic result parsing (less reliable than runner)
                        if tag == 'move':
                             match = re.search(r'Moving\s+"(.*)"\s+to\s+"(.*)"', line_strip)
                             if match: results.append({'source': match.group(1), 'destination': match.group(2), 'status': "Moved" if not simulation else "Would move", 'rule': "Unknown"})

                stderr_output = process.stderr.read()
                if stderr_output: self.queue.put({'type': 'output', 'text': f"STDERR:\n{stderr_output.strip()}", 'tag': 'error'})

                process.wait()
                success = process.returncode == 0
                message = f"{'Simulation' if simulation else 'Organization'} {'completed successfully' if success else 'failed'}."
                if not success: message += f" (Code: {process.returncode})"
                self.queue.put({'type': 'complete', 'success': success, 'message': message, 'results': results})

            finally:
                try: os.unlink(temp_path)
                except OSError: pass
        except Exception as e:
             # Ensure exceptions in this fallback are also reported
             self.queue.put({'type': 'output', 'text': f"Error running command: {str(e)}", 'tag': 'error'})
             self.queue.put({'type': 'complete', 'success': False, 'message': "Process failed due to command error."})


    def _get_current_config(self):
        """Get the current configuration from the parent application or custom path."""
        # If using custom config, load it directly
        if self.use_custom_config_var.get():
            custom_path = self.custom_config_path_var.get()
            if custom_path and os.path.exists(custom_path):
                try:
                    with open(custom_path, 'r', encoding='utf-8') as f: return yaml.safe_load(f)
                except Exception as load_err: raise ValueError(f"Error loading custom config '{custom_path}': {load_err}") from load_err
            else: raise ValueError(f"Custom config file not found: {custom_path}")

        # Otherwise, try to get from ConfigPanel via event (less direct)
        # This part might need adjustment based on how main_window handles the event
        try:
            # Attempt to find ConfigPanel directly if within the same notebook
            parent_notebook = self.nametowidget(self.winfo_parent())
            if isinstance(parent_notebook, ttk.Notebook):
                 for tab_id in parent_notebook.tabs():
                     tab = parent_notebook.nametowidget(tab_id)
                     if hasattr(tab, 'get_current_config') and "config" in str(tab).lower():
                          return tab.get_current_config(from_editor=True) # Get from editor

            # Fallback: Use config manager if available (might be slightly out of sync with editor)
            if self.organize_runner and hasattr(self.organize_runner, 'config_manager') and self.organize_runner.config_manager:
                 return self.organize_runner.config_manager.config

            # Last resort: Ask main window (implementation dependent)
            self.event_generate("<<RequestConfig>>")
            print("Warning: Requesting config via event, might not be immediate.")
            return None # Cannot guarantee immediate return via event

        except Exception as e:
            print(f"Error getting configuration: {e}")
            return None


    def _thread_progress_callback(self, value, status=None):
        """Callback for progress updates from the thread."""
        self.queue.put({'type': 'progress', 'value': value, 'status': status})

    def _thread_output_callback(self, text, tag="info"):
        """Callback for output updates from the thread."""
        self.queue.put({'type': 'output', 'text': text, 'tag': tag})

    # --- Public methods ---
    def run_simulation(self):
        """Run the organization process in simulation mode."""
        if self.is_running: messagebox.showwarning("Process Running", "A process is already running."); return
        self._run_process(simulation=True)

    def run_organization(self):
        """Run the actual organization process."""
        if self.is_running: messagebox.showwarning("Process Running", "A process is already running."); return
        if not messagebox.askyesno("Run Organization", "Run the organization process? Files will be moved."): return
        self._run_process(simulation=False)

    def get_results(self):
        """Get the results from the last run."""
        return self.current_results
