"""
Google Veo-3 video generation module.

This module provides video generation capabilities using Google's Veo-3 models
with support for seamless stitching via source frame encoding.
"""
from pathlib import Path
from typing import Iterable, Union, Optional
from ..config import Veo3Config
from ..providers import Veo3APIClient
from ..logger import get_library_logger


def generate_video_with_veo3(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    source_frame: Optional[str] = None,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration_seconds: int = 8,
    seed: Optional[int] = None,
    out_path: str = "veo3_output.mp4",
    config: Optional[Veo3Config] = None,
    model: Optional[str] = None
) -> str:
    """
    Generate video with Veo-3, supporting seamless stitching via source frame.
    
    This function orchestrates the Veo-3 video generation process:
    1. Validates and prepares reference images
    2. Encodes source frame (if provided) as the first frame of the video
    3. Constructs the API request with prompt, source frame, and reference images
    4. Initiates video generation with automatic retry on capacity issues
    5. Downloads the generated video
    
    Args:
        prompt: Text description of the desired video content
        file_paths: Paths to reference image files (up to 3 for style/content guidance)
        source_frame: Path to source frame (first frame) for seamless stitching
        width: Video width in pixels. Defaults to 1280.
        height: Video height in pixels. Defaults to 720.
        fps: Frames per second. Defaults to 24.
        duration_seconds: Video duration in seconds. Defaults to 8.
        seed: Random seed for reproducible results. Defaults to None.
        out_path: Output file path. Defaults to "veo3_output.mp4".
        config: Veo-3 configuration. If None, loads from environment.
        model: Veo model to use. If None, uses config default.
        
    Returns:
        Path to the saved video file
        
    Raises:
        RuntimeError: If API calls fail or video generation fails
        FileNotFoundError: If reference image files don't exist
        ValueError: If file types are unsupported
        KeyboardInterrupt: If user cancels during retry backoff
        
    Examples:
        >>> # Basic text-to-video generation
        >>> video_path = generate_video_with_veo3("A peaceful lake at sunset")
        
        >>> # With reference images for style guidance
        >>> images = ["style1.jpg", "style2.jpg"]
        >>> video_path = generate_video_with_veo3(
        ...     "A video tour of this lake",
        ...     file_paths=images,
        ...     width=1920,
        ...     height=1080
        ... )
        
        >>> # With source frame for stitching
        >>> video_path = generate_video_with_veo3(
        ...     "Continue this scene smoothly",
        ...     source_frame="last_frame.png",
        ...     duration_seconds=5
        ... )
    """
    logger = get_library_logger()
    logger.info("Generating video with Veo-3")
    
    # Initialize configuration if not provided
    if config is None:
        logger.debug("Loading Veo-3 config from environment")
        config = Veo3Config.from_environment()
    
    # Initialize API client
    logger.debug("Initializing Veo-3 API client")
    api_client = Veo3APIClient(config)
    
    # Step 1: Validate and prepare image files
    validated_paths = []
    if file_paths:
        file_list = list(file_paths)
        logger.info(f"Validating {len(file_list)} image files")
        validated_paths = api_client.upload_files(file_list)
    
    # Step 2: Generate video with Veo-3
    # Use specified model or fall back to config default
    selected_model = model or config.default_model
    logger.info(f"Using Veo-3 model: {selected_model}")
    
    video_content = api_client.generate_video(
        prompt=prompt,
        reference_images=validated_paths,
        source_frame=source_frame,
        width=width,
        height=height,
        fps=fps,
        duration_seconds=duration_seconds,
        seed=seed,
        model=selected_model
    )
    
    # Step 3: Track the generation for artifact management
    from ..artifact_manager import get_artifact_manager
    artifact_manager = get_artifact_manager()
    
    # Note: Veo-3 may not return a file_id immediately, so we track differently
    artifact_manager.track_artifact(
        provider="google",
        model_used=selected_model,
        prompt=prompt,
        file_id=None,  # Veo-3 provides direct content
        file_name=out_path,
        width=width,
        height=height,
        duration_seconds=duration_seconds,
    )
    
    # Step 4: Save the video content to file
    logger.info(f"Saving video to {out_path}...")
    
    # Write the video content to the output file
    output_path = Path(out_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(video_content)
    
    logger.info(f"Video generation complete: {output_path}")
    return str(output_path)