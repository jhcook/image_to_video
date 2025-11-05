"""
Google Veo-3 API client with retry logic and proper parameter separation.

This module implements the Veo 3.1 API specification correctly by separating:
- Source frame (`image` parameter): First frame for seamless stitching
- Reference images (`reference_images` parameter): Style/content guidance

Handles API calls, error handling, and exponential backoff retry mechanisms
for Google's Veo-3 and Veo 3.1 video generation models.

Key Features:
- Automatic base64 encoding of images
- Separate handling of source frames vs reference images
- Exponential backoff retry logic for capacity issues
- Comprehensive error handling and logging
- Support for both Veo 3.0 and 3.1 models

See Also:
    - Veo API documentation: https://ai.google.dev/gemini-api/docs/video
    - SOURCE_FRAME_IMPLEMENTATION.md for technical details
"""

import time
import random
import json
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from .config import Veo3Config
from .auth import get_google_credentials
from video_gen.exceptions import AuthenticationError, RateLimitError, Veo3APIError, VideoProcessingError
from video_gen.logger import get_library_logger


# HTTP Status Code Constants
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMIT = 429
HTTP_SERVICE_UNAVAILABLE = 503

# Response Truncation Limits
ERROR_RESPONSE_PREVIEW_LENGTH = 500
DETAILED_ERROR_RESPONSE_LENGTH = 1000

# Error Message Keywords
QUOTA_KEYWORDS = ['quota']
CAPACITY_KEYWORDS = ['capacity', 'resource']


class Veo3APIClient:
    """Google Veo-3 API client with retry logic and error handling."""
    
    def __init__(self, config: Veo3Config):
        """
        Initialize the Veo-3 API client.
        
        Args:
            config: Veo3Config instance containing API credentials and settings
        """
        if requests is None:
            raise ImportError("Please `pip install requests` for Veo-3 support.")
            
        self.config = config
        self.logger = get_library_logger()
        # Access config attributes directly since Veo3Config is a dataclass
        self.api_key = config.api_key
        self.project_id = config.project_id
        self.location = config.location

        # Track auth source to enable refresh-on-401 for OAuth flows
        self._auth_source = "env"
        # If no API key, try browser-based OAuth and mark as oauth source
        if not self.api_key:
            creds = get_google_credentials()
            self.api_key = creds.token  # Use OAuth2 access token
            self._auth_source = "oauth"
        
        # Veo models are ONLY available through Vertex AI endpoint
        # Gemini API does NOT support Veo models
        if not self.project_id:
            raise ValueError(
                "❌ GOOGLE_CLOUD_PROJECT is required for Veo models.\n"
                "Veo is only available through Vertex AI, not Gemini API.\n"
                "\nTo fix:\n"
                "1. Set your project ID: export GOOGLE_CLOUD_PROJECT='your-project-id'\n"
                "2. Get OAuth2 token: export GOOGLE_API_KEY=\"$(gcloud auth application-default print-access-token)\"\n"
                "\nSee VEO_AUTH_GUIDE.md for detailed setup instructions."
            )
        
        self.base_url = "https://aiplatform.googleapis.com/v1"
        self.use_vertex_ai = True
        self.logger.debug(f"Using Vertex AI endpoint: {self.base_url}")
        
        # Default retry settings
        self.max_retries = getattr(config, 'max_retries', float('inf'))
        self.base_delay = getattr(config, 'retry_base_delay', 30)
        self.max_delay = getattr(config, 'retry_max_delay', 300)
        
        self.logger.debug(f"Veo3APIClient initialized: project={self.project_id}, location={self.location}")
        
    def generate_video(
        self,
        prompt: str,
        reference_images: List[str] = None,
        source_frame: str = None,
        width: int = 1280,
        height: int = 720,
        fps: int = 24,
        duration_seconds: int = 8,
        seed: Optional[int] = None,
        model: str = "veo-3.0-generate-001"
    ) -> bytes:
        """
        Generate a video using Google's Veo-3 model with proper API parameter separation.
        
        This method correctly implements the Veo 3.1 API specification by separating:
        - Source frame (`image` parameter): The first frame of the video
        - Reference images (`reference_images` parameter): Style/content guidance
        
        Args:
            prompt: Text description for the video
            reference_images: Optional list of reference image file paths (up to 3).
                            These images guide style and content consistency.
                            All clips in a sequence typically use the same references.
            source_frame: Optional path to source frame (first frame) PNG.
                         Used for seamless stitching - the last frame from the
                         previous clip becomes the first frame of this clip.
            width: Video width in pixels (default: 1280)
            height: Video height in pixels (default: 720)
            fps: Frames per second (default: 24)
            duration_seconds: Video duration in seconds (default: 8)
            seed: Optional seed for reproducibility
            model: Model to use (e.g., veo-3.0-generate-001, veo-3.1-fast-generate-preview)
            
        Returns:
            Video content as bytes (MP4 format)
            
        Raises:
            Exception: If video generation fails after all retries
            RuntimeError: If source frame or reference images cannot be encoded
            
        API Structure:
            The generated request includes:
            {
              "image": {...},              # Source frame (if provided)
              "reference_images": [...],   # Reference images (if provided)
              "prompt": "...",
              "video_config": {...}
            }
            
        Example:
            # Clip 1: No source frame
            >>> video1 = client.generate_video(
            ...     prompt="Pan across room",
            ...     reference_images=["room1.png", "room2.png"]
            ... )
            
            # Clip 2: With source frame from clip 1
            >>> video2 = client.generate_video(
            ...     prompt="Continue panning",
            ...     source_frame="clip1_last_frame.png",
            ...     reference_images=["room1.png", "room2.png"]
            ... )
        """
        if not prompt:
            raise ValueError("Prompt cannot be empty or None")
        
        self.logger.info(f"Generating Veo-3 video: model={model}, {width}x{height}, {fps}fps, {duration_seconds}s")
        self.logger.debug(f"Prompt: {prompt[:100]}...")
        
        request_data = self._prepare_request(
            prompt, reference_images, source_frame, width, height, fps, duration_seconds, seed
        )
        
        return self._make_request_with_retry(request_data, model)
    
    def _prepare_request(
        self,
        prompt: str,
        reference_images: List[str] = None,
        source_frame: str = None,
        width: int = 1280,
        height: int = 720,
        fps: int = 24,
        duration_seconds: int = 8,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prepare the API request payload for Veo-3 with proper parameter separation.
        
        This method implements the Veo 3.1 API specification by creating a request
        with two distinct image parameters:
        
        1. `image`: The source/first frame (for seamless stitching)
        2. `reference_images`: Up to 3 style/content reference images
        
        Args:
            prompt: Text description for the video
            reference_images: Optional list of reference image paths (up to 3)
            source_frame: Optional path to source frame (first frame) image
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            duration_seconds: Video duration in seconds
            seed: Optional random seed
            
        Returns:
            Dictionary containing the complete API request structure
            
        Request Structure:
            {
              "instances": [{
                "prompt": str,
                "image": {                          # Source frame (optional)
                  "bytesBase64Encoded": str
                },
                "reference_images": [               # Reference images (optional)
                  {"image": {"bytesBase64Encoded": str}},
                  ...
                ],
                "video_config": {
                  "width": int,
                  "height": int,
                  "fps": int,
                  "duration_seconds": int,
                  "seed": int (optional)
                }
              }]
            }
            
        Processing:
            - Source frame: Read, encode to base64, set as `image` parameter
            - Reference images: Read each, encode to base64, add to array
            - Images validated before encoding (existence, readability)
            - Encoding failures logged but don't halt processing
        """
        
        # Base request structure for Veo-3
        request_data = {
            "instances": [{
                "prompt": prompt,
                "video_config": {
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "duration_seconds": duration_seconds
                }
            }]
        }
        
        # Add seed if provided
        if seed is not None:
            request_data["instances"][0]["video_config"]["seed"] = seed
        
        # Add source frame (first frame) if provided - for stitching
        if source_frame:
            self.logger.info(f"Using source frame for seamless stitching: {source_frame}")
            try:
                with open(source_frame, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    request_data["instances"][0]["image"] = {
                        "bytesBase64Encoded": image_data
                    }
                self.logger.debug(f"Encoded source frame: {source_frame}")
            except Exception as e:
                self.logger.error(f"Failed to encode source frame {source_frame}: {e}")
                raise
        
        # Add reference images if provided (up to 3 for style/content guidance)
        if reference_images:
            self.logger.debug(f"Encoding {len(reference_images)} reference images")
            encoded_images = []
            for image_path in reference_images:
                try:
                    with open(image_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                        encoded_images.append({
                            "image": {
                                "bytesBase64Encoded": image_data
                            }
                        })
                    self.logger.debug(f"Encoded reference image: {image_path}")
                except Exception as e:
                    # Skip images that can't be encoded
                    self.logger.warning(f"Failed to encode reference image {image_path}: {e}")
            
            if encoded_images:
                request_data["instances"][0]["reference_images"] = encoded_images
                self.logger.info(f"Added {len(encoded_images)} reference images to request")
        
        return request_data
    
    def _make_request_with_retry(self, request_data: Dict[str, Any], model: str = "veo-3.0-generate-001") -> bytes:
        """Make API request with exponential backoff retry logic."""
        
        # Vertex AI endpoint (Veo is only available through Vertex AI)
        url = f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model}:predict"
        attempt = 0
        while attempt < self.max_retries:
            try:
                # Build headers fresh each attempt to pick up refreshed tokens
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                self.logger.debug(f"Making Veo-3 API request via Vertex AI (attempt {attempt + 1})")
                self.logger.debug(f"Project: {self.project_id}, Location: {self.location}, Model: {model}")
                response = requests.post(
                    url,
                    headers=headers,
                    json=request_data,
                    timeout=300  # 5 minute timeout
                )
                
                # Handle response
                if response.status_code == 200:
                    self.logger.info("Veo-3 API request successful")
                    return self._process_successful_response(response)
                
                retry = self._handle_error_response(response, url, attempt)
                
                # If retry requested and attempts remain, back off and try again
                if retry and attempt < self.max_retries - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    self.logger.info(f"Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                    attempt += 1
                    continue
                
                # If not retrying, treat as fatal for this request
                raise Veo3APIError(
                    f"Veo-3 request failed with status {response.status_code}: {response.text[:300]}"
                )
                
            except KeyboardInterrupt:
                self.logger.warning("Operation cancelled by user")
                raise
            except requests.RequestException as e:
                self.logger.warning(f"Request exception: {e}")
                if attempt < self.max_retries - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    self.logger.info(f"Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                attempt += 1
        
        raise Veo3APIError(f"❌ Veo-3 video generation failed after {self.max_retries} attempts")

    def _handle_error_response(self, response, url: str, attempt: int) -> bool:
        """Handle non-200 responses. Return True if we should retry."""
        status = response.status_code
        
        # Map status codes to handlers
        error_handlers = {
            HTTP_RATE_LIMIT: self._handle_rate_limit_error,
            HTTP_SERVICE_UNAVAILABLE: self._handle_service_unavailable,
            HTTP_UNAUTHORIZED: self._handle_auth_error,
            HTTP_NOT_FOUND: self._handle_not_found_error,
            HTTP_BAD_REQUEST: self._handle_bad_request_error,
        }
        
        handler = error_handlers.get(status)
        if handler:
            return handler(response, url, attempt)
        
        # Default: log and retry
        return self._handle_unexpected_error(response, status)
    
    def _handle_rate_limit_error(self, response, url: str, attempt: int) -> bool:
        """Handle 429 rate limit errors."""
        self.logger.warning(f"Rate limited ({HTTP_RATE_LIMIT}), attempt {attempt + 1}/{self.max_retries}")
        try:
            error_data = response.json()
            self.logger.error(f"{HTTP_RATE_LIMIT} Error details: {error_data}")
            error_msg = error_data.get('error', {}).get('message', '').lower()
            
            if any(keyword in error_msg for keyword in QUOTA_KEYWORDS):
                self.logger.error("⚠️  QUOTA LIMIT: You've exceeded your API quota")
            elif any(keyword in error_msg for keyword in CAPACITY_KEYWORDS):
                self.logger.warning("⏳ CAPACITY: Veo service is at capacity, will retry")
            else:
                self.logger.warning(f"Rate limit reason: {error_msg}")
        except ValueError:
            self.logger.error(f"{HTTP_RATE_LIMIT} Response (raw): {response.text[:ERROR_RESPONSE_PREVIEW_LENGTH]}")
        return True
    
    def _handle_service_unavailable(self, response, url: str, attempt: int) -> bool:
        """Handle 503 service unavailable errors."""
        self.logger.warning(f"Service unavailable ({HTTP_SERVICE_UNAVAILABLE}), attempt {attempt + 1}/{self.max_retries}")
        return True
    
    def _handle_auth_error(self, response, url: str, attempt: int) -> bool:
        """Handle 401 authentication errors with auto re-auth for OAuth flows.

        Returns True if we refreshed credentials and the caller should retry.
        """
        self.logger.error(f"Authentication failed ({HTTP_UNAUTHORIZED})")
        self.logger.error(f"Response: {response.text[:ERROR_RESPONSE_PREVIEW_LENGTH]}")

        # Try to transparently refresh OAuth2 credentials and retry once
        try:
            self.logger.info("Attempting to refresh Google OAuth2 credentials...")
            # get_google_credentials handles both gcloud tokens and browser OAuth with refresh
            creds = get_google_credentials()
            if hasattr(creds, "token") and creds.token:
                self.api_key = creds.token
                self._auth_source = "oauth"
                self.logger.info("✅ Obtained a fresh access token; will retry the request")
                return True
            else:
                self.logger.error("Credential refresh did not return a valid token")
        except Exception as e:
            self.logger.error(f"Re-authentication failed: {e}")

        # If we reach here, we cannot auto-refresh; provide guidance and stop
        error_msg = (
            "❌ Authentication failed with Vertex AI and automatic re-authentication was not possible.\n"
            "This can happen if you're using a static token or lack OAuth setup.\n\n"
            "To fix:\n"
            "  • Get a fresh token: gcloud auth application-default print-access-token\n"
            "  • Then set: export GOOGLE_API_KEY=\"$(gcloud auth application-default print-access-token)\"\n"
            "  • Or run with --google-login / --google-login-browser to set up OAuth\n\n"
            "For long-term use, consider a service account. See VEO_AUTH_GUIDE.md"
        )
        raise AuthenticationError(error_msg)
    
    def _handle_not_found_error(self, response, url: str, attempt: int) -> bool:
        """Handle 404 not found errors."""
        self.logger.error(f"Endpoint not found ({HTTP_NOT_FOUND}): {url}")
        raise Veo3APIError(
            "❌ Veo-3 endpoint not found. Please check your project ID and location.\n"
            f"URL: {url}"
        )
    
    def _handle_bad_request_error(self, response, url: str, attempt: int) -> bool:
        """Handle 400 bad request errors."""
        self.logger.error(f"Bad request ({HTTP_BAD_REQUEST}) - likely request format issue")
        try:
            error_data = response.json()
            self.logger.error(f"Error details: {error_data}")
        except ValueError:
            self.logger.error(f"Response (raw): {response.text[:DETAILED_ERROR_RESPONSE_LENGTH]}")
        return False
    
    def _handle_unexpected_error(self, response, status: int) -> bool:
        """Handle unexpected error status codes."""
        self.logger.warning(f"Unexpected status code {status}, will retry")
        self.logger.error(f"Response: {response.text[:DETAILED_ERROR_RESPONSE_LENGTH]}")
        return True
    
    def _process_successful_response(self, response: Any) -> bytes:
        """Process a successful API response and extract video content."""
        try:
            response_data = response.json()
            predictions = response_data.get("predictions", [])
            
            if not predictions:
                raise VideoProcessingError("No predictions in Veo-3 response")
            
            return self._extract_video_from_prediction(predictions[0])
            
        except json.JSONDecodeError as e:
            raise Veo3APIError(f"Invalid JSON response from Veo-3: {e}")
        except VideoProcessingError:
            raise
        except Exception as e:
            raise Veo3APIError(f"Error processing Veo-3 response: {e}")
    
    def _extract_video_from_prediction(self, prediction: Dict[str, Any]) -> bytes:
        """Extract video bytes from a prediction object."""
        video_data = prediction.get("video")
        if not video_data:
            raise VideoProcessingError("No video data found in Veo-3 response")
        
        # Try base64 encoded bytes first
        if "bytesBase64Encoded" in video_data:
            return base64.b64decode(video_data["bytesBase64Encoded"])
        
        # Fall back to URI download
        if "uri" in video_data:
            return self._download_video_from_uri(video_data["uri"])
        
        raise VideoProcessingError("Video data contains neither base64 bytes nor URI")
    
    def _download_video_from_uri(self, uri: str) -> bytes:
        """Download video content from a URI."""
        try:
            # First try without auth (most URIs are pre-signed/public)
            response = requests.get(uri, timeout=300)
            if response.status_code in (HTTP_UNAUTHORIZED, 403):
                # Retry with Authorization header
                self.logger.info("Video URI requires authorization; retrying with bearer token")
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = requests.get(uri, headers=headers, timeout=300)
                if response.status_code == HTTP_UNAUTHORIZED:
                    # Attempt to refresh OAuth token and retry once
                    try:
                        self.logger.info("Refreshing Google OAuth2 credentials for video download...")
                        creds = get_google_credentials()
                        if hasattr(creds, "token") and creds.token:
                            self.api_key = creds.token
                            headers = {"Authorization": f"Bearer {self.api_key}"}
                            response = requests.get(uri, headers=headers, timeout=300)
                    except Exception as reauth_err:
                        self.logger.error(f"Re-authentication during download failed: {reauth_err}")

            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            raise Veo3APIError(f"Failed to download video from URI: {e}")
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        base_delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0.8, 1.2)  # ±20% jitter
        return base_delay * jitter
    
    def upload_files(self, file_paths: List[str]) -> List[str]:
        """
        Upload files for Veo-3 reference (if needed).
        
        Note: Veo-3 typically uses inline base64 encoding rather than separate uploads,
        so this method may not be used in the current implementation.
        
        Args:
            file_paths: List of file paths to upload
            
        Returns:
            List of file identifiers (may be the original paths for Veo-3)
        """
        
        # For Veo-3, we typically encode images inline rather than upload separately
        # So we just validate the files exist and return the paths
        validated_paths = []
        for path in file_paths:
            file_path = Path(path)
            if file_path.exists() and file_path.is_file():
                validated_paths.append(str(file_path))
        
        return validated_paths
