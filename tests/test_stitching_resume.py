import os
import unittest
from unittest.mock import patch

from video_gen import video_generator as vg


class TestStitchingResume(unittest.TestCase):
    def setUp(self):
        # Create dummy files for clip_1.mp4 and clip_2.mp4
        self.files = ["clip_1.mp4", "clip_2.mp4", "clip_3.mp4"]
        for f in self.files[:2]:
            with open(f, "wb") as fp:
                fp.write(b"dummy")

    def tearDown(self):
        for f in self.files:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

    def test_resume_skips_completed_and_continues(self):
        prompts = ["p1", "p2", "p3"]
        out_paths = self.files.copy()

        call_log = {"calls": []}

        def fake_generate(**kwargs):
            call_log["calls"].append(kwargs)
            # Return the third clip path
            return out_paths[2]

        with patch.object(vg, "generate_video_with_runway_veo", side_effect=fake_generate):
            with patch.object(vg, "extract_last_frame_as_png", return_value="frame.png"):
                outputs = vg.generate_video_sequence_with_veo3_stitching(
                    prompts=prompts,
                    file_paths_list=[[], [], []],
                    provider="runway",
                    model="veo3.1_fast",
                    duration_seconds=5,
                    delay_between_clips=0,
                    out_paths=out_paths,
                    resume=True,
                )
        # Should include pre-existing two clips and the newly generated third
        self.assertEqual(outputs, out_paths)
        # Only one generation call should have been made for the remaining clip
        self.assertEqual(len(call_log["calls"]), 1)
        self.assertEqual(call_log["calls"][0]["out_path"], out_paths[2])


if __name__ == "__main__":
    unittest.main()
