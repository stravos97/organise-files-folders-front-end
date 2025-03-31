import pytest
import os
import sys
import subprocess
import platform
import importlib # Needed for module import
from unittest.mock import patch, MagicMock, ANY

# Assuming OrganizeRunner is in organize_gui.core.organize_runner
from organize_gui.core.organize_runner import OrganizeRunner
import organize_gui.core.organize_runner # Import the module itself for patching __file__

# --- Tests for OrganizeRunner ---

@patch.object(OrganizeRunner, '_find_organize_command', return_value='/mock/path/to/organize')
@patch.object(OrganizeRunner, '_find_organize_script', return_value='/mock/path/to/script.sh')
def test_organize_runner_init(mock_find_script, mock_find_command):
    """ Test the basic initialization of OrganizeRunner. """
    # Pass a mock config_manager or None
    mock_config_manager = MagicMock()
    runner = OrganizeRunner(config_manager=mock_config_manager)

    assert runner.organize_cmd == '/mock/path/to/organize'
    assert runner.script_path == '/mock/path/to/script.sh'
    assert runner.is_running is False
    assert runner.current_process is None
    assert runner.config_manager == mock_config_manager
    mock_find_command.assert_called_once()
    mock_find_script.assert_called_once()


# --- Tests for _find_organize_command ---

@pytest.mark.parametrize(
    "os_name_param, which_where_rc, which_where_output, sys_executable_param, scripts_exist, bin_exist, usr_local_exist, expected_cmd",
    [
        # Found via which (Unix)
        ("posix", 0, "/usr/bin/organize\n", "/usr/py/bin/python", False, False, False, "organize"),
        # Found via where (Windows)
        ("nt", 0, "C:\\Py\\Scripts\\organize.exe\r\n", "C:\\Py\\python.exe", False, False, False, "organize"),
        # Not found via which, found in sys.executable/bin (Unix)
        ("posix", 1, "", "/usr/py/bin/python", False, True, False, "/usr/py/bin/organize"),
        # Not found via where, found in sys.executable/Scripts (Windows) - Adjusted based on actual failure
        ("nt", 1, "", "C:\\Py\\python.exe", True, False, False, "Scripts/organize.exe"), # Use forward slash as observed
        # Not found via which/bin, found in /usr/local/bin (Unix)
        ("posix", 1, "", "/usr/py/bin/python", False, False, True, "/usr/local/bin/organize"),
        # Not found anywhere (Unix) - Fallback
        ("posix", 1, "", "/usr/py/bin/python", False, False, False, "organize"),
        # Not found anywhere (Windows) - Fallback
        ("nt", 1, "", "C:\\Py\\python.exe", False, False, False, "organize"),
        # Subprocess run error - Fallback
        ("posix", -1, "", "/usr/py/bin/python", False, False, False, "organize"), # Simulate subprocess error
    ]
)
@patch.object(OrganizeRunner, '_find_organize_script', return_value='/mock/script') # Mock the other init helper
def test_find_organize_command(
    mock_find_script, # Comes first due to patch order
    monkeypatch,      # Use monkeypatch fixture
    os_name_param, which_where_rc, which_where_output, sys_executable_param, scripts_exist, bin_exist, usr_local_exist, expected_cmd
):
    """
    Test _find_organize_command by checking runner.organize_cmd after instantiation,
    using monkeypatch for OS/subprocess mocks. Refactored.
    """
    # --- Setup Mocks using Monkeypatch ---
    monkeypatch.setattr(os, 'name', os_name_param) # Apply os.name mock first
    monkeypatch.setattr(sys, 'executable', sys_executable_param)

    # Mock subprocess.run
    mock_subprocess_run = MagicMock() # Create mock instance
    if which_where_rc == -1: # Simulate error
        mock_subprocess_run.side_effect = subprocess.SubprocessError("Test Error")
    else:
        mock_run_result = MagicMock()
        mock_run_result.returncode = which_where_rc
        mock_run_result.stdout = which_where_output
        mock_subprocess_run.return_value = mock_run_result
    monkeypatch.setattr(subprocess, 'run', mock_subprocess_run) # Apply mock

    # Use real os.path.dirname based on mocked sys.executable
    python_dir = os.path.dirname(sys.executable) # Now sys.executable is mocked

    # Configure os.path.exists mock
    mock_exists_func = MagicMock() # Create a mock function for side_effect
    def exists_side_effect(path):
        # Use the monkeypatched os.name
        current_os_name = os.name
        # Use os.path.join consistently for path construction
        scripts_path = os.path.join(python_dir, 'Scripts', 'organize.exe')
        bin_path = os.path.join(python_dir, 'organize')
        usr_local_path = '/usr/local/bin/organize'

        if current_os_name == 'nt' and path == scripts_path:
            return scripts_exist
        elif current_os_name == 'posix' and path == bin_path:
            return bin_exist
        elif current_os_name == 'posix' and path == usr_local_path:
            return usr_local_exist
        # Mock existence for the script path to avoid interference
        elif path == mock_find_script.return_value:
             return True # Assume script path exists
        return False # Default to not existing for other paths
    mock_exists_func.side_effect = exists_side_effect
    monkeypatch.setattr(os.path, 'exists', mock_exists_func)
    # --- End Setup Mocks ---

    # Instantiate the runner - this calls _find_organize_command via __init__
    # Use os.name which is now correctly monkeypatched for this run
    current_os_name = os.name
    runner = OrganizeRunner()

    # Assert the result stored in the instance attribute
    assert runner.organize_cmd == expected_cmd

    # Check subprocess.run was called correctly *during init*
    if which_where_rc != -1: # If no SubprocessError was simulated
        expected_subproc_cmd = ['where', 'organize'] if current_os_name == 'nt' else ['which', 'organize']
        mock_subprocess_run.assert_called_once_with(expected_subproc_cmd, capture_output=True, text=True, check=False)
    else:
         assert mock_subprocess_run.called # Check it was called before erroring

    # Check os.path.exists calls using the mock object's assert_any_call
    if which_where_rc != 0 and which_where_rc != -1: # Only check paths if which/where failed
        if current_os_name == 'nt':
            mock_exists_func.assert_any_call(os.path.join(python_dir, 'Scripts', 'organize.exe'))
        else: # posix
            mock_exists_func.assert_any_call(os.path.join(python_dir, 'organize'))
            if not bin_exist: # Only check /usr/local/bin if not found in python bin
                 mock_exists_func.assert_any_call('/usr/local/bin/organize')


# --- Tests for _find_organize_script ---

@pytest.mark.parametrize(
    "script_locations_exist, expected_script_path",
    [
        # Unix: Found in organize_gui/config/
        ({"config_sh": True}, "/mock/base/organize_gui/config/organize-files.sh"),
        # Unix: Found in organize_gui/
        ({"base_sh": True}, "/mock/base/organize_gui/organize-files.sh"),
        # Unix: Found in parent/config/
        ({"parent_config_sh": True}, "/mock/base/config/organize-files.sh"),
        # Unix: Found in parent/
        ({"parent_sh": True}, "/mock/base/organize-files.sh"),
        # Unix: Not found (fallback)
        ({}, "/mock/base/organize_gui/config/organize-files.sh"),
        # Windows: Found in organize_gui/config/
        ({"config_bat": True}, "/mock/base/organize_gui/config/organize-files.bat"),
        # Windows: Found in organize_gui/
        ({"base_bat": True}, "/mock/base/organize_gui/organize-files.bat"),
        # Windows: Not found (fallback)
        ({}, "/mock/base/organize_gui/config/organize-files.bat"),
    ]
)
@patch.object(OrganizeRunner, '_find_organize_command', return_value='mock_cmd') # Mock the other init helper
def test_find_organize_script(
    mock_find_cmd, # Comes first due to patch order
    monkeypatch,   # Use monkeypatch fixture
    script_locations_exist, expected_script_path
):
    """ Test finding the organize script using monkeypatch for OS mocks. Refactored. """
    # --- Setup Mocks using Monkeypatch ---
    # Determine OS name from expected path
    os_name_for_test = 'nt' if expected_script_path.endswith('.bat') else 'posix'
    monkeypatch.setattr(os, 'name', os_name_for_test)

    # Mock file structure resolution based on __file__
    runner_file_path = "/mock/base/organize_gui/core/organize_runner.py"
    # Use importlib to get the module object for patching __file__
    runner_module = importlib.import_module('organize_gui.core.organize_runner')
    monkeypatch.setattr(runner_module, '__file__', runner_file_path, raising=False)

    # Mock os.path.abspath and os.path.dirname
    monkeypatch.setattr(os.path, 'abspath', lambda p: runner_file_path if p == runner_module.__file__ else p)
    base_dir = "/mock/base/organize_gui"
    parent_dir = "/mock/base"
    def dirname_side_effect(path):
        if path == runner_file_path: return "/mock/base/organize_gui/core"
        if path == "/mock/base/organize_gui/core": return base_dir
        if path == base_dir: return parent_dir
        return os.path.dirname(path) # Fallback
    monkeypatch.setattr(os.path, 'dirname', dirname_side_effect)

    # Define potential script paths
    script_name = "organize-files.bat" if os.name == "nt" else "organize-files.sh" # Use monkeypatched os.name
    paths = {
        "config_sh": os.path.join(base_dir, "config", "organize-files.sh"),
        "base_sh": os.path.join(base_dir, "organize-files.sh"),
        "parent_config_sh": os.path.join(parent_dir, "config", "organize-files.sh"),
        "parent_sh": os.path.join(parent_dir, "organize-files.sh"),
        "config_bat": os.path.join(base_dir, "config", "organize-files.bat"),
        "base_bat": os.path.join(base_dir, "organize-files.bat"),
        "parent_config_bat": os.path.join(parent_dir, "config", "organize-files.bat"), # Not explicitly checked but good practice
        "parent_bat": os.path.join(parent_dir, "organize-files.bat"), # Not explicitly checked
    }

    # Configure os.path.exists mock
    mock_exists_func = MagicMock() # Create mock function
    def exists_side_effect(path):
        # Check against potential script paths based on parametrization
        for key, loc_path in paths.items():
            if path == loc_path:
                return script_locations_exist.get(key, False)
        # Mock existence for the command path to avoid interference
        if path == mock_find_cmd.return_value:
             return True # Assume command path exists
        return False
    mock_exists_func.side_effect = exists_side_effect
    monkeypatch.setattr(os.path, 'exists', mock_exists_func)
    # --- End Setup Mocks ---

    # Instantiate the runner - this calls _find_organize_script via __init__
    runner = OrganizeRunner()

    # Assert the result stored in the instance attribute
    assert runner.script_path == expected_script_path

    # Check os.path.exists calls made during _find_organize_script
    checked_paths = []
    current_os_name = os.name # Use monkeypatched os.name
    if current_os_name == 'nt':
        checked_paths.append(paths["config_bat"])
        if not script_locations_exist.get("config_bat"):
            checked_paths.append(paths["base_bat"])
            # The original code doesn't check parent paths for .bat
    else: # posix
        checked_paths.append(paths["config_sh"])
        if not script_locations_exist.get("config_sh"):
            checked_paths.append(paths["base_sh"])
            if not script_locations_exist.get("base_sh"):
                 checked_paths.append(paths["parent_config_sh"])
                 if not script_locations_exist.get("parent_config_sh"):
                          checked_paths.append(paths["parent_sh"])

    for p in checked_paths:
        mock_exists_func.assert_any_call(p) # Use the correct mock object


# --- Tests for run method ---

# Helper to create a mock runner instance with specific init values
def create_runner(monkeypatch, cmd='organize_cmd', script='/path/script.sh', script_exists=True):
    monkeypatch.setattr(OrganizeRunner, '_find_organize_command', lambda self: cmd)
    monkeypatch.setattr(OrganizeRunner, '_find_organize_script', lambda self: script)
    # Mock os.path.exists specifically for the script path check within run()
    original_exists = os.path.exists
    # We need to handle the case where os.path itself might be mocked by the test calling create_runner
    def exists_for_script(p):
        if p == script:
            return script_exists
        # If os.path.exists was mocked, call that mock, otherwise call original
        if isinstance(original_exists, MagicMock):
            return original_exists(p)
        elif callable(original_exists):
             try:
                 # Check if it's a monkeypatched function
                 if hasattr(original_exists, '__wrapped__'):
                      # This might indicate a deeper mock, try calling it
                      return original_exists(p)
                 else: # Assume it's the real function or a simple lambda
                      return original_exists(p)
             except Exception: # Fallback if calling fails unexpectedly
                  return False
        return False # Default fallback

    monkeypatch.setattr(os.path, 'exists', exists_for_script)
    return OrganizeRunner()

def test_run_already_running(monkeypatch):
    """ Test calling run when is_running is True. """
    runner = create_runner(monkeypatch)
    runner.is_running = True
    mock_output_callback = MagicMock()
    result = runner.run(output_callback=mock_output_callback)
    assert result == {'success': False, 'message': "Process already running."}
    mock_output_callback.assert_called_once_with("Process already running.", "error")

@patch.object(OrganizeRunner, '_run_with_script')
@patch.object(OrganizeRunner, '_run_with_command')
def test_run_uses_script_when_exists(mock_run_cmd, mock_run_script, monkeypatch):
    """ Test that run calls _run_with_script if script exists. """
    script_path = '/path/exists/script.sh'
    # Ensure os.path.exists returns True only for the script path during run's check
    monkeypatch.setattr(os.path, 'exists', lambda p: p == script_path)
    runner = create_runner(monkeypatch, script=script_path, script_exists=True) # create_runner uses the monkeypatched exists

    runner.run(config_path='/config.yaml', simulation=True, verbose=True)
    mock_run_script.assert_called_once_with(True, ANY, ANY, '/config.yaml', True)
    mock_run_cmd.assert_not_called()

@patch.object(OrganizeRunner, '_run_with_script')
@patch.object(OrganizeRunner, '_run_with_command')
def test_run_uses_command_when_script_missing(mock_run_cmd, mock_run_script, monkeypatch):
    """ Test that run calls _run_with_command if script does not exist. """
    script_path = '/path/missing/script.sh'
     # Ensure os.path.exists returns False for the script path during run's check
    monkeypatch.setattr(os.path, 'exists', lambda p: False)
    runner = create_runner(monkeypatch, script=script_path, script_exists=False) # create_runner uses the monkeypatched exists

    runner.run(config_path='/config.yaml', simulation=False, verbose=False)
    mock_run_cmd.assert_called_once_with(False, ANY, ANY, '/config.yaml', False)
    mock_run_script.assert_not_called()

@patch('organize_gui.core.organize_runner.tempfile.NamedTemporaryFile')
@patch('organize_gui.core.organize_runner.yaml.dump')
@patch('organize_gui.core.organize_runner.os.unlink')
@patch.object(OrganizeRunner, '_run_with_command') # Assume command runner used for temp file
def test_run_with_config_data(mock_run_cmd, mock_unlink, mock_yaml_dump, mock_tempfile, monkeypatch):
    """ Test run creates, uses, and deletes a temp file for config_data. """
    # Ensure script doesn't exist to force command runner
    monkeypatch.setattr(os.path, 'exists', lambda p: False)
    runner = create_runner(monkeypatch, script_exists=False)

    # Setup mock for NamedTemporaryFile
    mock_temp_file_obj = MagicMock()
    mock_temp_file_obj.name = "/tmp/fake_config.yaml"
    # Make the file handle mock usable in a 'with' statement
    mock_temp_file_context = MagicMock()
    mock_temp_file_context.__enter__.return_value = mock_temp_file_obj
    mock_temp_file_context.__exit__.return_value = None
    mock_tempfile.return_value = mock_temp_file_context

    config_data = {'rules': [{'name': 'Temp Rule'}]}
    mock_output_callback = MagicMock()

    # Mock os.path.exists again for the unlink check at the end
    # It needs to return True for the temp file path
    original_exists = os.path.exists
    def final_exists_check(p):
        if p == "/tmp/fake_config.yaml":
            return True
        return original_exists(p) # Or just False if no other checks needed
    monkeypatch.setattr(os.path, 'exists', final_exists_check)


    runner.run(config_data=config_data, simulation=True, output_callback=mock_output_callback)

    # Check temp file creation and usage
    mock_tempfile.assert_called_once_with(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
    mock_yaml_dump.assert_called_once_with(config_data, mock_temp_file_obj, default_flow_style=False, sort_keys=False, indent=2)
    mock_run_cmd.assert_called_once_with(True, ANY, mock_output_callback, "/tmp/fake_config.yaml", False) # verbose=False default

    # Check temp file deletion
    mock_unlink.assert_called_once_with("/tmp/fake_config.yaml")
    # Check debug message for deletion
    mock_output_callback.assert_any_call("Deleted temporary config file: /tmp/fake_config.yaml", "debug")

@patch('organize_gui.core.organize_runner.tempfile.NamedTemporaryFile', side_effect=IOError("Cannot create temp file"))
def test_run_with_config_data_tempfile_error(mock_tempfile, monkeypatch):
    """ Test run handles errors during temporary file creation. """
    runner = create_runner(monkeypatch)
    config_data = {'rules': [{'name': 'Temp Rule'}]}
    mock_output_callback = MagicMock()

    result = runner.run(config_data=config_data, output_callback=mock_output_callback)

    assert result['success'] is False
    # Check specific error message if possible, otherwise general check
    assert "Failed to write temporary config file" in result['message'] or "Cannot create temp file" in result['message']
    # Check that the error message *as formatted by the exception handler* was passed to the callback
    mock_output_callback.assert_any_call(f"Error running process: {result['message'].split(': ', 1)[1]}", "error")


def test_run_with_invalid_config_data(monkeypatch):
    """ Test run handles invalid config_data structure. """
    runner = create_runner(monkeypatch)
    mock_output_callback = MagicMock()

    result = runner.run(config_data="not a dict", output_callback=mock_output_callback)
    assert result['success'] is False
    assert "Invalid config_data provided" in result['message']
    # Check that the error message *as formatted by the exception handler* was passed to the callback
    mock_output_callback.assert_any_call(f"Error running process: {result['message'].split(': ', 1)[1]}", "error")

    # Reset mock for second call
    mock_output_callback.reset_mock()
    result = runner.run(config_data={"no_rules": True}, output_callback=mock_output_callback)
    assert result['success'] is False
    assert "Invalid config_data provided" in result['message']
    # Check the call for the second invalid case
    mock_output_callback.assert_called_once_with(f"Error running process: {result['message'].split(': ', 1)[1]}", "error")


# Add tests for other methods below
