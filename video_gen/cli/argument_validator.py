"""
Argument validation for the video generation CLI.

This module handles validation of parsed arguments including prompt validation,
provider validation, and cross-option dependencies.
"""

from typing import Dict, Any, List, Union
from ..config import VideoProvider

# Type alias for providers (can be VideoProvider literals or list of VideoProvider)
ProviderType = Union[VideoProvider, List[VideoProvider]]


class ArgumentValidator:
    """Validates parsed CLI arguments and ensures they are consistent."""
    
    def __init__(self, supported_providers: ProviderType):
        """Initialize with list of supported providers."""
        if isinstance(supported_providers, list):
            self.supported_providers = supported_providers
        else:
            self.supported_providers = [supported_providers]
    
    def validate_and_finalize(self, result: Dict[str, Any]) -> None:
        """Validate all parsed arguments and handle conversions."""
        # Handle prompt-related conversions and validation
        self._handle_prompt_conversion(result)
        self._validate_prompt_provided(result)
    
    def _handle_prompt_conversion(self, result: Dict[str, Any]) -> None:
        """Convert prompts from list to single string if appropriate."""
        # Single prompt: convert from list to string
        if len(result['prompts']) == 1:
            result['prompt'] = result['prompts'][0]
            self._validate_prompt_not_empty(result['prompt'])
            
        # Multiple prompts: check if stitching is enabled
        elif len(result['prompts']) > 1 and not result.get('stitch', False):
            raise ValueError(f"Multiple prompts require --stitch mode.\nFound {len(result['prompts'])} prompts but --stitch not enabled.\nTip: Add --stitch flag or use only one -p argument")
            # If stitch is enabled, keep prompts as list for stitching mode
    
    def _validate_prompt_not_empty(self, prompt: str) -> None:
        """Validate that a prompt is not empty or whitespace-only."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
    
    def _validate_prompt_provided(self, result: Dict[str, Any]) -> None:
        """Ensure at least one prompt is provided."""
        if not result.get('prompt') and not result.get('prompts'):
            raise ValueError("At least one prompt is required. Use positional argument or -p/--prompt flag")
    
    def validate_provider(self, provider: str) -> None:
        """Validate that the specified provider is supported."""
        if provider not in self.supported_providers:
            supported_list = ', '.join(self.supported_providers)
            raise ValueError(f"Unsupported provider '{provider}'. Supported: {supported_list}")
    
    def validate_stitch_requirements(self, result: Dict[str, Any]) -> None:
        """Validate stitching mode requirements."""
        if result.get('stitch'):
            if len(result.get('prompts', [])) < 2:
                raise ValueError("Stitching mode requires at least 2 prompts. Use multiple -p flags.")
            
            provider = result.get('provider', 'openai')
            if provider not in ['google', 'runway']:
                raise ValueError(f"Stitching mode only supported with 'google' or 'runway' providers, not '{provider}'")
    
    def validate_dimensions(self, width: int, height: int) -> None:
        """Validate video dimensions are reasonable."""
        if width < 64 or height < 64:
            raise ValueError("Video dimensions must be at least 64x64")
        if width > 4096 or height > 4096:
            raise ValueError("Video dimensions cannot exceed 4096x4096")
    
    def validate_duration(self, duration: int, provider: str) -> None:
        """Validate duration is within provider limits."""
        if duration < 1:
            raise ValueError("Duration must be at least 1 second")
        
        # Provider-specific limits
        max_duration = {
            'openai': 20,
            'azure': 20, 
            'google': 30,
            'runway': 10
        }.get(provider, 30)
        
        if duration > max_duration:
            raise ValueError(f"Duration cannot exceed {max_duration} seconds for provider '{provider}'")
    
    def validate_fps(self, fps: int) -> None:
        """Validate frames per second is reasonable."""
        if fps < 1:
            raise ValueError("FPS must be at least 1")
        if fps > 60:
            raise ValueError("FPS cannot exceed 60")