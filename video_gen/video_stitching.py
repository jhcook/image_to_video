"""
Video stitching functionality for seamless video sequence generation.

This module provides capabilities for generating sequences of videos with smooth
frame-to-frame transitions, particularly for Veo models that support source frame
input for continuous video generation.
"""
from __future__ import annotations

import time
from typing import Any, List, Optional, Union
import logging

from .config import Veo3Config, RunwayConfig
from .exceptions import InsufficientCreditsError
from .logger import get_library_logger
from .video_utils import (
    extract_last_frame_as_png,
    build_expected_out_paths,
    compute_resume_state,
    validate_stitch_model,
)


def generate_video_sequence_with_veo3_stitching(
    prompts: List[str],
    file_paths_list: Optional[List[List[str]]] = None,
    width: int = 1280,
    height: int = 720,
    duration_seconds: int = 8,
    seed: Optional[int] = None,
    out_paths: Optional[List[str]] = None,
    config: Optional[Union[Veo3Config, RunwayConfig]] = None,
    model: Optional[str] = None,
    delay_between_clips: int = 10,
    provider: str = "veo3",
    resume: bool = False,
) -> List[str]:
    """
    Generate a sequence of Veo video clips with seamless frame transitions.

    Supports both Google Veo (provider="veo3") and RunwayML Veo (provider="runway").
    Each clip uses the last frame of the previous clip as the first frame of the next,
    creating smooth continuity between video segments.

    Args:
        prompts: List of text prompts for each video clip
        file_paths_list: Optional list of reference image paths for each clip
        width: Video width in pixels
        height: Video height in pixels  
        duration_seconds: Duration of each clip in seconds
        seed: Random seed for reproducible results
        out_paths: Optional list of output paths for each clip
        config: Provider configuration (auto-detected if None)
        model: Model to use (must be a Veo model)
        delay_between_clips: Seconds to wait between clip generations
        provider: Provider to use ("veo3" or "runway") 
        resume: Whether to resume from existing clips
        
    Returns:
        List of paths to generated video clips
        
    Raises:
        ValueError: If model doesn't support stitching
        InsufficientCreditsError: If provider runs out of credits
    """
    logger = get_library_logger()
    
    # Config and model validation
    config = get_stitch_config(provider, config)
    validate_stitch_model(model)
    
    # Setup initial state and resume detection
    expected_paths = build_expected_out_paths(len(prompts), out_paths, provider)
    outputs, start_idx, last_frame_path = _initialize_stitching_state(resume, expected_paths)
    
    # Generate remaining clips
    clip_params: dict[str, Any] = {
        'width': width,
        'height': height,
        'duration_seconds': duration_seconds,
        'seed': seed,
        'out_paths': out_paths,
        'config': config,
        'model': model,
        'delay_between_clips': delay_between_clips,
    }
    
    return _generate_clip_sequence(
        prompts, file_paths_list, outputs, start_idx, last_frame_path,
        clip_params, provider, logger
    )

def _initialize_stitching_state(
    resume: bool, 
    expected_paths: List[str]
) -> tuple[List[str], int, Optional[str]]:
    """Initialize stitching state, handling resume if needed."""
    outputs: List[str] = []
    start_idx = 0
    last_frame_path: Optional[str] = None
    
    if resume:
        outputs, start_idx, last_frame_path = compute_resume_state(expected_paths)
    
    return outputs, start_idx, last_frame_path

def _generate_clip_sequence(
    prompts: List[str],
    file_paths_list: Optional[List[List[str]]],
    outputs: List[str],
    start_idx: int,
    last_frame_path: Optional[str],
    clip_params: dict[str, Any],
    provider: str,
    logger: logging.Logger
) -> List[str]:
    """Generate the sequence of video clips."""
    current_last_frame = last_frame_path
    
    for idx in range(start_idx, len(prompts)):
        try:
            video_path, current_last_frame = _generate_single_clip_in_sequence(
                idx, prompts, file_paths_list, current_last_frame, clip_params, provider, logger
            )
            
            outputs.append(video_path)
            _handle_clip_completion(idx, len(prompts), clip_params['delay_between_clips'], logger)
            
        except InsufficientCreditsError as e:
            _handle_insufficient_credits(idx, len(prompts), logger, e)
            break
    
    return outputs

def _generate_single_clip_in_sequence(
    idx: int,
    prompts: List[str],
    file_paths_list: Optional[List[List[str]]],
    last_frame_path: Optional[str],
    clip_params: dict[str, Any],
    provider: str,
    logger: logging.Logger
) -> tuple[str, Optional[str]]:
    """Generate a single clip in the sequence and return its path and last frame."""
    prompt = prompts[idx]
    reference_images, source_frame, out_path = prepare_clip_params(
        idx, file_paths_list, last_frame_path, clip_params.get('out_paths'), provider
    )
    log_clip_generation(logger, idx, len(prompts), reference_images, source_frame)
    
    video_path = generate_veo_clip(
        provider=provider,
        prompt=prompt,
        reference_images=reference_images,
        source_frame=source_frame,
        width=clip_params['width'],
        height=clip_params['height'],
        duration_seconds=clip_params['duration_seconds'],
        seed=clip_params['seed'],
        out_path=out_path,
        config=clip_params['config'],
        model=clip_params['model'],
    )
    
    new_last_frame = extract_last_frame_as_png(video_path)
    return video_path, new_last_frame

def _handle_clip_completion(idx: int, total_clips: int, delay_between_clips: int, logger: logging.Logger) -> None:
    """Handle actions after a clip is completed."""
    sleep_between_clips(logger, idx, total_clips, delay_between_clips)

def _handle_insufficient_credits(idx: int, total_clips: int, logger: logging.Logger, error: InsufficientCreditsError) -> None:
    """Handle insufficient credits error during stitching."""
    logger.error(
        "Stopping stitching due to insufficient RunwayML credits after clip %d/%d.\n%s",
        idx + 1,
        total_clips,
        str(error),
    )


def get_stitch_config(provider: str, config: Optional[Union[Veo3Config, RunwayConfig]]) -> Union[Veo3Config, RunwayConfig]:
    """Get configuration for stitching provider."""
    if config is not None:
        return config
    if provider == "veo3":
        return Veo3Config.from_environment()
    return RunwayConfig.from_environment()


def generate_veo_clip(
    *,
    provider: str,
    prompt: str,
    reference_images: List[str],
    source_frame: Optional[str],
    width: int,
    height: int,
    duration_seconds: int,
    seed: Optional[int],
    out_path: str,
    config: Union[Veo3Config, RunwayConfig],
    model: Optional[str],
) -> str:
    """
    Generate a single video clip using the specified Veo provider.
    
    This function routes to the appropriate provider-specific generation function
    and handles the parameter mapping between different provider APIs.
    """
    # Import here to avoid circular imports
    from .video_generator import generate_video_with_veo3, generate_video_with_runway
    
    if provider == "veo3":
        return generate_video_with_veo3(
            prompt=prompt,
            file_paths=reference_images,
            source_frame=source_frame,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
            seed=seed,
            out_path=out_path,
            config=config,  # type: ignore[arg-type]
            model=model,
        )
    else:
        return generate_video_with_runway(
            prompt=prompt,
            reference_images=reference_images,
            first_frame=source_frame,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
            seed=seed,
            out_path=out_path,
            config=config,  # type: ignore[arg-type]
            model=model,
        )


def prepare_clip_params(
    idx: int, 
    file_paths_list: Optional[List[List[str]]], 
    last_frame_path: Optional[str], 
    out_paths: Optional[List[str]], 
    provider: str = "veo3"
) -> tuple[List[str], Optional[str], str]:
    """
    Prepare parameters for generating a single clip in a stitched sequence.
    
    Args:
        idx: Index of the current clip (0-based)
        file_paths_list: List of reference image paths for each clip
        last_frame_path: Path to the last frame from the previous clip
        out_paths: List of output paths for each clip
        provider: Provider name for path generation
        
    Returns:
        Tuple of (reference_images, source_frame, out_path)
    """
    reference_images = file_paths_list[idx] if file_paths_list else []
    source_frame = last_frame_path if idx > 0 else None
    
    # Generate default output path based on provider
    if out_paths:
        out_path = out_paths[idx]
    else:
        prefix = "veo3" if provider == "veo3" else "runway_veo"
        out_path = f"{prefix}_clip_{idx + 1}.mp4"
    
    return reference_images, source_frame, out_path


def log_clip_generation(logger: Any, idx: int, total: int, reference_images: List[str], source_frame: Optional[str]) -> None:
    """Log information about the current clip being generated."""
    if source_frame:
        logger.info(
            f"Generating clip {idx+1}/{total} with source frame + {len(reference_images)} reference image(s)..."
        )
    else:
        logger.info(
            f"Generating clip {idx+1}/{total} with {len(reference_images)} image(s)..."
        )


def sleep_between_clips(logger: Any, idx: int, total: int, delay_seconds: int) -> None:
    """Sleep between clip generations to avoid rate limiting."""
    if idx < total - 1 and delay_seconds > 0:
        logger.info(
            f"Waiting {delay_seconds}s before next clip to avoid rate limiting..."
        )
        time.sleep(delay_seconds)