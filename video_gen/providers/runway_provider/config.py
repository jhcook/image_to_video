"""RunwayML Gen-4 configuration."""

import os
from dataclasses import dataclass
from typing import Tuple

# Constants
IMAGE_MIME_PREFIX = "image/"
ERROR_API_KEY_EMPTY = "API key cannot be empty"
ERROR_DIMENSIONS_INVALID = "Video dimensions must be positive"
ERROR_FPS_INVALID = "FPS must be positive"
ERROR_DURATION_INVALID = "Duration must be positive"


@dataclass
class RunwayConfig:
    """Configuration class for RunwayML video generation."""
    
    # API Configuration
    api_key: str
    base_url: str = "https://api.dev.runwayml.com/v1"
    
    # Default video settings
    default_width: int = 1280
    default_height: int = 720
    default_fps: int = 24
    default_duration: int = 5  # RunwayML supports 5 or 10 seconds (Gen-4), 2-10 seconds (Veo)
    default_output: str = "runway_output.mp4"
    default_model: str = "gen4_turbo"  # Options: gen4_turbo, gen4, veo3, veo3.1, veo3.1_fast
    
    # Supported models
    SUPPORTED_MODELS = (
        "gen4_turbo",      # RunwayML Gen-4 Turbo (fastest)
        "gen4",            # RunwayML Gen-4 (higher quality)
        "gen4_aleph",      # RunwayML Gen-4 Aleph (video editing and transformation)
        "veo3",            # Google Veo 3.0 via RunwayML (40 credits/sec)
        "veo3.1",          # Google Veo 3.1 via RunwayML (40 credits/sec)
        "veo3.1_fast",     # Google Veo 3.1 Fast via RunwayML (20 credits/sec)
    )
    
    # Retry configuration
    retry_base_delay: int = 30      # Initial retry delay in seconds
    retry_max_delay: int = 300      # Maximum retry delay in seconds
    retry_jitter_percent: float = 0.2  # Jitter percentage (±20%)
    
    # Supported file types
    supported_image_mime_prefixes: Tuple[str, ...] = (IMAGE_MIME_PREFIX,)
    
    @classmethod
    def from_environment(cls) -> "RunwayConfig":
        """
        Create configuration from environment variables.
        
        Returns:
            RunwayConfig: Configuration instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv("RUNWAY_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Missing RUNWAY_API_KEY in environment or .env file\n"
                "Set it with: export RUNWAY_API_KEY=your_key_here\n"
                "Or create a .env file with: RUNWAY_API_KEY=your_key_here"
            )
        
        base_url = os.getenv("RUNWAY_BASE_URL", "https://api.dev.runwayml.com/v1")
        model = os.getenv("RUNWAY_MODEL", "gen4_turbo")
        
        return cls(api_key=api_key, base_url=base_url, default_model=model)
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If any configuration values are invalid
        """
        if not self.api_key:
            raise ValueError(ERROR_API_KEY_EMPTY)
        
        if not self.base_url:
            raise ValueError("Base URL cannot be empty")
        
        if self.default_width <= 0 or self.default_height <= 0:
            raise ValueError(ERROR_DIMENSIONS_INVALID)
        
        if self.default_fps <= 0:
            raise ValueError(ERROR_FPS_INVALID)
        
        # Validate duration based on model
        is_veo = self.default_model.startswith("veo")
        is_aleph = self.default_model == "gen4_aleph"
        
        if is_veo:
            # Veo models support 2-10 seconds
            if not (2 <= self.default_duration <= 10):
                raise ValueError("Veo models support duration between 2-10 seconds")
        elif is_aleph:
            # Aleph supports variable duration for video editing tasks
            if not (2 <= self.default_duration <= 30):
                raise ValueError("Aleph model supports duration between 2-30 seconds")
        else:
            # Gen-4 models support 5 or 10 seconds
            if self.default_duration not in [5, 10]:
                raise ValueError("Gen-4 models support duration of 5 or 10 seconds")
