import pytest
from unittest.mock import Mock, call

# Assuming the function is in organize_gui.core.output_parser
from organize_gui.core.output_parser import parse_organize_output

# --- Tests for parse_organize_output ---

def test_parse_simulation_output_basic():
    """ Test parsing a simple simulation output. """
    stdout_lines = [
        "Simulating...",
        "Rule \"Move Docs\"",
        "✓ /path/to/doc1.txt",
        "  Would move \"/path/to/doc1.txt\" to \"/dest/Docs/doc1.txt\"",
        "✓ /path/to/image.jpg",
        "Rule \"Move Images\"",
        "  Would move \"/path/to/image.jpg\" to \"/dest/Images/image.jpg\"",
        "Simulation finished.",
    ]
    stderr_lines = []
    mock_output_callback = Mock()
    mock_progress_callback = Mock()
    is_running_flag_func = lambda: True # Always true for this test

    results = parse_organize_output(
        iter(stdout_lines),
        iter(stderr_lines),
        is_running_flag_func,
        mock_output_callback,
        mock_progress_callback,
        simulation=True
    )

    # Check returned results list
    expected_results = [
        {'source': '/path/to/doc1.txt', 'destination': '/dest/Docs/doc1.txt', 'status': 'Would move', 'rule': 'Move Docs'},
        {'source': '/path/to/image.jpg', 'destination': '/dest/Images/image.jpg', 'status': 'Would move', 'rule': 'Move Images'}
    ]
    assert results == expected_results

    # Check calls to output_callback (excluding file processing lines)
    expected_output_calls = [
        call("Simulating...", "heading"),
        call("Rule \"Move Docs\"", "heading"),
        # ✓ /path/to/doc1.txt -> triggers internal callback, not this one directly
        call("Would move \"/path/to/doc1.txt\" to \"/dest/Docs/doc1.txt\"", "move"),
        # ✓ /path/to/image.jpg -> triggers internal callback, not this one directly
        call("Rule \"Move Images\"", "heading"),
        call("Would move \"/path/to/image.jpg\" to \"/dest/Images/image.jpg\"", "move"),
        call("Simulation finished.", "heading"), # Contains "simulation" -> heading tag
    ]
    # Filter out the internal "Processing:" calls made by the parser itself
    actual_output_calls = [c for c in mock_output_callback.call_args_list if not c.args[0].startswith("Processing:")]
    assert actual_output_calls == expected_output_calls

    # Check calls to progress_callback (approximate check)
    assert mock_progress_callback.call_count >= 2 # Should be called for each file + final
    # Check the final call
    mock_progress_callback.assert_called_with(100, "Parsing complete")


def test_parse_real_run_output():
    """ Test parsing output from a real run (not simulation). """
    stdout_lines = [
        "Rule \"Move Videos\"",
        "✓ /path/to/vid1.mp4",
        "  Moving \"/path/to/vid1.mp4\" to \"/dest/Videos/vid1.mp4\"",
        "✓ /path/to/vid2.mkv",
        "  Moving \"/path/to/vid2.mkv\" to \"/dest/Videos/vid2.mkv\"",
    ]
    stderr_lines = []
    mock_output_callback = Mock()
    mock_progress_callback = Mock()
    is_running_flag_func = lambda: True

    results = parse_organize_output(
        iter(stdout_lines), iter(stderr_lines), is_running_flag_func,
        mock_output_callback, mock_progress_callback, simulation=False
    )

    expected_results = [
        {'source': '/path/to/vid1.mp4', 'destination': '/dest/Videos/vid1.mp4', 'status': 'Moved', 'rule': 'Move Videos'},
        {'source': '/path/to/vid2.mkv', 'destination': '/dest/Videos/vid2.mkv', 'status': 'Moved', 'rule': 'Move Videos'}
    ]
    assert results == expected_results

    expected_output_calls = [
        call("Rule \"Move Videos\"", "heading"),
        call("Moving \"/path/to/vid1.mp4\" to \"/dest/Videos/vid1.mp4\"", "move"),
        call("Moving \"/path/to/vid2.mkv\" to \"/dest/Videos/vid2.mkv\"", "move"),
    ]
    actual_output_calls = [c for c in mock_output_callback.call_args_list if not c.args[0].startswith("Processing:")]
    assert actual_output_calls == expected_output_calls
    mock_progress_callback.assert_called_with(100, "Parsing complete")


def test_parse_output_with_errors():
    """ Test parsing output containing errors. """
    stdout_lines = [
        "Rule \"Cleanup\"",
        "✓ /path/to/file.tmp",
        "  Error: Could not delete file \"/path/to/file.tmp\" - Permission denied",
        "✗ /path/to/other.tmp", # File pattern with error marker
    ]
    stderr_lines = ["Some error occurred on stderr"]
    mock_output_callback = Mock()
    mock_progress_callback = Mock()
    is_running_flag_func = lambda: True

    results = parse_organize_output(
        iter(stdout_lines), iter(stderr_lines), is_running_flag_func,
        mock_output_callback, mock_progress_callback, simulation=False
    )

    # Check results list includes the error
    expected_results = [
        {'source': '/path/to/file.tmp', 'status': 'Error', 'rule': 'Cleanup'}
    ]
    assert results == expected_results

    # Check output callback includes error lines and stderr
    expected_output_calls = [
        call("Rule \"Cleanup\"", "heading"),
        call("Error: Could not delete file \"/path/to/file.tmp\" - Permission denied", "error"),
        call("STDERR:\nSome error occurred on stderr", "error"),
    ]
    # Filter out "Processing:" calls
    actual_output_calls = [c for c in mock_output_callback.call_args_list if not c.args[0].startswith("Processing:")]
    # Check if expected calls are a subset of actual calls (order might vary slightly with stderr)
    for expected_call in expected_output_calls:
         assert expected_call in actual_output_calls, f"Expected call not found: {expected_call}"

    mock_progress_callback.assert_called_with(100, "Parsing complete")


def test_parse_output_with_echo():
    """ Test parsing output containing echo actions. """
    stdout_lines = [
        "Rule \"Notify\"",
        "✓ /path/to/report.pdf",
        "  echo: Processed report.pdf",
    ]
    stderr_lines = []
    mock_output_callback = Mock()
    mock_progress_callback = Mock()
    is_running_flag_func = lambda: True

    results = parse_organize_output(
        iter(stdout_lines), iter(stderr_lines), is_running_flag_func,
        mock_output_callback, mock_progress_callback, simulation=False
    )

    assert results == [] # Echo doesn't add to results list

    expected_output_calls = [
        call("Rule \"Notify\"", "heading"),
        call("echo: Processed report.pdf", "echo"),
    ]
    actual_output_calls = [c for c in mock_output_callback.call_args_list if not c.args[0].startswith("Processing:")]
    assert actual_output_calls == expected_output_calls
    mock_progress_callback.assert_called_with(100, "Parsing complete")


def test_parse_output_stops_when_flag_is_false():
    """ Test that parsing stops when is_running_flag_func returns False. """
    stdout_lines = [
        "Rule \"Rule 1\"",
        "✓ file1.txt",
        "  Moving \"file1.txt\" to \"dest/file1.txt\"", # Should process this
        "Rule \"Rule 2\"", # Should stop before processing this rule
        "✓ file2.txt",
        "  Moving \"file2.txt\" to \"dest/file2.txt\"",
    ]
    stderr_lines = []
    mock_output_callback = Mock()
    mock_progress_callback = Mock()

    # Flag function that returns False after the first rule is processed
    call_count = 0
    def is_running_flag_func():
        nonlocal call_count
        call_count += 1
        return call_count <= 3 # Allow Simulating, Rule, ✓, Moving lines

    results = parse_organize_output(
        iter(stdout_lines), iter(stderr_lines), is_running_flag_func,
        mock_output_callback, mock_progress_callback, simulation=False
    )

    # Only the first move should be in results
    expected_results = [
        {'source': 'file1.txt', 'destination': 'dest/file1.txt', 'status': 'Moved', 'rule': 'Rule 1'}
    ]
    assert results == expected_results

    # Check that output callback only received calls for the first part
    expected_output_calls = [
        call("Rule \"Rule 1\"", "heading"),
        call("Moving \"file1.txt\" to \"dest/file1.txt\"", "move"),
    ]
    actual_output_calls = [c for c in mock_output_callback.call_args_list if not c.args[0].startswith("Processing:")]
    assert actual_output_calls == expected_output_calls

    # Progress might not reach 100 if stopped early
    assert mock_progress_callback.called

def test_parse_copy_action():
    """ Test parsing output for copy actions. """
    stdout_lines = [
        "Rule \"Copy Reports\"",
        "✓ /path/to/report_v1.pdf",
        "  Copying \"/path/to/report_v1.pdf\" to \"/dest/Reports/report_v1.pdf\"",
    ]
    mock_output_callback = Mock()
    results = parse_organize_output(iter(stdout_lines), iter([]), lambda: True, mock_output_callback, None, simulation=False)
    expected_results = [{'source': '/path/to/report_v1.pdf', 'destination': '/dest/Reports/report_v1.pdf', 'status': 'Copied', 'rule': 'Copy Reports'}]
    assert results == expected_results
    # Check callback tag (assuming 'copy' tag will be added)
    actual_output_calls = [c for c in mock_output_callback.call_args_list if not c.args[0].startswith("Processing:")]
    assert call("Copying \"/path/to/report_v1.pdf\" to \"/dest/Reports/report_v1.pdf\"", "copy") in actual_output_calls

def test_parse_rename_action():
    """ Test parsing output for rename actions. """
    stdout_lines = [
        "Rule \"Rename Images\"",
        "✓ /path/to/IMG_001.jpg",
        "  Renaming \"/path/to/IMG_001.jpg\" to \"/path/to/Vacation_001.jpg\"",
    ]
    mock_output_callback = Mock()
    results = parse_organize_output(iter(stdout_lines), iter([]), lambda: True, mock_output_callback, None, simulation=False)
    expected_results = [{'source': '/path/to/IMG_001.jpg', 'destination': '/path/to/Vacation_001.jpg', 'status': 'Renamed', 'rule': 'Rename Images'}]
    assert results == expected_results
    # Check callback tag (assuming 'rename' tag will be added)
    actual_output_calls = [c for c in mock_output_callback.call_args_list if not c.args[0].startswith("Processing:")]
    assert call("Renaming \"/path/to/IMG_001.jpg\" to \"/path/to/Vacation_001.jpg\"", "rename") in actual_output_calls

def test_parse_delete_action():
    """ Test parsing output for delete actions. """
    stdout_lines = [
        "Rule \"Delete Temp Files\"",
        "✓ /path/to/old.tmp",
        "  Deleting \"/path/to/old.tmp\"",
    ]
    mock_output_callback = Mock()
    results = parse_organize_output(iter(stdout_lines), iter([]), lambda: True, mock_output_callback, None, simulation=False)
    expected_results = [{'source': '/path/to/old.tmp', 'destination': None, 'status': 'Deleted', 'rule': 'Delete Temp Files'}]
    assert results == expected_results
     # Check callback tag (assuming 'delete' tag will be added)
    actual_output_calls = [c for c in mock_output_callback.call_args_list if not c.args[0].startswith("Processing:")]
    assert call("Deleting \"/path/to/old.tmp\"", "delete") in actual_output_calls

def test_parse_skipped_status():
    """ Test parsing output for skipped files. """
    stdout_lines = [
        "Rule \"Move Important\"",
        "✓ /path/to/file.txt",
        "  Skipped (conflict)", # Example skipped message
    ]
    mock_output_callback = Mock()
    results = parse_organize_output(iter(stdout_lines), iter([]), lambda: True, mock_output_callback, None, simulation=False)
    expected_results = [{'source': '/path/to/file.txt', 'destination': None, 'status': 'Skipped', 'rule': 'Move Important'}]
    assert results == expected_results
    # Check callback tag (assuming 'skipped' tag will be added)
    actual_output_calls = [c for c in mock_output_callback.call_args_list if not c.args[0].startswith("Processing:")]
    assert call("Skipped (conflict)", "skipped") in actual_output_calls


# Finished testing output_parser.py
