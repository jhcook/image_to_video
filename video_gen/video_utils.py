"""
Video generation utility functions.

This module contains utility functions used across the video generation pipeline:
- Frame extraction utilities for video stitching
- Model validation and provider matching  
- Path building and resume state computation
- Sora API response parsing helpers
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import get_available_models, VideoProvider


def extract_last_frame_as_png(video_path: str, output_dir: str | None = None) -> str:
    """
    Extract the last frame of a video as a PNG file using ffmpeg.
    
    This function is used in Veo 3.1 stitching to extract the final frame
    from each clip, which is then passed as the source frame (first frame
    parameter) to the next clip for seamless transitions.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save the PNG (uses temp dir if None)
        
    Returns:
        Path to the extracted PNG file in the output directory
        
    Raises:
        RuntimeError: If ffmpeg command fails to execute
        
    Technical Details:
        - Uses ffmpeg filter: select=eq(n\\,prev_n+1) to select last frame
        - Outputs high-quality PNG for re-encoding
        - Raw string (r"...") prevents escape sequence issues
        - Frame stored in temp directory by default for automatic cleanup
    """
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    output_png = str(Path(output_dir) / (Path(video_path).stem + "_last.png"))
    # Use simpler approach: just extract the last frame
    cmd = [
        "ffmpeg", "-y", "-sseof", "-1", "-i", str(video_path),
        "-update", "1", "-q:v", "1",
        output_png
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        raise RuntimeError(f"Failed to extract last frame: {e}")
    return output_png


def build_expected_out_paths(count: int, out_paths: Optional[List[str]], provider: str) -> List[str]:
    """Build expected output paths for video sequence generation."""
    if out_paths:
        return list(out_paths)
    prefix = "veo3" if provider == "veo3" else "runway_veo"
    return [f"{prefix}_clip_{i + 1}.mp4" for i in range(count)]


def compute_resume_state(expected_paths: List[str]) -> tuple[List[str], int, Optional[str]]:
    """
    Compute resume state for video sequence generation.
    
    Checks which videos have already been generated and extracts the last frame
    from the most recent video for continuation.
    
    Args:
        expected_paths: List of expected output video paths
        
    Returns:
        Tuple of (outputs, start_idx, last_frame_path):
        - outputs: List of existing output video paths
        - start_idx: Index to start generation from
        - last_frame_path: Path to last frame PNG for stitching
    """
    outputs: List[str] = []
    last_done = -1
    for idx, p in enumerate(expected_paths):
        pp = Path(p)
        if pp.exists() and pp.stat().st_size > 0:
            outputs.append(p)
            last_done = idx
        else:
            break

    last_frame_path: Optional[str] = None
    if last_done >= 0:
        try:
            last_frame_path = extract_last_frame_as_png(expected_paths[last_done])
        except Exception:
            last_frame_path = None

    start_idx = last_done + 1
    return outputs, start_idx, last_frame_path


def find_matching_providers(model: str, current_provider: str) -> List[str]:
    """Find providers that support the given model (excluding current provider)."""
    all_providers: List[VideoProvider] = ["openai", "azure", "google", "runway"]
    matching_providers: List[str] = []
    
    for other_provider in all_providers:
        if other_provider == current_provider:
            continue
        try:
            other_models = get_available_models(other_provider, query_api=False)
            if model in other_models:
                matching_providers.append(other_provider)
        except Exception:
            # Skip if we can't get models for this provider
            continue
    
    return matching_providers


def build_model_error_message(model: str, provider: str, available_models: List[str], matching_providers: List[str]) -> str:
    """Build helpful error message for model validation failures."""
    if matching_providers:
        providers_str = "', '".join(matching_providers)
        return (
            f"Model '{model}' is not available for provider '{provider}'. "
            f"This model is available for provider(s): '{providers_str}'. "
            f"Use --provider {matching_providers[0]} instead."
        )
    else:
        return (
            f"Model '{model}' is not recognized for provider '{provider}'. "
            f"Available models for '{provider}': {', '.join(available_models)}"
        )


def validate_model_for_provider(model: str, provider: VideoProvider, logger: Any) -> None:
    """
    Validate that the specified model is compatible with the provider.
    
    Raises ValueError with a helpful message if the model doesn't belong to the provider.
    If the model is found in a different provider, suggests the correct provider.
    
    Args:
        model: The model name to validate
        provider: The provider to check against
        logger: Logger instance for debug messages
        
    Raises:
        ValueError: If model is not compatible with the provider
    """
    try:
        # Get available models for the current provider (don't query API to keep it fast)
        available_models = get_available_models(provider, query_api=False)
        
        if model not in available_models:
            logger.debug(f"Model '{model}' not found in provider '{provider}'. Checking other providers...")
            
            # Check which provider(s) support this model
            matching_providers = find_matching_providers(model, provider)
            
            # Build and raise helpful error message
            error_message = build_model_error_message(model, provider, available_models, matching_providers)
            raise ValueError(error_message)
    
    except ValueError:
        # Re-raise ValueError (our validation error)
        raise
    except Exception as e:
        # Log but don't fail on validation errors (e.g., if we can't query models)
        logger.debug(f"Could not validate model '{model}' for provider '{provider}': {e}")


def validate_stitch_model(model: Optional[str]) -> None:
    """Validate that model is compatible with stitching functionality."""
    if not model or not model.startswith("veo"):
        raise ValueError(
            "Stitching is only supported for Veo models (veo-3.1* or veo3/veo3.1/veo3.1_fast)."
        )


# Sora API response parsing utilities

def sora_build_content_items(prompt: str, file_ids: List[str]) -> List[Dict[str, Any]]:
    """Build content items array for Sora API requests."""
    items: List[Dict[str, Any]] = [{"type": "input_text", "text": prompt}]
    for file_id in file_ids:
        items.append({"type": "input_image", "image": {"file_id": file_id}})
    return items


def sora_extract_async_video_id(response: Any) -> Optional[str]:
    """Extract video ID from OpenAI Videos API async response."""
    # New Videos API returns video job object with direct id field
    if hasattr(response, 'id'):
        return response.id  # type: ignore
    
    # Fallback for old API structure (legacy support)
    outputs = getattr(response, "output", None) or []  # type: ignore
    for item in outputs:  # type: ignore
        video = getattr(item, "video", None)  # type: ignore
        if video and getattr(video, "file_id", None):
            return video.file_id  # type: ignore
        if isinstance(item, dict):
            vid = item.get("video") or {}  # type: ignore
            if isinstance(vid, dict) and vid.get("file_id"):  # type: ignore
                return vid["file_id"]  # type: ignore
    return None


def sora_extract_sync_video_id(response: Any) -> Optional[str]:
    """Extract video ID from OpenAI Videos API sync response."""
    # New Videos API returns video job object with direct id field
    if hasattr(response, 'id'):
        return response.id
    
    # Fallback for old API structure (legacy support)
    if hasattr(response, 'choices') and response.choices:
        choice = response.choices[0]
        if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
            return sora_extract_from_content(choice.message.content)
    return None


def sora_extract_from_content(content: Any) -> Optional[str]:
    """Extract video ID from Sora response content."""
    if isinstance(content, list):
        for item in content:  # type: ignore
            if isinstance(item, dict) and item.get('type') == 'video':  # type: ignore
                return item.get('video', {}).get('file_id')  # type: ignore
    elif isinstance(content, dict) and content.get('type') == 'video':  # type: ignore
        return content.get('video', {}).get('file_id')  # type: ignore
    return None