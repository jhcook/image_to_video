"""
RunwayML video generation module.

This module provides video generation capabilities using RunwayML's Gen-4 models
and Google Veo models via RunwayML's API.
"""
from pathlib import Path
from typing import Iterable, Union, List, Optional

from ..config import RunwayConfig
from ..providers import RunwayGen4Client, RunwayVeoClient
from ..logger import get_library_logger


def generate_video_with_runway(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    model: Optional[str] = None,
    width: int = 1280,
    height: int = 720,
    duration_seconds: int = 5,
    seed: Optional[int] = None,
    out_path: Optional[str] = None,
    config: Optional[RunwayConfig] = None
) -> str:
    """
    Generate a video using RunwayML's Gen-4 models.
    
    RunwayML supports image-to-video with a single image reference.
    If multiple images are provided, only the first one is used.
    
    Args:
        prompt: Text description of the desired video content
        file_paths: Paths to image files for reference. Only first image is used.
        model: Model to use. Defaults to None (uses config default).
        width: Video width in pixels. Defaults to 1280.
        height: Video height in pixels. Defaults to 720.
        duration_seconds: Video duration in seconds (5 or 10). Defaults to 5.
        seed: Random seed for reproducible results. Defaults to None.
        out_path: Output file path. Auto-generated if None.
        config: RunwayML configuration. If None, loads from environment.
        
    Returns:
        Path to the saved video file
        
    Raises:
        ValueError: If configuration is invalid or duration not 5 or 10
        RuntimeError: If API calls fail or video generation fails
        FileNotFoundError: If reference image file doesn't exist
        KeyboardInterrupt: If user cancels during retry backoff
        
    Examples:
        >>> # Text-to-video
        >>> video_path = generate_video_with_runway("A peaceful lake at sunset")
        
        >>> # Image-to-video
        >>> video_path = generate_video_with_runway(
        ...     "A timelapse on a sunny day",
        ...     file_paths=["lake.jpg"],
        ...     duration_seconds=10
        ... )
    """
    logger = get_library_logger()
    logger.info("Generating video with RunwayML Gen-4")
    
    # Step 1: Initialize configuration
    if config is None:
        logger.debug("Loading RunwayML config from environment")
        config = RunwayConfig.from_environment()
    
    # Step 2: Initialize API client
    logger.debug("Initializing RunwayML Gen-4 API client")
    api_client = RunwayGen4Client(config)
    
    # Step 3: Prepare image input (only first image supported)
    image_path = None
    if file_paths:
        file_list = list(file_paths)
        if len(file_list) > 1:
            logger.warning(f"RunwayML Gen-4 only supports 1 image reference. Using first of {len(file_list)} provided.")
        image_path = str(file_list[0])
        logger.info(f"Using image reference: {image_path}")
    
    # Step 4: Generate default output path if not provided
    if out_path is None:
        out_path = "runway_gen4_output.mp4"
    
    # Step 5: Generate video
    selected_model = model or config.default_model
    logger.info(f"Using RunwayML model: {selected_model}")
    
    video_path = api_client.generate_video(
        prompt=prompt,
        image_path=image_path,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
        seed=seed,
        model=selected_model,
        out_path=out_path
    )
    
    # Step 6: Track artifact
    from ..artifact_manager import get_artifact_manager
    artifact_manager = get_artifact_manager()
    
    artifact_manager.track_artifact(
        provider="runway",
        model_used=selected_model,
        prompt=prompt,
        file_id=None,  # RunwayML provides direct file path
        file_name=out_path,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
    )
    
    logger.info(f"Video generation complete: {video_path}")
    return video_path


def generate_video_with_runway_veo(
    prompt: str,
    reference_images: Optional[List[str]] = None,
    first_frame: Optional[str] = None,
    *,
    model: Optional[str] = None,
    width: int = 1280,
    height: int = 720,
    duration_seconds: int = 5,
    seed: Optional[int] = None,
    out_path: Optional[str] = None,
    config: Optional[RunwayConfig] = None
) -> str:
    """
    Generate a video using Google Veo models via RunwayML API.
    
    Supports Veo 3, Veo 3.1, and Veo 3.1 Fast models with advanced features:
    - Reference images (up to 3) for style/content guidance
    - First keyframe for seamless stitching between clips
    - Last keyframe (future feature)
    
    Args:
        prompt: Text description of the desired video content
        reference_images: Optional list of paths to reference images (up to 3).
                         These guide the style and content of the generation.
        first_frame: Optional path to first keyframe image for stitching.
                    Used to ensure smooth transitions between clips.
        model: Veo model to use (veo3, veo3.1, veo3.1_fast). Required.
        width: Video width in pixels. Defaults to 1280.
        height: Video height in pixels. Defaults to 720.
        duration_seconds: Video duration in seconds (2-10). Defaults to 5.
        seed: Random seed for reproducible results (not supported by Veo). Defaults to None.
        out_path: Output file path. Auto-generated if None.
        config: RunwayML configuration. If None, loads from environment.
        
    Returns:
        Path to the saved video file
        
    Raises:
        ValueError: If configuration is invalid or model is not a Veo model
        RuntimeError: If API calls fail or video generation fails
        FileNotFoundError: If reference image or first_frame file doesn't exist
        KeyboardInterrupt: If user cancels during retry backoff
        
    Examples:
        >>> # Text-to-video with Veo 3.1 Fast
        >>> video_path = generate_video_with_runway_veo(
        ...     "A peaceful lake at sunset",
        ...     model="veo3.1_fast"
        ... )
        
        >>> # With reference images for style guidance
        >>> video_path = generate_video_with_runway_veo(
        ...     "A cinematic scene based on these references",
        ...     reference_images=["style1.jpg", "mood2.jpg"],
        ...     model="veo3.1"
        ... )
        
        >>> # With first frame for stitching
        >>> video_path = generate_video_with_runway_veo(
        ...     "Continue this scene smoothly",
        ...     first_frame="last_frame.png",
        ...     model="veo3.1",
        ...     duration_seconds=8
        ... )
    """
    logger = get_library_logger()
    logger.info("Generating video with RunwayML Veo")
    
    # Step 1: Initialize configuration
    if config is None:
        logger.debug("Loading RunwayML config from environment")
        config = RunwayConfig.from_environment()
    
    # Step 2: Initialize Veo API client
    logger.debug("Initializing RunwayML Veo API client")
    api_client = RunwayVeoClient(config)
    
    # Step 3: Validate Veo model
    if not model:
        raise ValueError("Model is required for Veo generation. Use 'veo3', 'veo3.1', or 'veo3.1_fast'.")
    
    if not model.startswith("veo"):
        raise ValueError(f"Model '{model}' is not a Veo model. Use 'veo3', 'veo3.1', or 'veo3.1_fast'.")
    
    # Step 4: Validate reference images limit
    if reference_images and len(reference_images) > 3:
        logger.warning(f"Veo supports max 3 reference images. Using first 3 of {len(reference_images)} provided.")
        reference_images = reference_images[:3]
    
    # Step 5: Generate default output path if not provided
    if out_path is None:
        out_path = f"runway_veo_{model.replace('.', '_')}_output.mp4"
    
    # Step 6: Generate video
    logger.info(f"Using RunwayML Veo model: {model}")
    
    video_path = api_client.generate_video(
        prompt=prompt,
        reference_images=reference_images or [],
        first_frame=first_frame,
        model=model,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
        seed=seed,
        out_path=out_path
    )
    
    # Step 7: Track artifact
    from ..artifact_manager import get_artifact_manager
    artifact_manager = get_artifact_manager()
    
    artifact_manager.track_artifact(
        provider="runway",
        model_used=model,
        prompt=prompt,
        file_id=None,  # RunwayML provides direct file path
        file_name=out_path,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
    )
    
    logger.info(f"Video generation complete: {video_path}")
    return video_path