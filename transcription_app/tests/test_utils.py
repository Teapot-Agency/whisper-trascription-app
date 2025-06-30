"""Unit tests for utility functions."""

import unittest
import tempfile
import os
from ..utils.file_utils import sanitize_filename, validate_audio_file, get_file_info
from ..utils.dependencies import safe_import_pydub, safe_import_ffmpeg

class TestFileUtils(unittest.TestCase):
    """Test file utility functions."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test normal filename
        self.assertEqual(sanitize_filename("normal_file.mp3"), "normal_file.mp3")
        
        # Test filename with invalid characters
        self.assertEqual(sanitize_filename("file<>with|invalid?.mp3"), "file__with_invalid_.mp3")
        
        # Test very long filename
        long_name = "a" * 200 + ".mp3"
        sanitized = sanitize_filename(long_name)
        self.assertTrue(len(sanitized) <= 100)
        self.assertTrue(sanitized.endswith(".mp3"))
    
    def test_validate_audio_file(self):
        """Test audio file validation."""
        # Test with None
        valid, error = validate_audio_file(None, ['mp3', 'wav'])
        self.assertFalse(valid)
        self.assertIn("No file uploaded", error)

class TestDependencies(unittest.TestCase):
    """Test dependency checking functions."""
    
    def test_safe_import_pydub(self):
        """Test safe pydub import."""
        AudioSegment, split_on_silence, error = safe_import_pydub()
        # Should either work or fail gracefully
        if AudioSegment is None:
            self.assertIsNotNone(error)
        else:
            self.assertIsNone(error)
    
    def test_safe_import_ffmpeg(self):
        """Test safe ffmpeg import."""
        ffmpeg, error = safe_import_ffmpeg()
        # Should either work or fail gracefully
        if ffmpeg is None:
            self.assertIsNotNone(error)
        else:
            self.assertIsNone(error)

if __name__ == '__main__':
    unittest.main()