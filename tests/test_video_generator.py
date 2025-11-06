"""
Unit tests for video_generator.py helper functions.

Tests the refactored helper functions that support video generation
and stitching workflows, including config loading, model validation,
output path generation, and resume state computation.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from video_gen.video_stitching import get_stitch_config
from video_gen.video_utils import (
    validate_stitch_model,
    build_expected_out_paths,
    compute_resume_state,
)
from video_gen.config import Veo3Config, RunwayConfig


class TestStitchConfigLoading(unittest.TestCase):
    """Test _get_stitch_config helper function."""

    @patch('video_gen.video_stitching.Veo3Config.from_environment')
    def test_veo3_provider_loads_veo3_config(self, mock_from_env: Mock) -> None:
        """Should load Veo3Config when provider is veo3 and config is None."""
        mock_config = MagicMock(spec=Veo3Config)
        mock_from_env.return_value = mock_config
        
        result = get_stitch_config("veo3", None)
        
        mock_from_env.assert_called_once()
        self.assertEqual(result, mock_config)

    @patch('video_gen.video_stitching.RunwayConfig.from_environment')
    def test_runway_provider_loads_runway_config(self, mock_from_env: Mock) -> None:
        """Should load RunwayConfig when provider is runway and config is None."""
        mock_config = MagicMock(spec=RunwayConfig)
        mock_from_env.return_value = mock_config
        
        result = get_stitch_config("runway", None)
        
        mock_from_env.assert_called_once()
        self.assertEqual(result, mock_config)

    def test_returns_provided_config_when_not_none(self):
        """Should return the provided config without loading from environment."""
        mock_config = MagicMock(spec=Veo3Config)
        
        result = get_stitch_config("veo3", mock_config)
        
        self.assertEqual(result, mock_config)


class TestStitchModelValidation(unittest.TestCase):
    """Test _validate_stitch_model helper function."""

    def test_valid_veo3_model_passes(self):
        """Should not raise for valid veo3 model."""
        try:
            validate_stitch_model("veo3")
            validate_stitch_model("veo3.1")
            validate_stitch_model("veo3.1_fast")
        except ValueError:
            self.fail("_validate_stitch_model raised ValueError for valid veo model")

    def test_valid_google_veo_model_passes(self):
        """Should not raise for valid Google Veo model names."""
        try:
            validate_stitch_model("veo-3.1-generate-preview")
            validate_stitch_model("veo-3.1-fast-generate-preview")
            validate_stitch_model("veo-3.0-generate-001")
        except ValueError:
            self.fail("_validate_stitch_model raised ValueError for valid veo model")

    def test_invalid_model_raises(self):
        """Should raise ValueError for non-veo models."""
        with self.assertRaises(ValueError) as ctx:
            validate_stitch_model("gen4")
        
        self.assertIn("Stitching is only supported for Veo models", str(ctx.exception))

    def test_none_model_raises(self):
        """Should raise ValueError when model is None."""
        with self.assertRaises(ValueError) as ctx:
            validate_stitch_model(None)
        
        self.assertIn("Stitching is only supported for Veo models", str(ctx.exception))

    def test_empty_string_model_raises(self):
        """Should raise ValueError when model is empty string."""
        with self.assertRaises(ValueError) as ctx:
            validate_stitch_model("")
        
        self.assertIn("Stitching is only supported for Veo models", str(ctx.exception))


class TestBuildExpectedOutPaths(unittest.TestCase):
    """Test build_expected_out_paths helper function."""

    def test_with_custom_out_paths(self):
        """Should return custom paths when provided."""
        custom_paths = ["custom1.mp4", "custom2.mp4", "custom3.mp4"]
        
        result = build_expected_out_paths(3, custom_paths, "veo3")
        
        self.assertEqual(result, custom_paths)

    def test_default_paths_veo3_provider(self):
        """Should generate veo3_clip_N.mp4 for veo3 provider."""
        result = build_expected_out_paths(3, None, "veo3")
        
        self.assertEqual(result, [
            "veo3_clip_1.mp4",
            "veo3_clip_2.mp4",
            "veo3_clip_3.mp4",
        ])

    def test_default_paths_runway_provider(self):
        """Should generate runway_veo_clip_N.mp4 for runway provider."""
        result = build_expected_out_paths(3, None, "runway")
        
        self.assertEqual(result, [
            "runway_veo_clip_1.mp4",
            "runway_veo_clip_2.mp4",
            "runway_veo_clip_3.mp4",
        ])

    def test_single_clip(self):
        """Should generate single clip path correctly."""
        result = build_expected_out_paths(1, None, "veo3")
        
        self.assertEqual(result, ["veo3_clip_1.mp4"])

    def test_many_clips(self):
        """Should handle larger clip counts."""
        result = build_expected_out_paths(10, None, "runway")
        
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0], "runway_veo_clip_1.mp4")
        self.assertEqual(result[9], "runway_veo_clip_10.mp4")


class TestComputeResumeState(unittest.TestCase):
    """Test compute_resume_state helper function."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_file(self, name: str, size: int = 100):
        """Helper to create a test file with given size."""
        path = Path(self.temp_dir) / name
        path.write_bytes(b"x" * size)
        return str(path)

    def test_no_existing_clips(self):
        """Should return empty state when no clips exist."""
        expected_paths = [
            str(Path(self.temp_dir) / "clip1.mp4"),
            str(Path(self.temp_dir) / "clip2.mp4"),
        ]
        
        outputs, start_idx, last_frame = compute_resume_state(expected_paths)
        
        self.assertEqual(outputs, [])
        self.assertEqual(start_idx, 0)
        self.assertIsNone(last_frame)

    def test_all_clips_completed(self):
        """Should detect all completed clips and extract last frame."""
        clip1 = self._create_test_file("clip1.mp4")
        clip2 = self._create_test_file("clip2.mp4")
        expected_paths = [clip1, clip2]
        
        with patch('video_gen.video_utils.extract_last_frame_as_png') as mock_extract:
            mock_extract.return_value = "/tmp/last_frame.png"
            
            outputs, start_idx, last_frame = compute_resume_state(expected_paths)
        
        self.assertEqual(outputs, [clip1, clip2])
        self.assertEqual(start_idx, 2)  # Should start after last clip
        mock_extract.assert_called_once_with(clip2)
        self.assertEqual(last_frame, "/tmp/last_frame.png")

    def test_partial_completion(self):
        """Should detect partially completed clips."""
        clip1 = self._create_test_file("clip1.mp4")
        clip2_path = str(Path(self.temp_dir) / "clip2.mp4")  # doesn't exist
        clip3_path = str(Path(self.temp_dir) / "clip3.mp4")  # doesn't exist
        expected_paths = [clip1, clip2_path, clip3_path]
        
        with patch('video_gen.video_utils.extract_last_frame_as_png') as mock_extract:
            mock_extract.return_value = "/tmp/last_frame.png"
            
            outputs, start_idx, _ = compute_resume_state(expected_paths)
        
        self.assertEqual(outputs, [clip1])
        self.assertEqual(start_idx, 1)  # Should resume at clip 2
        mock_extract.assert_called_once_with(clip1)

    def test_zero_byte_file_not_counted(self):
        """Should skip zero-byte files (incomplete downloads)."""
        clip1 = self._create_test_file("clip1.mp4", size=100)
        clip2 = self._create_test_file("clip2.mp4", size=0)  # zero bytes
        clip3_path = str(Path(self.temp_dir) / "clip3.mp4")  # doesn't exist
        expected_paths = [clip1, clip2, clip3_path]
        
        with patch('video_gen.video_utils.extract_last_frame_as_png') as mock_extract:
            mock_extract.return_value = "/tmp/last_frame.png"
            
            outputs, start_idx, _ = compute_resume_state(expected_paths)
        
        # Should stop at clip1 since clip2 is zero bytes
        self.assertEqual(outputs, [clip1])
        self.assertEqual(start_idx, 1)

    def test_frame_extraction_failure_returns_none(self):
        """Should return None for last_frame if extraction fails."""
        clip1 = self._create_test_file("clip1.mp4")
        expected_paths = [clip1]
        
        with patch('video_gen.video_utils.extract_last_frame_as_png') as mock_extract:
            mock_extract.side_effect = RuntimeError("ffmpeg failed")
            
            outputs, start_idx, last_frame = compute_resume_state(expected_paths)
        
        self.assertEqual(outputs, [clip1])
        self.assertEqual(start_idx, 1)
        self.assertIsNone(last_frame)  # Should gracefully handle failure


if __name__ == "__main__":
    unittest.main()
