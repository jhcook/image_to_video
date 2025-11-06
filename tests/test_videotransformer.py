import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import argparse

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from videotransformer import (
    create_parser,
    validate_video_file,
    check_credentials_and_display_header,
    display_transformation_info,
    handle_exceptions,
    main
)


class TestCreateParser(unittest.TestCase):
    """Test argument parser creation and configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = create_parser()

    def test_parser_creation(self):
        """Test that parser is created with correct program name."""
        self.assertIsInstance(self.parser, argparse.ArgumentParser)
        self.assertEqual(self.parser.prog, "videotransformer.py")

    def test_required_arguments(self):
        """Test that required arguments are properly configured."""
        # Should require --video and -p/--prompt
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])

        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--video", "test.mp4"])

        with self.assertRaises(SystemExit):
            self.parser.parse_args(["-p", "test prompt"])

    def test_video_argument(self):
        """Test video argument configuration."""
        args = self.parser.parse_args(["--video", "input.mp4", "-p", "test"])
        self.assertEqual(args.video, "input.mp4")

    def test_prompt_arguments(self):
        """Test prompt argument configuration."""
        # Test -p flag
        args = self.parser.parse_args(["-p", "transform this", "--video", "test.mp4"])
        self.assertEqual(args.prompt, "transform this")

        # Test --prompt flag
        args = self.parser.parse_args(["--prompt", "another prompt", "--video", "test.mp4"])
        self.assertEqual(args.prompt, "another prompt")

    def test_optional_arguments_defaults(self):
        """Test optional arguments have correct defaults."""
        args = self.parser.parse_args(["--video", "test.mp4", "-p", "prompt"])

        self.assertEqual(args.width, 1280)
        self.assertEqual(args.height, 720)
        self.assertEqual(args.duration, 5)
        self.assertIsNone(args.seed)
        self.assertIsNone(args.output)
        self.assertFalse(args.verbose)

    def test_optional_arguments_custom_values(self):
        """Test optional arguments accept custom values."""
        args = self.parser.parse_args([
            "--video", "test.mp4",
            "-p", "prompt",
            "--width", "1920",
            "--height", "1080",
            "--duration", "10",
            "--seed", "42",
            "--output", "output.mp4",
            "--verbose"
        ])

        self.assertEqual(args.width, 1920)
        self.assertEqual(args.height, 1080)
        self.assertEqual(args.duration, 10)
        self.assertEqual(args.seed, 42)
        self.assertEqual(args.output, "output.mp4")
        self.assertTrue(args.verbose)

    def test_duration_validation(self):
        """Test duration argument validation."""
        # Valid durations
        for duration in [2, 15, 30]:
            args = self.parser.parse_args([
                "--video", "test.mp4",
                "-p", "prompt",
                "--duration", str(duration)
            ])
            self.assertEqual(args.duration, duration)

        # Invalid durations should be rejected
        for invalid_duration in [1, 31, 100]:
            with self.assertRaises(SystemExit):
                self.parser.parse_args([
                    "--video", "test.mp4",
                    "-p", "prompt",
                    "--duration", str(invalid_duration)
                ])


class TestValidateVideoFile(unittest.TestCase):
    """Test video file validation functionality."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_file(self, name: str):
        """Helper to create a test file."""
        path = Path(self.temp_dir) / name
        path.write_text("dummy content")
        return str(path)

    def test_valid_video_file(self):
        """Test validation passes for existing files."""
        # Test various video extensions
        for ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm']:
            with self.subTest(ext=ext):
                video_path = self._create_test_file(f"test{ext}")
                # Should not raise
                validate_video_file(video_path)

    def test_nonexistent_file_raises(self):
        """Test that nonexistent files raise FileNotFoundError."""
        nonexistent_path = str(Path(self.temp_dir) / "nonexistent.mp4")
        with self.assertRaises(FileNotFoundError) as ctx:
            validate_video_file(nonexistent_path)

        self.assertIn("Video file not found", str(ctx.exception))
        self.assertIn(nonexistent_path, str(ctx.exception))

    def test_unknown_extension_warning(self):
        """Test that unknown extensions produce warnings but don't fail."""
        # This should work but might print a warning
        video_path = self._create_test_file("test.unknown")
        # Should not raise (we're permissive about extensions)
        validate_video_file(video_path)


class TestCheckCredentialsAndDisplayHeader(unittest.TestCase):
    """Test credential checking and header display."""

    @patch('videotransformer.RunwayConfig.from_environment')
    @patch('builtins.print')
    def test_credentials_found(self, mock_print: Mock, mock_from_env: Mock) -> None:
        """Test when API credentials are available."""
        mock_config = MagicMock()
        mock_config.api_key = "test_key"
        mock_from_env.return_value = mock_config

        result = check_credentials_and_display_header()

        mock_from_env.assert_called_once()
        self.assertEqual(result, mock_config)

        # Check that header was printed
        calls = mock_print.call_args_list
        self.assertTrue(any("🎬 AI Video Transformer" in str(call) for call in calls))
        self.assertTrue(any("✅ API credentials found" in str(call) for call in calls))

    @patch('videotransformer.RunwayConfig.from_environment')
    @patch('builtins.print')
    def test_credentials_missing(self, mock_print: Mock, mock_from_env: Mock) -> None:
        """Test when API credentials are missing."""
        mock_config = MagicMock()
        mock_config.api_key = None
        mock_from_env.return_value = mock_config

        with self.assertRaises(SystemExit):
            check_credentials_and_display_header()

        # Check that error message was printed
        calls = mock_print.call_args_list
        self.assertTrue(any("❌ API credentials not found" in str(call) for call in calls))


class TestDisplayTransformationInfo(unittest.TestCase):
    """Test transformation information display."""

    @patch('builtins.print')
    def test_display_basic_info(self, mock_print: Mock) -> None:
        """Test basic transformation info display."""
        args = argparse.Namespace(
            video="input.mp4",
            prompt="Transform this video",
            width=1280,
            height=720,
            duration=5,
            seed=None,
            output=None
        )

        display_transformation_info(args)

        calls = mock_print.call_args_list
        self.assertTrue(any("🎯 Video Transformation:" in str(call) for call in calls))
        self.assertTrue(any("input.mp4" in str(call) for call in calls))
        self.assertTrue(any("Transform this video" in str(call) for call in calls))

    @patch('builtins.print')
    def test_display_with_all_options(self, mock_print: Mock) -> None:
        """Test display with all optional parameters."""
        args = argparse.Namespace(
            video="input.mp4",
            prompt="Transform this video with options",
            width=1920,
            height=1080,
            duration=10,
            seed=42,
            output="output.mp4"
        )

        display_transformation_info(args)

        calls = mock_print.call_args_list
        output = " ".join(str(call) for call in calls)

        self.assertIn("1920x1080", output)
        self.assertIn("10 seconds", output)
        self.assertIn("Seed: 42", output)
        self.assertIn("output.mp4", output)


class TestHandleExceptions(unittest.TestCase):
    """Test exception handling functionality."""

    @patch('builtins.print')
    @patch('sys.exit')
    def test_authentication_error(self, mock_exit: Mock, mock_print: Mock) -> None:
        """Test AuthenticationError handling."""
        from video_gen.exceptions import AuthenticationError

        error = AuthenticationError("Invalid API key")
        handle_exceptions(error)

        calls = mock_print.call_args_list
        self.assertTrue(any("❌ Authentication Error:" in str(call) for call in calls))
        mock_exit.assert_called_once_with(1)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_file_not_found_error(self, mock_exit: Mock, mock_print: Mock) -> None:
        """Test FileNotFoundError handling."""
        error = FileNotFoundError("File not found: test.mp4")
        handle_exceptions(error)

        calls = mock_print.call_args_list
        self.assertTrue(any("❌ File Error:" in str(call) for call in calls))
        mock_exit.assert_called_once_with(1)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_400_bad_request_error(self, mock_exit: Mock, mock_print: Mock) -> None:
        """Test 400 Bad Request error handling."""
        error = Exception("400 Client Error: Bad Request - Invalid model")

        handle_exceptions(error)

        calls = mock_print.call_args_list
        self.assertTrue(any("❌ Invalid Request:" in str(call) for call in calls))
        self.assertTrue(any("Invalid model" in str(call) for call in calls))
        mock_exit.assert_called_once_with(1)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_insufficient_credits_error(self, mock_exit: Mock, mock_print: Mock) -> None:
        """Test insufficient credits error handling."""
        error = Exception("Insufficient credits")

        handle_exceptions(error)

        calls = mock_print.call_args_list
        self.assertTrue(any("💳 Insufficient Credits:" in str(call) for call in calls))
        mock_exit.assert_called_once_with(1)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_rate_limit_error(self, mock_exit: Mock, mock_print: Mock) -> None:
        """Test rate limit error handling."""
        error = Exception("Rate limit exceeded")

        handle_exceptions(error)

        calls = mock_print.call_args_list
        self.assertTrue(any("⏱️  Rate Limit Exceeded:" in str(call) for call in calls))
        mock_exit.assert_called_once_with(1)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_generic_error(self, mock_exit: Mock, mock_print: Mock) -> None:
        """Test generic error handling."""
        error = Exception("Some unexpected error")

        handle_exceptions(error)

        calls = mock_print.call_args_list
        self.assertTrue(any("❌ Unexpected Error:" in str(call) for call in calls))
        mock_exit.assert_called_once_with(1)


class TestMainFunction(unittest.TestCase):
    """Test the main function execution flow."""

    @patch('videotransformer.edit_video_with_runway_aleph')
    @patch('videotransformer.check_credentials_and_display_header')
    @patch('videotransformer.display_transformation_info')
    @patch('videotransformer.validate_video_file')
    @patch('videotransformer.init_library_logger')
    @patch('builtins.print')
    def test_main_success_flow(self, mock_print: Mock, mock_init_logger: Mock,
                              mock_validate: Mock, mock_display_info: Mock,
                              mock_check_creds: Mock, mock_edit_video: Mock) -> None:
        """Test successful main execution flow."""
        # Mock successful execution
        mock_config = MagicMock()
        mock_check_creds.return_value = mock_config
        mock_edit_video.return_value = "output_transformed.mp4"

        # Mock command line arguments
        test_args = [
            "--video", "input.mp4",
            "-p", "transform this video",
            "--width", "1280",
            "--height", "720",
            "--duration", "5"
        ]

        with patch('sys.argv', ['videotransformer.py'] + test_args):
            main()

        # Verify calls
        mock_validate.assert_called_once_with("input.mp4")
        mock_init_logger.assert_called_once()
        mock_check_creds.assert_called_once()
        mock_display_info.assert_called_once()
        mock_edit_video.assert_called_once_with(
            prompt="transform this video",
            video_path="input.mp4",
            width=1280,
            height=720,
            duration_seconds=5,
            seed=None,
            out_path=None,
            config=mock_config
        )

        # Check success message
        calls = mock_print.call_args_list
        self.assertTrue(any("✅ Video transformation completed successfully!" in str(call) for call in calls))

    @patch('videotransformer.validate_video_file')
    @patch('builtins.print')
    def test_main_validation_failure(self, mock_print: Mock, mock_validate: Mock) -> None:
        """Test main function when video validation fails."""
        mock_validate.side_effect = FileNotFoundError("Video file not found")

        test_args = ["--video", "nonexistent.mp4", "-p", "prompt"]

        with patch('sys.argv', ['videotransformer.py'] + test_args):
            with self.assertRaises(SystemExit):
                main()

        mock_validate.assert_called_once_with("nonexistent.mp4")

    @patch('videotransformer.check_credentials_and_display_header')
    @patch('videotransformer.validate_video_file')
    @patch('builtins.print')
    def test_main_credential_failure(self, mock_print: Mock, mock_validate: Mock, mock_check_creds: Mock) -> None:
        """Test main function when credentials check fails."""
        mock_check_creds.side_effect = SystemExit(1)

        test_args = ["--video", "input.mp4", "-p", "prompt"]

        with patch('sys.argv', ['videotransformer.py'] + test_args):
            with self.assertRaises(SystemExit):
                main()

        mock_validate.assert_called_once_with("input.mp4")
        mock_check_creds.assert_called_once()

    @patch('videotransformer.edit_video_with_runway_aleph')
    @patch('videotransformer.check_credentials_and_display_header')
    @patch('videotransformer.display_transformation_info')
    @patch('videotransformer.validate_video_file')
    @patch('videotransformer.init_library_logger')
    @patch('builtins.print')
    def test_main_with_verbose_output(self, mock_print: Mock, mock_init_logger: Mock,
                                     mock_validate: Mock, mock_display_info: Mock,
                                     mock_check_creds: Mock, mock_edit_video: Mock) -> None:
        """Test main function with verbose output enabled."""
        mock_config = MagicMock()
        mock_check_creds.return_value = mock_config
        mock_edit_video.return_value = "output.mp4"

        test_args = [
            "--video", "input.mp4",
            "-p", "transform this",
            "--verbose"
        ]

        with patch('sys.argv', ['videotransformer.py'] + test_args):
            main()

        # Verify verbose logger initialization
        mock_init_logger.assert_called_once_with(verbose=True, log_to_file=True)

    @patch('videotransformer.handle_exceptions')
    @patch('videotransformer.edit_video_with_runway_aleph')
    @patch('videotransformer.check_credentials_and_display_header')
    @patch('videotransformer.display_transformation_info')
    @patch('videotransformer.validate_video_file')
    @patch('videotransformer.init_library_logger')
    def test_main_transformation_error(self, mock_init_logger: Mock, mock_validate: Mock,
                                      mock_display_info: Mock, mock_check_creds: Mock,
                                      mock_edit_video: Mock, mock_handle_exceptions: Mock) -> None:
        """Test main function when video transformation fails."""
        mock_config = MagicMock()
        mock_check_creds.return_value = mock_config
        mock_edit_video.side_effect = Exception("Transformation failed")

        test_args = ["--video", "input.mp4", "-p", "prompt"]

        with patch('sys.argv', ['videotransformer.py'] + test_args):
            main()

        # Verify exception was handled
        mock_handle_exceptions.assert_called_once()
        args, _ = mock_handle_exceptions.call_args
        self.assertIsInstance(args[0], Exception)
        self.assertEqual(str(args[0]), "Transformation failed")


if __name__ == "__main__":
    unittest.main()