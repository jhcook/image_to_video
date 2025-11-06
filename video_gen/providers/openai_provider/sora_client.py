"""
OpenAI Sora API client with retry logic for video generation.

Handles API calls, error handling, and exponential backoff retry mechanisms.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Union

import openai
from openai import OpenAI

from ...logger import get_library_logger
from ...retry_utils import handle_capacity_retry
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
        seed: Optional[int] = None,
        model: Optional[str] = None
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
        selected_model = model or self.config.default_model
        self.logger.info(f"Creating Sora-2 video request: model={selected_model}, {width}x{height}, {fps}fps, {duration_seconds}s")
        self.logger.debug(f"Content items: {len(content_items)} items, seed: {seed}")
        
        prompt_text = self._extract_prompt_from_content(content_items)
        return self._execute_video_request_with_retry(selected_model, prompt_text, width, height, duration_seconds, seed)
    
    def _extract_prompt_from_content(self, content_items: List[Union[Dict[str, Any], str]]) -> str:
        """
        Extract text prompt from content items.
        
        Args:
            content_items: List of content items containing text and images
            
        Returns:
            Extracted prompt text or default fallback
        """
        prompt_text = ""
        
        for item in content_items:
            if isinstance(item, dict):
                if item.get("type") in ["text", "input_text"]:
                    prompt_text += item.get("text", "")
                elif item.get("type") == "image_url":
                    # For now, we'll handle images separately
                    # The new API expects file uploads
                    pass
            elif isinstance(item, str):
                prompt_text += item
        
        # Fallback if no prompt found
        return prompt_text.strip() or "Generate a video"
    
    def _execute_video_request_with_retry(
        self, 
        model: str, 
        prompt: str, 
        width: int, 
        height: int, 
        duration_seconds: int, 
        seed: Optional[int] = None
    ) -> Any:
        """
        Execute video request with infinite retry on capacity issues.
        
        Args:
            model: Model to use for generation
            prompt: Text prompt for video generation
            width: Video width in pixels
            height: Video height in pixels
            duration_seconds: Video duration in seconds
            seed: Optional random seed
            
        Returns:
            API response object
            
        Raises:
            RuntimeError: For non-retryable errors
        """
        retry_count = 0
        
        while True:  # Retry forever until success
            try:
                self.logger.debug(f"Sending API request (attempt {retry_count + 1})")
                
                video_params = self._prepare_video_parameters(model, prompt, width, height, duration_seconds, seed)
                response = self.client.videos.create(**video_params)
                
                self.logger.info("Sora-2 API request successful")
                return response
                
            except Exception as e:
                if self._should_retry_error(e):
                    retry_count += 1
                    self.logger.warning(f"Capacity issue detected, retrying... (attempt {retry_count})")
                    self._handle_capacity_retry(retry_count)
                    continue
                else:
                    self._handle_non_retryable_error(e, model, duration_seconds)
    
    def _prepare_video_parameters(
        self, 
        model: str, 
        prompt: str, 
        width: int, 
        height: int, 
        duration_seconds: int, 
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prepare video creation parameters for API request.
        
        Args:
            model: Model to use for generation
            prompt: Text prompt for video generation
            width: Video width in pixels
            height: Video height in pixels
            duration_seconds: Video duration in seconds
            seed: Optional random seed
            
        Returns:
            Dictionary of API parameters
        """
        video_params = {
            "model": model,
            "prompt": prompt,
            "seconds": str(duration_seconds),
            "size": f"{width}x{height}",
        }
        
        if seed is not None:
            video_params["seed"] = str(seed)
        
        self.logger.debug(f"Video creation parameters: {video_params}")
        return video_params
    
    def _should_retry_error(self, error: Exception) -> bool:
        """
        Determine if an error should trigger a retry.
        
        Args:
            error: Exception that occurred
            
        Returns:
            True if error should trigger retry, False otherwise
        """
        error_str = str(error)
        return "503" in error_str and "capacity" in error_str.lower()
    
    def _handle_non_retryable_error(self, error: Exception, model: str, duration_seconds: int) -> None:
        """
        Handle errors that should not trigger retries.
        
        Args:
            error: Exception that occurred
            model: Model that was being used
            duration_seconds: Video duration that was requested
            
        Raises:
            Various exceptions based on error type
        """
        error_str = str(error)
        self.logger.debug(f"API error occurred: {error_str}")
        
        if self._is_connection_error(error_str, error):
            self._handle_connection_error()
        elif self._is_organization_verification_error(error_str):
            self._handle_organization_verification_error()
        elif self._is_invalid_duration_error(error_str):
            self._handle_invalid_duration_error(duration_seconds)
        elif "404" in error_str or "not found" in error_str.lower():
            self._handle_model_not_found_error(model, error_str)
        elif "401" in error_str or "unauthorized" in error_str.lower():
            self._handle_authentication_error()
        else:
            self.logger.error(f"Unexpected API error: {error}")
            raise RuntimeError(f"API Error: {error}")
    
    def _is_connection_error(self, error_str: str, error: Exception) -> bool:
        """Check if error is a connection/SSL error."""
        return ("ssl" in error_str.lower() or "certificate" in error_str.lower() or 
                "connection" in error_str.lower() or "apiconnectionerror" in str(type(error)).lower())
    
    def _is_organization_verification_error(self, error_str: str) -> bool:
        """Check if error is an organization verification error."""
        return "403" in error_str and "organization must be verified" in error_str.lower()
    
    def _is_invalid_duration_error(self, error_str: str) -> bool:
        """Check if error is an invalid duration error."""
        return "400" in error_str and "Invalid value" in error_str and "seconds" in error_str
    
    def _handle_connection_error(self) -> None:
        """Handle connection/SSL errors with helpful guidance."""
        print("\n" + "="*60)
        print("🔒 Connection/SSL Error")
        print("="*60)
        print("Failed to connect to OpenAI API due to network/SSL issues.")
        print("\n💡 Quick fixes:")
        print("   • Check your internet connection")
        print("   • Try running: pip install --upgrade certifi")
        print("   • If using corporate network, check proxy settings")
        print("   • Temporarily try a different network (mobile hotspot)")
        print("\n🔄 Alternative options:")
        print("   • Try Google Veo: --provider google")
        print("   • Try RunwayML: --provider runway")
        print("="*60)
        from ...exceptions import AuthenticationError
        raise AuthenticationError("Connection/SSL error - see instructions above")
    
    def _handle_organization_verification_error(self) -> None:
        """Handle organization verification errors with helpful guidance."""
        self.logger.warning(
            "Organization verification required for Sora models.\n"
            "If you've already verified, please wait up to 15 minutes for access to propagate.\n"
            "You can continue using other providers in the meantime."
        )
        print("\n" + "="*60)
        print("⚠️  OpenAI Organization Verification Required")
        print("="*60)
        print("Your OpenAI organization needs to be verified to use Sora models.")
        print()
        print("✅ If you haven't verified yet:")
        print("   Visit: https://platform.openai.com/settings/organization/general")
        print("   Click 'Verify Organization'")
        print()
        print("⏳ If you've already verified:")
        print("   Please wait up to 15 minutes for access to propagate")
        print("   Then try again with the same command")
        print()
        print("🔄 Alternative options while waiting:")
        print("   • Try Google Veo: --provider google")
        print("   • Try RunwayML: --provider runway")
        print("="*60)
        from ...exceptions import AuthenticationError
        raise AuthenticationError(
            "OpenAI organization verification required. "
            "See instructions above and try again after verification propagates."
        )
    
    def _handle_invalid_duration_error(self, duration_seconds: int) -> None:
        """Handle invalid duration errors with helpful guidance."""
        print("\n" + "="*60)
        print("⚠️  Invalid Duration Parameter")
        print("="*60)
        print(f"You requested {duration_seconds} seconds, but OpenAI Sora only supports:")
        print("   • 4 seconds  (--duration 4)")
        print("   • 8 seconds  (--duration 8)")
        print("   • 12 seconds (--duration 12)")
        print()
        print("🔄 Please try again with a supported duration:")
        print("   ./image2video.py --provider openai --duration 8 [other options]")
        print("="*60)
        raise RuntimeError(
            f"Invalid duration: {duration_seconds}s. OpenAI Sora only supports 4, 8, or 12 seconds."
        )
    
    def _handle_authentication_error(self) -> None:
        """Handle authentication errors with helpful guidance."""
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
    
    def _handle_model_not_found_error(self, model: str, error_str: str) -> None:
        """
        Handle model not found error with helpful guidance.
        
        Args:
            model: The model that was not found
            error_str: The error string from the API
            
        Raises:
            RuntimeError: Always, with detailed error message
        """
        self.logger.error(f"Sora model not found: {model}")
        
        # Try to get available models from the API
        available_models = []
        try:
            models = self.client.models.list()
            available_models = [m.id for m in models.data if m.id.startswith("sora")]
        except Exception:
            # Fall back to common models if API query fails
            available_models = ["sora-2", "sora-2-pro"]
        
        error_msg = (
            f"\n{'='*60}\n"
            f"❌ Model Not Found: '{model}'\n"
            f"{'='*60}\n\n"
            f"The model '{model}' does not exist or you do not have access to it.\n\n"
        )
        
        if available_models:
            error_msg += "✅ Available models in your account:\n"
            for m in available_models:
                error_msg += f"   • {m}\n"
            error_msg += "\nTo use an available model:\n"
            error_msg += f"   ./image2video.py --provider openai --model {available_models[0]} -p \"Your prompt\"\n\n"
        else:
            error_msg += "⚠️  Could not retrieve available models from your account.\n\n"
        
        error_msg += (
            "Common reasons:\n"
            "  1. Model name typo - Check spelling and use --list-models\n"
            "  2. Sora access not enabled - Visit https://platform.openai.com/\n"
            "  3. Model requires waitlist approval\n"
            "  4. Using wrong API key (check OPENAI_API_KEY)\n\n"
            "To see all available models:\n"
            "   ./image2video.py --list-models openai\n\n"
            f"Original API error:\n"
            f"   {error_str}\n"
            f"{'='*60}"
        )
        
        raise RuntimeError(error_msg)
    
    def _handle_capacity_retry(self, retry_count: int) -> None:
        """
        Handle capacity retry with exponential backoff.
        
        Args:
            retry_count: Current retry attempt number
            
        Raises:
            RuntimeError: If user cancels during backoff
        """
        handle_capacity_retry(retry_count, self.config, self.logger)
    
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
        self.logger.info(f"Polling async video job: {job_id}")
        
        status = getattr(response, "status", None) or "queued"
        last_state = None
        
        while status not in {"completed", "failed", "cancelled"}:
            if status != last_state:
                self.logger.info(f"Job status: {status}")
                last_state = status
            time.sleep(3)  # Poll every 3 seconds
            
            try:
                self.logger.debug("Retrieving video job status")
                response = self.client.videos.retrieve(job_id)
                status = getattr(response, "status", None) or "queued"
            except Exception as e:
                self.logger.debug(f"Error retrieving job status: {e}, will retry")
                continue
        
        if status != "completed":
            self.logger.error(f"Video job failed with status: {status}")
            raise RuntimeError(f"Video job did not complete successfully: {status}")
        
        self.logger.info("Video job completed successfully")
        return response
    
    def download_video(self, video_id: str, output_path: str) -> None:
        """
        Download a video file from OpenAI.
        
        Args:
            video_id: OpenAI video job ID  
            output_path: Local path to save the video
        """
        self.logger.info(f"Downloading video: {video_id}")
        
        try:
            # Use direct HTTP request for video content download
            import httpx
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            
            self.logger.debug(f"Downloading from: https://api.openai.com/v1/videos/{video_id}/content")
            response = httpx.get(
                f"https://api.openai.com/v1/videos/{video_id}/content",
                headers=headers,
                timeout=300  # 5 minute timeout for large video downloads
            )
            response.raise_for_status()
            
            blob = response.content
            self.logger.debug(f"Writing video to: {output_path} ({len(blob)} bytes)")
            
            # Save video to specified output path
            with open(output_path, "wb") as f:
                f.write(blob)
            
            self.logger.info(f"Video downloaded successfully: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to download video {video_id}: {e}")
            raise RuntimeError(f"Failed to download video: {e}")
