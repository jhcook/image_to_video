"""Azure AI Foundry Sora configuration."""

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
class AzureSoraConfig:
    """Configuration class for Azure AI Foundry Sora-2 video generation."""
    
    # API Configuration
    api_key: str
    azure_endpoint: str
    api_version: str = "2024-10-01-preview"  # Azure OpenAI API version
    default_model: str = "sora-2"  # Options: "sora-2" or "sora-2-pro"
    
    # Default video settings
    default_width: int = 1280
    default_height: int = 720
    default_fps: int = 24
    default_duration: int = 8
    default_output: str = "azure_sora_output.mp4"
    
    # Retry configuration
    retry_base_delay: int = 30      # Initial retry delay in seconds
    retry_max_delay: int = 300      # Maximum retry delay in seconds
    retry_jitter_percent: float = 0.2  # Jitter percentage (±20%)
    
    # Supported file types
    supported_image_mime_prefixes: Tuple[str, ...] = (IMAGE_MIME_PREFIX,)
    
    @classmethod
    def from_environment(cls) -> "AzureSoraConfig":
        """
        Create configuration from environment variables.
        
        Expected environment variables:
        - AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
        - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint URL
        - AZURE_OPENAI_API_VERSION: (optional) API version, defaults to 2024-10-01-preview
        
        Returns:
            AzureSoraConfig: Configuration instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if not api_key:
            raise ValueError(
                "Missing AZURE_OPENAI_API_KEY in environment or .env file\n"
                "Set it with: export AZURE_OPENAI_API_KEY=your_azure_key\n"
                "Or create a .env file with: AZURE_OPENAI_API_KEY=your_azure_key\n"
                "Get your key from: https://ai.azure.com/"
            )
        
        if not azure_endpoint:
            raise ValueError(
                "Missing AZURE_OPENAI_ENDPOINT in environment or .env file\n"
                "Set it with: export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/\n"
                "Or create a .env file with: AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/\n"
                "Get your endpoint from: https://ai.azure.com/"
            )
        
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")
        
        return cls(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version
        )
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If any configuration values are invalid
        """
        if not self.api_key:
            raise ValueError(ERROR_API_KEY_EMPTY)
        
        if not self.azure_endpoint:
            raise ValueError("Azure endpoint cannot be empty")
        
        if not self.azure_endpoint.startswith("https://"):
            raise ValueError("Azure endpoint must start with https://")
        
        if self.default_width <= 0 or self.default_height <= 0:
            raise ValueError(ERROR_DIMENSIONS_INVALID)
        
        if self.default_fps <= 0:
            raise ValueError(ERROR_FPS_INVALID)
        
        if self.default_duration <= 0:
            raise ValueError(ERROR_DURATION_INVALID)
