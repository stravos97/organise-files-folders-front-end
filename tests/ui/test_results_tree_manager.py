"""
Unit tests for organize_gui.ui.results_tree_manager
"""

import unittest
from unittest.mock import MagicMock

# Adjust import path as necessary
from organize_gui.ui.results_tree_manager import ResultsTreeManager

class TestResultsTreeManagerFormatSize(unittest.TestCase):
    """Test suite specifically for the _format_size logic."""

    def setUp(self):
        """Set up a dummy ResultsTreeManager instance for testing internal methods."""
        # Mock the parent frame, not needed for _format_size
        mock_parent = MagicMock()
        self.manager = ResultsTreeManager(mock_parent)
        # Prevent actual widget creation during tests
        self.manager._create_widgets = MagicMock()

    def test_format_size_zero(self):
        """Test formatting zero bytes."""
        self.assertEqual(self.manager._format_size(0), "0 B")

    def test_format_size_bytes(self):
        """Test formatting sizes in bytes."""
        self.assertEqual(self.manager._format_size(1), "1 B")
        self.assertEqual(self.manager._format_size(1023), "1023 B")

    def test_format_size_kilobytes(self):
        """Test formatting sizes in kilobytes."""
        self.assertEqual(self.manager._format_size(1024), "1.00 KB")
        self.assertEqual(self.manager._format_size(1536), "1.50 KB") # 1.5 KB
        self.assertEqual(self.manager._format_size(1024 * 500), "500.00 KB")
        self.assertEqual(self.manager._format_size(1024 * 1023), "1023.00 KB")

    def test_format_size_megabytes(self):
        """Test formatting sizes in megabytes."""
        self.assertEqual(self.manager._format_size(1024 * 1024), "1.00 MB")
        self.assertEqual(self.manager._format_size(1024 * 1024 * 2.75), "2.75 MB")
        self.assertEqual(self.manager._format_size(1024 * 1024 * 900.123), "900.12 MB")

    def test_format_size_gigabytes(self):
        """Test formatting sizes in gigabytes."""
        self.assertEqual(self.manager._format_size(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(self.manager._format_size(1024**3 * 15.8), "15.80 GB")

    def test_format_size_terabytes(self):
        """Test formatting sizes in terabytes."""
        self.assertEqual(self.manager._format_size(1024**4), "1.00 TB")
        self.assertEqual(self.manager._format_size(1024**4 * 3.14159), "3.14 TB")

    def test_format_size_petabytes(self):
        """Test formatting sizes in petabytes."""
        self.assertEqual(self.manager._format_size(1024**5), "1.00 PB")
        self.assertEqual(self.manager._format_size(1024**5 * 123), "123.00 PB")

    def test_format_size_large_petabytes(self):
        """Test formatting sizes beyond petabytes (should stay PB)."""
        self.assertEqual(self.manager._format_size(1024**6), "1024.00 PB") # Stays PB


# Note: Testing other methods like populate_tree, sorting, context menus,
# and the details dialog is not practical with standard unit tests due to
# heavy reliance on Tkinter widgets and events.

if __name__ == '__main__':
    unittest.main()
