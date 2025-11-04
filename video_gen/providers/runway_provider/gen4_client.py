"""
RunwayML Gen-4 API client with retry logic for video generation.

Handles API calls for RunwayML's native Gen-4 and Gen-4 Turbo models.
"""

import time
import random
import base64
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from .config import RunwayConfig
from ...logger import get_library_logger


class RunwayGen4Client:
    """RunwayML Gen-4 API client with retry logic and error handling."""

    def __init__(self, config: RunwayConfig):
        """
        Initialize the RunwayML Gen-4 API client.

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
                f"RUNWAY_API_KEY appears to be a placeholder: '{self.api_key}'\n"
                "Replace it with your actual API key from:\n"
                "https://app.runwayml.com/settings/api-keys"
            )

        # Default retry settings
        self.max_retries = float('inf')  # Retry indefinitely
        self.base_delay = config.retry_base_delay
        self.max_delay = config.retry_max_delay

        self.logger.debug("RunwayGen4Client initialized")

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
        image_path: str,
        width: int = 1280,
        height: int = 720,
        duration: int = 5,
        model: str = "gen4",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a Gen-4 image-to-video generation task.

        Gen-4 models support:
        - promptImage: Source image for video generation
        - seed: Random seed for reproducibility

        Args:
            prompt: Text description for the video
            image_path: Path to source image
            width: Video width
            height: Video height
            duration: Video duration (5 or 10 seconds for Gen-4)
            model: Model to use (gen4 or gen4_turbo)
            seed: Optional random seed for reproducibility

        Returns:
            Task response with task ID

        Raises:
            RuntimeError: If API request fails
        """
        self.logger.info(f"Creating RunwayML Gen-4 task: model={model}, {width}x{height}, {duration}s")
        self.logger.debug(f"Prompt: {prompt[:100]}...")

        # RunwayML uses ratio format like "1280:720"
        ratio = f"{width}:{height}"

        # Encode the source image
        self.logger.debug(f"Encoding source image: {image_path}")
        prompt_image = self._encode_image_to_base64(image_path)

        # Build request payload
        payload: Dict[str, Any] = {
            "model": model,
            "promptText": prompt,
            "promptImage": prompt_image,
            "ratio": ratio,
            "duration": duration
        }

        # Add seed if provided
        if seed is not None:
            payload["seed"] = seed
            self.logger.debug(f"Using seed: {seed}")

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

                if response.status_code == 401:
                    self.logger.error(
                        "Authentication failed (401 Unauthorized). This usually means:\n"
                        "  1. RUNWAY_API_KEY is not set or invalid\n"
                        "  2. API key is a placeholder value like 'your_runway_api_key_here'\n"
                        "  3. API key doesn't have access to Gen-4 models\n\n"
                        "Solutions:\n"
                        "  • Get your API key from: https://app.runwayml.com/settings/api-keys\n"
                        "  • Set it in .env: RUNWAY_API_KEY=your_actual_key\n"
                        "  • Verify the key has model access in your RunwayML account"
                    )
                    raise RuntimeError(
                        "RunwayML authentication failed. Invalid or missing API key.\n"
                        "Get your key from https://app.runwayml.com/settings/api-keys\n"
                        "and set RUNWAY_API_KEY in your .env file."
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

            except requests.exceptions.SSLError as e:
                # Handle SSL certificate verification errors gracefully
                error_msg = str(e)
                if "CERTIFICATE_VERIFY_FAILED" in error_msg:
                    self.logger.error(
                        "SSL certificate verification failed. This is usually caused by:\n"
                        "  1. Corporate firewall/proxy intercepting SSL connections\n"
                        "  2. Missing or outdated system CA certificates\n"
                        "  3. Antivirus software interfering with SSL\n\n"
                        "Quick fixes:\n"
                        "  • Update certificates: 'pip install --upgrade certifi'\n"
                        "  • On macOS: '/Applications/Python 3.x/Install Certificates.command'\n"
                        "  • Corporate network: Contact IT for root certificate\n\n"
                        "For detailed troubleshooting, see: docs/technical/ssl-troubleshooting.md"
                    )
                raise RuntimeError(
                    f"SSL certificate verification failed. Cannot connect to RunwayML API.\n"
                    f"See logs for troubleshooting steps or docs/technical/ssl-troubleshooting.md\n"
                    f"Original error: {error_msg}"
                )

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

            except requests.exceptions.SSLError as e:
                error_msg = str(e)
                if "CERTIFICATE_VERIFY_FAILED" in error_msg:
                    self.logger.error(
                        "SSL certificate verification failed during polling. "
                        "See earlier logs for troubleshooting steps."
                    )
                    raise RuntimeError(
                        f"SSL certificate verification failed. Cannot poll RunwayML task.\n"
                        f"Original error: {error_msg}"
                    )
                # Other SSL errors, retry
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

        Raises:
            RuntimeError: If download fails including SSL errors
        """
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return output_path

        except requests.exceptions.SSLError as e:
            error_msg = str(e)
            if "CERTIFICATE_VERIFY_FAILED" in error_msg:
                self.logger.error(
                    "SSL certificate verification failed during video download. "
                    "See earlier logs for troubleshooting steps."
                )
                raise RuntimeError(
                    f"SSL certificate verification failed. Cannot download video.\n"
                    f"Original error: {error_msg}"
                )
            raise RuntimeError(f"SSL error downloading video: {error_msg}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to download video: {e}")

    def generate_video(
        self,
        prompt: str,
        image_path: str,
        width: int = 1280,
        height: int = 720,
        duration: int = 5,
        output_path: str = "runway_gen4_output.mp4",
        model: str = "gen4",
        seed: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a video and download it (convenience method).

        Args:
            prompt: Text description for the video
            image_path: Path to source image
            width: Video width
            height: Video height
            duration: Video duration (5 or 10 seconds)
            output_path: Local path to save video
            model: Model to use (gen4 or gen4_turbo)
            seed: Optional random seed for reproducibility
            **kwargs: Additional arguments (ignored for compatibility)

        Returns:
            Path to saved video file
        """
        # Create task
        task_response = self.create_image_to_video_task(
            prompt=prompt,
            image_path=image_path,
            width=width,
            height=height,
            duration=duration,
            model=model,
            seed=seed
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
