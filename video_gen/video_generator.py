from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, Union

from .exceptions import InsufficientCreditsError
from .config import (
    SoraConfig,
    Veo3Config,
    RunwayConfig,
    VideoProvider,
    create_config_for_provider,
    get_available_models,
)
from .providers import (
    SoraAPIClient,
    AzureSoraAPIClient,
    Veo3APIClient,
    RunwayGen4Client,
    RunwayVeoClient,
)
from .file_handler import FileHandler
from .logger import get_library_logger


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
    """
    logger = get_library_logger()

    # Config and model validation
    config = _get_stitch_config(provider, config)
    _validate_stitch_model(model)

    outputs: List[str] = []
    last_frame_path: Optional[str] = None

    expected_paths = _build_expected_out_paths(len(prompts), out_paths, provider)

    # Resume support: detect already-generated clips and last frame
    start_idx = 0
    if resume:
        outputs, start_idx, last_frame_path = _compute_resume_state(expected_paths)

    # Iterate and generate remaining clips
    for idx in range(start_idx, len(prompts)):
        prompt = prompts[idx]
        reference_images, source_frame, out_path = _veo3_prepare_clip_params(
            idx, file_paths_list, last_frame_path, out_paths, provider
        )
        _veo3_log_clip(logger, idx, len(prompts), reference_images, source_frame)

        try:
            video_path = _generate_veo_clip(
                provider=provider,
                prompt=prompt,
                reference_images=reference_images,
                source_frame=source_frame,
                width=width,
                height=height,
                duration_seconds=duration_seconds,
                seed=seed,
                out_path=out_path,
                config=config,
                model=model,
            )
        except InsufficientCreditsError as e:
            logger.error(
                "Stopping stitching due to insufficient RunwayML credits after clip %d/%d.\n%s",
                idx + 1,
                len(prompts),
                str(e),
            )
            return outputs

        outputs.append(video_path)
        last_frame_path = extract_last_frame_as_png(video_path)
        _veo3_sleep_between_clips(logger, idx, len(prompts), delay_between_clips)

    return outputs


def _get_stitch_config(provider: str, config: Optional[Union[Veo3Config, RunwayConfig]]):
    if config is not None:
        return config
    if provider == "veo3":
        return Veo3Config.from_environment()
    return RunwayConfig.from_environment()


def _validate_stitch_model(model: Optional[str]) -> None:
    if not model or not model.startswith("veo"):
        raise ValueError(
            "Stitching is only supported for Veo models (veo-3.1* or veo3/veo3.1/veo3.1_fast)."
        )


def _build_expected_out_paths(count: int, out_paths: Optional[List[str]], provider: str) -> List[str]:
    if out_paths:
        return list(out_paths)
    prefix = "veo3" if provider == "veo3" else "runway_veo"
    return [f"{prefix}_clip_{i + 1}.mp4" for i in range(count)]


def _compute_resume_state(expected_paths: List[str]) -> tuple[List[str], int, Optional[str]]:
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


def _generate_veo_clip(
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
        return generate_video_with_runway_veo(
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


def _veo3_prepare_clip_params(idx, file_paths_list, last_frame_path, out_paths, provider="veo3"):
    reference_images = file_paths_list[idx] if file_paths_list else []
    source_frame = last_frame_path if idx > 0 else None
    
    # Generate default output path based on provider
    if out_paths:
        out_path = out_paths[idx]
    else:
        prefix = "veo3" if provider == "veo3" else "runway_veo"
        out_path = f"{prefix}_clip_{idx + 1}.mp4"
    
    return reference_images, source_frame, out_path


def _veo3_log_clip(logger, idx, total, reference_images, source_frame):
    if source_frame:
        logger.info(
            f"Generating clip {idx+1}/{total} with source frame + {len(reference_images)} reference image(s)..."
        )
    else:
        logger.info(
            f"Generating clip {idx+1}/{total} with {len(reference_images)} image(s)..."
        )


def _veo3_sleep_between_clips(logger, idx, total, delay_seconds):
    if idx < total - 1 and delay_seconds > 0:
        logger.info(
            f"Waiting {delay_seconds}s before next clip to avoid rate limiting..."
        )
        import time
        time.sleep(delay_seconds)
"""
Main video generation orchestration module.

Coordinates file handling, API calls, and video generation workflow for
multiple providers (Sora-2, Veo-3, and RunwayML).

Veo 3.1 Stitching Support:
--------------------------
This module includes specialized support for Veo 3.1 seamless stitching through
the generate_video_sequence_with_veo3_stitching() function, which:

1. Generates multiple video clips with different prompts
2. Extracts the last frame from each clip using ffmpeg
3. Passes the extracted frame as the source frame (image parameter) to the next clip
4. Maintains reference images across all clips for style consistency

The implementation follows the Veo 3.1 API specification by separating:
- Source frame: The exact first frame of each clip (for seamless transitions)
- Reference images: Style and content guidance (up to 3 images)

Key Functions:
- generate_video_sequence_with_veo3_stitching(): Multi-clip orchestration
- extract_last_frame_as_png(): Frame extraction using ffmpeg
- generate_video_with_veo3(): Single clip generation with source frame support

See Also:
    - SOURCE_FRAME_IMPLEMENTATION.md for technical details
    - STITCHING_EXAMPLES.md for usage examples
    - Veo 3.1 API docs: https://ai.google.dev/gemini-api/docs/video
"""


def _validate_model_for_provider(model: str, provider: VideoProvider, logger) -> None:
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
            all_providers = ["openai", "azure", "google", "runway"]
            matching_providers = []
            
            for other_provider in all_providers:
                if other_provider == provider:
                    continue
                try:
                    other_models = get_available_models(other_provider, query_api=False)
                    if model in other_models:
                        matching_providers.append(other_provider)
                except Exception:
                    # Skip if we can't get models for this provider
                    continue
            
            # Build helpful error message
            if matching_providers:
                providers_str = "', '".join(matching_providers)
                raise ValueError(
                    f"Model '{model}' is not available for provider '{provider}'. "
                    f"This model is available for provider(s): '{providers_str}'. "
                    f"Use --provider {matching_providers[0]} instead."
                )
            else:
                raise ValueError(
                    f"Model '{model}' is not recognized for provider '{provider}'. "
                    f"Available models for '{provider}': {', '.join(available_models)}"
                )
    
    except ValueError:
        # Re-raise ValueError (our validation error)
        raise
    except Exception as e:
        # Log but don't fail on validation errors (e.g., if we can't query models)
        logger.debug(f"Could not validate model '{model}' for provider '{provider}': {e}")


def generate_video(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    provider: VideoProvider = "openai",
    model: str = None,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration_seconds: int = 8,
    seed: int = None,
    out_path: str = None,
    config = None
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
        
    Examples:
        >>> # Generate with Sora-2 (default)
        >>> video_path = generate_video("A peaceful lake at sunset")
        
        >>> # Generate with Google Veo-3
        >>> video_path = generate_video(
        ...     "A peaceful lake at sunset",
        ...     provider="google"
        ... )
        
        >>> # With image references
        >>> images = ["lake1.jpg", "lake2.jpg"]
        >>> video_path = generate_video(
        ...     "A video tour of this lake",
        ...     file_paths=images,
        ...     provider="openai",
        ...     width=1920,
        ...     height=1080
        ... )
    """
    logger = get_library_logger()
    logger.info(f"Starting video generation with provider: {provider}")
    logger.debug(f"Parameters: {width}x{height}, {fps}fps, {duration_seconds}s, model={model}")
    
    # Validate model is compatible with provider
    if model is not None:
        _validate_model_for_provider(model, provider, logger)
    
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


def generate_video_with_veo3(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    source_frame: str = None,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration_seconds: int = 8,
    seed: int = None,
    out_path: str = "veo3_output.mp4",
    config: Veo3Config = None,
    model: str = None
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
        logger.info(f"Validating {len(list(file_paths))} image files")
        validated_paths = api_client.upload_files(list(file_paths))
    
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
    
    # Step 3: Save video to file
    output_path = Path(out_path)
    logger.info(f"Saving video to: {output_path}")
    with open(output_path, 'wb') as f:
        f.write(video_content)
    
    logger.info(f"Video saved successfully: {output_path}")
    return str(output_path)


def generate_video_with_sora2(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration_seconds: int = 8,
    seed: int = None,
    out_path: str = "openai_output.mp4",
    config: SoraConfig = None,
    model: str = None
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
    # Initialize config, client, file handler
    config, api_client, file_handler = _sora_init(config)

    # Step 1: Upload any reference files (images) and get their IDs
    file_ids = file_handler.upload_files(file_paths)

    # Step 2: Build the multi-part content message: text prompt + image references
    content_items = _sora_build_content_items(prompt, file_ids)

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
        video_file_id = _sora_extract_async_video_id(response)
    else:
        video_file_id = _sora_extract_sync_video_id(response)
    
    if not video_file_id:
        raise RuntimeError("Could not locate video file ID in response output")
    
    # Step 5: Download the generated video file
    api_client.download_video(video_file_id, out_path)
    
    return out_path


def _sora_init(config):
    if config is None:
        config = SoraConfig.from_environment()
    api_client = SoraAPIClient(config)
    file_handler = FileHandler(config, api_client.client)
    return config, api_client, file_handler


def _sora_build_content_items(prompt: str, file_ids: list[str]):
    items = [{"type": "input_text", "text": prompt}]
    for file_id in file_ids:
        items.append({"type": "input_image", "image": {"file_id": file_id}})
    return items


def _sora_extract_async_video_id(response) -> str | None:
    outputs = getattr(response, "output", None) or []
    for item in outputs:
        video = getattr(item, "video", None)
        if video and getattr(video, "file_id", None):
            return video.file_id
        if isinstance(item, dict):
            vid = item.get("video") or {}
            if isinstance(vid, dict) and vid.get("file_id"):
                return vid["file_id"]
    return None


def _sora_extract_sync_video_id(response) -> str | None:
    if hasattr(response, 'choices') and response.choices:
        choice = response.choices[0]
        if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
            return _sora_extract_from_content(choice.message.content)
    return None


def _sora_extract_from_content(content) -> str | None:
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'video':
                return item.get('video', {}).get('file_id')
    elif isinstance(content, dict) and content.get('type') == 'video':
        return content.get('video', {}).get('file_id')
    return None


def generate_video_with_azure_sora(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration_seconds: int = 8,
    seed: int = None,
    out_path: str = "azure_sora_output.mp4",
    config = None,
    model: str = None
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
        model: Model name to use (sora-2 or sora-2-pro)
        
    Returns:
        Path to the saved video file
        
    Raises:
        RuntimeError: If API calls fail or video generation fails
        FileNotFoundError: If reference image files don't exist
        ValueError: If file types are unsupported or Azure config invalid
        KeyboardInterrupt: If user cancels during retry backoff
    """
    from .providers.azure_provider import AzureSoraAPIClient
    from .config import AzureSoraConfig
    from .file_handler import FileHandler
    
    logger = get_library_logger()
    logger.info("Generating video with Azure AI Foundry Sora-2")
    
    # Initialize configuration if not provided
    if config is None:
        logger.debug("Loading Azure Sora config from environment")
        config = AzureSoraConfig.from_environment()
    
    # Initialize API client and file handler
    logger.debug("Initializing Azure Sora API client")
    api_client = AzureSoraAPIClient(config)
    file_handler = FileHandler(config, api_client.client)
    
    # Step 1: Upload any reference files (images) and get their IDs
    file_ids = file_handler.upload_files(file_paths)
    
    # Step 2: Build the multi-part content message: text prompt + image references
    content_items = _sora_build_content_items(prompt, file_ids)
    
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
        video_file_id = _sora_extract_async_video_id(response)
    else:
        video_file_id = _sora_extract_sync_video_id(response)
    
    if not video_file_id:
        raise RuntimeError("Could not locate video file ID in Azure response output")
    
    # Step 5: Download the generated video file
    api_client.download_video(video_file_id, out_path)
    
    logger.info(f"Azure Sora video saved successfully: {out_path}")
    return out_path


def generate_video_with_runway(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    model: str = None,
    width: int = 1280,
    height: int = 720,
    duration_seconds: int = 5,
    seed: int = None,
    out_path: str = None,
    config: RunwayConfig = None
) -> str:
    """
    Generate a video using RunwayML's Gen-4 models.
    
    RunwayML supports image-to-video with a single image reference.
    If multiple images are provided, only the first one is used.
    
    Args:
        prompt: Text description of the desired video content
        file_paths: Paths to image files for reference. Only first image is used.
        width: Video width in pixels. Defaults to 1280.
        height: Video height in pixels. Defaults to 720.
        fps: Frames per second (note: RunwayML may use its own FPS). Defaults to 24.
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
    # Step 1: Initialize configuration
    if config is None:
        config = RunwayConfig.from_environment()
    
    config.validate()
    
    # Use specified model or default from config
    selected_model = model if model is not None else config.default_model
    
    # Validate duration
    if duration_seconds not in [5, 10]:
        duration_seconds = 5
    
    # Step 2: Set output path
    if out_path is None:
        out_path = config.default_output
    
    # Step 3: Handle image input (RunwayML uses single image)
    image_path = None
    file_list = list(file_paths)
    
    if file_list:
        if len(file_list) > 1:
            # Only use first image - RunwayML supports single image only
            pass
        image_path = str(file_list[0])
    
    # Step 4: Initialize API client and generate video
    api_client = RunwayGen4Client(config)
    
    return api_client.generate_video(
        prompt=prompt,
        image_path=image_path,
        width=width,
        height=height,
        duration=duration_seconds,
        output_path=out_path,
        model=selected_model,
        seed=seed
    )


def generate_video_with_runway_veo(
    prompt: str,
    reference_images: List[str] = None,
    first_frame: str = None,
    *,
    model: str = None,
    width: int = 1280,
    height: int = 720,
    duration_seconds: int = 5,
    seed: int = None,
    out_path: str = None,
    config: RunwayConfig = None
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
        
        >>> # With reference images and first frame (stitching)
        >>> video_path = generate_video_with_runway_veo(
        ...     "Continue panning across the room",
        ...     reference_images=["room1.png", "room2.png"],
        ...     first_frame="prev_clip_last_frame.png",
        ...     model="veo3.1",
        ...     duration_seconds=8
        ... )
    """
    # Step 1: Initialize configuration
    if config is None:
        config = RunwayConfig.from_environment()
    
    config.validate()
    
    # Use specified model or default from config
    selected_model = model if model is not None else config.default_model
    
    # Validate that it's a Veo model
    if not selected_model.startswith("veo"):
        raise ValueError(f"This function is for Veo models only. Got: {selected_model}")
    
    # Validate duration (Veo supports 2-10 seconds)
    if not (2 <= duration_seconds <= 10):
        duration_seconds = 5
    
    # Step 2: Set output path
    if out_path is None:
        out_path = f"runway_{selected_model}_output.mp4"
    
    # Step 3: Initialize API client and generate video
    api_client = RunwayVeoClient(config)
    
    # Note: RunwayML Veo models don't support seed parameter
    return api_client.generate_video(
        prompt=prompt,
        first_frame=first_frame,
        reference_images=reference_images,
        width=width,
        height=height,
        duration=duration_seconds,
        output_path=out_path,
        model=selected_model
    )