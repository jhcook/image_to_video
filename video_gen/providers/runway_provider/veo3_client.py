"""
RunwayML Veo API client with retry logic for video generation.

Handles API calls for Google Veo models (Veo 3.0, 3.1, 3.1 Fast) via RunwayML.
"""

import time
import random
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from .config import RunwayConfig
from ...logger import get_library_logger


class RunwayVeoClient:
    """RunwayML Veo API client with retry logic and error handling."""

    def __init__(self, config: RunwayConfig):
        """
        Initialize the RunwayML Veo API client.

        Args:
            config: Configuration containing API credentials and settings
        """
        if requests is None:
            raise ImportError("Please `pip install requests` for RunwayML support.")

        self.config = config
        self.logger = get_library_logger()
        self.api_key = config.api_key
        self.base_url = config.base_url

        # Default retry settings
        self.max_retries = float('inf')  # Retry indefinitely
        self.base_delay = config.retry_base_delay
        self.max_delay = config.retry_max_delay

        self.logger.debug("RunwayVeoClient initialized")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06"
        }

    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode an image file to base64 data URI.

        Args:
            image_path: Path to the image file

        Returns:
            Base64 encoded data URI string
        """
        import mimetypes

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/png'  # Default to PNG

        # Read and encode image
        with open(path, 'rb') as f:
            image_data = f.read()

        encoded = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"

    def create_image_to_video_task(
        self,
        prompt: str,
        width: int = 1280,
        height: int = 720,
        duration: int = 5,
        model: str = "veo3.1_fast",
        first_frame: Optional[str] = None,
        last_frame: Optional[str] = None,
        reference_images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a Veo image-to-video or text-to-video generation task.

        Veo models support:
        - firstKeyframe: Source frame for seamless stitching
        - lastKeyframe: End frame for transitions
        - referenceImages: Up to 3 images for style/content guidance

        Args:
            prompt: Text description for the video
            width: Video width
            height: Video height
            duration: Video duration (2-10 seconds for Veo)
            model: Model to use (veo3, veo3.1, veo3.1_fast)
            first_frame: Optional first keyframe path for stitching
            last_frame: Optional last keyframe path for transitions
            reference_images: Optional list of reference image paths (up to 3)

        Returns:
            Task response with task ID

        Raises:
            RuntimeError: If API request fails
        """
        self.logger.info(f"Creating RunwayML Veo task: model={model}, {width}x{height}, {duration}s")
        self.logger.debug(f"Prompt: {prompt[:100]}...")

        # RunwayML uses ratio format like "1280:720"
        ratio = f"{width}:{height}"

        # Build request payload
        payload: Dict[str, Any] = {
            "model": model,
            "promptText": prompt,
            "ratio": ratio,
            "duration": duration
        }

        # Add first keyframe if provided
        if first_frame:
            self.logger.debug(f"Encoding first keyframe: {first_frame}")
            payload["firstKeyframe"] = self._encode_image_to_base64(first_frame)
            self.logger.info("Added first keyframe")

        # Add last keyframe if provided
        if last_frame:
            self.logger.debug(f"Encoding last keyframe: {last_frame}")
            payload["lastKeyframe"] = self._encode_image_to_base64(last_frame)
            self.logger.info("Added last keyframe for stitching")

        # Add reference images if provided
        if reference_images:
            if len(reference_images) > 3:
                self.logger.warning(
                    f"Veo supports max 3 reference images, truncating from {len(reference_images)}"
                )
                reference_images = reference_images[:3]

            self.logger.debug(f"Encoding {len(reference_images)} reference images")
            payload["referenceImages"] = [
                self._encode_image_to_base64(ref_img) for ref_img in reference_images
            ]
            self.logger.info(f"Added {len(reference_images)} reference images")

        # Make API request with retry logic
        return self._make_request_with_retry(payload)

    def _make_request_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with exponential backoff retry logic."""
        retry_count = 0
        while True:
            try:
                self.logger.debug(f"Sending RunwayML API request (attempt {retry_count + 1})")
                response = requests.post(
                    f"{self.base_url}/image_to_video",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )

                if response.status_code in (429, 503):
                    self.logger.warning(
                        f"Rate limited or service unavailable ({response.status_code}), retrying..."
                    )
                    self._handle_capacity_retry(retry_count)
                    retry_count += 1
                    continue

                response.raise_for_status()
                task_response = response.json()
                self.logger.info(f"RunwayML task created: {task_response.get('id', 'unknown')}")
                return task_response

            except requests.exceptions.Timeout:
                self.logger.warning("Request timeout, retrying...")
                self._handle_capacity_retry(retry_count)
                retry_count += 1
                continue

            except requests.exceptions.RequestException as e:
                self.logger.error(f"RunwayML API error: {e}")
                raise RuntimeError(f"RunwayML API request failed: {e}")

    def _handle_capacity_retry(self, retry_count: int) -> None:
        """
        Handle capacity issues with exponential backoff.

        Args:
            retry_count: Current retry attempt number
        """
        # Calculate exponential backoff with cap
        delay = min(self.base_delay * (2 ** retry_count), self.max_delay)

        # Add jitter to prevent thundering herd
        jitter = delay * self.config.retry_jitter_percent * (random.random() - 0.5)
        actual_delay = max(1, delay + jitter)

        try:
            time.sleep(actual_delay)
        except KeyboardInterrupt:
            raise RuntimeError("Operation cancelled by user")

    def poll_task(self, task_id: str, poll_interval: int = 5) -> Dict[str, Any]:
        """
        Poll a task until it completes.

        Args:
            task_id: The task ID to poll
            poll_interval: Seconds between polling attempts

        Returns:
            Final task response with output

        Raises:
            RuntimeError: If task fails or polling fails
        """
        while True:
            try:
                response = requests.get(
                    f"{self.base_url}/tasks/{task_id}",
                    headers=self._get_headers(),
                    timeout=10
                )
                response.raise_for_status()
                task_data = response.json()

                status = task_data.get("status")

                if status == "SUCCEEDED":
                    return task_data

                if status == "FAILED":
                    error_msg = task_data.get("failure", {}).get("reason", "Unknown error")
                    raise RuntimeError(f"RunwayML task failed: {error_msg}")

                # Otherwise keep polling
                time.sleep(poll_interval)
                continue

            except requests.exceptions.RequestException:
                time.sleep(poll_interval)
                continue

    def download_video(self, url: str, output_path: str) -> str:
        """
        Download generated video from URL.

        Args:
            url: Video URL from task output
            output_path: Local path to save video

        Returns:
            Path to saved video file
        """
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return output_path

    def generate_video(
        self,
        prompt: str,
        width: int = 1280,
        height: int = 720,
        duration: int = 5,
        output_path: str = "runway_veo_output.mp4",
        model: str = "veo3.1_fast",
        first_frame: Optional[str] = None,
        last_frame: Optional[str] = None,
        reference_images: Optional[List[str]] = None
    ) -> str:
        """
        Generate a video and download it (convenience method).

        Args:
            prompt: Text description for the video
            width: Video width
            height: Video height
            duration: Video duration (2-10 seconds)
            output_path: Local path to save video
            model: Model to use (veo3, veo3.1, veo3.1_fast)
            first_frame: Optional first keyframe path for stitching
            last_frame: Optional last keyframe path for transitions
            reference_images: Optional list of reference image paths (up to 3)

        Returns:
            Path to saved video file
        """
        # Create task
        task_response = self.create_image_to_video_task(
            prompt=prompt,
            width=width,
            height=height,
            duration=duration,
            model=model,
            first_frame=first_frame,
            last_frame=last_frame,
            reference_images=reference_images
        )

        task_id = task_response.get("id")
        if not task_id:
            raise RuntimeError("No task ID in response")

        # Poll until complete
        completed_task = self.poll_task(task_id)

        # Get output URL
        output_urls = completed_task.get("output", [])
        if not output_urls:
            raise RuntimeError("No output URL in completed task")

        video_url = output_urls[0]

        # Download video
        return self.download_video(video_url, output_path)
