import unittest
from video_gen.file_handler import FileHandler
from video_gen.config import SoraConfig


class DummyClient:
    pass


class TestFileHandlerExpand(unittest.TestCase):
    def setUp(self):
        # Minimal config; api_key value won't be used for expand_image_paths
        self.config = SoraConfig(api_key="dummy")
        self.handler = FileHandler(self.config, DummyClient())

    def test_none_input(self):
        self.assertEqual(self.handler.expand_image_paths(None), [])

    def test_list_of_paths(self):
        paths = self.handler.expand_image_paths(["a.png", "b.jpg"]) 
        self.assertEqual(paths, ["a.png", "b.jpg"]) 

    def test_comma_string(self):
        paths = self.handler.expand_image_paths("a.png, b.jpg , c.webp")
        self.assertEqual(paths, ["a.png", "b.jpg", "c.webp"]) 

    def test_wildcard_no_match_returns_empty_for_that_pattern(self):
        # This will expand to empty on most systems; function should just skip it and not error
        paths = self.handler.expand_image_paths(["__no_such_dir__/*.xyz"]) 
        self.assertEqual(paths, [])


if __name__ == "__main__":
    unittest.main()
