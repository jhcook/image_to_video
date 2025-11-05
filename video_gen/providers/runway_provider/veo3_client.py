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
from ...exceptions import InsufficientCreditsError
from ...logger import get_library_logger
from ...retry_utils import handle_capacity_retry


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

        self.logger.debug("RunwayVeoClient initialized")

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
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        original_size_kb = path.stat().st_size / 1024
        
        # Try to use original if small enough
        if original_size_kb <= max_size_kb:
            return self._encode_original_image(path)
        
        # Check if PIL is available for compression
        try:
            from PIL import Image as pil_image
        except ImportError:
            self.logger.warning(
                f"Image {path.name} is {original_size_kb:.0f}KB (>{max_size_kb}KB) "
                "but PIL not available for compression. Install: pip install pillow"
            )
            return self._encode_original_image(path)
        
        # Compress using PIL
        return self._compress_and_encode_image(path, original_size_kb, max_size_kb, pil_image)
    
    def _encode_original_image(self, path: Path) -> str:
        """Encode original image without compression."""
        import mimetypes
        
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'
        
        with open(path, 'rb') as f:
            image_data = f.read()
        
        encoded = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    
    def _compress_and_encode_image(self, path: Path, original_size_kb: float, max_size_kb: int, pil_image) -> str:
        """Compress image using PIL and encode to base64."""
        from io import BytesIO
        
        self.logger.debug(
            f"Compressing {path.name} ({original_size_kb:.0f}KB) to under {max_size_kb}KB"
        )
        
        img = pil_image.open(path)
        img = self._convert_to_rgb(img, pil_image)
        
        # Try progressive quality reduction
        result = self._try_quality_compression(img, path, original_size_kb, max_size_kb)
        if result:
            return result
        
        # Last resort: resize and compress
        return self._resize_and_compress(img, path, original_size_kb)
    
    def _convert_to_rgb(self, img, pil_image):
        """Convert image to RGB if necessary."""
        if img.mode in ('RGBA', 'LA', 'P'):
            background = pil_image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            return background
        return img
    
    def _try_quality_compression(self, img, path: Path, original_size_kb: float, max_size_kb: int) -> Optional[str]:
        """Try compressing with different quality levels."""
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
    
    def _resize_and_compress(self, img, path: Path, original_size_kb: float) -> str:
        """Resize image and compress as last resort."""
        from io import BytesIO
        
        self.logger.warning(f"Resizing {path.name} to reduce size further")
        img.thumbnail((1920, 1080))
        
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
        # Validate required parameters
        if not prompt:
            raise ValueError("Prompt is required for video generation")
        
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

        # RunwayML Veo API requires 'promptImage' (the source/first frame)
        # Determine what to use as promptImage
        prompt_image_source = None
        
        if first_frame:
            # Use explicit first_frame as promptImage
            prompt_image_source = first_frame
            self.logger.debug(f"Using first_frame as promptImage: {first_frame}")
        elif reference_images and len(reference_images) > 0:
            # Use first reference image as promptImage
            prompt_image_source = reference_images[0]
            self.logger.debug(f"Using first reference image as promptImage: {reference_images[0]}")
        
        if not prompt_image_source:
            raise ValueError(
                "RunwayML Veo API requires a source image (promptImage).\n"
                "Provide either first_frame or at least one reference_image."
            )
        
        # Encode and add promptImage (required field)
        self.logger.debug(f"Encoding promptImage: {prompt_image_source}")
        payload["promptImage"] = self._encode_image_to_base64(prompt_image_source)
        self.logger.info("Added promptImage (source frame)")

        # Add first keyframe if provided (for stitching)
        if first_frame:
            self.logger.debug(f"Encoding firstKeyframe: {first_frame}")
            payload["firstKeyframe"] = self._encode_image_to_base64(first_frame)
            self.logger.info("Added firstKeyframe for stitching")

        # Add last keyframe if provided
        if last_frame:
            self.logger.debug(f"Encoding lastKeyframe: {last_frame}")
            payload["lastKeyframe"] = self._encode_image_to_base64(last_frame)
            self.logger.info("Added lastKeyframe")

        # Add remaining reference images (excluding the one used as promptImage)
        if reference_images and len(reference_images) > 1:
            # Use remaining images as reference (skip first if it was used as promptImage and no first_frame)
            ref_images_to_use = reference_images if first_frame else reference_images[1:]
            
            if len(ref_images_to_use) > 3:
                self.logger.warning(
                    f"Veo supports max 3 reference images, truncating from {len(ref_images_to_use)}"
                )
                ref_images_to_use = ref_images_to_use[:3]

            if ref_images_to_use:
                self.logger.debug(f"Encoding {len(ref_images_to_use)} reference images")
                payload["referenceImages"] = [
                    self._encode_image_to_base64(ref_img) for ref_img in ref_images_to_use
                ]
                self.logger.info(f"Added {len(ref_images_to_use)} reference images")

        # Make API request with retry logic
        return self._make_request_with_retry(payload)

    def _make_request_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with exponential backoff retry logic."""
        retry_count = 0
        while True:
            try:
                response = self._send_request(payload, retry_count)
                return self._handle_response(response, payload)
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
        payload_summary = {k: f"<{len(v)} chars>" if isinstance(v, str) and len(v) > 100 
                          else f"<{len(v)} items>" if isinstance(v, list) 
                          else v 
                          for k, v in payload.items()}
        self.logger.debug(f"Payload structure: {payload_summary}")
        
        return requests.post(
            f"{self.base_url}/image_to_video",
            headers=self._get_headers(),
            json=payload,
            timeout=30
        )
    
    def _handle_response(self, response, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle API response with status code routing."""
        if response.status_code == 400:
            self._handle_400_error(response, payload)
        elif response.status_code == 401:
            self._handle_401_error()
        elif response.status_code == 413:
            self._handle_413_error(payload)
        elif response.status_code in (429, 503):
            raise requests.exceptions.Timeout()  # Trigger retry
        
        response.raise_for_status()
        task_response = response.json()
        self.logger.info(f"RunwayML task created: {task_response.get('id', 'unknown')}")
        return task_response
    
    def _handle_400_error(self, response, payload: Dict[str, Any]):
        """Handle 400 Bad Request errors."""
        try:
            error_data = response.json()
            error_message = error_data.get('error', error_data)
            self.logger.error(f"Bad Request (400): {error_message}")
            self.logger.error(f"Full API response: {response.text}")
        except Exception:
            self.logger.error(f"Bad Request (400): {response.text[:500]}")
            error_message = None
        
        error_text = response.text
        
        # Check for specific error types
        if self._is_insufficient_credits(error_text, error_message):
            raise InsufficientCreditsError(
                (
                    "RunwayML: insufficient credits to create a Veo task.\n"
                    "Next steps:\n"
                    "  • Add credits in your Runway account: https://app.runwayml.com/settings/billing\n"
                    "  • Or switch provider/model (e.g., --provider veo3 to use Google Veo directly)\n"
                    "  • Or reduce the number/length of clips and retry\n"
                ),
                provider="runway"
            )
        
        if "invalid_union" in error_text or "expected string, received undefined" in error_text:
            model_name = payload.get('model', 'unknown')
            raise RuntimeError(
                f"RunwayML Veo API validation error.\n"
                f"This may indicate:\n"
                f"  1. API format changed - check RunwayML documentation\n"
                f"  2. Model '{model_name}' may not support the requested parameters\n"
                f"  3. Incompatible combination of firstKeyframe/referenceImages\n\n"
                f"API Error: {error_text[:500]}\n\n"
                f"Try: --provider veo3 (native Google Veo API) as an alternative"
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
            "  3. API key doesn't have access to Veo models\n\n"
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
    
    def _handle_413_error(self, payload: Dict[str, Any]):
        """Handle 413 Payload Too Large errors."""
        self.logger.error(
            "Request too large (413). This usually means:\n"
            "  1. Too many reference images or images are too large\n"
            "  2. Images need to be compressed/resized before encoding\n"
            "  3. Prompt text is extremely long\n\n"
            "Solutions:\n"
            "  • Reduce number of reference images (max 3)\n"
            "  • Use smaller/compressed images (resize to max 1920x1080)\n"
            "  • Reduce prompt length\n\n"
            f"Current: promptImage + {len(payload.get('referenceImages', []))} reference images"
        )
        raise RuntimeError(
            "RunwayML API rejected request: payload too large (413).\n"
            "Try using smaller/compressed images or fewer reference images."
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
