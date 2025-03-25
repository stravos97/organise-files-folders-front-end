"""
Enhanced Preview and Run panel for the File Organization System.

This implementation provides a complete interface for simulating and running
the file organization process, with real-time feedback and progress tracking.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import datetime
import subprocess
import tempfile
import yaml
import re

class PreviewPanel(ttk.Frame):
    """Enhanced panel for previewing and running the organization process."""
    
    def __init__(self, parent, organize_runner=None):
        """Initialize the preview panel."""
        super().__init__(parent)
        
        # Initialize the organize runner
        self.organize_runner = organize_runner
        
        # Process state
        self.is_running = False
        
        # Queue for thread communication
        self.queue = queue.Queue()
        
        # Result tracking
        self.current_results = []
        
        # Create the UI components
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI components for the preview panel."""
        # Main layout container
        main_frame = ttk.Frame(self, padding=(10, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Actions frame
        actions_frame = ttk.LabelFrame(main_frame, text="Actions", padding=(10, 5))
        actions_frame.pack(fill=tk.X, pady=5)
        
        # Action buttons
        sim_button = ttk.Button(
            actions_frame, 
            text="Run Simulation", 
            command=self.run_simulation,
            width=20
        )
        sim_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        run_button = ttk.Button(
            actions_frame, 
            text="Run Organization", 
            command=self.run_organization,
            width=20
        )
        run_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding=(10, 5))
        options_frame.pack(fill=tk.X, pady=5)
        
        # Verbose output option
        self.verbose_var = tk.BooleanVar(value=True)
        verbose_check = ttk.Checkbutton(
            options_frame,
            text="Verbose Output",
            variable=self.verbose_var
        )
        verbose_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Custom config option
        self.custom_config_var = tk.BooleanVar(value=False)
        custom_config_check = ttk.Checkbutton(
            options_frame,
            text="Use Custom Config File",
            variable=self.custom_config_var,
            command=self._toggle_custom_config
        )
        custom_config_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Custom config path
        self.custom_config_frame = ttk.Frame(options_frame)
        self.custom_config_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        self.custom_config_var = tk.StringVar()
        self.custom_config_entry = ttk.Entry(self.custom_config_frame, textvariable=self.custom_config_var, width=30)
        self.custom_config_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.custom_config_button = ttk.Button(self.custom_config_frame, text="Browse...", command=self._browse_config)
        self.custom_config_button.pack(side=tk.LEFT)
        
        # Hide custom config path initially
        self.custom_config_frame.pack_forget()
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=(10, 5))
        progress_frame.pack(fill=tk.X, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            orient=tk.HORIZONTAL, 
            length=100, 
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, pady=5)
        
        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding=(10, 5))
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Output text with scrollbars
        output_frame_inner = ttk.Frame(output_frame)
        output_frame_inner.pack(fill=tk.BOTH, expand=True)
        
        y_scrollbar = ttk.Scrollbar(output_frame_inner)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scrollbar = ttk.Scrollbar(output_frame_inner, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.output_text = tk.Text(
            output_frame_inner, 
            wrap=tk.NONE, 
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
            height=20
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        y_scrollbar.config(command=self.output_text.yview)
        x_scrollbar.config(command=self.output_text.xview)
        
        # Tag configuration for colored output
        self.output_text.tag_config("info", foreground="#000000")  # Black
        self.output_text.tag_config("success", foreground="#008800")  # Green
        self.output_text.tag_config("warning", foreground="#FF8800")  # Orange
        self.output_text.tag_config("error", foreground="#FF0000")  # Red
        self.output_text.tag_config("move", foreground="#0000FF")  # Blue
        self.output_text.tag_config("echo", foreground="#888888")  # Gray
        self.output_text.tag_config("heading", font=("", 10, "bold"))  # Bold
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        clear_button = ttk.Button(
            button_frame, 
            text="Clear Output", 
            command=self._clear_output
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        stop_button = ttk.Button(
            button_frame, 
            text="Stop Process", 
            command=self._stop_process
        )
        stop_button.pack(side=tk.LEFT, padx=5)
        
        save_output_button = ttk.Button(
            button_frame, 
            text="Save Output", 
            command=self._save_output
        )
        save_output_button.pack(side=tk.RIGHT, padx=5)
    
    def _toggle_custom_config(self):
        """Toggle the custom config file entry."""
        if self.custom_config_var.get():
            self.custom_config_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        else:
            self.custom_config_frame.pack_forget()
    
    def _browse_config(self):
        """Browse for a custom config file."""
        filetypes = [("YAML files", "*.yaml"), ("All files", "*.*")]
        filename = tk.filedialog.askopenfilename(
            title="Select Configuration File", 
            filetypes=filetypes
        )
        if filename:
            self.custom_config_var.set(filename)
    
    def _clear_output(self):
        """Clear the output text."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # Reset progress
        self.progress_var.set(0)
        self.status_var.set("Ready")
    
    def _stop_process(self):
        """Stop the current process."""
        if not self.is_running:
            return
        
        # Confirm stop
        if not messagebox.askyesno("Stop Process", 
                                  "Are you sure you want to stop the current process?"):
            return
        
        # Set state to not running
        self.is_running = False
        
        # Update status
        self.status_var.set("Stopping...")
        
        # Add message to output
        self._add_output("Process manually stopped by user.", "warning")
        
        # The process will check self.is_running and stop on the next iteration
    
    def _save_output(self):
        """Save the output text to a file."""
        filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
        filename = tk.filedialog.asksaveasfilename(
            title="Save Output", 
            filetypes=filetypes,
            defaultextension=".txt"
        )
        if filename:
            try:
                output_text = self.output_text.get("1.0", tk.END)
                with open(filename, "w") as f:
                    f.write(output_text)
                messagebox.showinfo("Save Output", f"Output saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save output: {str(e)}")
    
    def _update_progress(self, value, status_text=None):
        """Update the progress bar and status text."""
        self.progress_var.set(value)
        if status_text:
            self.status_var.set(status_text)
        
        # Force UI update
        self.update_idletasks()
    
    def _add_output(self, text, tag="info"):
        """Add text to the output area with the specified tag."""
        self.output_text.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.output_text.insert(tk.END, f"[{timestamp}] ", "info")
        
        # Add the message with the specified tag
        self.output_text.insert(tk.END, f"{text}\n", tag)
        
        # Scroll to the bottom
        self.output_text.see(tk.END)
        
        # Disable text widget again
        self.output_text.config(state=tk.DISABLED)
        
        # Force UI update
        self.update_idletasks()
    
    def _process_queue(self):
        """Process messages from the queue."""
        try:
            while True:
                message = self.queue.get_nowait()
                
                if message['type'] == 'progress':
                    self._update_progress(message['value'], message.get('status'))
                elif message['type'] == 'output':
                    self._add_output(message['text'], message.get('tag', 'info'))
                elif message['type'] == 'complete':
                    self._process_complete(message.get('success', True), message.get('message'), message.get('results', []))
                
                self.queue.task_done()
        except queue.Empty:
            # Schedule to check queue again after 100ms
            if self.is_running:
                self.after(100, self._process_queue)
    
    def _process_complete(self, success, message=None, results=None):
        """Handle process completion."""
        self.is_running = False
        
        if success:
            self._update_progress(100, "Complete")
            self._add_output(message or "Process completed successfully.", "success")
        else:
            self._update_progress(0, "Failed")
            self._add_output(message or "Process failed.", "error")
        
        # Store results
        if results:
            self.current_results = results
        
        # Notify that results are available
        self.event_generate("<<ProcessComplete>>", when="tail")
    
    def _run_process(self, simulation=True):
        """Run the organization process in a separate thread."""
        # Clear output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # Reset progress
        self._update_progress(0, "Starting...")
        
        # Set running flag
        self.is_running = True
        
        # Start processing queue
        self.after(100, self._process_queue)
        
        # Start process in a thread
        thread = threading.Thread(
            target=self._thread_process, 
            args=(simulation,), 
            daemon=True
        )
        thread.start()
    
    def _thread_process(self, simulation):
        """Run the organization process in a thread."""
        try:
            # Add initial output
            if simulation:
                self.queue.put({
                    'type': 'output',
                    'text': "Starting simulation...",
                    'tag': 'heading'
                })
            else:
                self.queue.put({
                    'type': 'output',
                    'text': "Starting organization process...",
                    'tag': 'heading'
                })
            
            # Check if we should use the organize runner
            if self.organize_runner:
                # Run using the organize runner
                result = self.organize_runner.run(
                    simulation=simulation,
                    progress_callback=self._thread_progress_callback,
                    output_callback=self._thread_output_callback,
                    config_path=self.custom_config_var.get() if self.custom_config_var.get() else None,
                    verbose=self.verbose_var.get()
                )
                
                # Process complete
                self.queue.put({
                    'type': 'complete',
                    'success': result['success'],
                    'message': result.get('message'),
                    'results': result.get('results', [])
                })
            else:
                # Run using direct subprocess call
                self._run_organize_command(simulation)
        except Exception as e:
            # Handle exceptions
            self.queue.put({
                'type': 'output',
                'text': f"Error: {str(e)}",
                'tag': 'error'
            })
            self.queue.put({
                'type': 'complete',
                'success': False,
                'message': "Process failed due to an error."
            })
    
    def _run_organize_command(self, simulation):
        """Run the organize command using subprocess."""
        try:
            # Get the configuration from the parent application
            config = self._get_current_config()
            
            if not config:
                self.queue.put({
                    'type': 'output',
                    'text': "No configuration available.",
                    'tag': 'error'
                })
                self.queue.put({
                    'type': 'complete',
                    'success': False,
                    'message': "No configuration available."
                })
                return
            
            # Create a temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
                temp_path = temp_file.name
                yaml.dump(config, temp_file, default_flow_style=False, sort_keys=False)
            
            try:
                # Prepare command
                if os.name == 'nt':  # Windows
                    cmd = ['organize.exe']
                else:
                    cmd = ['organize']
                
                # Add simulation/run mode
                if simulation:
                    cmd.append('sim')
                else:
                    cmd.append('run')
                
                # Add config file
                cmd.append(temp_path)
                
                # Add verbose flag if requested
                if self.verbose_var.get():
                    cmd.append('--verbose')
                
                # Log the command
                self.queue.put({
                    'type': 'output',
                    'text': f"Running command: {' '.join(cmd)}",
                    'tag': 'info'
                })
                
                # Start the process
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Process output
                results = []
                file_pattern = re.compile(r'^\s*[✓✗]\s+(.*)')
                move_pattern = re.compile(r'.*Moving\s+"(.*)"\s+to\s+"(.*)"')
                error_pattern = re.compile(r'^\s*Error:.*', re.IGNORECASE)
                
                total_lines = 0
                processed_files = 0
                
                for line in iter(process.stdout.readline, ''):
                    if not self.is_running:
                        # Process manually stopped
                        process.terminate()
                        break
                    
                    total_lines += 1
                    
                    # Extract information from the line
                    file_match = file_pattern.match(line)
                    move_match = move_pattern.match(line)
                    error_match = error_pattern.match(line)
                    
                    if file_match:
                        processed_files += 1
                        file_path = file_match.group(1)
                        
                        # Add to output with appropriate tag
                        self.queue.put({
                            'type': 'output',
                            'text': f"Processing: {file_path}",
                            'tag': 'info'
                        })
                        
                        # Update progress approximation
                        progress = min(processed_files / max(1, processed_files + 100) * 100, 95)
                        self.queue.put({
                            'type': 'progress',
                            'value': progress,
                            'status': f"Processed {processed_files} files..."
                        })
                    
                    elif move_match:
                        source = move_match.group(1)
                        dest = move_match.group(2)
                        
                        # Add to results
                        result = {
                            'source': source,
                            'destination': dest,
                            'status': "Moved" if not simulation else "Would move",
                            'rule': "Unknown"  # We don't get rule info from command line output
                        }
                        results.append(result)
                        
                        # Add to output
                        self.queue.put({
                            'type': 'output',
                            'text': f"{'Would move' if simulation else 'Moving'}: {source} → {dest}",
                            'tag': 'move'
                        })
                    
                    elif error_match:
                        # Add to output
                        self.queue.put({
                            'type': 'output',
                            'text': line.strip(),
                            'tag': 'error'
                        })
                    
                    elif "Simulation mode" in line:
                        # Heading for simulation
                        self.queue.put({
                            'type': 'output',
                            'text': line.strip(),
                            'tag': 'heading'
                        })
                    
                    elif line.startswith("Rule "):
                        # Rule heading
                        self.queue.put({
                            'type': 'output',
                            'text': line.strip(),
                            'tag': 'heading'
                        })
                    
                    else:
                        # Other output
                        line = line.strip()
                        if line:
                            tag = 'info'
                            if line.startswith("Found"):
                                tag = 'echo'
                            
                            self.queue.put({
                                'type': 'output',
                                'text': line,
                                'tag': tag
                            })
                
                # Process any errors from stderr
                for line in iter(process.stderr.readline, ''):
                    if line.strip():
                        self.queue.put({
                            'type': 'output',
                            'text': line.strip(),
                            'tag': 'error'
                        })
                
                # Check return code
                if process.returncode is None:
                    process.wait()
                
                if process.returncode == 0:
                    message = "Simulation completed successfully." if simulation else "Organization completed successfully."
                    self.queue.put({
                        'type': 'complete',
                        'success': True,
                        'message': message,
                        'results': results
                    })
                else:
                    self.queue.put({
                        'type': 'complete',
                        'success': False,
                        'message': f"Process failed with return code {process.returncode}",
                        'results': results
                    })
            
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        
        except Exception as e:
            # Handle exceptions
            self.queue.put({
                'type': 'output',
                'text': f"Error: {str(e)}",
                'tag': 'error'
            })
            self.queue.put({
                'type': 'complete',
                'success': False,
                'message': "Process failed due to an error."
            })
    
    def _get_current_config(self):
        """Get the current configuration from the parent application."""
        # Try to get config from ConfigPanel
        try:
            parent = self.winfo_parent()
            parent_widget = self.nametowidget(parent)
            
            # If parent is notebook, get the current tab
            if isinstance(parent_widget, ttk.Notebook):
                root = parent_widget.winfo_toplevel()
                
                # Find ConfigPanel
                for widget in root.winfo_children():
                    if hasattr(widget, 'get_current_config'):
                        return widget.get_current_config()
            
            # If using custom config, load it directly
            if self.custom_config_var.get() and os.path.exists(self.custom_config_var.get()):
                with open(self.custom_config_var.get(), 'r') as f:
                    return yaml.safe_load(f)
            
            # Try message passing
            self.event_generate("<<RequestConfig>>")
            
            # Default to empty config
            return {'rules': []}
            
        except Exception as e:
            self.queue.put({
                'type': 'output',
                'text': f"Error getting configuration: {str(e)}",
                'tag': 'error'
            })
            return None
    
    def _thread_progress_callback(self, value, status=None):
        """Callback for progress updates from the thread."""
        self.queue.put({
            'type': 'progress',
            'value': value,
            'status': status
        })
    
    def _thread_output_callback(self, text, tag="info"):
        """Callback for output updates from the thread."""
        self.queue.put({
            'type': 'output',
            'text': text,
            'tag': tag
        })
    
    # Public methods
    
    def run_simulation(self):
        """Run the organization process in simulation mode."""
        if self.is_running:
            messagebox.showwarning("Process Running", 
                                  "A process is already running. Please wait for it to complete.")
            return
        
        self._run_process(simulation=True)
    
    def run_organization(self):
        """Run the actual organization process."""
        if self.is_running:
            messagebox.showwarning("Process Running", 
                                  "A process is already running. Please wait for it to complete.")
            return
        
        # Confirm before running
        if not messagebox.askyesno("Run Organization", 
                                  "Are you sure you want to run the organization process? " 
                                  "Files will be moved according to the configuration."):
            return
        
        self._run_process(simulation=False)
    
    def get_results(self):
        """Get the current results."""
        return self.current_results