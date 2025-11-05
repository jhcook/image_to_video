#!/usr/bin/env python3
"""
Test that unknown command-line arguments are rejected.
"""
import unittest
from video_gen.arg_parser import SoraArgumentParser


class TestUnknownArguments(unittest.TestCase):
    """Test unknown argument validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = SoraArgumentParser()
    
    def test_unknown_flag_raises(self):
        """Test that unknown flags raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.parser.parse_arguments(["test prompt", "--backend", "veo3"])
        
        error_msg = str(ctx.exception)
        self.assertIn("--backend", error_msg)
        self.assertIn("Unknown argument", error_msg)
    
    def test_unknown_short_flag_raises(self):
        """Test that unknown short flags raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.parser.parse_arguments(["test prompt", "-x"])
        
        error_msg = str(ctx.exception)
        self.assertIn("-x", error_msg)
        self.assertIn("Unknown argument", error_msg)
    
    def test_unknown_option_with_value_raises(self):
        """Test that unknown options with values raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.parser.parse_arguments(["test prompt", "--invalid-option", "value"])
        
        error_msg = str(ctx.exception)
        self.assertIn("--invalid-option", error_msg)
        self.assertIn("Unknown argument", error_msg)
    
    def test_multiple_unknown_args_first_is_caught(self):
        """Test that first unknown argument is caught when multiple present."""
        with self.assertRaises(ValueError) as ctx:
            self.parser.parse_arguments([
                "test prompt",
                "--unknown1", "val1",
                "--unknown2", "val2"
            ])
        
        error_msg = str(ctx.exception)
        # Should catch the first unknown argument
        self.assertIn("--unknown1", error_msg)
    
    def test_valid_arguments_pass(self):
        """Test that valid arguments don't raise errors."""
        # Should not raise
        result = self.parser.parse_arguments([
            "test prompt",
            "--provider", "openai",
            "--model", "sora-2"
        ])
        
        self.assertEqual(result['prompt'], "test prompt")
        self.assertEqual(result['provider'], "openai")
        self.assertEqual(result['model'], "sora-2")
    
    def test_all_valid_flags_pass(self):
        """Test that all valid flags are accepted."""
        # Should not raise
        result = self.parser.parse_arguments([
            "test prompt",
            "--provider", "openai",
            "--width", "1920",
            "--height", "1080",
            "--fps", "30",
            "--duration", "10",
            "--seed", "42",
            "--model", "sora-2",
            "--output", "test.mp4"
        ])
        
        self.assertEqual(result['width'], 1920)
        self.assertEqual(result['height'], 1080)
        self.assertEqual(result['fps'], 30)
        self.assertEqual(result['duration'], 10)
        self.assertEqual(result['seed'], 42)
    
    def test_boolean_flags_pass(self):
        """Test that boolean flags are accepted."""
        # Should not raise
        result = self.parser.parse_arguments([
            "--stitch",
            "--resume",
            "--google-login",
            "-p", "prompt1", "prompt2", "prompt3"
        ])
        
        self.assertTrue(result['stitch'])
        self.assertTrue(result['resume'])
        self.assertTrue(result['google-login'])
    
    def test_typo_in_flag_is_caught(self):
        """Test that typos in flag names are caught."""
        # Common typos that should be caught
        typos = [
            "--providor",  # typo in provider
            "--widht",     # typo in width
            "--modell",    # typo in model
            "--imges",     # typo in images
        ]
        
        for typo in typos:
            with self.subTest(typo=typo):
                with self.assertRaises(ValueError) as ctx:
                    self.parser.parse_arguments(["test prompt", typo, "value"])
                
                error_msg = str(ctx.exception)
                self.assertIn(typo, error_msg)
                self.assertIn("Unknown argument", error_msg)


if __name__ == "__main__":
    unittest.main()
