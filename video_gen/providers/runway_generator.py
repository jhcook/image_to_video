"""
RunwayML video generation module.

This module provides video generation capabilities using RunwayML's Gen-4 models
and Google Veo models via RunwayML's API.
"""
import time
from pathlib import Path
from typing import Iterable, Union, List, Optional

from ..config import RunwayConfig
from ..providers import RunwayGen4Client, RunwayVeoClient
from ..logger import get_library_logger


def _route_to_veo_if_needed(
    prompt: str,
    file_paths: Iterable[Union[str, Path]],
    reference_images: Optional[List[str]],
    first_frame: Optional[str],
    selected_model: str,
    width: int,
    height: int,
    duration_seconds: int,
    seed: Optional[int],
    out_path: Optional[str],
    config: RunwayConfig
) -> Optional[str]:
    """Route VEO models to the appropriate function, return None for Gen-4 models."""
    if not selected_model or not selected_model.startswith("veo"):
        return None
    
    # Use reference_images if provided, otherwise convert file_paths
    if reference_images:
        ref_images = reference_images
    else:
        ref_images = [str(path) for path in file_paths] if file_paths else []
    
    return generate_video_with_runway_veo(
        prompt=prompt,
        reference_images=ref_images,
        first_frame=first_frame,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
        seed=seed,
        out_path=out_path,
        config=config,
        model=selected_model
    )


def _prepare_gen4_inputs(
    file_paths: Iterable[Union[str, Path]],
    out_path: Optional[str],
    duration_seconds: int
) -> tuple[Optional[str], str, int]:
    """Prepare inputs for Gen-4 model generation."""
    # Prepare image input (only first image supported)
    image_path = None
    if file_paths:
        file_list = list(file_paths)
        if len(file_list) > 1:
            logger = get_library_logger()
            logger.warning(f"RunwayML Gen-4 only supports 1 image reference. Using first of {len(file_list)} provided.")
        image_path = str(file_list[0])
    
    # Generate default output path if not provided
    if out_path is None:
        out_path = "runway_gen4_output.mp4"
    
    # Validate duration for Gen-4 models (must be 5 or 10)
    if duration_seconds not in [5, 10]:
        duration_seconds = 5
    
    return image_path, out_path, duration_seconds


def generate_video_with_runway(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    reference_images: Optional[List[str]] = None,  # For compatibility with stitching
    first_frame: Optional[str] = None,  # For compatibility with stitching
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
    
    # Use specified model or default from config
    selected_model = model if model is not None else config.default_model
    
    # Route VEO models to the appropriate function
    veo_result = _route_to_veo_if_needed(
        prompt, file_paths, reference_images, first_frame, selected_model,
        width, height, duration_seconds, seed, out_path, config
    )
    if veo_result is not None:
        return veo_result
    
    # Prepare Gen-4 inputs
    image_path, out_path, duration_seconds = _prepare_gen4_inputs(
        file_paths, out_path, duration_seconds
    )
    
    if image_path:
        logger.info(f"Using image reference: {image_path}")
    
    # Step 2: Initialize API client and generate video
    logger.debug("Initializing RunwayML Gen-4 API client")
    api_client = RunwayGen4Client(config)
    
    # Step 3: Generate video
    logger.info(f"Using RunwayML model: {selected_model}")
    
    video_path = api_client.generate_video(
        prompt=prompt,
        image_path=image_path or "",  # Gen4 requires a string, empty string for text-to-video
        width=width,
        height=height,
        duration=duration_seconds,
        output_path=out_path,
        model=selected_model,
        seed=seed
    )
    
    # Step 4: Track artifact
    from ..artifact_manager import get_artifact_manager
    artifact_manager = get_artifact_manager()
    
    artifact_manager.add_artifact(
        task_id=f"runway_{selected_model}_{int(time.time())}",
        provider="runway",
        model=selected_model,
        prompt=prompt,
        metadata={
            "width": width,
            "height": height,
            "duration_seconds": duration_seconds,
            "file_path": video_path
        }
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
        raise ValueError(f"This function is for Veo models only. Got: {model}")
    
    # Step 4: Validate duration (Veo supports 2-10 seconds)
    if not (2 <= duration_seconds <= 10):
        logger.warning(f"Duration {duration_seconds}s not in range 2-10. Clamping to 5 seconds.")
        duration_seconds = 5
    
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
        duration=duration_seconds,
        output_path=out_path
    )
    
    # Step 7: Track artifact
    from ..artifact_manager import get_artifact_manager
    artifact_manager = get_artifact_manager()
    
    artifact_manager.add_artifact(
        task_id=f"runway_{model}_{int(time.time())}",
        provider="runway",
        model=model,
        prompt=prompt,
        metadata={
            "width": width,
            "height": height,
            "duration_seconds": duration_seconds,
            "file_path": video_path
        }
    )
    
    logger.info(f"Video generation complete: {video_path}")
    return video_path