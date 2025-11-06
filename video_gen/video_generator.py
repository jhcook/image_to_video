"""
Main video generation orchestration module.

This module provides the unified interface for video generation across different
providers (OpenAI Sora, Azure Sora, Google Veo, RunwayML). It includes the main
generate_video() function that routes requests to appropriate provider-specific
implementations.

The provider-specific generation logic has been extracted to separate modules:
- video_gen.providers.sora_generator: OpenAI and Azure Sora implementations
- video_gen.providers.veo3_generator: Google Veo-3 implementation  
- video_gen.providers.videotransformer: RunwayML Gen-4, Veo, and Aleph implementations

Utility functions have been moved to:
- video_gen.video_utils: Frame extraction, model validation, path utilities
- video_gen.video_stitching: Multi-clip stitching with seamless transitions
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union, Optional, Any

from .config import VideoProvider
from .logger import get_library_logger
from .video_utils import validate_model_for_provider, extract_last_frame_as_png  # type: ignore
from .providers.sora_generator import generate_video_with_sora2, generate_video_with_azure_sora
from .providers.veo3_generator import generate_video_with_veo3
from .providers.runway_generator import generate_video_with_runway, generate_video_with_runway_veo  # type: ignore
from .providers.runway_aleph_functions import edit_video_with_runway_aleph
from .video_stitching import generate_video_sequence_with_veo3_stitching  # type: ignore


def generate_video(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    provider: VideoProvider = "openai",
    model: Optional[str] = None,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration_seconds: int = 8,
    seed: Optional[int] = None,
    out_path: Optional[str] = None,
    config: Optional[Any] = None
) -> str:
    """
    Generate a video using the specified provider (OpenAI, Azure, Google, or Runway).
    
    This is the main unified function that routes to the appropriate provider
    and orchestrates the video generation process.
    
    Args:
        prompt: Text description of the desired video content
        file_paths: Paths to image files for reference. Defaults to empty tuple.
        provider: Video generation provider to use ("openai", "azure", "google", or "runway")
        model: Specific model to use (provider-dependent). Defaults to None (uses provider default).
        width: Video width in pixels. Defaults to 1280.
        height: Video height in pixels. Defaults to 720.
        fps: Frames per second. Defaults to 24.
        duration_seconds: Video duration in seconds. Defaults to 8.
        seed: Random seed for reproducible results. Defaults to None.
        out_path: Output file path. Auto-generated if None.
        config: Backend configuration. If None, loads from environment.
        
    Returns:
        Path to the saved video file
        
    Raises:
        ValueError: If provider is not supported
        RuntimeError: If API calls fail or video generation fails
        FileNotFoundError: If reference image files don't exist
        KeyboardInterrupt: If user cancels during retry backoff
    """
    logger = get_library_logger()
    logger.info(f"Starting video generation with provider: {provider}")
    logger.debug(f"Parameters: {width}x{height}, {fps}fps, {duration_seconds}s, model={model}")
    
    # Validate model is compatible with provider
    if model is not None:
        validate_model_for_provider(model, provider, logger)
    
    if provider == "openai":
        return generate_video_with_sora2(
            prompt=prompt,
            file_paths=file_paths,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration_seconds,
            seed=seed,
            out_path=out_path or "openai_output.mp4",
            config=config,
            model=model
        )
    elif provider == "azure":
        return generate_video_with_azure_sora(
            prompt=prompt,
            file_paths=file_paths,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration_seconds,
            seed=seed,
            out_path=out_path or "azure_output.mp4",
            config=config,
            model=model
        )
    elif provider == "google":
        return generate_video_with_veo3(
            prompt=prompt,
            file_paths=file_paths,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration_seconds,
            seed=seed,
            out_path=out_path or "google_output.mp4",
            config=config,
            model=model
        )
    elif provider == "runway":
        return generate_video_with_runway(
            prompt=prompt,
            file_paths=file_paths,
            model=model,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
            seed=seed,
            out_path=out_path or "runway_output.mp4",
            config=config
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}. Use 'openai', 'azure', 'google', or 'runway'")


# Re-export provider-specific functions for backward compatibility
__all__ = [
    "generate_video",
    "generate_video_with_sora2",
    "generate_video_with_azure_sora", 
    "generate_video_with_veo3",
    "generate_video_with_runway",
    "edit_video_with_runway_aleph",
]
