"""
Utility function for parsing the output stream of the organize-tool process.
"""

import re

def parse_organize_output(stdout_stream, stderr_stream, is_running_flag_func, output_callback, progress_callback, simulation):
    """
    Parses stdout and stderr streams from the organize process.

    Args:
        stdout_stream: The process's stdout stream iterator.
        stderr_stream: The process's stderr stream iterator.
        is_running_flag_func (callable): A function that returns True if the process should continue running.
        output_callback (callable): Function to call with output text (text, tag).
        progress_callback (callable): Function to call with progress updates (value, status).
        simulation (bool): Whether this was a simulation run.

    Returns:
        list: A list of result dictionaries extracted from the output.
    """
    results = []
    # Regex patterns
    file_pattern = re.compile(r'^\s*[✓✗]\s+(.*)') # Matches the line indicating a file is being processed
    rule_pattern = re.compile(r'^\s*Rule\s+"([^"]+)"')
    # Action patterns (match the indented line following a file line)
    move_pattern = re.compile(r'^\s+Moving\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?')
    would_move_pattern = re.compile(r'^\s+Would move\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?')
    copy_pattern = re.compile(r'^\s+Copying\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?')
    would_copy_pattern = re.compile(r'^\s+Would copy\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?') # Added for simulation
    rename_pattern = re.compile(r'^\s+Renaming\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?')
    would_rename_pattern = re.compile(r'^\s+Would rename\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?') # Added for simulation
    delete_pattern = re.compile(r'^\s+Deleting\s+"?([^"]+)"?')
    would_delete_pattern = re.compile(r'^\s+Would delete\s+"?([^"]+)"?') # Added for simulation
    skipped_pattern = re.compile(r'^\s+Skipped\s*(?:\((.*)\))?') # Capture optional reason
    error_pattern = re.compile(r'^\s*Error:.*', re.IGNORECASE)
    echo_pattern = re.compile(r'^\s+echo:\s*(.*)')

    processed_files = 0
    current_rule = ""
    current_source_file = None # Track the file associated with the last ✓/✗

    # Process stdout line by line
    for line in stdout_stream:
        if not is_running_flag_func(): break # Check stop flag

        line_strip = line.strip()
        if not line_strip: continue

        tag = "info" # Default tag
        log_line = True # Whether to pass the line to output_callback

        rule_match = rule_pattern.match(line_strip)
        file_match = file_pattern.match(line_strip)
        error_match = error_pattern.match(line_strip) # Check for global errors first

        if rule_match:
            current_rule = rule_match.group(1)
            # Do NOT reset current_source_file here, wait for action or next file
            tag = "heading"
        elif file_match:
            processed_files += 1
            current_source_file = file_match.group(1) # Store the source file path
            # Log processing message internally, don't show raw ✓/✗ line
            if output_callback: output_callback(f"Processing: {current_source_file}", "info")
            if progress_callback:
                # Estimate progress (this is very approximate)
                progress = min(processed_files / max(1, processed_files + 50) * 100, 98)
                progress_callback(progress, f"Processed {processed_files} files...")
            log_line = False # Don't log the raw ✓/✗ line itself
        elif current_source_file: # Only process action lines if we have a source file context
            # Check for specific actions/statuses
            move_match = move_pattern.match(line) if not simulation else None
            would_move_match = would_move_pattern.match(line) if simulation else None
            copy_match = copy_pattern.match(line) if not simulation else None
            would_copy_match = would_copy_pattern.match(line) if simulation else None
            rename_match = rename_pattern.match(line) if not simulation else None
            would_rename_match = would_rename_pattern.match(line) if simulation else None
            delete_match = delete_pattern.match(line) if not simulation else None
            would_delete_match = would_delete_pattern.match(line) if simulation else None
            skipped_match = skipped_pattern.match(line)
            echo_match = echo_pattern.match(line)
            # Check error again for action-specific errors
            action_error_match = error_pattern.match(line_strip)

            if move_match or would_move_match:
                match = move_match or would_move_match
                # Source might differ slightly if rename happened before move? Use stored one.
                dest = match.group(2)
                status = "Moved" if not simulation else "Would move"
                results.append({'source': current_source_file, 'destination': dest, 'status': status, 'rule': current_rule})
                tag = "move"
                current_source_file = None # Reset after processing action
            elif copy_match or would_copy_match:
                match = copy_match or would_copy_match
                dest = match.group(2)
                status = "Copied" if not simulation else "Would copy"
                results.append({'source': current_source_file, 'destination': dest, 'status': status, 'rule': current_rule})
                tag = "copy"
                current_source_file = None # Reset after processing action
            elif rename_match or would_rename_match:
                match = rename_match or would_rename_match
                dest = match.group(2) # Destination is the new name/path
                status = "Renamed" if not simulation else "Would rename"
                results.append({'source': current_source_file, 'destination': dest, 'status': status, 'rule': current_rule})
                tag = "rename"
                current_source_file = None # Reset after processing action
            elif delete_match or would_delete_match:
                match = delete_match or would_delete_match
                status = "Deleted" if not simulation else "Would delete"
                results.append({'source': current_source_file, 'destination': None, 'status': status, 'rule': current_rule})
                tag = "delete"
                current_source_file = None # Reset after processing action
            elif skipped_match:
                status = "Skipped"
                # reason = skipped_match.group(1) # Optional reason
                results.append({'source': current_source_file, 'destination': None, 'status': status, 'rule': current_rule})
                tag = "skipped"
                current_source_file = None # Reset after processing action
            elif action_error_match: # Handle errors associated with the current file
                tag = "error"
                results.append({'source': current_source_file, 'status': "Error", 'rule': current_rule})
                current_source_file = None # Reset after processing action
            elif echo_match:
                tag = "echo"
                # Don't add echo to results, just log it
                current_source_file = None # Reset after processing action
            else:
                # If an indented line doesn't match known patterns, treat as info
                tag = "info"
                # Don't reset current_source_file here, might be multi-line info
        elif error_match: # Handle global errors not tied to a specific file
             tag = "error"
             # Don't add to results unless we can associate with a file
        elif "simulating" in line_strip.lower() or "simulation" in line_strip.lower():
             tag = "heading"
        # Fallback for lines not matching specific patterns but maybe useful info
        else:
             tag = "info"


        if log_line and output_callback:
            output_callback(line_strip, tag)

    # Process any remaining stderr only if the stream exists
    if stderr_stream:
        try:
            stderr_output = "".join(stderr_stream) # Read all remaining stderr
            if stderr_output.strip() and output_callback:
                output_callback(f"STDERR:\n{stderr_output.strip()}", "error")
        except TypeError:
             # Handle cases where stderr_stream might not be iterable as expected
             if output_callback: output_callback("Warning: Could not process stderr stream.", "warning")


    # Final progress update (might be called again by caller, but good fallback)
    if progress_callback: progress_callback(100, "Parsing complete")

    return results
