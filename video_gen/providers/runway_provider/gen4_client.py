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
from ...exceptions import InsufficientCreditsError
from ...logger import get_library_logger
from ...retry_utils import handle_capacity_retry


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

    def _is_insufficient_credits(self, response_text: str, error_message: Any) -> bool:
        """Return True if response indicates insufficient credits."""
        parts = []
        if error_message is not None:
            parts.append(str(error_message))
        if response_text:
            parts.append(response_text)
        combined = " ".join(parts).lower()
        return (
            "insufficient credits" in combined
            or "not enough credit" in combined
            or "not enough credits" in combined
            or "do not have enough credits" in combined
        )

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

    def _encode_image_to_base64(self, image_path: str, max_size_kb: int = 800) -> str:
        """
        Encode an image file to base64 data URI with automatic compression.
        
        Images are compressed/resized if they exceed max_size_kb to avoid
        413 "Request Too Large" errors from the API.

        Args:
            image_path: Path to the image file
            max_size_kb: Maximum size in KB before compression (default: 800KB)

        Returns:
            Base64 encoded data URI string
        """
        try:
            from PIL import Image as pil_image_module
        except ImportError:
            pil_image_module = None

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        original_size_kb = path.stat().st_size / 1024
        
        # Use original if small enough or no PIL available
        if original_size_kb <= max_size_kb or pil_image_module is None:
            return self._encode_original_image(path, original_size_kb, max_size_kb, pil_image_module)
        
        # Compress using PIL
        return self._compress_and_encode_image(path, original_size_kb, max_size_kb, pil_image_module)
    
    def _encode_original_image(self, path, original_size_kb: float, max_size_kb: int, pil_image):
        """Encode original image without compression."""
        import mimetypes
        
        if original_size_kb > max_size_kb and pil_image is None:
            self.logger.warning(
                f"Image {path.name} is {original_size_kb:.0f}KB (>{max_size_kb}KB) "
                "but PIL not available for compression. Install: pip install pillow"
            )
        
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'
        
        with open(path, 'rb') as f:
            image_data = f.read()
        
        encoded = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    
    def _compress_and_encode_image(self, path, original_size_kb: float, max_size_kb: int, pil_image):
        """Compress and encode image using PIL."""
        from io import BytesIO
        
        self.logger.debug(
            f"Compressing {path.name} ({original_size_kb:.0f}KB) to under {max_size_kb}KB"
        )
        
        img = pil_image.open(path)
        img = self._convert_to_rgb(img, pil_image)
        
        # Try quality compression first
        result = self._try_quality_compression(img, path, original_size_kb, max_size_kb)
        if result:
            return result
        
        # Fallback to resizing
        return self._resize_and_compress(img, path, original_size_kb)
    
    def _convert_to_rgb(self, img, pil_image):
        """Convert RGBA/LA/P images to RGB."""
        if img.mode in ('RGBA', 'LA', 'P'):
            background = pil_image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            return background
        return img
    
    def _try_quality_compression(self, img, path, original_size_kb: float, max_size_kb: int):
        """Try progressive quality compression."""
        from io import BytesIO
        
        for quality in [85, 75, 65, 55, 45]:
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            compressed_size_kb = len(buffer.getvalue()) / 1024
            
            if compressed_size_kb <= max_size_kb:
                self.logger.info(
                    f"Compressed {path.name}: {original_size_kb:.0f}KB → {compressed_size_kb:.0f}KB "
                    f"(quality={quality})"
                )
                encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return f"data:image/jpeg;base64,{encoded}"
        return None
    
    def _resize_and_compress(self, img, path, original_size_kb: float):
        """Resize image as last resort."""
        from io import BytesIO
        from PIL import Image
        
        self.logger.warning(f"Resizing {path.name} to reduce size further")
        img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        final_size_kb = len(buffer.getvalue()) / 1024
        
        self.logger.info(
            f"Resized and compressed {path.name}: {original_size_kb:.0f}KB → {final_size_kb:.0f}KB"
        )
        
        encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"

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
        # Validate required parameters
        if not prompt:
            raise ValueError("Prompt is required for video generation")
        
        self.logger.info(f"Creating RunwayML Gen-4 task: model={model}, {width}x{height}, {duration}s")
        self.logger.debug(f"Prompt: {prompt[:100]}...")

        # RunwayML uses ratio format like "1280:720"
        ratio = f"{width}:{height}"

        # Encode the source image (if provided)
        self.logger.debug(f"Encoding source image: {image_path}")
        prompt_image = None
        if image_path is not None:
            prompt_image = self._encode_image_to_base64(image_path)

        # Build request payload
        payload: Dict[str, Any] = {
            "model": model,
            "promptText": prompt,
            "ratio": ratio,
            "duration": duration
        }

        # Add image if provided (image-to-video), otherwise text-to-video
        if prompt_image is not None:
            payload["promptImage"] = prompt_image

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
                response = self._send_request(payload, retry_count)
                return self._handle_response(response)
            except requests.exceptions.SSLError as e:
                self._handle_ssl_error(e)
            except requests.exceptions.Timeout:
                self.logger.warning("Request timeout, retrying...")
                self._handle_capacity_retry(retry_count)
                retry_count += 1
            except requests.exceptions.RequestException as e:
                self.logger.error(f"RunwayML API error: {e}")
                raise RuntimeError(f"RunwayML API request failed: {e}")
    
    def _send_request(self, payload: Dict[str, Any], retry_count: int):
        """Send API request with logging."""
        self.logger.debug(f"Sending RunwayML API request (attempt {retry_count + 1})")
        return requests.post(
            f"{self.base_url}/image_to_video",
            headers=self._get_headers(),
            json=payload,
            timeout=30
        )
    
    def _handle_response(self, response) -> Dict[str, Any]:
        """Handle API response with status code routing."""
        if response.status_code == 400:
            self._handle_400_error(response)
        elif response.status_code == 401:
            self._handle_401_error()
        elif response.status_code == 413:
            self._handle_413_error()
        elif response.status_code in (429, 503):
            raise requests.exceptions.Timeout()  # Trigger retry
        
        response.raise_for_status()
        task_response = response.json()
        self.logger.info(f"RunwayML task created: {task_response.get('id', 'unknown')}")
        return task_response
    
    def _handle_400_error(self, response):
        """Handle 400 Bad Request errors."""
        try:
            error_data = response.json()
            error_message = error_data.get('error', error_data)
            self.logger.error(f"Bad Request (400): {error_message}")
        except Exception:
            self.logger.error(f"Bad Request (400): {response.text[:500]}")
            error_message = None
        
        # Check for insufficient credits
        if self._is_insufficient_credits(response.text, error_message):
            raise InsufficientCreditsError(
                (
                    "RunwayML: insufficient credits to create a Gen-4 task.\n"
                    "Next steps:\n"
                    "  • Add credits in your Runway account: https://app.runwayml.com/settings/billing\n"
                    "  • Or reduce the number/length of clips and retry\n"
                ),
                provider="runway"
            )
        
        raise RuntimeError(
            f"RunwayML API rejected the request (400 Bad Request).\n"
            f"Error: {response.text[:500]}\n"
            "This usually means invalid parameters (width, height, duration, etc.)"
        )
    
    def _handle_401_error(self):
        """Handle 401 Unauthorized errors."""
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
    
    def _handle_413_error(self):
        """Handle 413 Payload Too Large errors."""
        self.logger.error(
            "Request too large (413). This usually means:\n"
            "  1. Source image is too large\n"
            "  2. Image needs to be compressed/resized before encoding\n"
            "  3. Prompt text is extremely long\n\n"
            "Solutions:\n"
            "  • Use smaller/compressed images (resize to max 1920x1080)\n"
            "  • Reduce prompt length"
        )
        raise RuntimeError(
            "RunwayML API rejected request: payload too large (413).\n"
            "Try using a smaller/compressed image."
        )
    
    def _handle_ssl_error(self, e):
        """Handle SSL certificate verification errors."""
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

    def _handle_capacity_retry(self, retry_count: int) -> None:
        """
        Handle capacity issues with exponential backoff.

        Args:
            retry_count: Current retry attempt number
            
        Raises:
            RuntimeError: If user cancels during backoff
        """
        handle_capacity_retry(retry_count, self.config, self.logger)

    def _parse_polling_response(self, response) -> Dict[str, Any]:
        """
        Parse and validate the polling response from RunwayML API.
        
        Args:
            response: The HTTP response from the polling request
            
        Returns:
            Parsed task data as dictionary
            
        Raises:
            RuntimeError: If response is invalid
        """
        try:
            task_data = response.json()
        except ValueError as e:
            self.logger.error(f"Failed to parse JSON response: {response.text}")
            raise RuntimeError(f"Invalid JSON response from RunwayML: {e}")
        
        if not isinstance(task_data, dict):
            self.logger.error(f"Expected dict, got {type(task_data)}: {task_data}")
            raise RuntimeError(f"Unexpected response format from RunwayML: {type(task_data)}")
        
        return task_data

    def _handle_task_status(self, task_data: Dict[str, Any]) -> str:
        """
        Check task status and handle completion states.
        
        Args:
            task_data: Parsed task response data
            
        Returns:
            Task status string ('SUCCEEDED', 'FAILED', 'IN_PROGRESS')
            
        Raises:
            RuntimeError: If task failed
        """
        status = task_data.get("status")

        if status == "SUCCEEDED":
            return "SUCCEEDED"

        if status == "FAILED":
            error_msg = task_data.get("failure", {}).get("reason", "Unknown error")
            raise RuntimeError(f"RunwayML task failed: {error_msg}")

        # Task is still in progress
        return "IN_PROGRESS"

    def _handle_polling_exceptions(self, e: Exception, poll_interval: int) -> bool:
        """
        Handle exceptions during polling and decide whether to retry.
        
        Args:
            e: The exception that occurred
            poll_interval: Seconds to wait before retry
            
        Returns:
            True if should continue polling, False if should give up
            
        Raises:
            RuntimeError: For SSL certificate verification failures
        """
        if isinstance(e, requests.exceptions.SSLError):
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
            self.logger.warning(f"SSL error during polling, retrying: {error_msg}")
            time.sleep(poll_interval)
            return True
        
        if isinstance(e, requests.exceptions.Timeout):
            self.logger.warning("Request timeout during polling, retrying...")
            time.sleep(poll_interval)
            return True
            
        if isinstance(e, requests.exceptions.ConnectionError):
            self.logger.warning("Connection error during polling, retrying...")
            time.sleep(poll_interval)
            return True
            
        if isinstance(e, requests.exceptions.HTTPError):
            # For 5xx server errors, retry; for 4xx client errors, give up
            status_code = getattr(e.response, 'status_code', None)
            if status_code and 500 <= status_code < 600:
                self.logger.warning(f"Server error {status_code} during polling, retrying...")
                time.sleep(poll_interval)
                return True
            else:
                self.logger.error(f"Client error {status_code} during polling, giving up")
                return False
        
        if isinstance(e, requests.exceptions.RequestException):
            self.logger.warning(f"Request exception during polling, retrying: {e}")
            time.sleep(poll_interval)
            return True
            
        # Unknown exception, don't retry
        self.logger.error(f"Unknown exception during polling: {e}")
        return False

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
                
                task_data = self._parse_polling_response(response)
                status = self._handle_task_status(task_data)
                
                # If task succeeded, return the data
                if status == "SUCCEEDED":
                    return task_data
                
                # Otherwise keep polling
                time.sleep(poll_interval)

            except Exception as e:
                should_continue = self._handle_polling_exceptions(e, poll_interval)
                if not should_continue:
                    raise

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

        # Track artifact for later download
        from ...artifact_manager import get_artifact_manager
        artifact_manager = get_artifact_manager()
        artifact_manager.add_artifact(
            task_id=task_id,
            provider="runway",
            model=model,
            prompt=prompt,
            metadata={
                "width": width,
                "height": height,
                "duration": duration,
                "image_path": image_path
            }
        )

        # Poll until complete
        completed_task = self.poll_task(task_id)

        # Get output URL and update artifact
        output_urls = completed_task.get("output", [])
        if not output_urls:
            raise RuntimeError("No output URL in completed task")

        download_url = output_urls[0]
        artifact_manager.update_download_url(task_id, download_url)

        self.logger.info("Runway task completed. You can download later with:")
        self.logger.info(f"   python -m video_gen.artifact_manager download {task_id}")

        # Continue with existing download logic
        # Get output URL

        video_url = output_urls[0]

        # Download video
        return self.download_video(video_url, output_path)
