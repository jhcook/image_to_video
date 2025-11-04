"""
Configuration module for video generation backends.

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

VideoBackend = Literal["sora2", "azure-sora", "veo3", "runway"]


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


def create_config_for_backend(backend: VideoBackend):
    """
    Create appropriate configuration for the specified backend.
    
    Args:
        backend: The video generation backend to use
        
    Returns:
        Configuration instance for the specified backend
        
    Raises:
        ValueError: If backend is not supported or configuration is invalid
    """
    config_map = {
        "sora2": SoraConfig,
        "azure-sora": AzureSoraConfig,
        "veo3": Veo3Config,
        "runway": RunwayConfig
    }
    
    config_class = config_map.get(backend)
    if not config_class:
        raise ValueError(f"Unsupported backend: {backend}. Use 'sora2', 'azure-sora', 'veo3', or 'runway'")
    
    return config_class.from_environment()


def get_available_backends() -> list[VideoBackend]:
    """
    Get list of available backends based on environment configuration.
    
    Returns:
        List of available backend names
    """
    backend_checks = {
        "sora2": lambda: bool(os.getenv("OPENAI_API_KEY")),
        "azure-sora": lambda: bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT")),
        "veo3": lambda: bool(
            os.getenv("GOOGLE_API_KEY") or 
            os.getenv("VEO3_API_KEY") or 
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        ),
        "runway": lambda: bool(os.getenv("RUNWAY_API_KEY"))
    }
    
    return [backend for backend, check in backend_checks.items() if check()]


def get_default_model(backend: VideoBackend) -> str:
    """
    Get the default model for a backend.
    
    Args:
        backend: The video generation backend
        
    Returns:
        Default model name for that backend
        
    Raises:
        ValueError: If backend is not supported
    """
    default_models = {
        "sora2": "sora-2",
        "azure-sora": "sora-2",
        "veo3": DEFAULT_VEO_MODEL,
        "runway": "gen4_turbo"
    }
    
    if backend not in default_models:
        raise ValueError(f"Unsupported backend: {backend}")
    
    return default_models[backend]


def get_available_models(backend: VideoBackend, query_api: bool = False) -> list[str]:
    """
    Get list of available models for the specified backend.
    
    This function uses a hybrid approach:
    - OpenAI: Can query the API live via models.list() to get current models
    - Veo-3/RunwayML: Use hardcoded lists (these APIs don't have model list endpoints)
    
    Args:
        backend: The video generation backend
        query_api: If True, query the API for available models (OpenAI only)
        
    Returns:
        List of available model names for that backend
        
    Raises:
        ValueError: If backend is not supported
    """
    # For OpenAI, optionally query the API for available models
    if backend == "sora2" and query_api:
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
    
    # Hardcoded lists (fallback or for backends without list API)
    models_by_backend = {
        "sora2": [
            "sora-2",      # Standard quality
            "sora-2-pro"   # Higher quality, more advanced
        ],
        "azure-sora": [
            "sora-2",      # Standard quality (Azure deployment)
            "sora-2-pro"   # Higher quality, more advanced (Azure deployment)
        ],
        "veo3": [
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
    
    if backend not in models_by_backend:
        raise ValueError(f"Unsupported backend: {backend}")
    
    return models_by_backend[backend]


def print_available_models(backend: VideoBackend = None, query_api: bool = True) -> None:
    """
    Print available models for one or all backends.
    
    Args:
        backend: Specific backend to show models for, or None for all
        query_api: If True, query APIs for live model lists (OpenAI only)
    """
    backends_to_show = [backend] if backend else ["sora2", "azure-sora", "veo3", "runway"]
    
    _print_header(query_api, backend)
    
    for b in backends_to_show:
        _print_backend_models(b, query_api)
    
    _print_footer(query_api)


def _print_header(query_api: bool, backend: Optional[VideoBackend]) -> None:
    """Print the models list header."""
    print("=" * 60)
    print("Available Models by Backend")
    # Only mention API querying if we're actually showing OpenAI/Azure backends
    if query_api and (backend in ["sora2", "azure-sora"] or backend is None):
        print("(Querying OpenAI API for live model list...)")
    print("=" * 60)


def _print_backend_models(backend: VideoBackend, query_api: bool) -> None:
    """Print models for a specific backend."""
    models = get_available_models(backend, query_api=query_api)
    
    descriptions = _get_backend_descriptions()
    model_details = _get_model_details()
    default_model = get_default_model(backend)
    
    print(f"\n{descriptions.get(backend, backend.upper())} Backend:")
    print("-" * 60)
    
    for model in models:
        is_default = model == default_model
        default_marker = " (default)" if is_default else ""
        detail = model_details.get(model, "")
        print(f"  • {model}{default_marker}")
        if detail:
            print(f"    {detail}")
    
    _print_backend_status(backend)


def _get_backend_descriptions() -> dict:
    """Get backend name descriptions."""
    return {
        "sora2": "OpenAI Sora-2 (Direct API)",
        "azure-sora": "Azure AI Foundry Sora-2",
        "veo3": "Google Veo-3",
        "runway": "RunwayML (Gen-4 & Veo)"
    }


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


def _print_backend_status(backend: VideoBackend) -> None:
    """Print environment variable requirements and availability status."""
    env_vars = {
        "sora2": "OPENAI_API_KEY",
        "azure-sora": "AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT",
        "veo3": "GOOGLE_API_KEY",
        "runway": "RUNWAY_API_KEY"
    }
    
    available = backend in get_available_backends()
    status = "✅ Available" if available else "❌ Not configured"
    print(f"\n    Environment: {env_vars.get(backend, 'Unknown')}")
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
    print("  • Each backend uses its default model if --model is not specified.")
    if query_api:
        print("  • OpenAI models are queried live from the API.")
        print("  • Veo-3 and RunwayML models use hardcoded lists (no API list endpoint).")
    print("=" * 60)