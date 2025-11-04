"""
Configuration for OpenAI Sora video generation.
"""

import os
from dataclasses import dataclass

# Import constants from parent config
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

IMAGE_MIME_PREFIX = "image/"
ERROR_API_KEY_EMPTY = "API key cannot be empty"
ERROR_DIMENSIONS_INVALID = "Width and height must be positive"
ERROR_FPS_INVALID = "FPS must be positive"
ERROR_DURATION_INVALID = "Duration must be positive"


@dataclass
class SoraConfig:
    """Configuration class for Sora-2 video generation."""
    
    # API Configuration
    api_key: str
    default_model: str = "sora-2"  # Options: "sora-2" or "sora-2-pro"
    
    # Default video settings
    default_width: int = 1280
    default_height: int = 720
    default_fps: int = 24
    default_duration: int = 8
    default_output: str = "sora2_output.mp4"
    
    # Retry configuration
    retry_base_delay: int = 30      # Initial retry delay in seconds
    retry_max_delay: int = 300      # Maximum retry delay in seconds
    retry_jitter_percent: float = 0.2  # Jitter percentage (±20%)
    
    # Supported file types
    supported_image_mime_prefixes: tuple = (IMAGE_MIME_PREFIX,)
    
    @classmethod
    def from_environment(cls) -> "SoraConfig":
        """
        Create configuration from environment variables.
        
        Returns:
            SoraConfig: Configuration instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "Missing OPENAI_API_KEY in environment or .env file\n"
                "Set it with: export OPENAI_API_KEY=your_key_here\n"
                "Or create a .env file with: OPENAI_API_KEY=your_key_here"
            )
        
        return cls(api_key=api_key)
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If any configuration values are invalid
        """
        if not self.api_key:
            raise ValueError(ERROR_API_KEY_EMPTY)
        
        if self.default_width <= 0 or self.default_height <= 0:
            raise ValueError(ERROR_DIMENSIONS_INVALID)
        
        if self.default_fps <= 0:
            raise ValueError(ERROR_FPS_INVALID)
        
        if self.default_duration <= 0:
            raise ValueError(ERROR_DURATION_INVALID)
