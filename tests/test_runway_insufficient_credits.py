import unittest
from unittest.mock import patch, MagicMock

from video_gen.providers.runway_provider.config import RunwayConfig
from video_gen.providers.runway_provider.veo3_client import RunwayVeoClient
from video_gen.providers.runway_provider.gen4_client import RunwayGen4Client
from video_gen.exceptions import InsufficientCreditsError


class TestRunwayInsufficientCredits(unittest.TestCase):
    def setUp(self):
        self.config = RunwayConfig(api_key="rk_test_123")

    @patch("video_gen.providers.runway_provider.veo3_client.requests.post")
    def test_veo3_insufficient_credits_raises(self, mock_post):
        # Mock a 400 response indicating insufficient credits
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "You do not have enough credits to run this task."
        mock_resp.json.return_value = {"error": mock_resp.text}
        mock_post.return_value = mock_resp

        client = RunwayVeoClient(self.config)
        # Avoid reading real files
        with patch.object(client, "_encode_image_to_base64", return_value="data:image/jpeg;base64,AAAA"):
            with self.assertRaises(InsufficientCreditsError):
                client.create_image_to_video_task(
                    prompt="test",
                    width=1280,
                    height=720,
                    duration=5,
                    model="veo3.1_fast",
                    first_frame="/tmp/fake.jpg",
                    reference_images=["/tmp/fake2.jpg"]
                )

    @patch("video_gen.providers.runway_provider.gen4_client.requests.post")
    def test_gen4_insufficient_credits_raises(self, mock_post):
        # Mock a 400 response indicating insufficient credits
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Insufficient credits"
        mock_resp.json.return_value = {"error": mock_resp.text}
        mock_post.return_value = mock_resp

        client = RunwayGen4Client(self.config)
        with patch.object(client, "_encode_image_to_base64", return_value="data:image/jpeg;base64,AAAA"):
            with self.assertRaises(InsufficientCreditsError):
                client.create_image_to_video_task(
                    prompt="test",
                    image_path="/tmp/fake.jpg",
                    width=1280,
                    height=720,
                    duration=5,
                    model="gen4"
                )


class TestStitchingGracefulStop(unittest.TestCase):
    def test_stitching_stops_on_insufficient_credits(self):
        prompts = ["clip1", "clip2", "clip3"]

        # First call returns a path, second call raises InsufficientCreditsError
        call_state = {"count": 0}

        def fake_generate(*args, **kwargs):
            if call_state["count"] == 0:
                call_state["count"] += 1
                return "clip1.mp4"
            raise InsufficientCreditsError("Insufficient credits", provider="runway")

        from video_gen import video_generator as vg

        with patch.object(vg, "generate_video_with_runway_veo", side_effect=fake_generate):
            with patch.object(vg, "extract_last_frame_as_png", return_value="frame.png"):
                outputs = vg.generate_video_sequence_with_veo3_stitching(
                    prompts=prompts,
                    file_paths_list=[[], [], []],
                    provider="runway",
                    model="veo3.1_fast",
                    duration_seconds=5,
                    delay_between_clips=0
                )
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0], "clip1.mp4")


if __name__ == "__main__":
    unittest.main()
