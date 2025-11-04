"""
OpenAI Sora API client with retry logic for video generation.

Handles API calls, error handling, and exponential backoff retry mechanisms.
"""

import time
import random
from typing import Dict, Any, List

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from ...logger import get_library_logger
from .config import SoraConfig


class SoraAPIClient:
    """OpenAI API client with Sora-specific functionality and retry logic."""
    
    def __init__(self, config: SoraConfig):
        """
        Initialize the API client.
        
        Args:
            config: Sora configuration containing API key and retry settings
        """
        if OpenAI is None:
            raise ImportError("Please `pip install openai` first.")
        
        self.config = config
        self.logger = get_library_logger()
        
        # Validate API key
        if not config.api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. Get your API key from:\n"
                "https://platform.openai.com/api-keys\n"
                "and set it in your .env file: OPENAI_API_KEY=sk-..."
            )
        
        # Check for placeholder values
        if config.api_key in ("your_openai_api_key_here", "your_api_key_here", "sk-..."):
            raise ValueError(
                f"OPENAI_API_KEY appears to be a placeholder: '{config.api_key}'\n"
                "Replace it with your actual API key from:\n"
                "https://platform.openai.com/api-keys"
            )
        
        self.client = OpenAI(api_key=config.api_key)
        self.logger.debug("SoraAPIClient initialized")
    
    def create_video_request(
        self,
        content_items: List[Dict[str, Any]],
        width: int,
        height: int,
        fps: int,
        duration_seconds: int,
        seed: int = None,
        model: str = None
    ) -> Any:
        """
        Create a video generation request with retry logic.
        
        Args:
            content_items: List of content items (text + images)
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            duration_seconds: Video duration in seconds
            seed: Optional random seed
            model: Model to use (sora-2 or sora-2-pro), defaults to config default
            
        Returns:
            OpenAI API response object
            
        Raises:
            RuntimeError: For non-retryable API errors
            KeyboardInterrupt: If user cancels during retry
        """
        # Use specified model or fall back to config default
        selected_model = model or self.config.default_model
        
        retry_count = 0
        self.logger.info(f"Creating Sora-2 video request: model={selected_model}, {width}x{height}, {fps}fps, {duration_seconds}s")
        self.logger.debug(f"Content items: {len(content_items)} items, seed: {seed}")
        
        while True:  # Retry forever until success
            try:
                self.logger.debug(f"Sending API request (attempt {retry_count + 1})")
                response = self.client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {
                            "role": "user",
                            "content": content_items,
                        }
                    ],
                    extra_body={
                        "video": {
                            "format": "mp4",
                            "dimensions": f"{width}x{height}",
                            "duration": duration_seconds,
                            "fps": fps,
                            **({"seed": seed} if seed is not None else {}),
                        }
                    }
                )
                
                # Success - return response
                self.logger.info("Sora-2 API request successful")
                return response
                
            except Exception as e:
                error_str = str(e)
                self.logger.debug(f"API error occurred: {error_str}")
                
                # Check for capacity issues that should trigger retry
                if "503" in error_str and "capacity" in error_str.lower():
                    retry_count += 1
                    self.logger.warning(f"Capacity issue detected, retrying... (attempt {retry_count})")
                    self._handle_capacity_retry(retry_count)
                    continue
                
                # Handle other errors that shouldn't trigger retry
                elif "404" in error_str or "not found" in error_str.lower():
                    self.logger.error("Sora-2 model not found")
                    raise RuntimeError("Sora-2 model not found. Please check if you have access to the Sora API.")
                elif "401" in error_str or "unauthorized" in error_str.lower():
                    self.logger.error(
                        "Authentication failed (401 Unauthorized). This usually means:\n"
                        "  1. OPENAI_API_KEY is invalid or expired\n"
                        "  2. API key doesn't have access to Sora models\n"
                        "  3. Sora access not enabled for your account\n\n"
                        "Solutions:\n"
                        "  • Verify your API key at: https://platform.openai.com/api-keys\n"
                        "  • Check Sora access in your account settings\n"
                        "  • Join the waitlist if you don't have access yet"
                    )
                    raise RuntimeError(
                        "OpenAI authentication failed. Invalid API key or no Sora access.\n"
                        "Verify your key at https://platform.openai.com/api-keys"
                    )
                else:
                    self.logger.error(f"Unexpected API error: {e}")
                    raise RuntimeError(f"API Error: {e}")
    
    def _handle_capacity_retry(self, retry_count: int) -> None:
        """
        Handle capacity retry with exponential backoff.
        
        Args:
            retry_count: Current retry attempt number
            
        Raises:
            KeyboardInterrupt: If user cancels during backoff
        """
        # Calculate delay with exponential backoff and jitter
        delay = min(
            self.config.retry_base_delay * (2 ** min(retry_count - 1, 4)),
            self.config.retry_max_delay
        )
        
        # Add random jitter to avoid thundering herd
        jitter = delay * self.config.retry_jitter_percent * (random.random() - 0.5)
        actual_delay = max(1, delay + jitter)
        
        self.logger.info(f"Waiting {actual_delay:.1f}s before retry {retry_count}...")
        
        try:
            time.sleep(actual_delay)
        except KeyboardInterrupt:
            self.logger.warning("Operation cancelled by user")
            raise RuntimeError("Operation cancelled by user")
    
    def poll_async_job(self, response: Any) -> Any:
        """
        Poll an asynchronous job until completion.
        
        Args:
            response: Initial API response with job ID
            
        Returns:
            Completed response object
            
        Raises:
            RuntimeError: If job fails or cannot retrieve status
        """
        job_id = response.id
        self.logger.info(f"Polling async job: {job_id}")
        
        status = getattr(response, "status", None) or "queued"
        last_state = None
        
        while status not in {"completed", "failed", "canceled"}:
            if status != last_state:
                self.logger.info(f"Job status: {status}")
                last_state = status
            time.sleep(3)  # Poll every 3 seconds
            
            # Try to retrieve job status using available API endpoints
            try:
                self.logger.debug("Retrieving job status via responses.retrieve")
                response = self.client.responses.retrieve(job_id)
            except Exception as e1:
                self.logger.debug(f"responses.retrieve failed: {e1}, trying chat.completions.retrieve")
                try:
                    response = self.client.chat.completions.retrieve(job_id)
                except Exception as e2:
                    self.logger.debug(f"chat.completions.retrieve also failed: {e2}, will retry")
                    continue
            status = getattr(response, "status", None) or "queued"
        
        if status != "completed":
            self.logger.error(f"Job failed with status: {status}")
            raise RuntimeError(f"Video job did not complete successfully: {status}")
        
        self.logger.info("Job completed successfully")
        return response
    
    def download_video(self, video_file_id: str, output_path: str) -> None:
        """
        Download a video file from OpenAI.
        
        Args:
            video_file_id: OpenAI file ID of the video
            output_path: Local path to save the video
        """
        self.logger.info(f"Downloading video file: {video_file_id}")
        content = self.client.files.content(video_file_id)
        
        # Handle both streaming and direct bytes responses
        data = getattr(content, "read", None)
        if callable(data):
            blob = data()
        else:
            blob = content  # already bytes
        
        self.logger.debug(f"Writing video to: {output_path} ({len(blob)} bytes)")
        # Save video to specified output path
        with open(output_path, "wb") as f:
            f.write(blob)
        
        self.logger.info(f"Video downloaded successfully: {output_path}")
