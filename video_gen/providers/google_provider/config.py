# Copied from google/config.py
"""Google Veo-3 configuration."""

import os
from dataclasses import dataclass
from typing import Optional, Tuple

# Constants
IMAGE_MIME_PREFIX = "image/"
DEFAULT_VEO_MODEL = "veo-3.1-fast-generate-preview"
ERROR_API_KEY_EMPTY = "API key cannot be empty"
ERROR_DIMENSIONS_INVALID = "Video dimensions must be positive"
ERROR_FPS_INVALID = "FPS must be positive"
ERROR_DURATION_INVALID = "Duration must be positive"


@dataclass
class Veo3Config:
	"""Configuration class for Google Veo-3 video generation."""
    
	# API Configuration
	api_key: str
	project_id: Optional[str] = None
	location: str = "us-central1"
	default_model: str = DEFAULT_VEO_MODEL  # Veo 3.1 fast generation (default)
    
	# Default video settings
	default_width: int = 1280
	default_height: int = 720
	default_fps: int = 24
	default_duration: int = 8
	default_output: str = "veo3_output.mp4"
    
	# Retry configuration
	retry_base_delay: int = 30      # Initial retry delay in seconds
	retry_max_delay: int = 300      # Maximum retry delay in seconds
	retry_jitter_percent: float = 0.2  # Jitter percentage (±20%)
    
	# Supported file types
	supported_image_mime_prefixes: Tuple[str, ...] = (IMAGE_MIME_PREFIX,)
    
	@classmethod
	def from_environment(cls) -> "Veo3Config":
		"""
		Create configuration from environment variables.
        
		Returns:
			Veo3Config: Configuration instance
            
		Raises:
			ValueError: If required environment variables are missing
		"""
		# Primary: GOOGLE_API_KEY, fallback to VEO3_API_KEY or service account
		api_key = (
			os.getenv("GOOGLE_API_KEY") or
			os.getenv("VEO3_API_KEY") or
			os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
		)
        
		if not api_key:
			raise ValueError(
				"Missing Veo-3 API credentials in environment or .env file\n"
				"Set GOOGLE_API_KEY:\n"
				"  export GOOGLE_API_KEY=your_key_here\n"
				"Or create a .env file with: GOOGLE_API_KEY=your_key_here"
			)
        
		# Project ID is optional (not required for API key authentication)
		project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("VEO3_PROJECT_ID")
        
		# Support both GOOGLE_CLOUD_LOCATION and VEO3_LOCATION (prefer GOOGLE_CLOUD_LOCATION)
		location = (
			os.getenv("GOOGLE_CLOUD_LOCATION") or 
			os.getenv("VEO3_LOCATION") or 
			"us-central1"
		)
        
		return cls(api_key=api_key, project_id=project_id, location=location)
    
	def validate(self) -> None:
		"""
		Validate configuration values.
        
		Raises:
			ValueError: If any configuration values are invalid
		"""
		if not self.api_key:
			raise ValueError(ERROR_API_KEY_EMPTY)
        
		# Project ID is optional for API key authentication
        
		if not self.location:
			raise ValueError("Location cannot be empty")
        
		if self.default_width <= 0 or self.default_height <= 0:
			raise ValueError(ERROR_DIMENSIONS_INVALID)
        
		if self.default_fps <= 0:
			raise ValueError(ERROR_FPS_INVALID)
        
		if self.default_duration <= 0:
			raise ValueError(ERROR_DURATION_INVALID)
