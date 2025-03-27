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
    file_pattern = re.compile(r'^\s*[✓✗]\s+(.*)')
    move_pattern = re.compile(r'.*Moving\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?')
    would_move_pattern = re.compile(r'.*Would move\s+"?([^"]+)"?\s+to\s+"?([^"]+)"?')
    error_pattern = re.compile(r'^\s*Error:.*', re.IGNORECASE)
    rule_pattern = re.compile(r'^\s*Rule\s+"([^"]+)"')
    processed_files = 0
    current_rule = ""

    # Process stdout line by line
    for line in stdout_stream:
        if not is_running_flag_func(): break # Check stop flag

        line_strip = line.strip()
        if not line_strip: continue

        rule_match = rule_pattern.match(line_strip)
        file_match = file_pattern.match(line_strip)
        move_match = move_pattern.match(line_strip) if not simulation else None
        would_move_match = would_move_pattern.match(line_strip) if simulation else None
        error_match = error_pattern.match(line_strip)

        tag = "info" # Default tag

        if rule_match:
            current_rule = rule_match.group(1)
            tag = "heading"
        elif file_match:
            processed_files += 1
            file_path = file_match.group(1)
            if output_callback: output_callback(f"Processing: {file_path}", "info")
            if progress_callback:
                progress = min(processed_files / max(1, processed_files + 50) * 100, 98)
                progress_callback(progress, f"Processed {processed_files} files...")
            continue # Don't log the raw ✓/✗ line
        elif move_match or would_move_match:
            match = move_match or would_move_match
            source, dest = match.group(1), match.group(2)
            status = "Moved" if not simulation else "Would move"
            results.append({'source': source, 'destination': dest, 'status': status, 'rule': current_rule})
            tag = "move"
        elif error_match:
            tag = "error"
            path_match = re.search(r'"([^"]+)"', line_strip)
            if path_match: results.append({'source': path_match.group(1), 'status': "Error", 'rule': current_rule})
        elif "simulating" in line_strip.lower() or "simulation" in line_strip.lower():
            tag = "heading"
        elif "echo:" in line_strip.lower():
            tag = "echo"

        if output_callback: output_callback(line_strip, tag)

    # Process any remaining stderr
    stderr_output = "".join(stderr_stream) # Read all remaining stderr
    if stderr_output.strip() and output_callback:
        output_callback(f"STDERR:\n{stderr_output.strip()}", "error")

    # Final progress update (might be called again by caller, but good fallback)
    if progress_callback: progress_callback(100, "Parsing complete")

    return results
