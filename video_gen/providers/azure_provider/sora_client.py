"""
Azure AI Foundry Sora-2 API client for video generation.

This module provides a client to interact with Azure OpenAI's Sora-2 API for video generation,
including handling async job polling and video download.
"""

import logging
import time
import random
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path
from openai import AzureOpenAI

from .config import AzureSoraConfig
from ...retry_utils import handle_capacity_retry


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


class AzureSoraAPIClient:
    """Azure OpenAI API client with Sora-specific functionality and retry logic."""
    
    def __init__(self, config: AzureSoraConfig):
        """
        Initialize the Azure API client.
        
        Args:
            config: Azure Sora configuration containing endpoint, API key, and retry settings
        """
        if AzureOpenAI is None:
            raise ImportError("Please `pip install openai` (version 1.0.0+) first.")
        
        self.config = config
        self.logger = get_logger(__name__)
        
        # Validate Azure endpoint
        if not config.azure_endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT not set. Get your endpoint from:\n"
                "https://ai.azure.com/ (Azure AI Foundry)\n"
                "Format: https://<resource-name>.openai.azure.com/"
            )
        
        # Check for placeholder endpoint
        if "your-resource-name" in config.azure_endpoint or config.azure_endpoint == "https://your-endpoint.openai.azure.com/":
            raise ValueError(
                f"AZURE_OPENAI_ENDPOINT appears to be a placeholder: '{config.azure_endpoint}'\n"
                "Replace it with your actual Azure OpenAI endpoint from:\n"
                "https://ai.azure.com/"
            )
        
        # Validate API key if provided
        if config.api_key:
            if config.api_key in ("your_azure_api_key_here", "your_api_key_here"):
                raise ValueError(
                    f"AZURE_OPENAI_API_KEY appears to be a placeholder: '{config.api_key}'\n"
                    "Replace it with your actual API key from Azure portal,\n"
                    "or remove it to use Azure CLI authentication (az login)"
                )
        
        self.client = AzureOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.azure_endpoint,
            api_version=config.api_version
        )
        self.logger.debug(f"AzureSoraAPIClient initialized: endpoint={config.azure_endpoint}")
    
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
            Azure OpenAI API response object
            
        Raises:
            RuntimeError: For non-retryable API errors
            KeyboardInterrupt: If user cancels during retry
        """
        # Use specified model or fall back to config default
        selected_model = model or self.config.default_model
        
        retry_count = 0
        self.logger.info(f"Creating Azure Sora video request: model={selected_model}, {width}x{height}, {fps}fps, {duration_seconds}s")
        self.logger.debug(f"Content items: {len(content_items)} items, seed: {seed}")
        
        while True:  # Retry forever until success
            try:
                self.logger.debug(f"Sending Azure API request (attempt {retry_count + 1})")
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
                self.logger.info("Azure Sora API request successful")
                return response
                
            except Exception as e:
                error_str = str(e)
                self.logger.debug(f"Azure API error occurred: {error_str}")
                
                # Check for capacity issues that should trigger retry
                if self._is_capacity_error(error_str):
                    retry_count += 1
                    self.logger.warning(f"Azure capacity issue detected, retrying... (attempt {retry_count})")
                    self._handle_capacity_retry(retry_count)
                    continue
                
                # Handle non-retryable errors
                self._handle_fatal_error(error_str, e)
    
    def _is_capacity_error(self, error_str: str) -> bool:
        """Check if error indicates capacity/rate limit issue."""
        return "503" in error_str and "capacity" in error_str.lower()
    
    def _handle_fatal_error(self, error_str: str, exception: Exception) -> None:
        """Handle non-retryable API errors."""
        if "404" in error_str or "not found" in error_str.lower():
            # Extract model name from error if possible
            model_name = "Unknown"
            if "model" in error_str.lower():
                # Try to extract model name from error message
                import re
                match = re.search(r'model[`\s]+["\']?([\w.-]+)', error_str, re.IGNORECASE)
                if match:
                    model_name = match.group(1)
            
            self.logger.error(f"Sora model not found in Azure deployment: {model_name}")
            
            error_msg = (
                f"\n{'='*60}\n"
                f"❌ Model Not Found in Azure: '{model_name}'\n"
                f"{'='*60}\n\n"
                "The model is not deployed in your Azure AI Foundry resource.\n\n"
                "Common models available:\n"
                "   • sora-1 (if deployed)\n"
                "   • sora-2 (standard)\n"
                "   • sora-2-pro (advanced)\n\n"
                "Required steps:\n"
                "   1. Visit https://ai.azure.com/\n"
                "   2. Select your Azure OpenAI resource\n"
                "   3. Go to 'Deployments' → 'Create new deployment'\n"
                "   4. Select the Sora model you want to use\n"
                "   5. Deployment name must match model name\n\n"
                "To list available models:\n"
                "   ./image2video.py --list-models azure-sora\n\n"
                f"Original error:\n"
                f"   {error_str}\n"
                f"{'='*60}"
            )
            raise RuntimeError(error_msg)
        elif "401" in error_str or "unauthorized" in error_str.lower():
            self.logger.error(
                "Authentication failed (401 Unauthorized). This usually means:\n"
                "  1. AZURE_OPENAI_API_KEY is invalid or expired\n"
                "  2. Azure CLI not authenticated (if not using API key)\n"
                "  3. Missing permissions on the Azure OpenAI resource\n\n"
                "Solutions:\n"
                "  • Verify API key in Azure portal: https://portal.azure.com/\n"
                "  • Or authenticate Azure CLI: az login\n"
                "  • Check you have 'Cognitive Services User' role on the resource\n"
                "  • Verify resource exists: https://ai.azure.com/"
            )
            raise RuntimeError(
                "Azure authentication failed. Invalid API key or insufficient permissions.\n"
                "Check your AZURE_OPENAI_API_KEY or run: az login"
            )
        elif "403" in error_str or "forbidden" in error_str.lower():
            self.logger.error("Access forbidden - check Azure permissions")
            raise RuntimeError(
                "Access forbidden. Please check:\n"
                "1. Your Azure subscription has access to Sora models\n"
                "2. Your API key has the correct permissions\n"
                "3. Your resource is in a supported region"
            )
        else:
            self.logger.error(f"Unexpected Azure API error: {exception}")
            raise RuntimeError(f"Azure API Error: {exception}")
    
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
        self.logger.info(f"Polling Azure async job: {job_id}")
        
        status = getattr(response, "status", None) or "queued"
        last_state = None
        
        while status not in {"completed", "failed", "canceled"}:
            if status != last_state:
                self.logger.info(f"Azure job status: {status}")
                last_state = status
            time.sleep(3)  # Poll every 3 seconds
            
            # Try to retrieve job status using available API endpoints
            try:
                self.logger.debug("Retrieving Azure job status via responses.retrieve")
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
            self.logger.error(f"Azure job failed with status: {status}")
            raise RuntimeError(f"Azure video job did not complete successfully: {status}")
        
        self.logger.info("Azure job completed successfully")
        return response
    
    def download_video(self, video_file_id: str, output_path: str) -> None:
        """
        Download a video file from Azure OpenAI.
        
        Args:
            video_file_id: Azure OpenAI file ID of the video
            output_path: Local path to save the video
        """
        self.logger.info(f"Downloading Azure video file: {video_file_id}")
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
        
        self.logger.info(f"Video downloaded successfully from Azure: {output_path}")
