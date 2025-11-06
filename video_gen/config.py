"""
Configuration module for video generation providers.

Handles environment variables, API keys, and default settings for
both Sora-2 and Veo-3 video generation models.
"""

import os
from dataclasses import dataclass
from typing import Optional, Literal

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed; assume environment variables are set elsewhere
    pass

# Import all provider configs
from .providers.openai_provider import SoraConfig
from .providers.azure_provider import AzureSoraConfig
from .providers.google_provider import Veo3Config
from .providers.runway_provider import RunwayConfig

# Constants
IMAGE_MIME_PREFIX = "image/"
DEFAULT_VEO_MODEL = "veo-3.1-fast-generate-preview"
DEFAULT_VEO_MODEL_FAST = DEFAULT_VEO_MODEL  # Alias for clarity
VEO_31_PREFIX = "veo-3.1"

# Error messages
ERROR_API_KEY_EMPTY = "API key cannot be empty"
ERROR_DIMENSIONS_INVALID = "Width and height must be positive"
ERROR_FPS_INVALID = "FPS must be positive"
ERROR_DURATION_INVALID = "Duration must be positive"

VideoProvider = Literal["openai", "azure", "google", "runway"]


@dataclass
class BaseConfig:
    """Base configuration class for video generation."""
    
    # Default video settings
    default_width: int = 1280
    default_height: int = 720
    default_fps: int = 24
    default_duration: int = 8
    default_output: str = "video_output.mp4"
    
    # Retry configuration
    retry_base_delay: int = 30      # Initial retry delay in seconds
    retry_max_delay: int = 300      # Maximum retry delay in seconds
    retry_jitter_percent: float = 0.2  # Jitter percentage (±20%)
    
    # Supported file types
    supported_image_mime_prefixes: tuple = (IMAGE_MIME_PREFIX,)


    # Re-export for backward compatibility (all configs now defined in provider modules)


def create_config_for_provider(provider: VideoProvider):
    """
    Create appropriate configuration for the specified provider.
    
    Args:
        provider: The video generation provider to use
        
    Returns:
        Configuration instance for the specified provider
        
    Raises:
        ValueError: If provider is not supported or configuration is invalid
    """
    config_map = {
        "openai": SoraConfig,
        "azure": AzureSoraConfig,
        "google": Veo3Config,
        "runway": RunwayConfig
    }
    
    config_class = config_map.get(provider)
    if not config_class:
        raise ValueError(f"Unsupported provider: {provider}. Use 'openai', 'azure', 'google', or 'runway'")
    
    return config_class.from_environment()


def get_available_providers() -> list[VideoProvider]:
    """
    Get list of available providers based on environment configuration.
    
    Returns:
        List of available provider names
    """
    provider_checks = {
        "openai": lambda: bool(os.getenv("OPENAI_API_KEY")),
        "azure": lambda: bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT")),
        "google": lambda: bool(
            os.getenv("GOOGLE_API_KEY") or 
            os.getenv("VEO3_API_KEY") or 
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        ),
        "runway": lambda: bool(os.getenv("RUNWAY_API_KEY"))
    }
    
    return [provider for provider, check in provider_checks.items() if check()]


def get_default_model(provider: VideoProvider) -> str:
    """
    Get the default model for a provider.
    
    Args:
        provider: The video generation provider
        
    Returns:
        Default model name for that provider

    Raises:
        ValueError: If provider is not supported
    """
    default_models = {
        "openai": "sora-2",
        "azure": "sora-2",
        "google": DEFAULT_VEO_MODEL,
        "runway": "gen4_turbo"
    }
    
    if provider not in default_models:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return default_models[provider]


def get_available_models(provider: VideoProvider, query_api: bool = False) -> list[str]:
    """
    Get list of available models for the specified provider.
    
    This function uses a hybrid approach:
    - OpenAI: Can query the API live via models.list() to get current models
    - Google Veo/RunwayML: Use hardcoded lists (these APIs don't have model list endpoints)
    
    Args:
        provider: The video generation provider
        query_api: If True, query the API for available models (OpenAI only)
        
    Returns:
        List of available model names for that provider
        
    Raises:
        ValueError: If provider is not supported
    """
    # For OpenAI, optionally query the API for available models
    if provider == "openai" and query_api:
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                client = OpenAI(api_key=api_key)
                models = client.models.list()
                # Filter for Sora models
                sora_models = [m.id for m in models.data if m.id.startswith("sora")]
                if sora_models:
                    return sorted(sora_models)
        except Exception:
            # Fall back to hardcoded list if API query fails
            pass
    
    # Hardcoded lists (fallback or for providers without list API)
    models_by_provider = {
        "openai": [
            "sora-2",      # Standard quality
            "sora-2-pro"   # Higher quality, more advanced
        ],
        "azure": [
            "sora-2",      # Standard quality (Azure deployment)
            "sora-2-pro"   # Higher quality, more advanced (Azure deployment)
        ],
        "google": [
            "veo-3.1-generate-preview",      # Standard quality (3.1)
            DEFAULT_VEO_MODEL,                # Fast generation (3.1)
            "veo-3.0-generate-001",      # Standard quality (3.0)
            "veo-3.0-fast-generate-001"  # Fast generation (3.0)
        ],
        "runway": [
            "gen4_turbo",   # Runway Gen-4 (fast)
            "gen4",         # Runway Gen-4 (quality)
            "veo3.1_fast",  # Google Veo 3.1 Fast via Runway
            "veo3.1",       # Google Veo 3.1 via Runway
            "veo3"          # Google Veo 3.0 via Runway
        ]
    }
    
    if provider not in models_by_provider:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return models_by_provider[provider]


def print_available_providers() -> None:
    """
    Print all providers with their availability status and requirements.
    """
    print("=" * 70)
    print("Available Video Generation Providers")
    print("=" * 70)
    
    all_providers = ["openai", "azure", "google", "runway"]
    available = get_available_providers()
    descriptions = _get_provider_descriptions()
    
    print("\nConfigured Providers:")
    print("-" * 70)
    
    for provider in all_providers:
        is_available = provider in available
        status = "✅ Available" if is_available else "❌ Not configured"
        desc = descriptions.get(provider, provider.upper())
        
        print(f"\n  {provider:<10} {status}")
        print(f"  {desc}")
        
        # Show environment requirements
        env_requirements = _get_provider_env_requirements(provider)
        print(f"  Requires: {env_requirements}")
    
    print("\n" + "=" * 70)
    print("\nTo configure a provider, set the required environment variables:")
    print("  export OPENAI_API_KEY='your-key'              # For OpenAI")
    print("  export AZURE_OPENAI_API_KEY='your-key'        # For Azure")
    print("  export AZURE_OPENAI_ENDPOINT='your-endpoint'  # For Azure")
    print("  export GOOGLE_API_KEY='your-key'              # For Google")
    print("  export RUNWAY_API_KEY='your-key'              # For Runway")
    print("\nOr use --google-login for Google Veo (interactive authentication)")
    print("\nUse --list-models [provider] to see available models for each provider")
    print("=" * 70)


def print_available_models(provider: Optional[VideoProvider] = None, query_api: bool = True) -> None:
    """
    Print available models for one or all providers.
    
    Args:
        provider: Specific provider to show models for, or None for all
        query_api: If True, query APIs for live model lists (OpenAI only)
    """
    providers_to_show = [provider] if provider else ["openai", "azure", "google", "runway"]
    
    _print_header(query_api, provider)
    
    for b in providers_to_show:
        _print_provider_models(b, query_api)
    
    _print_footer(query_api)


def _print_header(query_api: bool, provider: Optional[VideoProvider]) -> None:
    """Print the models list header."""
    print("=" * 60)
    print("Available Models by provider")
    # Only mention API querying if we're actually showing OpenAI/Azure providers
    if query_api and (provider in ["openai", "azure"] or provider is None):
        print("(Querying OpenAI API for live model list...)")
    print("=" * 60)


def _print_provider_models(provider: VideoProvider, query_api: bool) -> None:
    """Print models for a specific provider."""
    models = get_available_models(provider, query_api=query_api)
    
    descriptions = _get_provider_descriptions()
    model_details = _get_model_details()
    default_model = get_default_model(provider)
    
    print(f"\n{descriptions.get(provider, provider.upper())} provider:")
    print("-" * 60)
    
    for model in models:
        is_default = model == default_model
        default_marker = " (default)" if is_default else ""
        detail = model_details.get(model, "")
        print(f"  • {model}{default_marker}")
        if detail:
            print(f"    {detail}")
    
    _print_provider_status(provider)


def _get_provider_descriptions() -> dict:
    """Get provider name descriptions."""
    return {
        "openai": "OpenAI Sora-2 (Direct API)",
        "azure": "Azure AI Foundry Sora-2",
        "google": "Google Veo-3",
        "runway": "RunwayML (Gen-4 & Veo)"
    }


def _get_provider_env_requirements(provider: VideoProvider) -> str:
    """Get environment variable requirements for a provider."""
    requirements = {
        "openai": "OPENAI_API_KEY",
        "azure": "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT",
        "google": "GOOGLE_API_KEY (or use --google-login)",
        "runway": "RUNWAY_API_KEY"
    }
    return requirements.get(provider, "Unknown")


def _get_model_details() -> dict:
    """Get detailed descriptions for each model."""
    return {
        "sora-2": "Standard quality video generation with text and image prompts",
        "sora-2-pro": "Higher quality, more advanced video generation",
        "veo-3.1-generate-preview": "Standard quality (Veo 3.1), $0.40 per video with audio",
        DEFAULT_VEO_MODEL: "Fast generation (Veo 3.1), $0.15 per video with audio",
        "veo-3.0-generate-001": "Standard quality (Veo 3.0), $0.40 per video with audio",
        "veo-3.0-fast-generate-001": "Fast generation (Veo 3.0), $0.15 per video with audio",
        "gen4_turbo": "Fast generation, optimized for speed (5-10s videos)",
        "gen4": "High quality generation, optimized for detail (5-10s videos)",
        "veo3.1_fast": "Veo 3.1 Fast via Runway (2-10s, lower cost)",
        "veo3.1": "Veo 3.1 via Runway (2-10s, highest quality on Veo)",
        "veo3": "Veo 3.0 via Runway (2-10s)"
    }


def _print_provider_status(provider: VideoProvider) -> None:
    """Print environment variable requirements and availability status."""
    env_vars = {
        "openai": "OPENAI_API_KEY",
        "azure": "AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT",
        "google": "GOOGLE_API_KEY",
        "runway": "RUNWAY_API_KEY"
    }
    
    available = provider in get_available_providers()
    status = "✅ Available" if available else "❌ Not configured"
    print(f"\n    Environment: {env_vars.get(provider, 'Unknown')}")
    print(f"    Status: {status}")


def _print_footer(query_api: bool) -> None:
    """Print usage instructions footer."""
    print("\n" + "=" * 60)
    print("\nTo use a specific model:")
    print("  --model sora-2 or --model sora-2-pro   # Sora-2 models")
    print("  --model veo-3.0-generate-001           # Veo-3 standard quality (Google)")
    print("  --model veo-3.0-fast-generate-001      # Veo-3 fast generation (Google)")
    print("  --model gen4_turbo or --model gen4     # Runway Gen-4 models")
    print("  --model veo3.1_fast | veo3.1 | veo3    # Runway Veo models")
    print("\nOr set environment variables:")
    print("  export RUNWAY_MODEL=gen4               # For RunwayML")
    print("\nNote:")
    print("  • Each provider uses its default model if --model is not specified.")
    if query_api:
        print("  • OpenAI models are queried live from the API.")
        print("  • Veo-3 and RunwayML models use hardcoded lists (no API list endpoint).")
    print("=" * 60)