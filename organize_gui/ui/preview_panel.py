"""
Preview and Run panel for the File Organization System.

This module defines the UI components for simulating and running the
file organization process, as well as scheduling automated runs.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import datetime

from core.organize_runner import OrganizeRunner

class PreviewPanel(ttk.Frame):
    """Panel for previewing and running the organization process."""
    
    def __init__(self, parent):
        """Initialize the preview panel."""
        super().__init__(parent)
        
        # Create the organize runner
        self.organize_runner = OrganizeRunner()
        
        # Queue for thread communication
        self.queue = queue.Queue()
        
        # Current process state
        self.is_running = False
        
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
        
        schedule_button = ttk.Button(
            actions_frame, 
            text="Schedule...", 
            command=self._show_schedule_dialog,
            width=15
        )
        schedule_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
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
        
        # Output text with scrollbar
        output_scroll = ttk.Scrollbar(output_frame)
        output_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output_text = tk.Text(
            output_frame, 
            wrap=tk.WORD, 
            yscrollcommand=output_scroll.set,
            height=20
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        output_scroll.config(command=self.output_text.yview)
        
        # Tag configuration for colored output
        self.output_text.tag_config("info", foreground="black")
        self.output_text.tag_config("success", foreground="green")
        self.output_text.tag_config("warning", foreground="orange")
        self.output_text.tag_config("error", foreground="red")
    
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
                    self._process_complete(message.get('success', True), message.get('message'))
                
                self.queue.task_done()
        except queue.Empty:
            # Schedule to check queue again after 100ms
            if self.is_running:
                self.after(100, self._process_queue)
    
    def _process_complete(self, success, message=None):
        """Handle process completion."""
        self.is_running = False
        
        if success:
            self._update_progress(100, "Complete")
            self._add_output(message or "Process completed successfully.", "success")
        else:
            self._update_progress(0, "Failed")
            self._add_output(message or "Process failed.", "error")
        
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
                    'tag': 'info'
                })
            else:
                self.queue.put({
                    'type': 'output',
                    'text': "Starting organization process...",
                    'tag': 'info'
                })
            
            # Run the process
            result = self.organize_runner.run(
                simulation=simulation,
                progress_callback=self._thread_progress_callback,
                output_callback=self._thread_output_callback
            )
            
            # Process complete
            self.queue.put({
                'type': 'complete',
                'success': result['success'],
                'message': result.get('message')
            })
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
    
    def _show_schedule_dialog(self):
        """Show the scheduling dialog."""
        # Create a top-level window
        dialog = tk.Toplevel(self)
        dialog.title("Schedule Organization")
        dialog.geometry("400x300")
        dialog.transient(self)  # Make dialog modal
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scheduling options
        ttk.Label(main_frame, text="Schedule Type:").pack(anchor=tk.W, pady=(10, 5))
        
        schedule_var = tk.StringVar(value="daily")
        schedule_frame = ttk.Frame(main_frame)
        schedule_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(
            schedule_frame, 
            text="Daily", 
            variable=schedule_var, 
            value="daily"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            schedule_frame, 
            text="Weekly", 
            variable=schedule_var, 
            value="weekly"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            schedule_frame, 
            text="Monthly", 
            variable=schedule_var, 
            value="monthly"
        ).pack(side=tk.LEFT)
        
        # Time selection
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(time_frame, text="Run at:").pack(side=tk.LEFT)
        
        hour_var = tk.StringVar(value="02")
        hour_combo = ttk.Combobox(
            time_frame, 
            textvariable=hour_var,
            values=[f"{h:02d}" for h in range(24)],
            width=3,
            state="readonly"
        )
        hour_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        
        minute_var = tk.StringVar(value="00")
        minute_combo = ttk.Combobox(
            time_frame, 
            textvariable=minute_var,
            values=[f"{m:02d}" for m in range(0, 60, 5)],
            width=3,
            state="readonly"
        )
        minute_combo.pack(side=tk.LEFT, padx=5)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding=(10, 5))
        options_frame.pack(fill=tk.X, pady=10)
        
        simulation_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Run in simulation mode (no actual changes)",
            variable=simulation_var
        ).pack(anchor=tk.W, pady=5)
        
        notify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Notify when complete",
            variable=notify_var
        ).pack(anchor=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Schedule",
            command=lambda: self._schedule_task(
                schedule_var.get(),
                f"{hour_var.get()}:{minute_var.get()}",
                simulation_var.get(),
                notify_var.get(),
                dialog
            ),
            width=10
        ).pack(side=tk.RIGHT, padx=5)
    
    def _schedule_task(self, schedule_type, time, simulation, notify, dialog):
        """Schedule a task with the provided options."""
        # In a real implementation, this would create a scheduled task
        # using the system's scheduler (cron, Task Scheduler, etc.)
        
        # Close the dialog
        dialog.destroy()
        
        # Display confirmation
        message = f"Organization scheduled to run {schedule_type} at {time}."
        if simulation:
            message += " (Simulation mode)"
        
        messagebox.showinfo("Task Scheduled", message)
        
        # Add info to output
        self._add_output(f"Scheduled: {message}", "info")
    
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