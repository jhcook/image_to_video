# API Reference

Programmatic API for generating videos from Python. Import from `video_gen`.

## Top-Level Functions (video_gen.video_generator)

### generate_video

Signature:
```
generate_video(
  prompt: str,
  file_paths: Iterable[Union[str, Path]] = (),
  *,
  backend: Literal["sora2", "azure-sora", "veo3", "runway"] = "sora2",
  model: Optional[str] = None,
  width: int = 1280,
  height: int = 720,
  fps: int = 24,
  duration_seconds: int = 8,
  seed: Optional[int] = None,
  out_path: Optional[str] = None,
  config = None
) -> str
```

Description:
- Unified entry point that routes to the selected backend
- Saves result to `out_path` and returns the file path

Raises:
- `ValueError` for invalid backend
- `FileNotFoundError` for missing images
- `RuntimeError` for API failures

---

### generate_video_with_sora2

```
generate_video_with_sora2(prompt, file_paths=(), width=1280, height=720, fps=24,
                          duration_seconds=8, seed=None, out_path="sora2_output.mp4",
                          config: SoraConfig = None, model: Optional[str] = None) -> str
```

- Direct OpenAI Sora-2 generation
- Uploads images to OpenAI, handles retries, and downloads video

---

### generate_video_with_azure_sora

```
generate_video_with_azure_sora(prompt, file_paths=(), width=1280, height=720, fps=24,
                               duration_seconds=8, seed=None, out_path="azure_sora_output.mp4",
                               config: AzureSoraConfig = None, model: Optional[str] = None) -> str
```

- Azure AI Foundry Sora-2 deployment
- Same behavior as OpenAI Sora but uses Azure credentials and endpoint

---

### generate_video_with_veo3

```
generate_video_with_veo3(prompt, file_paths=(), source_frame=None, width=1280, height=720,
                         fps=24, duration_seconds=8, seed=None, out_path="veo3_output.mp4",
                         config: Veo3Config = None, model: Optional[str] = None) -> str
```

- Google Veo-3 generator with stitching support via `source_frame`
- Accepts up to 3 reference images (style/content guidance)

---

### generate_video_with_runway

```
generate_video_with_runway(prompt, file_paths=(), model=None, width=1280, height=720,
                           duration_seconds=5, seed=None, out_path=None, config: RunwayConfig = None) -> str
```

- RunwayML Gen-4 client (single-image reference, duration 5 or 10)
- Model: `gen4_turbo` (default) or `gen4`

---

### generate_video_with_runway_veo

```
generate_video_with_runway_veo(prompt, reference_images=None, first_frame=None, model=None,
                               width=1280, height=720, duration_seconds=5, seed=None,
                               out_path=None, config: RunwayConfig = None) -> str
```

- Google Veo models via RunwayML
- Supports reference images (up to 3) and `first_frame` for stitching

---

### generate_video_sequence_with_veo3_stitching

```
generate_video_sequence_with_veo3_stitching(prompts, file_paths_list=None, width=1280, height=720,
                                            duration_seconds=8, seed=None, out_paths=None, config=None,
                                            model=None, delay_between_clips=10, backend="veo3") -> List[str]
```

- Orchestrates N clips with automatic frame extraction between clips
- `backend` can be `veo3` (Google) or `runway` (Runway Veo)

---

### extract_last_frame_as_png

```
extract_last_frame_as_png(video_path: str, output_dir: Optional[str] = None) -> str
```

- Uses ffmpeg to extract the last frame of a video to PNG (for stitching)

## Configuration Objects (video_gen.config)

- `SoraConfig` (OpenAI)
- `AzureSoraConfig` (Azure)
- `Veo3Config` (Google Veo)
- `RunwayConfig` (RunwayML)
- `VideoBackend` (Literal type for backends)
- `create_config_for_backend(backend)` constructor

All configs support:
- `from_environment()` to read env and .env
- Validation of required fields
- Reasonable defaults for optional fields

## Provider Clients (video_gen.providers)

Import re-exports:

```
from video_gen.providers import (
  SoraAPIClient,
  AzureSoraAPIClient,
  Veo3APIClient,
  RunwayGen4Client,
  RunwayVeoClient,
)
```

Each client encapsulates provider-specific HTTP/API logic and is generally used internally by `video_generator.py`. You can use them directly for advanced scenarios.

## Exceptions (video_gen.exceptions)

Domain-specific error types for clearer handling. Common ones include:
- `ConfigurationError`
- `ApiRequestError`
- `RetryExhaustedError`

## Logging (video_gen.logger)

- `get_library_logger()` returns a configured logger that writes detailed DEBUG logs to `logs/video_gen.log` with rotation.

## Example: Programmatic Use

```python
from video_gen.video_generator import generate_video, generate_video_sequence_with_veo3_stitching

# Simple one-off video
path = generate_video(
    prompt="Cinematic ocean waves at sunset",
    backend="sora2",
    width=1920,
    height=1080,
)
print(path)

# Seamless stitched sequence (Veo 3.1)
outputs = generate_video_sequence_with_veo3_stitching(
    prompts=["Pan right", "Dolly forward", "Pan left"],
    file_paths_list=[["ref1.jpg", "ref2.jpg"]] * 3,
    model="veo-3.1-fast-generate-preview",
)
print(outputs)
```
