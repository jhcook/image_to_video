"""
OpenAI Sora video generation module.

This module provides video generation capabilities using OpenAI's Sora models,
including both direct OpenAI API access and Azure OpenAI deployments.
"""
from pathlib import Path
from typing import Any, Iterable, Optional, Union, Tuple

from ..config import SoraConfig
from ..providers import SoraAPIClient, AzureSoraAPIClient
from ..file_handler import FileHandler
from ..logger import get_library_logger
from ..video_utils import (
    sora_build_content_items,
    sora_extract_async_video_id,
    sora_extract_sync_video_id,
)


def sora_init(config: Optional[SoraConfig] = None) -> tuple[SoraConfig, SoraAPIClient, FileHandler]:
    """Initialize Sora configuration, API client, and file handler."""
    if config is None:
        config = SoraConfig.from_environment()
    api_client = SoraAPIClient(config)
    file_handler = FileHandler(config, api_client.client)
    return config, api_client, file_handler


def azure_sora_init(config: Any = None) -> Tuple[Any, Any, Any]:
    """Initialize Azure Sora configuration, API client, and file handler."""
    if config is None:
        from ..config import AzureSoraConfig
        config = AzureSoraConfig.from_environment()
    api_client = AzureSoraAPIClient(config)
    file_handler = FileHandler(config, api_client.client)
    return config, api_client, file_handler


def generate_video_with_sora2(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration_seconds: int = 8,
    seed: Optional[int] = None,
    out_path: str = "openai_output.mp4",
    config: Optional[SoraConfig] = None,
    model: Optional[str] = None
) -> str:
    """
    Generate a video using OpenAI's Sora-2 model with text prompts and image references.
    
    This is the main function that orchestrates the entire video generation process:
    1. Uploads reference images to OpenAI
    2. Constructs the API request with prompt and images
    3. Initiates video generation with automatic retry on capacity issues
    4. Polls for completion (if async)
    5. Downloads the generated video
    
    The function implements exponential backoff retry logic for capacity issues,
    starting with 30-second delays and increasing up to 5 minutes between retries.
    It will retry indefinitely until the API becomes available or the user cancels.
    
    Args:
        prompt: Text description of the desired video content
        file_paths: Paths to image files for reference. Defaults to empty tuple.
        width: Video width in pixels. Defaults to 1280.
        height: Video height in pixels. Defaults to 720.
        fps: Frames per second. Defaults to 24.
        duration_seconds: Video duration in seconds. Defaults to 8.
        seed: Random seed for reproducible results. Defaults to None.
        out_path: Output file path. Defaults to "openai_output.mp4".
        config: Sora configuration. If None, loads from environment.
        model: Model to use. Defaults to None (uses provider default).
        
    Returns:
        Path to the saved video file
        
    Raises:
        RuntimeError: If API calls fail (non-capacity issues) or video generation fails
        FileNotFoundError: If reference image files don't exist
        ValueError: If file types are unsupported
        KeyboardInterrupt: If user cancels during retry backoff
        
    Examples:
        >>> # Text-only generation (will retry on capacity issues)
        >>> video_path = generate_video_with_sora2("A peaceful lake at sunset")
        
        >>> # With image references
        >>> images = ["lake1.jpg", "lake2.jpg"]
        >>> video_path = generate_video_with_sora2(
        ...     "A video tour of this lake",
        ...     file_paths=images,
        ...     width=1920,
        ...     height=1080,
        ...     duration_seconds=10
        ... )
        
    Note:
        If the Sora-2 model is at capacity, this function will automatically retry
        with exponential backoff delays. Use Ctrl+C to cancel if needed.
    """
    logger = get_library_logger()
    
    # Initialize config, client, file handler
    config, api_client, file_handler = sora_init(config)

    # Step 1: Upload any reference files (images) and get their IDs
    file_ids = file_handler.upload_files(file_paths)

    # Step 2: Build the multi-part content message: text prompt + image references
    content_items = sora_build_content_items(prompt, file_ids)

    # Step 3: Initiate video generation with retry logic
    response = api_client.create_video_request(
        content_items=content_items,
        width=width,
        height=height,
        fps=fps,
        duration_seconds=duration_seconds,
        seed=seed,
        model=model
    )

    # Step 4: Handle response - could be async (with polling) or sync (immediate)
    video_file_id = None

    if hasattr(response, 'id') and hasattr(response, 'status'):
        # Asynchronous job - poll for completion and extract id
        response = api_client.poll_async_job(response)
        video_file_id = sora_extract_async_video_id(response)
    else:
        video_file_id = sora_extract_sync_video_id(response)
    
    if not video_file_id:
        raise RuntimeError("Could not locate video file ID in response output")
    
    # Track artifact for later download
    from ..artifact_manager import get_artifact_manager
    artifact_manager = get_artifact_manager()
    artifact_manager.track_artifact(
        provider="openai",
        model_used=model or "sora-1",
        prompt=prompt,
        file_id=video_file_id,
        file_name=out_path,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
    )

    # Step 5: Download the video file to local storage
    logger.info(f"Downloading video to {out_path}...")
    downloaded_path = file_handler.download_file(video_file_id, out_path)
    logger.info(f"Video generation complete: {downloaded_path}")
    
    return downloaded_path


def generate_video_with_azure_sora(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration_seconds: int = 8,
    seed: Optional[int] = None,
    out_path: str = "azure_sora_output.mp4",
    config: Any = None,
    model: Optional[str] = None
) -> str:
    """
    Generate a video using Azure AI Foundry Sora-2 deployment.
    
    This function is similar to generate_video_with_sora2 but uses Azure OpenAI
    endpoints and authentication instead of OpenAI's direct API.
    
    Args:
        prompt: Text description of the desired video content
        file_paths: Paths to image files for reference. Defaults to empty tuple.
        width: Video width in pixels. Defaults to 1280.
        height: Video height in pixels. Defaults to 720.
        fps: Frames per second. Defaults to 24.
        duration_seconds: Video duration in seconds. Defaults to 8.
        seed: Random seed for reproducible results. Defaults to None.
        out_path: Output file path. Defaults to "azure_sora_output.mp4".
        config: Azure Sora configuration. If None, loads from environment.
        model: Model to use. Defaults to None (uses provider default).
        
    Returns:
        Path to the saved video file
        
    Raises:
        RuntimeError: If API calls fail or video generation fails
        FileNotFoundError: If reference image files don't exist
        ValueError: If file types are unsupported
        
    Examples:
        >>> # Text-only generation
        >>> video_path = generate_video_with_azure_sora("A peaceful lake at sunset")
        
        >>> # With image references
        >>> images = ["lake1.jpg", "lake2.jpg"]
        >>> video_path = generate_video_with_azure_sora(
        ...     "A video tour of this lake",
        ...     file_paths=images,
        ...     width=1920,
        ...     height=1080
        ... )
    """
    logger = get_library_logger()
    
    # Initialize Azure config, client, file handler
    config, api_client, file_handler = azure_sora_init(config)

    # Step 1: Upload any reference files (images) and get their IDs
    file_ids = file_handler.upload_files(file_paths)

    # Step 2: Build the multi-part content message: text prompt + image references
    content_items = sora_build_content_items(prompt, file_ids)

    # Step 3: Initiate video generation
    response = api_client.create_video_request(
        content_items=content_items,
        width=width,
        height=height,
        fps=fps,
        duration_seconds=duration_seconds,
        seed=seed,
        model=model
    )

    # Step 4: Handle response - could be async (with polling) or sync (immediate)
    video_file_id = None

    if hasattr(response, 'id') and hasattr(response, 'status'):
        # Asynchronous job - poll for completion and extract id
        response = api_client.poll_async_job(response)
        video_file_id = sora_extract_async_video_id(response)
    else:
        video_file_id = sora_extract_sync_video_id(response)
    
    if not video_file_id:
        raise RuntimeError("Could not locate video file ID in response output")
    
    # Track artifact for later download
    from ..artifact_manager import get_artifact_manager
    artifact_manager = get_artifact_manager()
    artifact_manager.track_artifact(
        provider="azure",
        model_used=model or "sora-1",
        prompt=prompt,
        file_id=video_file_id,
        file_name=out_path,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
    )

    # Step 5: Download the video file to local storage
    logger.info(f"Downloading video to {out_path}...")
    downloaded_path = file_handler.download_file(video_file_id, out_path)
    logger.info(f"Video generation complete: {downloaded_path}")
    
    return downloaded_path