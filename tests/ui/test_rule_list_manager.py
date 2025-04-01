"""
Unit tests for organize_gui.ui.rule_list_manager
"""

import unittest
import tkinter as tk # Need tkinter root for StringVar if testing refresh_list
from unittest.mock import MagicMock

# Adjust import path as necessary
from organize_gui.ui.rule_list_manager import RuleListManager

class TestRuleListManagerCategoryLogic(unittest.TestCase):
    """Test suite specifically for the _get_rule_category logic."""

    def setUp(self):
        """Set up a dummy RuleListManager instance for testing internal methods."""
        # We don't need a real parent frame or rules_data for category testing
        # Mock the necessary parts if RuleListManager's __init__ requires them
        mock_parent = MagicMock()
        self.manager = RuleListManager(mock_parent, [])
        # Prevent actual widget creation during tests
        self.manager._create_widgets = MagicMock()

    def test_category_by_move_action_documents(self):
        """Test category detection based on move action destination (Documents)."""
        rule = {
            'actions': [{'move': {'dest': '/path/to/Organized/Documents/'}}]
        }
        self.assertEqual(self.manager._get_rule_category(rule), "Documents")

    def test_category_by_copy_action_media(self):
        """Test category detection based on copy action destination (Media)."""
        rule = {
            'actions': [{'copy': '/some/other/path/media/subdir/'}] # Non-dict action value
        }
        self.assertEqual(self.manager._get_rule_category(rule), "Media")

    def test_category_by_action_cleanup(self):
        """Test category detection for Cleanup destinations."""
        rule_cleanup = {'actions': [{'move': {'dest': '/path/to/cleanup/'}}]}
        rule_duplicates = {'actions': [{'move': {'dest': '/path/to/duplicates/'}}]}
        self.assertEqual(self.manager._get_rule_category(rule_cleanup), "Cleanup")
        self.assertEqual(self.manager._get_rule_category(rule_duplicates), "Cleanup")

    def test_category_by_extension_filter_development(self):
        """Test category detection based on extension filter (Development)."""
        rule = {
            'filters': [{'extension': ['py', 'js', 'java']}]
        }
        self.assertEqual(self.manager._get_rule_category(rule), "Development")

    def test_category_by_extension_filter_archives(self):
        """Test category detection based on extension filter (Archives)."""
        rule = {
            'filters': [{'extension': 'zip'}] # Single extension string
        }
        self.assertEqual(self.manager._get_rule_category(rule), "Archives")

    def test_category_priority_action_over_filter(self):
        """Test that action destination takes priority over filter."""
        rule = {
            'filters': [{'extension': ['py']}], # Suggests Development
            'actions': [{'move': {'dest': '/path/to/Organized/Media/'}}] # Suggests Media
        }
        self.assertEqual(self.manager._get_rule_category(rule), "Media")

    def test_category_no_hints(self):
        """Test default category 'Other' when no hints are found."""
        rule = {
            'filters': [{'size': '>10mb'}],
            'actions': [{'echo': 'Hello'}]
        }
        self.assertEqual(self.manager._get_rule_category(rule), "Other")

    def test_category_empty_rule(self):
        """Test default category 'Other' for an empty rule."""
        rule = {}
        self.assertEqual(self.manager._get_rule_category(rule), "Other")

    def test_category_malformed_action(self):
        """Test category detection with malformed action."""
        rule = {'actions': [{'move': None}]} # Malformed action
        self.assertEqual(self.manager._get_rule_category(rule), "Other")

    def test_category_malformed_filter(self):
        """Test category detection with malformed filter."""
        rule = {'filters': [{'extension': None}]} # Malformed filter
        self.assertEqual(self.manager._get_rule_category(rule), "Other")


# Note: Testing refresh_list, selection methods, etc., is generally not practical
# with standard unit tests due to the heavy reliance on Tkinter widgets.
# Those would typically require integration or GUI automation testing.

if __name__ == '__main__':
    unittest.main()
