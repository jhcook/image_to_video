import subprocess
import tempfile
from typing import List, Optional

def extract_last_frame_as_png(video_path: str, output_dir: str = None) -> str:
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
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", r"select=eq(n\\,prev_n+1)",
        "-vframes", "1",
        output_png
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        raise RuntimeError(f"Failed to extract last frame: {e}")
    return output_png
def generate_video_sequence_with_veo3_stitching(
    prompts,
    file_paths_list=None,
    width=1280,
    height=720,
    duration_seconds=8,
    seed=None,
    out_paths=None,
    config=None,
    model=None,
    delay_between_clips=10,
    backend="veo3"
):
    """
    Generate a sequence of Veo 3.1 video clips with seamless frame transitions.
    
    Supports both Google Veo (backend="veo3") and RunwayML Veo (backend="runway").
    
    This function orchestrates multi-clip video generation where the last frame
    from each clip is automatically extracted and used as the source frame (first
    frame parameter) for the next clip, ensuring perfect visual continuity.
    
    The implementation correctly uses Veo 3.1 API parameters:
    - `image`/`firstKeyframe`: Source frame from previous clip (for clips 2+)
    - `reference_images`: User's uploaded images (consistent across all clips)
    
    Args:
        prompts: List of text prompts (one per clip, each can be completely different)
        file_paths_list: Optional list of image lists for each clip. If provided,
                        each element is a list of reference images for that clip.
                        If None, no reference images are used.
        width: Video width in pixels (default: 1280)
        height: Video height in pixels (default: 720)
        duration_seconds: Duration for each clip in seconds (default: 8)
        seed: Optional random seed for reproducibility
        out_paths: Optional list of custom output paths (default: veo3_clip_N.mp4)
        config: Veo3Config instance (loads from environment if None)
        model: Veo 3.1 model name (must start with "veo-3.1")
        delay_between_clips: Seconds to wait between generating clips (default: 10)
                            Helps avoid rate limiting when generating multiple clips.
                            Set to 0 to disable. Recommended: 10-30 seconds.
        
    Returns:
        List of generated video file paths (one per prompt)
        
    Raises:
        ValueError: If model is not a Veo 3.1 model
        RuntimeError: If frame extraction or video generation fails
        
    Example:
        >>> prompts = [
        ...     "Pan right from foyer",
        ...     "Dolly forward to living area",
        ...     "Pan to sideboard"
        ... ]
        >>> outputs = generate_video_sequence_with_veo3_stitching(
        ...     prompts=prompts,
        ...     file_paths_list=[["img1.png"], ["img2.png"], ["img3.png"]],
        ...     model="veo-3.1-fast-generate-preview"
        ... )
        >>> print(outputs)  # ['veo3_clip_1.mp4', 'veo3_clip_2.mp4', 'veo3_clip_3.mp4']
        
    Workflow:
        1. Clip 1: Generate with reference images only (no source frame)
        2. Extract last frame from Clip 1
        3. Clip 2: Generate with source frame + reference images
        4. Extract last frame from Clip 2
        5. Clip 3: Generate with source frame + reference images
        6. Continue for all remaining clips...
        
    See Also:
        - extract_last_frame_as_png(): Frame extraction implementation
        - generate_video_with_veo3(): Single clip generation with source frame support
        - Veo 3.1 API docs: https://ai.google.dev/gemini-api/docs/video
    """
    logger = get_library_logger()
    
    # Load config based on backend
    if config is None:
        if backend == "veo3":
            config = Veo3Config.from_environment()
        else:  # runway
            config = RunwayConfig.from_environment()
    
    # Validate model
    if not model or not model.startswith("veo"):
        raise ValueError("Stitching is only supported for Veo models (veo-3.1* or veo3/veo3.1/veo3.1_fast).")
    
    outputs = []
    last_frame_path = None
    
    for idx, prompt in enumerate(prompts):
        reference_images, source_frame, out_path = _veo3_prepare_clip_params(
            idx, file_paths_list, last_frame_path, out_paths, backend
        )
        _veo3_log_clip(logger, idx, len(prompts), reference_images, source_frame)

        # Generate video with the appropriate backend
        if backend == "veo3":
            video_path = generate_video_with_veo3(
                prompt=prompt,
                file_paths=reference_images,
                source_frame=source_frame,
                width=width,
                height=height,
                duration_seconds=duration_seconds,
                seed=seed,
                out_path=out_path,
                config=config,
                model=model
            )
        else:  # runway
            video_path = generate_video_with_runway_veo(
                prompt=prompt,
                reference_images=reference_images,
                first_frame=source_frame,
                width=width,
                height=height,
                duration_seconds=duration_seconds,
                seed=seed,
                out_path=out_path,
                config=config,
                model=model
            )
        
        outputs.append(video_path)
        last_frame_path = extract_last_frame_as_png(video_path)

        _veo3_sleep_between_clips(logger, idx, len(prompts), delay_between_clips)
    return outputs


def _veo3_prepare_clip_params(idx, file_paths_list, last_frame_path, out_paths, backend="veo3"):
    reference_images = file_paths_list[idx] if file_paths_list else []
    source_frame = last_frame_path if idx > 0 else None
    
    # Generate default output path based on backend
    if out_paths:
        out_path = out_paths[idx]
    else:
        prefix = "veo3" if backend == "veo3" else "runway_veo"
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
multiple backends (Sora-2, Veo-3, and RunwayML).

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

from typing import Iterable, Union
from pathlib import Path

from .config import SoraConfig, Veo3Config, RunwayConfig, VideoBackend, create_config_for_backend
from .providers import SoraAPIClient, AzureSoraAPIClient, Veo3APIClient, RunwayGen4Client, RunwayVeoClient
from .file_handler import FileHandler
from .logger import get_library_logger


def generate_video(
    prompt: str,
    file_paths: Iterable[Union[str, Path]] = (),
    *,
    backend: VideoBackend = "sora2",
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
    Generate a video using the specified backend (Sora-2 or Veo-3).
    
    This is the main unified function that routes to the appropriate backend
    and orchestrates the video generation process.
    
    Args:
        prompt: Text description of the desired video content
        file_paths: Paths to image files for reference. Defaults to empty tuple.
        backend: Video generation backend to use ("sora2", "veo3", or "runway")
        model: Specific model to use (backend-dependent). Defaults to None (uses backend default).
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
        ValueError: If backend is not supported
        RuntimeError: If API calls fail or video generation fails
        FileNotFoundError: If reference image files don't exist
        KeyboardInterrupt: If user cancels during retry backoff
        
    Examples:
        >>> # Generate with Sora-2 (default)
        >>> video_path = generate_video("A peaceful lake at sunset")
        
        >>> # Generate with Veo-3
        >>> video_path = generate_video(
        ...     "A peaceful lake at sunset",
        ...     backend="veo3"
        ... )
        
        >>> # With image references
        >>> images = ["lake1.jpg", "lake2.jpg"]
        >>> video_path = generate_video(
        ...     "A video tour of this lake",
        ...     file_paths=images,
        ...     backend="sora2",
        ...     width=1920,
        ...     height=1080
        ... )
    """
    logger = get_library_logger()
    logger.info(f"Starting video generation with backend: {backend}")
    logger.debug(f"Parameters: {width}x{height}, {fps}fps, {duration_seconds}s, model={model}")
    
    if backend == "sora2":
        return generate_video_with_sora2(
            prompt=prompt,
            file_paths=file_paths,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration_seconds,
            seed=seed,
            out_path=out_path or "sora2_output.mp4",
            config=config,
            model=model
        )
    elif backend == "azure-sora":
        return generate_video_with_azure_sora(
            prompt=prompt,
            file_paths=file_paths,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration_seconds,
            seed=seed,
            out_path=out_path or "azure_sora_output.mp4",
            config=config,
            model=model
        )
    elif backend == "veo3":
        return generate_video_with_veo3(
            prompt=prompt,
            file_paths=file_paths,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration_seconds,
            seed=seed,
            out_path=out_path or "veo3_output.mp4",
            config=config,
            model=model
        )
    elif backend == "runway":
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
        raise ValueError(f"Unsupported backend: {backend}. Use 'sora2', 'azure-sora', 'veo3', or 'runway'")


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
    out_path: str = "sora2_output.mp4",
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
        out_path: Output file path. Defaults to "sora2_output.mp4".
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