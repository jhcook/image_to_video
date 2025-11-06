"""
RunwayML Aleph video editing and generation functions.

This module provides video editing capabilities using RunwayML's Aleph model.
"""
from pathlib import Path
from typing import Optional

from ..config import RunwayConfig
from ..providers import RunwayAlephClient
from ..logger import get_library_logger


def edit_video_with_runway_aleph(
    prompt: str,
    video_path: str,
    *,
    width: int = 1280,
    height: int = 720,
    duration_seconds: int = 5,
    seed: Optional[int] = None,
    out_path: Optional[str] = None,
    config: Optional[RunwayConfig] = None
) -> str:
    """
    Edit a video using RunwayML's Aleph model.
    
    Aleph is RunwayML's state-of-the-art video editing model that can transform
    existing videos based on text prompts. Unlike generation models, Aleph takes
    an input video and applies modifications while preserving temporal consistency.
    
    Args:
        prompt: Text description of the desired transformation/editing
        video_path: Path to the input video file to edit
        width: Video width in pixels. Defaults to 1280.
        height: Video height in pixels. Defaults to 720.
        duration_seconds: Video duration in seconds (2-30). Defaults to 5.
        seed: Random seed for reproducible results. Defaults to None.
        out_path: Output file path. Auto-generated if None.
        config: RunwayML configuration. If None, loads from environment.
        
    Returns:
        Path to the saved edited video file
        
    Raises:
        ValueError: If configuration is invalid or duration not in range 2-30
        RuntimeError: If API calls fail or video editing fails
        FileNotFoundError: If input video file doesn't exist
        KeyboardInterrupt: If user cancels during retry backoff
        
    Examples:
        >>> # Transform video style
        >>> edited_path = edit_video_with_runway_aleph(
        ...     "Transform this into an oil painting style",
        ...     "input_video.mp4"
        ... )
        
        >>> # Change environment
        >>> edited_path = edit_video_with_runway_aleph(
        ...     "Move this scene to a tropical beach setting",
        ...     "original.mp4",
        ...     duration_seconds=10,
        ...     out_path="beach_version.mp4"
        ... )
    """
    logger = get_library_logger()
    logger.info("Editing video with RunwayML Aleph")
    
    # Step 1: Initialize configuration
    if config is None:
        logger.debug("Loading RunwayML config from environment")
        config = RunwayConfig.from_environment()
    
    # Step 2: Initialize Aleph API client
    logger.debug("Initializing RunwayML Aleph API client")
    api_client = RunwayAlephClient(config)
    
    # Step 3: Generate default output path if not provided
    if out_path is None:
        input_name = Path(video_path).stem
        out_path = f"{input_name}_aleph_edited.mp4"
    
    # Step 4: Edit video
    logger.info(f"Editing video: {video_path}")
    logger.info(f"Transformation prompt: {prompt}")
    
    video_output_path = api_client.edit_video(
        prompt=prompt,
        input_video=video_path,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
        seed=seed,
        out_path=out_path
    )
    
    # Step 5: Track artifact
    from ..artifact_manager import get_artifact_manager
    artifact_manager = get_artifact_manager()
    
    artifact_manager.track_artifact(
        provider="runway",
        model_used="aleph",
        prompt=prompt,
        file_id=None,  # RunwayML provides direct file path
        file_name=out_path,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
    )
    
    logger.info(f"Video editing complete: {video_output_path}")
    return video_output_path


def generate_video_with_runway_aleph(
    prompt: str,
    image_path: Optional[str] = None,
    *,
    width: int = 1280,
    height: int = 720,
    duration_seconds: int = 5,
    seed: Optional[int] = None,
    out_path: Optional[str] = None,
    config: Optional[RunwayConfig] = None
) -> str:
    """
    Generate a video using RunwayML's Aleph model.
    
    While Aleph is primarily designed for video editing, it can also generate
    new videos from prompts and optional image references.
    
    Args:
        prompt: Text description of the desired video content
        image_path: Optional path to reference image. Defaults to None.
        width: Video width in pixels. Defaults to 1280.
        height: Video height in pixels. Defaults to 720.
        duration_seconds: Video duration in seconds (2-30). Defaults to 5.
        seed: Random seed for reproducible results. Defaults to None.
        out_path: Output file path. Auto-generated if None.
        config: RunwayML configuration. If None, loads from environment.
        
    Returns:
        Path to the saved video file
        
    Raises:
        ValueError: If configuration is invalid or duration not in range 2-30
        RuntimeError: If API calls fail or video generation fails
        FileNotFoundError: If reference image file doesn't exist
        KeyboardInterrupt: If user cancels during retry backoff
        
    Examples:
        >>> # Text-to-video with Aleph
        >>> video_path = generate_video_with_runway_aleph(
        ...     "A peaceful lake at sunset with cinematic quality"
        ... )
        
        >>> # Image-to-video with Aleph
        >>> video_path = generate_video_with_runway_aleph(
        ...     "Bring this image to life with subtle motion",
        ...     image_path="lake.jpg",
        ...     duration_seconds=10
        ... )
    """
    logger = get_library_logger()
    logger.info("Generating video with RunwayML Aleph")
    
    # Step 1: Initialize configuration
    if config is None:
        logger.debug("Loading RunwayML config from environment")
        config = RunwayConfig.from_environment()
    
    # Step 2: Initialize Aleph API client
    logger.debug("Initializing RunwayML Aleph API client")
    api_client = RunwayAlephClient(config)
    
    # Step 3: Generate default output path if not provided
    if out_path is None:
        out_path = "runway_aleph_output.mp4"
    
    # Step 4: Generate video
    logger.info("Generating video with Aleph model")
    logger.info(f"Prompt: {prompt}")
    if image_path:
        logger.info(f"Using image reference: {image_path}")
    
    video_output_path = api_client.generate_video(
        prompt=prompt,
        reference_images=[image_path] if image_path else None,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
        seed=seed,
        out_path=out_path
    )
    
    # Step 5: Track artifact
    from ..artifact_manager import get_artifact_manager
    artifact_manager = get_artifact_manager()
    
    artifact_manager.track_artifact(
        provider="runway",
        model_used="aleph",
        prompt=prompt,
        file_id=None,  # RunwayML provides direct file path
        file_name=out_path,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
    )
    
    logger.info(f"Video generation complete: {video_output_path}")
    return video_output_path