import unittest
import os
from video_gen.arg_parser import SoraArgumentParser


class TestSoraArgumentParser(unittest.TestCase):
    def setUp(self):
        # Ensure providers appear available for validation during tests
        os.environ.setdefault("OPENAI_API_KEY", "test-openai")
        os.environ.setdefault("AZURE_OPENAI_API_KEY", "test-azure")
        os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
        os.environ.setdefault("GOOGLE_API_KEY", "test-google")
        os.environ.setdefault("RUNWAY_API_KEY", "test-runway")
        self.parser = SoraArgumentParser()

    def test_positional_prompt_default_provider(self):
        args = self.parser.parse_arguments(["A simple prompt"])  # default provider openai
        self.assertEqual(args["provider"], "openai")
        self.assertEqual(args["prompt"], "A simple prompt")
        self.assertFalse(args["stitch"])        

    def test_single_prompt_flag(self):
        args = self.parser.parse_arguments(["-p", "Hello World"])  # -p single prompt
        self.assertEqual(args["prompt"], "Hello World")
        self.assertEqual(args["prompts"], [])  # normalized

    def test_stitching_mode_two_prompts(self):
        args = self.parser.parse_arguments([
            "--provider", "google",
            "--stitch",
            "-p", "Clip 1", "Clip 2",
            "--duration", "8",
            "--width", "1280",
            "--height", "720",
        ])
        self.assertEqual(args["provider"], "google")
        self.assertTrue(args["stitch"])
        self.assertEqual(args["prompts"], ["Clip 1", "Clip 2"])
        self.assertIsNone(args.get("prompt"))

    def test_azure_provider(self):
        args = self.parser.parse_arguments(["--provider", "azure", "Azure prompt"])
        self.assertEqual(args["provider"], "azure")
        self.assertEqual(args["prompt"], "Azure prompt")

    def test_invalid_provider_raises(self):
        with self.assertRaises(ValueError):
            self.parser.parse_arguments(["--provider", "invalid", "A prompt"])        

    def test_list_models_exits(self):
        # --list-models should exit early with code 0
        with self.assertRaises(SystemExit) as cm:
            self.parser.parse_arguments(["--list-models"])  
        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
