"""
Unit tests for organize_gui.core.duplicate_helpers
"""

import unittest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Assuming the module is importable relative to the tests directory
# Adjust the import path if necessary based on your project structure and how tests are run
from organize_gui.core.duplicate_helpers import score_metadata, decide_music_duplicate

class TestScoreMetadata(unittest.TestCase):
    """Test suite for the score_metadata function."""

    @patch('organize_gui.core.duplicate_helpers.Path')
    @patch('organize_gui.core.duplicate_helpers.mutagen.File')
    @patch('organize_gui.core.duplicate_helpers.os.path.getsize')
    def test_file_not_found(self, mock_getsize, mock_mutagen_file, mock_path):
        """Test score is 0 if file does not exist."""
        mock_path_instance = mock_path.return_value
        mock_path_instance.is_file.return_value = False
        self.assertEqual(score_metadata("nonexistent.mp3"), 0)
        mock_path.assert_called_once_with("nonexistent.mp3")
        mock_path_instance.is_file.assert_called_once()
        mock_mutagen_file.assert_not_called()
        mock_getsize.assert_not_called()

    @patch('organize_gui.core.duplicate_helpers.Path')
    @patch('organize_gui.core.duplicate_helpers.mutagen.File')
    @patch('organize_gui.core.duplicate_helpers.os.path.getsize')
    def test_mutagen_load_error(self, mock_getsize, mock_mutagen_file, mock_path):
        """Test score is 0 if mutagen cannot load the file."""
        mock_path_instance = mock_path.return_value
        mock_path_instance.is_file.return_value = True
        mock_mutagen_file.return_value = None # Simulate mutagen failing to load
        self.assertEqual(score_metadata("badfile.mp3"), 0)
        mock_path.assert_called_once_with("badfile.mp3")
        mock_path_instance.is_file.assert_called_once()
        mock_mutagen_file.assert_called_once_with(mock_path_instance)
        mock_getsize.assert_not_called() # Should not be called if mutagen fails

    @patch('organize_gui.core.duplicate_helpers.Path')
    @patch('organize_gui.core.duplicate_helpers.mutagen.File')
    @patch('organize_gui.core.duplicate_helpers.os.path.getsize')
    def test_id3_scoring_full(self, mock_getsize, mock_mutagen_file, mock_path):
        """Test ID3 scoring with all tags present."""
        mock_path_instance = mock_path.return_value
        mock_path_instance.is_file.return_value = True
        mock_getsize.return_value = 5_000_000 # 5MB -> 0.5 size score
        mock_audio = MagicMock()
        mock_audio.tags = True
        mock_audio.__contains__.side_effect = lambda key: key in ['TPE1', 'TIT2', 'TALB', 'TDRC', 'TCON', 'APIC:']
        mock_mutagen_file.return_value = mock_audio
        # Expected score: 1+1+1+1+1+0.5+0.5 = 6.0
        self.assertEqual(score_metadata("full_tags.mp3"), 6.0)

    @patch('organize_gui.core.duplicate_helpers.Path')
    @patch('organize_gui.core.duplicate_helpers.mutagen.File')
    @patch('organize_gui.core.duplicate_helpers.os.path.getsize')
    def test_id3_scoring_partial(self, mock_getsize, mock_mutagen_file, mock_path):
        """Test ID3 scoring with partial tags."""
        mock_path_instance = mock_path.return_value
        mock_path_instance.is_file.return_value = True
        mock_getsize.return_value = 5_000_000 # 5MB -> 0.5 size score
        mock_audio = MagicMock()
        mock_audio.tags = True
        mock_audio.__contains__.side_effect = lambda key: key in ['TPE1', 'TIT2'] # Only Artist, Title
        mock_mutagen_file.return_value = mock_audio
        # Expected score: 1+1+0+0+0+0+0.5 = 2.5
        self.assertEqual(score_metadata("partial_tags.mp3"), 2.5)

    @patch('organize_gui.core.duplicate_helpers.Path')
    @patch('organize_gui.core.duplicate_helpers.mutagen.File')
    @patch('organize_gui.core.duplicate_helpers.os.path.getsize')
    def test_id3_scoring_no_tags(self, mock_getsize, mock_mutagen_file, mock_path):
        """Test ID3 scoring with no tags."""
        mock_path_instance = mock_path.return_value
        mock_path_instance.is_file.return_value = True
        mock_getsize.return_value = 5_000_000 # 5MB -> 0.5 size score

        # Configure mock specifically for this case: has 'tags' attribute but it's None
        # Use spec to limit attributes, preventing accidental matching of other types
        mock_audio = MagicMock(spec=['tags']) # Only allow 'tags' attribute
        mock_audio.tags = None # Set tags to None (falsey)

        mock_mutagen_file.return_value = mock_audio
        # Expected score: 0 + 0.5 = 0.5
        self.assertEqual(score_metadata("no_tags.mp3"), 0.5)

    @patch('organize_gui.core.duplicate_helpers.Path')
    @patch('organize_gui.core.duplicate_helpers.mutagen.File')
    @patch('organize_gui.core.duplicate_helpers.os.path.getsize')
    def test_flac_vorbis_scoring(self, mock_getsize, mock_mutagen_file, mock_path):
        """Test scoring logic for FLAC/Vorbis tags."""
        mock_path_instance = mock_path.return_value
        mock_path_instance.is_file.return_value = True
        mock_getsize.return_value = 15_000_000 # 15MB -> 1.0 size score (capped)

        # Mock a FLAC/Vorbis file (dictionary-like access)
        mock_audio = MagicMock()
        mock_audio.tags = None # No ID3 tags attribute
        mock_audio.pictures = [] # No pictures initially
        mock_audio.get.side_effect = lambda key, default=None: {
            'artist': 'Artist Name', 'title': 'Track Title', 'album': 'Album Name',
            'date': '2023', 'genre': 'Rock'
        }.get(key, default)
        mock_mutagen_file.return_value = mock_audio

        # Expected score: 1(Artist)+1(Title)+1(Album)+1(Year)+1(Genre)+0(Art)+1.0(Size) = 6.0
        self.assertEqual(score_metadata("full_tags.flac"), 6.0)

        # Add picture
        mock_audio.pictures = [MagicMock()] # Simulate having a picture
        # Expected score: 1(Artist)+1(Title)+1(Album)+1(Year)+1(Genre)+0.5(Art)+1.0(Size) = 6.5
        self.assertEqual(score_metadata("full_tags_with_art.flac"), 6.5)

        # Partial tags
        mock_audio.pictures = []
        mock_audio.get.side_effect = lambda key, default=None: {'artist': 'Artist Name'}.get(key, default)
        # Expected score: 1(Artist)+0(Title)+0(Album)+0(Year)+0(Genre)+0(Art)+1.0(Size) = 2.0
        self.assertEqual(score_metadata("partial_tags.flac"), 2.0)

    @patch('organize_gui.core.duplicate_helpers.Path')
    @patch('organize_gui.core.duplicate_helpers.mutagen.File')
    @patch('organize_gui.core.duplicate_helpers.os.path.getsize')
    def test_mp4_aac_scoring_full(self, mock_getsize, mock_mutagen_file, mock_path):
        """Test MP4/AAC scoring with full tags."""
        mock_path_instance = mock_path.return_value
        mock_path_instance.is_file.return_value = True
        mock_getsize.return_value = 8_000_000 # 8MB -> 0.8 size score
        mock_audio = MagicMock()
        mock_audio.tags = None
        mock_audio.pictures = None
        mp4_tags = {
            '\xa9ART': ['Artist Name'], '\xa9nam': ['Track Title'], '\xa9alb': ['Album Name'],
            '\xa9day': ['2023'], '\xa9gen': ['Pop'], 'covr': [b'imagedata']
        }
        mock_audio.items.return_value = mp4_tags.items()
        mock_audio.keys.return_value = mp4_tags.keys()
        mock_audio.hasattr.side_effect = lambda attr: attr == 'items'
        mock_mutagen_file.return_value = mock_audio
        # Expected score: 1+1+1+1+1+0.5+0.8 = 5.8
        self.assertEqual(score_metadata("full_tags.m4a"), 5.8)

    @patch('organize_gui.core.duplicate_helpers.Path')
    @patch('organize_gui.core.duplicate_helpers.mutagen.File')
    @patch('organize_gui.core.duplicate_helpers.os.path.getsize')
    def test_mp4_aac_scoring_partial(self, mock_getsize, mock_mutagen_file, mock_path):
        """Test MP4/AAC scoring with partial tags."""
        mock_path_instance = mock_path.return_value
        mock_path_instance.is_file.return_value = True
        mock_getsize.return_value = 8_000_000 # 8MB -> 0.8 size score

        # Configure mock specifically for this case: has 'items' and 'keys', but not 'tags' or 'get'
        # Use spec to limit attributes
        mock_audio = MagicMock(spec=['items', 'keys', 'pictures']) # Allow only these attributes
        mock_audio.pictures = None # Explicitly set pictures to None
        mp4_tags = {'\xa9ART': ['Artist Name']}
        mock_audio.items.return_value = mp4_tags.items()
        mock_audio.keys.return_value = mp4_tags.keys()

        # Mock hasattr to only return True for 'items' (needed by score_metadata)
        # We need hasattr on the mock itself for the check in score_metadata
        mock_audio.hasattr = MagicMock(side_effect=lambda attr: attr == 'items')

        mock_mutagen_file.return_value = mock_audio
        # Expected score: 1+0+0+0+0+0+0.8 = 1.8
        self.assertEqual(score_metadata("partial_tags.m4a"), 1.8)

    @patch('organize_gui.core.duplicate_helpers.Path')
    @patch('organize_gui.core.duplicate_helpers.mutagen.File', side_effect=Exception("Mutagen error"))
    @patch('organize_gui.core.duplicate_helpers.os.path.getsize')
    def test_generic_exception_handling(self, mock_getsize, mock_mutagen_file, mock_path):
        """Test score is 0 if any unexpected exception occurs."""
        mock_path_instance = mock_path.return_value
        mock_path_instance.is_file.return_value = True
        self.assertEqual(score_metadata("exception.file"), 0)
        mock_mutagen_file.assert_called_once()
        mock_getsize.assert_not_called() # Should not be called if mutagen raises exception


class TestDecideMusicDuplicate(unittest.TestCase):
    """Test suite for the decide_music_duplicate function."""

    @patch('organize_gui.core.duplicate_helpers.os.path.exists')
    @patch('organize_gui.core.duplicate_helpers.score_metadata')
    def test_current_better_score(self, mock_score_metadata, mock_exists):
        """Test returns False (keep current) if current score is higher."""
        mock_exists.return_value = True # Both files exist
        mock_score_metadata.side_effect = [3.0, 5.0] # original_score, current_score
        duplicate_info = {"original": "/path/to/original.mp3"}
        current_path = Path("/path/to/current.mp3")

        self.assertFalse(decide_music_duplicate(duplicate_info, current_path))
        mock_exists.assert_any_call("/path/to/original.mp3")
        mock_exists.assert_any_call("/path/to/current.mp3")
        mock_score_metadata.assert_any_call("/path/to/original.mp3")
        mock_score_metadata.assert_any_call("/path/to/current.mp3")

    @patch('organize_gui.core.duplicate_helpers.os.path.exists')
    @patch('organize_gui.core.duplicate_helpers.score_metadata')
    def test_original_better_score(self, mock_score_metadata, mock_exists):
        """Test returns True (mark current as duplicate) if original score is higher."""
        mock_exists.return_value = True
        mock_score_metadata.side_effect = [5.0, 3.0] # original_score, current_score
        duplicate_info = {"original": "/path/to/original.mp3"}
        current_path = Path("/path/to/current.mp3")

        self.assertTrue(decide_music_duplicate(duplicate_info, current_path))
        mock_score_metadata.assert_any_call("/path/to/original.mp3")
        mock_score_metadata.assert_any_call("/path/to/current.mp3")

    @patch('organize_gui.core.duplicate_helpers.os.path.exists')
    @patch('organize_gui.core.duplicate_helpers.score_metadata')
    def test_equal_score(self, mock_score_metadata, mock_exists):
        """Test returns True (mark current as duplicate) if scores are equal."""
        mock_exists.return_value = True
        mock_score_metadata.side_effect = [4.0, 4.0] # original_score, current_score
        duplicate_info = {"original": "/path/to/original.mp3"}
        current_path = Path("/path/to/current.mp3")

        self.assertTrue(decide_music_duplicate(duplicate_info, current_path))
        mock_score_metadata.assert_any_call("/path/to/original.mp3")
        mock_score_metadata.assert_any_call("/path/to/current.mp3")

    @patch('organize_gui.core.duplicate_helpers.os.path.exists')
    @patch('organize_gui.core.duplicate_helpers.score_metadata')
    def test_original_missing(self, mock_score_metadata, mock_exists):
        """Test returns True (mark current as duplicate) if original file is missing."""
        mock_exists.side_effect = lambda p: p != "/path/to/original.mp3" # Original doesn't exist
        duplicate_info = {"original": "/path/to/original.mp3"}
        current_path = Path("/path/to/current.mp3")

        self.assertTrue(decide_music_duplicate(duplicate_info, current_path))
        mock_exists.assert_any_call("/path/to/original.mp3")
        mock_score_metadata.assert_not_called() # Scoring shouldn't happen if file missing

    @patch('organize_gui.core.duplicate_helpers.os.path.exists')
    @patch('organize_gui.core.duplicate_helpers.score_metadata')
    def test_current_missing(self, mock_score_metadata, mock_exists):
        """Test returns True (mark current as duplicate) if current file is missing (defensive)."""
        mock_exists.side_effect = lambda p: p != "/path/to/current.mp3" # Current doesn't exist
        duplicate_info = {"original": "/path/to/original.mp3"}
        current_path = Path("/path/to/current.mp3")

        self.assertTrue(decide_music_duplicate(duplicate_info, current_path))
        mock_exists.assert_any_call("/path/to/original.mp3")
        mock_exists.assert_any_call("/path/to/current.mp3")
        mock_score_metadata.assert_not_called()

    @patch('organize_gui.core.duplicate_helpers.os.path.exists', return_value=True)
    @patch('organize_gui.core.duplicate_helpers.score_metadata', side_effect=Exception("Scoring error"))
    def test_scoring_exception(self, mock_score_metadata, mock_exists):
        """Test returns True (mark current as duplicate) if score_metadata raises exception."""
        duplicate_info = {"original": "/path/to/original.mp3"}
        current_path = Path("/path/to/current.mp3")

        self.assertTrue(decide_music_duplicate(duplicate_info, current_path))
        # score_metadata should be called at least once before raising exception
        mock_score_metadata.assert_called()


if __name__ == '__main__':
    unittest.main()
