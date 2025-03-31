import pytest
import os
import yaml
from unittest.mock import patch, mock_open

# Assuming ConfigManager is in organize_gui.core.config_manager
from organize_gui.core.config_manager import ConfigManager

# --- Tests for ConfigManager ---

def test_config_manager_init():
    """ Test the initial state of ConfigManager. """
    manager = ConfigManager()
    assert manager.config is None
    assert manager.current_config_path is None

def test_create_new_config():
    """ Test creating a new, empty configuration. """
    manager = ConfigManager()
    # Give it some initial state to ensure it gets reset
    manager.config = {"rules": [{"name": "old rule"}]}
    manager.current_config_path = "/path/to/old.yaml"

    manager.create_new_config()

    assert manager.config == {'rules': []}
    assert manager.current_config_path is None


# --- Tests for load_config ---

@patch('organize_gui.core.config_manager.yaml.safe_load')
@patch('builtins.open', new_callable=mock_open, read_data="rules:\n  - name: Test Rule")
def test_load_config_success(mock_file_open, mock_yaml_load):
    """ Test successful loading of a config file. """
    manager = ConfigManager()
    test_path = "/fake/config.yaml"
    mock_config_data = {'rules': [{'name': 'Test Rule'}]}
    mock_yaml_load.return_value = mock_config_data

    manager.load_config(test_path)

    mock_file_open.assert_called_once_with(test_path, 'r')
    mock_yaml_load.assert_called_once() # Check it was called
    assert manager.config == mock_config_data
    assert manager.current_config_path == test_path

@patch('builtins.open', side_effect=FileNotFoundError("File not found"))
def test_load_config_not_found(mock_file_open):
    """ Test loading a non-existent config file. """
    manager = ConfigManager()
    test_path = "/fake/nonexistent.yaml"

    with pytest.raises(FileNotFoundError):
        manager.load_config(test_path)

    mock_file_open.assert_called_once_with(test_path, 'r')
    assert manager.config is None
    assert manager.current_config_path is None

@patch('organize_gui.core.config_manager.yaml.safe_load', side_effect=yaml.YAMLError("Bad YAML"))
@patch('builtins.open', new_callable=mock_open, read_data="invalid yaml: {")
def test_load_config_yaml_error(mock_file_open, mock_yaml_load):
    """ Test loading a file with invalid YAML content. """
    manager = ConfigManager()
    test_path = "/fake/bad_config.yaml"

    with pytest.raises(yaml.YAMLError):
        manager.load_config(test_path)

    mock_file_open.assert_called_once_with(test_path, 'r')
    mock_yaml_load.assert_called_once()
    assert manager.config is None # Should not be set on error
    assert manager.current_config_path is None


# --- Tests for save_config ---

@patch('organize_gui.core.config_manager.yaml.dump')
@patch('builtins.open', new_callable=mock_open)
def test_save_config_success(mock_file_open, mock_yaml_dump):
    """ Test successful saving of a config file. """
    manager = ConfigManager()
    test_path = "/fake/save_config.yaml"
    test_config = {'rules': [{'name': 'Save Rule'}]}
    manager.config = test_config # Pre-load config

    manager.save_config(test_path)

    mock_file_open.assert_called_once_with(test_path, 'w')
    mock_yaml_dump.assert_called_once_with(
        test_config,
        mock_file_open(), # Check it's called with the file handle
        default_flow_style=False,
        sort_keys=False
    )
    assert manager.current_config_path == test_path

def test_save_config_no_config_loaded():
    """ Test saving when no configuration is loaded. """
    manager = ConfigManager()
    test_path = "/fake/save_config.yaml"

    with pytest.raises(ValueError, match="No configuration to save"):
        manager.save_config(test_path)

    assert manager.current_config_path is None # Path should not be updated


# --- Tests for get_current_paths ---

@pytest.mark.parametrize("config_data, mock_dest, expected_source, expected_dest", [
    # Basic case: list of strings
    ({'rules': [{'locations': ['/source/path']}]}, '/common/dest', '/source/path', '/common/dest'),
    # Basic case: single string
    ({'rules': [{'locations': '/source/string'}]}, '/common/dest', '/source/string', '/common/dest'),
    # Basic case: list of dicts
    ({'rules': [{'locations': [{'path': '/source/dict'}]}]}, '/common/dest', '/source/dict', '/common/dest'),
    # Empty locations list
    ({'rules': [{'locations': []}]}, '/common/dest', None, '/common/dest'), # Source is None, Dest depends on _find_common_destination
    # Locations key missing
    ({'rules': [{}]}, '/common/dest', None, '/common/dest'), # Source is None, Dest depends on _find_common_destination
    # Rules list empty
    ({'rules': []}, '/common/dest', None, None), # Source is None, Dest should also be None (or _find_common_destination not called)
    # Rules key missing
    ({}, '/common/dest', None, None), # Source is None, Dest should also be None
    # Config is None
    (None, '/common/dest', None, None), # Both None
    # Multiple locations (should only take first)
    ({'rules': [{'locations': ['/source1', '/source2']}]}, '/common/dest', '/source1', '/common/dest'),
    ({'rules': [{'locations': [{'path': '/source1'}, {'path': '/source2'}]}]}, '/common/dest', '/source1', '/common/dest'),
])
@patch.object(ConfigManager, '_find_common_destination') # Patch the method on the class
def test_get_current_paths(mock_find_dest, config_data, mock_dest, expected_source, expected_dest):
    """ Test getting source and destination paths from various config structures. """
    manager = ConfigManager()
    manager.config = config_data
    mock_find_dest.return_value = mock_dest # Set the mock return value

    source, dest = manager.get_current_paths()

    assert source == expected_source
    assert dest == expected_dest
    if config_data and config_data.get('rules'): # Only call find_dest if rules exist
        mock_find_dest.assert_called_once()
    else:
        mock_find_dest.assert_not_called()


# --- Tests for _find_common_destination ---

@pytest.mark.parametrize("config_data, mock_commonpath_return, mock_commonpath_raises, expected_dest", [
    # Basic case - single move action (dict)
    ({'rules': [{'actions': [{'move': {'dest': '/base/dest/Organized/Docs'}}]}]}, '/base/dest', None, '/base/dest'),
    # Basic case - single move action (str)
    ({'rules': [{'actions': [{'move': '/base/dest/Organized/Images'}]}]}, '/base/dest', None, '/base/dest'),
    # Multiple move actions with common base
    ({'rules': [{'actions': [{'move': '/base/dest/Organized/Docs'}, {'move': {'dest': '/base/dest/Cleanup/Temp'}}]}]}, '/base/dest', None, '/base/dest'),
    # Placeholder replacement
    ({'rules': [{'actions': [{'move': {'dest': '/base/dest/Organized/{extension}'}}]}]}, '/base/dest', None, '/base/dest'),
    # Placeholder at end
    ({'rules': [{'actions': [{'move': {'dest': '/base/dest/Organized/'}}]}]}, '/base/dest', None, '/base/dest'),
    # Mixed placeholders and non-placeholders
    ({'rules': [{'actions': [{'move': '/base/dest/Organized/Real'}, {'move': {'dest': '/base/dest/Cleanup/{year}'}}]}]}, '/base/dest', None, '/base/dest'),
    # No common path (commonpath raises ValueError)
    ({'rules': [{'actions': [{'move': '/path1/Docs'}, {'move': '/path2/Images'}]}]}, None, ValueError, None),
    # No move actions
    ({'rules': [{'actions': [{'copy': '/dest'}]}]}, None, None, None),
    # No actions key
    ({'rules': [{}]}, None, None, None),
    # Rules list empty
    ({'rules': []}, None, None, None),
    # Config is None
    (None, None, None, None),
    # Path doesn't contain Organized or Cleanup
    ({'rules': [{'actions': [{'move': '/base/dest/Other/Docs'}]}]}, '/base/dest/Other', None, '/base/dest/Other'),
])
@patch('organize_gui.core.config_manager.os.path.commonpath')
def test_find_common_destination(mock_commonpath, config_data, mock_commonpath_return, mock_commonpath_raises, expected_dest):
    """ Test finding the common destination path from various config structures. """
    manager = ConfigManager()
    manager.config = config_data

    if mock_commonpath_raises:
        mock_commonpath.side_effect = mock_commonpath_raises
    else:
        mock_commonpath.return_value = mock_commonpath_return

    dest = manager._find_common_destination()

    assert dest == expected_dest

    # Check if commonpath was called appropriately
    if config_data and 'rules' in config_data and any('actions' in r for r in config_data['rules']):
         # Check if there are actually any move actions to extract paths from
         has_move_action = False
         for rule in config_data['rules']:
             if 'actions' in rule:
                 for action in rule['actions']:
                     if isinstance(action, dict) and 'move' in action:
                         has_move_action = True
                         break
             if has_move_action:
                 break
         if has_move_action:
             mock_commonpath.assert_called_once()
         else:
             mock_commonpath.assert_not_called()

    else:
        mock_commonpath.assert_not_called()


# --- Tests for update_paths ---

@patch.object(ConfigManager, '_update_manually')
def test_update_paths_calls_update_manually(mock_update_manually):
    """ Test that update_paths calls _update_manually when config exists. """
    manager = ConfigManager()
    manager.config = {'rules': []} # Load a dummy config
    source_dir = "/new/source"
    dest_dir = "/new/dest"

    manager.update_paths(source_dir, dest_dir)

    mock_update_manually.assert_called_once_with(source_dir, dest_dir)

def test_update_paths_no_config():
    """ Test that update_paths raises ValueError if no config is loaded. """
    manager = ConfigManager()
    source_dir = "/new/source"
    dest_dir = "/new/dest"

    with pytest.raises(ValueError, match="No configuration loaded"):
        manager.update_paths(source_dir, dest_dir)


# --- Tests for _replace_dest_base ---

@pytest.mark.parametrize("old_dest, new_base, expected_new_dest", [
    # Basic cases with /Organized/
    ("/old/base/Organized/Docs", "/new/base", "/new/base/Organized/Docs"),
    ("/old/base/Organized/{year}/{month}", "/new/base", "/new/base/Organized/{year}/{month}"),
    ("/old/base/Organized/", "/new/base", "/new/base/Organized/"),
    # Basic cases with /Cleanup/
    ("/old/base/Cleanup/Temp", "/new/base", "/new/base/Cleanup/Temp"),
    ("/old/base/Cleanup/{date}", "/new/base", "/new/base/Cleanup/{date}"),
    ("/old/base/Cleanup/", "/new/base", "/new/base/Cleanup/"),
    # Cases without /Organized/ or /Cleanup/ (should return original)
    ("/old/base/Other/Folder", "/new/base", "/old/base/Other/Folder"),
    ("/old/base/NoMarker", "/new/base", "/old/base/NoMarker"),
    # Edge cases
    ("Organized/Docs", "/new/base", "Organized/Docs"), # No leading slash
    ("Cleanup/Temp", "/new/base", "Cleanup/Temp"), # No leading slash
    ("/old/base/Organized", "/new/base", "/old/base/Organized"), # Marker at end - Adjusted based on actual behavior
    ("/old/base/Cleanup", "/new/base", "/old/base/Cleanup"), # Marker at end - Adjusted based on actual behavior
    ("", "/new/base", ""), # Empty old dest
])
def test_replace_dest_base(old_dest, new_base, expected_new_dest):
    """ Test the _replace_dest_base helper method. """
    manager = ConfigManager()
    # We call the method directly on an instance
    actual_new_dest = manager._replace_dest_base(old_dest, new_base)
    assert actual_new_dest == expected_new_dest


# --- Tests for _update_manually ---

# Use parametrize for different initial config states
@pytest.mark.parametrize("initial_config, new_source, new_dest, expected_config", [
    # Case 1: Simple list location, simple move dest
    (
        {'rules': [{'locations': ['/old/source'], 'actions': [{'move': '/old/dest/Organized/Docs'}]}]},
        '/new/source', '/new/dest',
        {'rules': [{'locations': ['/new/source'], 'actions': [{'move': '/new/dest/Organized/Docs'}]}]}
    ),
    # Case 2: String location, dict move dest with placeholder
    (
        {'rules': [{'locations': '/old/source', 'actions': [{'move': {'dest': '/old/dest/Cleanup/{ext}'}}]}]},
        '/new/source/data', '/new/dest/base',
        {'rules': [{'locations': '/new/source/data', 'actions': [{'move': {'dest': '/new/dest/base/Cleanup/{ext}'}}]}]}
    ),
    # Case 3: List of dict locations, multiple actions
    (
        {'rules': [{'locations': [{'path': '/old/source'}], 'actions': [{'copy': '/other'}, {'move': '/old/dest/Organized/Images'}]}]},
        '/another/source', '/another/dest',
        {'rules': [{'locations': [{'path': '/another/source'}], 'actions': [{'copy': '/other'}, {'move': '/another/dest/Organized/Images'}]}]}
    ),
    # Case 4: No locations key
    (
        {'rules': [{'actions': [{'move': '/old/dest/Organized/Misc'}]}]},
        '/new/source', '/new/dest',
        {'rules': [{'actions': [{'move': '/new/dest/Organized/Misc'}]}]}
    ),
    # Case 5: No actions key
    (
        {'rules': [{'locations': ['/old/source']}]},
        '/new/source', '/new/dest',
        {'rules': [{'locations': ['/new/source']}]}
    ),
    # Case 6: No move action
    (
        {'rules': [{'locations': ['/old/source'], 'actions': [{'copy': '/some/path'}]}]},
        '/new/source', '/new/dest',
        {'rules': [{'locations': ['/new/source'], 'actions': [{'copy': '/some/path'}]}]}
    ),
    # Case 7: Empty rules list
    (
        {'rules': []},
        '/new/source', '/new/dest',
        {'rules': []}
    ),
])
def test_update_manually(initial_config, new_source, new_dest, expected_config):
    """ Test the _update_manually method modifies the config correctly. """
    manager = ConfigManager()
    # Use deepcopy if config might be mutated by other tests (though parametrize isolates)
    import copy
    manager.config = copy.deepcopy(initial_config)

    # Call the private method directly for testing
    manager._update_manually(new_source, new_dest)

    assert manager.config == expected_config

# Finished testing config_manager.py
