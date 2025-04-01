import pytest
import pytest
import os
# No need for patch or monkeypatch if os.path.exists isn't called

# Assuming is_valid_path is in organize_gui.utils.validators
# Adjust the import path if necessary based on your project structure
from organize_gui.utils.validators import is_valid_path

# Note: is_valid_path only checks syntax, not existence.
@pytest.mark.parametrize("path_input, expected_result", [
    ("/valid/directory", True),      # Syntactically valid
    ("/valid/file.txt", True),       # Syntactically valid
    ("/non/existent/path", True),    # Syntactically valid (existence doesn't matter)
    ("valid_relative_path", True), # Syntactically valid
    ("", False),                     # Empty string is invalid
    (None, False),                   # None input is invalid
    ("  ", False),                   # Whitespace only is invalid
    ("/path/with/nul\0byte", False), # Contains invalid null byte (Unix)
    # Add Windows-specific tests if needed, e.g., "C:\CON", "COM1", "file*?.txt"
    # Add more test cases as needed
])
def test_is_valid_path_syntax(path_input, expected_result):
    """
    Tests the is_valid_path function for syntactic validity.
    Note: This function does NOT check if the path exists.
    """
    # Call the function under test
    actual_result = is_valid_path(path_input)

    # Assert that the actual result matches the expected result
    assert actual_result == expected_result


# --- Tests for is_valid_yaml ---

@pytest.mark.parametrize("yaml_content, expected_result", [
    # Valid YAML cases
    ("key: value", True),
    ("list:\n  - item1\n  - item2", True),
    ("nested:\n  key: value", True),
    ("{}", True), # Empty dictionary
    ("[]", True), # Empty list
    ("null", True), # Null value
    ("true", True), # Boolean true
    ("123", True), # Integer
    ("1.23", True), # Float
    # Invalid YAML cases - These should raise YAMLError
    ("key: value\n  extra_indent", True), # Indentation error (PyYAML parses this leniently)
    ("key: value:", False), # Syntax error (colon at end)
    ("key: [item1, item2", False), # Unclosed bracket
    ("\tkey: value", False), # Tab character (often problematic)
    # Edge cases - Strings that parse without error but might be semantically empty
    ("", True), # Empty string parses as None
    ("  ", True), # Whitespace string parses as None
    # Non-string inputs are now handled by the initial type check in the function
])
def test_is_valid_yaml(yaml_content, expected_result):
    """
    Tests the is_valid_yaml function. Checks if yaml.safe_load raises an error.
    Note: Empty/whitespace strings are considered valid as they parse to None.
    """
    # Import the function locally if it's not already imported at the top
    from organize_gui.utils.validators import is_valid_yaml

    # Call the function under test
    actual_result = is_valid_yaml(yaml_content)

    # Assert the result
    assert actual_result == expected_result


# --- Tests for is_valid_rule_name ---

@pytest.mark.parametrize("rule_name, expected_result", [
    # Valid cases
    ("Simple Rule", True),
    ("Rule_with_underscores_123", True),
    ("Rule with spaces", True),
    ("Rule-with-hyphens", True),
    ("A"*100, True), # Max length
    # Invalid cases
    ("", False), # Empty
    ("   ", False), # Whitespace only
    (None, False), # None input
    ("A"*101, False), # Too long
    ("Rule with > invalid", False), # Invalid char >
    ("Rule with < invalid", False), # Invalid char <
    ("Rule with : invalid", False), # Invalid char :
    ("Rule with \" invalid", False), # Invalid char "
    ("Rule with / invalid", False), # Invalid char /
    ("Rule with \\ invalid", False), # Invalid char \
    ("Rule with | invalid", False), # Invalid char |
    ("Rule with ? invalid", False), # Invalid char ?
    ("Rule with * invalid", False), # Invalid char *
    ("Rule with # invalid", False), # Invalid char #
    ("Rule with \0 null", False), # Invalid char null byte
])
def test_is_valid_rule_name(rule_name, expected_result):
    """
    Tests the is_valid_rule_name function.
    """
    from organize_gui.utils.validators import is_valid_rule_name

    # Call the function under test
    actual_result = is_valid_rule_name(rule_name)

    # Assert the result
    assert actual_result == expected_result


# --- Tests for is_valid_extension_list ---

@pytest.mark.parametrize("ext_list, expected_result", [
    # Valid cases
    (["txt", "jpg", "pdf"], True),
    (["docx"], True),
    ([], True), # Empty list is valid
    # Invalid cases - Input type
    ("not a list", False),
    (None, False),
    ({"set"}, False),
    # Invalid cases - Item types
    (["txt", 123], False), # Contains non-string
    (["txt", None], False), # Contains None
    # Invalid cases - Extension content
    (["txt", ""], False), # Contains empty string
    (["txt", "   "], False), # Contains whitespace string
    (["txt", ".jpg"], False), # Starts with dot
    (["txt", "jp g"], False), # Contains space
    (["txt", "jp/g"], False), # Contains slash
    (["txt", "jp\\g"], False), # Contains backslash
    (["txt", "jp*g"], False), # Contains asterisk
    (["txt", "jp<g"], False), # Contains invalid char
])
def test_is_valid_extension_list(ext_list, expected_result):
    """
    Tests the is_valid_extension_list function.
    """
    from organize_gui.utils.validators import is_valid_extension_list

    # Call the function under test
    actual_result = is_valid_extension_list(ext_list)

    # Assert the result
    assert actual_result == expected_result


# --- Tests for is_valid_filter ---

@pytest.mark.parametrize("filter_obj, expected_result", [
    # Valid cases
    ({"extension": "txt"}, True),
    ({"extension": ["txt", "pdf"]}, True),
    ({"name": "document"}, True),
    ({"regex": {"pattern": r"\d+"}}, True), # Assuming dict value is okay per signature
    ({"size": {">": "10MB"}}, True), # Assuming dict value is okay
    ({"created": "today"}, True),
    ({"lastmodified": {"<": "2 weeks ago"}}, True), # Assuming dict value is okay
    ({"exif": True}, True), # Assuming bool value is okay
    ({"duplicate": True}, True), # Assuming bool value is okay
    ({"python": "result = True"}, True),
    # Invalid cases - Structure/Type
    ("not a dict", False),
    (None, False),
    ({}, False), # Empty dict
    ({"extension": "txt", "name": "doc"}, False), # More than one key
    ({"unknown_filter": "value"}, False), # Unknown filter type
    # Invalid cases - Value types
    ({"extension": 123}, False), # Wrong value type for extension
    ({"name": ["doc"]}, False), # Wrong value type for name
    ({"regex": "pattern"}, False), # Wrong value type for regex (expected dict)
    ({"size": "10MB"}, False), # Wrong value type for size (expected dict)
    ({"created": ["today"]}, False), # Wrong value type for created
    ({"exif": "true"}, False), # Wrong value type for exif (expected bool)
    ({"duplicate": "yes"}, False), # Wrong value type for duplicate (expected bool/dict)
    ({"python": False}, False), # Wrong value type for python (expected str)
    # Invalid cases - Specific filter content (using extension list validator)
    ({"extension": ["txt", ".pdf"]}, False), # Invalid extension format in list
    ({"extension": ["txt", "p df"]}, False), # Invalid extension format in list
])
def test_is_valid_filter(filter_obj, expected_result):
    """
    Tests the is_valid_filter function.
    """
    from organize_gui.utils.validators import is_valid_filter

    # Call the function under test
    actual_result = is_valid_filter(filter_obj)

    # Assert the result
    assert actual_result == expected_result


# --- Tests for is_valid_action ---

@pytest.mark.parametrize("action_obj, expected_result", [
    # Valid cases
    ({"move": "/dest/path"}, True), # Simple move
    ({"move": {"dest": "/dest/path", "on_conflict": "rename"}}, True), # Move with options
    ({"copy": "/dest/path"}, True), # Simple copy
    ({"copy": {"dest": "/dest/path", "overwrite": True}}, True), # Copy with options
    ({"rename": "new_name_{counter}"}, True),
    ({"delete": True}, True),
    ({"trash": True}, True),
    ({"echo": "Processing {name}"}, True),
    ({"shell": "echo {path}"}, True),
    ({"python": "print(path)"}, True),
    ({"confirm": "Proceed?"}, True),
    # Invalid cases - Structure/Type
    ("not a dict", False),
    (None, False),
    ({}, False), # Empty dict
    ({"move": "path", "copy": "path"}, False), # More than one key
    ({"unknown_action": "value"}, False), # Unknown action type
    # Invalid cases - Value types
    ({"move": True}, False), # Wrong value type for move (expected str/dict)
    ({"copy": 123}, False), # Wrong value type for copy (expected str/dict)
    ({"rename": ["name"]}, False), # Wrong value type for rename (expected str)
    ({"delete": "yes"}, False), # Wrong value type for delete (expected bool)
    ({"trash": 0}, False), # Wrong value type for trash (expected bool)
    ({"echo": None}, False), # Wrong value type for echo (expected str)
    ({"shell": []}, False), # Wrong value type for shell (expected str)
    ({"python": True}, False), # Wrong value type for python (expected str)
    ({"confirm": 1}, False), # Wrong value type for confirm (expected str)
    # Invalid cases - Specific action content (move dest validation)
    ({"move": {"dest": ""}}, False), # Invalid dest path in move dict
    ({"move": {"dest": "/path/with/\0"}}, False), # Invalid dest path in move dict
    ({"move": {"on_conflict": "rename"}}, False), # Missing 'dest' in move dict
    # Invalid cases - String value path validation
    ({"move": "/path/with/\0"}, False), # Invalid path as string value for move
    ({"copy": "/path/with/\0"}, False), # Invalid path as string value for copy
    ({"move": ""}, False), # Empty string path for move
    ({"copy": "  "}, False), # Whitespace string path for copy
])
def test_is_valid_action(action_obj, expected_result):
    """
    Tests the is_valid_action function.
    """
    from organize_gui.utils.validators import is_valid_action

    # Call the function under test
    actual_result = is_valid_action(action_obj)

    # Assert the result
    assert actual_result == expected_result

# Finished testing validators.py
