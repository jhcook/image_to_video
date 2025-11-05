# Architecture

High-level overview of the modular, multi-provider architecture.

## Goals

- Clean separation of concerns
- Pluggable provider providers
- Library-first design with a simple CLI
- Strong logging and robust retries

## Top-Level Layout

```
image_to_video/
├── image2video.py          # CLI entry point (multi-provider)
├── image2video_mono.py     # Legacy monolith (Sora-only)
├── docs/                   # Documentation hub
└── video_gen/              # Core library package
    ├── __init__.py
    ├── arg_parser.py       # CLI options parsing
    ├── config.py           # Config objects + env loading
    ├── exceptions.py       # Domain exceptions
    ├── file_handler.py     # Path expansion + uploads
    ├── logger.py           # Centralized logging
    ├── providers/          # Provider integrations
    │   ├── __init__.py
    │   ├── openai_provider/
    │   ├── azure_provider/
    │   ├── google_provider/
    │   └── runway_provider/
    └── video_generator.py  # Orchestration + public API
```

## Key Modules

### video_gen/video_generator.py

- Public API surface for programmatic use:
  - `generate_video(...)`
  - `generate_video_with_openai(...)`
  - `generate_video_with_azure_sora(...)`
  - `generate_video_with_google(...)`
  - `generate_video_with_runway(...)`
  - `generate_video_with_runway_veo(...)`
  - Stitching helpers for Veo 3.1:
    - `generate_video_sequence_with_google_stitching(...)`
    - `extract_last_frame_as_png(...)`
- Routes requests to provider clients
- Applies cross-cutting concerns (logging, defaults, validation)

### video_gen/providers/

Provider-specific clients and configs.

- openai_provider/
  - `sora_client.py`, `config.py`
- azure_provider/
  - `sora_client.py`, `config.py`
- google_provider/
  - `google_client.py`, `config.py`, optional `auth.py`
- runway_provider/
  - `gen4_client.py` (Gen-4), `google_client.py` (Veo via Runway), `config.py`

Each client implements:
- Construct requests from normalized parameters
- Handle auth and retries per provider
- Download and save output videos

### video_gen/config.py

- Typed config objects per provider (e.g., `SoraConfig`, `AzureSoraConfig`, `Veo3Config`, `RunwayConfig`)
- `from_environment()` readers load from env + .env with validation
- `create_config_for_provider(provider)` convenience factory

### video_gen/file_handler.py

- Expands wildcard paths and comma-separated inputs
- Validates files exist and types are supported
- Uploads images (OpenAI, Azure) and returns IDs or temp URLs

### video_gen/arg_parser.py

- CLI parsing with consistent flags across providers
- `--provider`, `--model`, `--list-models`, `--stitch`, `--google-login`, etc.
- Generates helpful usage text and examples

### video_gen/logger.py

- Library logger via `get_library_logger()`
- DEBUG-level rotation to `logs/video_gen.log`
- Clean console + rich logs pattern

## Data Flow (Happy Path)

1. CLI parses options → structured args
2. Config loads from env/.env for selected provider
3. FileHandler validates/encodes/uploads images where needed
4. Provider client sends request with normalized parameters
5. API returns job or result; client handles polling if required
6. Video bytes saved to output path
7. Logs capture full trace for debugging

## Stitching Flow (Veo 3.1)

1. Generate clip N → save `clip_N.mp4`
2. Extract last frame with ffmpeg → `clip_N_last.png`
3. Use as source frame for clip N+1 (with same references)
4. Repeat for all clips
5. Concatenate outputs with ffmpeg

## Error Handling & Retries

- Provider clients implement retry on capacity/429 with exponential backoff
- Graceful cancellation with Ctrl+C during backoff loops
- Specific exceptions in `exceptions.py` for clearer handling

## Extensibility

To add a new provider:
- Create `video_gen/providers/<provider_name>/`
- Implement `<provider>_client.py` with a `generate_video(...)` that matches existing clients
- Add configuration in `<provider>/config.py`
- Export new client from `video_gen/providers/__init__.py`
- Extend `generate_video()` routing as needed
- Update docs and `--list-models` logic

## Notes

- The legacy monolith remains for reference and parity checks
- The modular API is used by the CLI, but also importable in your own scripts
- Logging defaults to DEBUG to aid troubleshooting, but console stays concise
