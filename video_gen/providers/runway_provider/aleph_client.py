"""
RunwayML Aleph API client for video editing and transformation.

Handles API calls for RunwayML's Aleph model which specializes in:
- Video editing and transformation
- Adding, removing, and transforming objects
- Generating any angle of a scene
- Modifying style and lighting
- Multi-task visual generation
"""

import time
import base64
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from .config import RunwayConfig
from ...exceptions import InsufficientCreditsError
from ...logger import get_library_logger

# Constants
REQUESTS_NOT_AVAILABLE_ERROR = "requests library not available"


class RunwayAlephClient:
    """RunwayML Aleph API client for video editing and transformation."""

    def __init__(self, config: RunwayConfig):
        """
        Initialize the RunwayML Aleph API client.

        Args:
            config: Configuration containing API credentials and settings
        """
        if requests is None:
            raise ImportError("Please `pip install requests` for RunwayML support.")

        self.config = config
        self.logger = get_library_logger()
        self.api_key = config.api_key
        self.base_url = config.base_url

        # Validate API key
        if not self.api_key:
            raise ValueError(
                "RUNWAY_API_KEY not set. Get your API key from:\n"
                "https://app.runwayml.com/settings/api-keys\n"
                "and set it in your .env file: RUNWAY_API_KEY=your_actual_key"
            )
        
        # Check for placeholder values
        if self.api_key in ("your_runway_api_key_here", "your_api_key_here", "sk-..."):
            raise ValueError(
                "Please replace placeholder RUNWAY_API_KEY with your actual API key.\n"
                "Get your real API key from: https://app.runwayml.com/settings/api-keys"
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06"
        }

    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 for API upload.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image data URL
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image encoding fails
        """
        try:
            path = Path(image_path)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            with open(path, 'rb') as f:
                image_data = f.read()
            
            import mimetypes
            mime_type, _ = mimetypes.guess_type(str(path))
            if not mime_type or not mime_type.startswith('image/'):
                mime_type = 'image/jpeg'  # fallback
            
            encoded = base64.b64encode(image_data).decode('utf-8')
            return f"data:{mime_type};base64,{encoded}"
            
        except Exception as e:
            raise ValueError(f"Failed to encode image {image_path}: {e}")

    def _encode_video(self, video_path: str) -> str:
        """
        Encode video to base64 for API upload.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Base64 encoded video data URL
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video encoding fails
        """
        try:
            path = Path(video_path)
            if not path.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            with open(path, 'rb') as f:
                video_data = f.read()
            
            import mimetypes
            mime_type, _ = mimetypes.guess_type(str(path))
            if not mime_type or not mime_type.startswith('video/'):
                mime_type = 'video/mp4'  # fallback
            
            encoded = base64.b64encode(video_data).decode('utf-8')
            return f"data:{mime_type};base64,{encoded}"
            
        except Exception as e:
            raise ValueError(f"Failed to encode video {video_path}: {e}")

    def edit_video(
        self,
        prompt: str,
        input_video: str,
        reference_images: Optional[List[str]] = None,
        *,
        width: int = 1280,
        height: int = 720,
        duration_seconds: Optional[int] = None,
        seed: Optional[int] = None,
        out_path: str = "aleph_output.mp4"
    ) -> str:
        """
        Edit and transform a video using Aleph model.
        
        Aleph specializes in:
        - Adding, removing, and transforming objects
        - Generating any angle of a scene  
        - Modifying style and lighting
        - Multi-task visual generation
        
        Args:
            prompt: Text description of the desired edits/transformations
            input_video: Path to input video file to edit
            reference_images: Optional list of reference images for style guidance
            width: Video width in pixels. Defaults to 1280.
            height: Video height in pixels. Defaults to 720.
            duration_seconds: Video duration. If None, uses input video duration.
            seed: Random seed for reproducible results. Defaults to None.
            out_path: Output file path. Defaults to "aleph_output.mp4".
            
        Returns:
            Path to the saved edited video file
            
        Raises:
            FileNotFoundError: If input video or reference images don't exist
            RuntimeError: If API calls fail or video editing fails
            ValueError: If parameters are invalid
        """
        self.logger.info(f"Editing video with Aleph: {input_video}")
        self.logger.info(f"Edit prompt: {prompt}")
        
        # Encode input video
        video_data = self._encode_video(input_video)
        
        # Encode reference images if provided
        reference_data: List[str] = []
        if reference_images:
            self.logger.info(f"Using {len(reference_images)} reference images")
            for img_path in reference_images:
                reference_data.append(self._encode_image(img_path))
        
        # Create task
        task_data = self._create_edit_task(
            prompt=prompt,
            video_data=video_data,
            reference_data=reference_data,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
            seed=seed
        )
        
        # Poll for completion
        task_id = task_data["id"]
        self.logger.info(f"Aleph task created: {task_id}")
        
        completed_task = self.poll_task(task_id)
        
        # Download result
        video_url = completed_task["output"]["video_url"]
        return self.download_video(video_url, out_path)

    def generate_video(
        self,
        prompt: str,
        reference_images: Optional[List[str]] = None,
        *,
        width: int = 1280,
        height: int = 720,
        duration_seconds: int = 5,
        seed: Optional[int] = None,
        out_path: str = "aleph_generated.mp4"
    ) -> str:
        """
        Generate a new video using Aleph model.
        
        Args:
            prompt: Text description of the desired video content
            reference_images: Optional list of reference images for style guidance
            width: Video width in pixels. Defaults to 1280.
            height: Video height in pixels. Defaults to 720.
            duration_seconds: Video duration in seconds. Defaults to 5.
            seed: Random seed for reproducible results. Defaults to None.
            out_path: Output file path. Defaults to "aleph_generated.mp4".
            
        Returns:
            Path to the saved generated video file
            
        Raises:
            FileNotFoundError: If reference images don't exist
            RuntimeError: If API calls fail or video generation fails
        """
        self.logger.info("Generating video with Aleph")
        self.logger.info(f"Generation prompt: {prompt}")
        
        # Encode reference images if provided
        reference_data: List[str] = []
        if reference_images:
            self.logger.info(f"Using {len(reference_images)} reference images")
            for img_path in reference_images:
                reference_data.append(self._encode_image(img_path))
        
        # Create generation task
        task_data = self._create_generation_task(
            prompt=prompt,
            reference_data=reference_data,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
            seed=seed
        )
        
        # Poll for completion
        task_id = task_data["id"]
        self.logger.info(f"Aleph generation task created: {task_id}")
        
        completed_task = self.poll_task(task_id)
        
        # Download result
        video_url = completed_task["output"]["video_url"]
        return self.download_video(video_url, out_path)

    def _create_edit_task(
        self,
        prompt: str,
        video_data: str,
        reference_data: List[str],
        width: int,
        height: int,
        duration_seconds: Optional[int],
        seed: Optional[int]
    ) -> Dict[str, Any]:
        """Create Aleph video editing task."""
        self.logger.info(f"Creating Aleph edit task: {width}x{height}")
        
        payload: Dict[str, Any] = {
            "model": "gen4_aleph",
            "promptText": prompt,
            "ratio": f"{width}:{height}",
            "promptImage": video_data,  # Use video as promptImage for Aleph
        }
        
        if duration_seconds is not None:
            payload["duration"] = duration_seconds
            
        if reference_data:
            # For multiple reference images, use the first one as promptImage
            # (Gen-4 style, though Aleph might support more)
            payload["promptImage"] = reference_data[0]
            
        if seed is not None:
            payload["seed"] = seed

        if requests is None:
            raise RuntimeError(REQUESTS_NOT_AVAILABLE_ERROR)

        response = requests.post(
            f"{self.base_url}/image_to_video",
            headers=self._get_headers(),
            json=payload,
            timeout=60
        )
        
        if response.status_code == 402:
            raise InsufficientCreditsError("Insufficient credits for Aleph video editing")
        
        # Log the response for debugging
        if response.status_code != 200:
            error_details = response.text
            self.logger.error(f"🚨 ALEPH API ERROR {response.status_code}: {error_details}")
            # Also log to console for immediate visibility
            print(f"🚨 ALEPH API ERROR {response.status_code}: {error_details}", file=sys.stderr)
        
        response.raise_for_status()
        return response.json()

    def _create_generation_task(
        self,
        prompt: str,
        reference_data: List[str],
        width: int,
        height: int,
        duration_seconds: int,
        seed: Optional[int]
    ) -> Dict[str, Any]:
        """Create Aleph video generation task."""
        self.logger.info(f"Creating Aleph generation task: {width}x{height}, {duration_seconds}s")
        
        payload: Dict[str, Any] = {
            "model": "gen4_aleph",
            "promptText": prompt,
            "ratio": f"{width}:{height}",
            "duration": duration_seconds,
        }
        
        if reference_data:
            # For generation, use the first reference image as promptImage
            payload["promptImage"] = reference_data[0]
            
        if seed is not None:
            payload["seed"] = seed

        if requests is None:
            raise RuntimeError(REQUESTS_NOT_AVAILABLE_ERROR)

        response = requests.post(
            f"{self.base_url}/image_to_video",
            headers=self._get_headers(),
            json=payload,
            timeout=60
        )
        
        if response.status_code == 402:
            raise InsufficientCreditsError("Insufficient credits for Aleph video generation")
        
        # Log the response for debugging
        if response.status_code != 200:
            error_details = response.text
            self.logger.error(f"🚨 ALEPH API ERROR {response.status_code}: {error_details}")
            # Also log to console for immediate visibility
            print(f"🚨 ALEPH API ERROR {response.status_code}: {error_details}", file=sys.stderr)
        
        response.raise_for_status()
        return response.json()

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
        retry_count = 0
        
        while True:
            try:
                response = self._get_task_status(task_id)
                task_data = response.json()
                status = task_data.get("status")

                if status == "SUCCEEDED":
                    self.logger.info(f"Aleph task {task_id} completed successfully")
                    return task_data

                if status == "FAILED":
                    error_msg = task_data.get("failure", {}).get("reason", "Unknown error")
                    raise RuntimeError(f"Aleph task failed: {error_msg}")

                # Task is still in progress
                self.logger.info(f"Aleph task {task_id} status: {status}, waiting {poll_interval}s...")
                time.sleep(poll_interval)

            except Exception as e:
                retry_count = self._handle_polling_error(e, retry_count, poll_interval, task_id)

    def _get_task_status(self, task_id: str):
        """Get task status from API."""
        if requests is None:
            raise RuntimeError(REQUESTS_NOT_AVAILABLE_ERROR)
        
        return requests.get(
            f"{self.base_url}/tasks/{task_id}",
            headers=self._get_headers(),
            timeout=10
        )

    def _handle_polling_error(self, e: Exception, retry_count: int, poll_interval: int, task_id: str) -> int:
        """Handle polling errors and decide whether to retry."""
        if requests is None:
            raise RuntimeError(REQUESTS_NOT_AVAILABLE_ERROR)
            
        if isinstance(e, requests.exceptions.SSLError):
            error_msg = str(e)
            if "CERTIFICATE_VERIFY_FAILED" in error_msg:
                self.logger.error("SSL certificate verification failed during polling")
                raise RuntimeError(f"SSL certificate verification failed: {error_msg}")
        
        if isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            retry_count += 1
            if retry_count >= 3:
                raise RuntimeError(f"Max retries exceeded for Aleph task {task_id}")
            
            self.logger.warning(f"Connection error, retrying in {poll_interval}s...")
            time.sleep(poll_interval)
            return retry_count
        
        # Unknown error, re-raise
        raise

    def download_video(self, url: str, output_path: str) -> str:
        """
        Download generated video from URL.

        Args:
            url: Video URL from API response
            output_path: Local path to save the video

        Returns:
            Path to the saved video file

        Raises:
            RuntimeError: If download fails
        """
        self.logger.info(f"Downloading Aleph video to: {output_path}")
        
        try:
            if requests is None:
                raise RuntimeError(REQUESTS_NOT_AVAILABLE_ERROR)
            
            response = requests.get(url, timeout=300)  # 5 minute timeout
            response.raise_for_status()
            
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Aleph video downloaded successfully: {output_path}")
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to download Aleph video: {e}")


# Backwards compatibility alias
RunwayAPIClient = RunwayAlephClient