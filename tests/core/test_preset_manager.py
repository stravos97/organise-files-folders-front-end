"""
Unit tests for organize_gui.core.preset_manager
"""

import unittest
import os
from unittest.mock import patch, mock_open, MagicMock
import yaml # Need to import yaml for the default config test

# Adjust import path as necessary
from organize_gui.core import preset_manager

class TestPresetManager(unittest.TestCase):
    """Test suite for preset manager functions."""

    def assertIsPresetConfig(self, config, expected_rule_count=None):
        """Helper assertion to check basic preset config structure."""
        self.assertIsInstance(config, dict)
        self.assertIn('rules', config)
        self.assertIsInstance(config['rules'], list)
        if expected_rule_count is not None:
            self.assertEqual(len(config['rules']), expected_rule_count)
        for rule in config['rules']:
            self.assertIsInstance(rule, dict)
            self.assertIn('name', rule)
            self.assertIn('enabled', rule)
            self.assertIn('filters', rule)
            self.assertIn('actions', rule)

    def test_get_find_duplicates_config(self):
        """Test the find duplicates preset."""
        config = preset_manager.get_find_duplicates_config()
        self.assertIsPresetConfig(config, expected_rule_count=1)
        # Check a specific detail
        self.assertEqual(config['rules'][0]['name'], "Find Duplicate Files")

    def test_get_rename_photos_config(self):
        """Test the rename photos preset."""
        config = preset_manager.get_rename_photos_config()
        self.assertIsPresetConfig(config, expected_rule_count=2)
        self.assertEqual(config['rules'][0]['name'], "Rename Photos with EXIF Data")
        self.assertEqual(config['rules'][1]['name'], "Rename Photos without EXIF Data (using creation date)")

    def test_get_photo_organization_config(self):
        """Test the photo organization preset."""
        config = preset_manager.get_photo_organization_config()
        self.assertIsPresetConfig(config, expected_rule_count=2)
        self.assertEqual(config['rules'][0]['name'], "Organize Photos by Date (EXIF)")
        self.assertEqual(config['rules'][1]['name'], "Organize Photos by Date (Created)")

    def test_get_music_organization_config(self):
        """Test the music organization preset."""
        config = preset_manager.get_music_organization_config()
        self.assertIsPresetConfig(config, expected_rule_count=2)
        self.assertEqual(config['rules'][0]['name'], "Organize Music Files by Extension")
        self.assertEqual(config['rules'][1]['name'], "Find Music Duplicates")

    def test_get_document_organization_config(self):
        """Test the document organization preset."""
        config = preset_manager.get_document_organization_config()
        self.assertIsPresetConfig(config, expected_rule_count=4)
        self.assertEqual(config['rules'][0]['name'], "Organize Text Documents")
        self.assertEqual(config['rules'][1]['name'], "Organize Office Documents")
        self.assertEqual(config['rules'][2]['name'], "Organize PDF Documents")
        self.assertEqual(config['rules'][3]['name'], "Organize Archive Files")

    def test_get_cleanup_rules_config(self):
        """Test the cleanup rules preset."""
        config = preset_manager.get_cleanup_rules_config()
        self.assertIsPresetConfig(config, expected_rule_count=2)
        self.assertEqual(config['rules'][0]['name'], "Clean Temporary Files")
        self.assertEqual(config['rules'][1]['name'], "Find Duplicates in Downloads")

    # --- Tests for get_default_organization_config ---

    @patch('organize_gui.core.preset_manager.os.path.exists')
    @patch('organize_gui.core.preset_manager.open', new_callable=mock_open, read_data="rules:\n  - name: Loaded Rule")
    @patch('organize_gui.core.preset_manager.yaml.safe_load')
    def test_get_default_config_found_and_loaded(self, mock_safe_load, mock_open_func, mock_exists):
        """Test loading default config when file exists and loads correctly."""
        # Simulate finding the file at the first possible path
        mock_exists.side_effect = lambda p: p == preset_manager.possible_paths[0]
        mock_loaded_data = {'rules': [{'name': 'Loaded Rule'}]}
        mock_safe_load.return_value = mock_loaded_data

        config = preset_manager.get_default_organization_config()

        mock_exists.assert_called_with(preset_manager.possible_paths[0])
        mock_open_func.assert_called_once_with(preset_manager.possible_paths[0], 'r')
        mock_safe_load.assert_called_once()
        self.assertEqual(config, mock_loaded_data)

    @patch('organize_gui.core.preset_manager.os.path.exists')
    @patch('organize_gui.core.preset_manager.open', new_callable=mock_open, read_data="invalid yaml:")
    @patch('organize_gui.core.preset_manager.yaml.safe_load', side_effect=yaml.YAMLError("Load failed"))
    def test_get_default_config_found_but_load_fails(self, mock_safe_load, mock_open_func, mock_exists):
        """Test fallback when default config exists but fails to load."""
        mock_exists.side_effect = lambda p: p == preset_manager.possible_paths[1] # Simulate finding it at second path

        config = preset_manager.get_default_organization_config()

        mock_exists.assert_any_call(preset_manager.possible_paths[0])
        mock_exists.assert_any_call(preset_manager.possible_paths[1])
        mock_open_func.assert_called_once_with(preset_manager.possible_paths[1], 'r')
        mock_safe_load.assert_called_once()
        self.assertEqual(config, {'rules': []}) # Should return fallback

    @patch('organize_gui.core.preset_manager.os.path.exists', return_value=False)
    @patch('organize_gui.core.preset_manager.open', new_callable=mock_open)
    @patch('organize_gui.core.preset_manager.yaml.safe_load')
    def test_get_default_config_not_found(self, mock_safe_load, mock_open_func, mock_exists):
        """Test fallback when no default config file is found."""
        config = preset_manager.get_default_organization_config()

        # Check that all possible paths were checked
        self.assertEqual(mock_exists.call_count, len(preset_manager.possible_paths))
        for path in preset_manager.possible_paths:
            mock_exists.assert_any_call(path)

        mock_open_func.assert_not_called()
        mock_safe_load.assert_not_called()
        self.assertEqual(config, {'rules': []}) # Should return fallback


if __name__ == '__main__':
    unittest.main()
