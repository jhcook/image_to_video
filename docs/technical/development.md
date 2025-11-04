# Development

Guidelines for contributing and extending the project.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Recommended tools:
- Python 3.10+
- ffmpeg installed (for stitching workflows)
- git pre-commit hooks (optional)

## Contributing Principles

- Favor the modular `video_gen/` package over monolithic changes
- Keep functions focused; add type hints and docstrings
- Log meaningful events; avoid excessive console noise
- Preserve backward-compatible CLI flags
- Include or update docs for user-facing changes

## Adding a New Backend

1. Create `video_gen/providers/<provider_name>/`
2. Add `config.py` with `from_environment()` and validation
3. Add a `<name>_client.py` exposing `generate_video(...)`
4. Export client in `video_gen/providers/__init__.py`
5. Wire into `video_gen/video_generator.py` routing
6. Add `--list-models` support (arg_parser/config)
7. Document in `docs/backends/<provider>.md`

## Code Style

- Black-compatible formatting (PEP 8)
- Descriptive names; avoid abbreviations in public APIs
- Explicit imports; keep `__init__.py` re-exports minimal and clear
- Handle errors with specific exceptions (see `video_gen/exceptions.py`)

## Logging

- Use `get_library_logger()` for library logs
- DEBUG-level to file: `logs/video_gen.log` with rotation
- Console stays concise; library logs capture details

## Testing

- Add unit tests for argument parsing and edge cases
- Add manual test recipes in docs where relevant
- Validate new provider flows end-to-end before merging

## Release Checklist

- Docs updated (user-guide, backend guide, reference/cli)
- Links verified from `docs/README.md`
- Quick start verified on a clean machine
- Backward compatibility confirmed for `image2video.py`

## Project Hygiene

- Keep secrets out of repo; use `.env` and environment variables
- Respect API provider rate limits; backoff on 429/503
- Validate inputs early; fail with actionable messages
- Avoid vendor lock-in; normalize parameters in orchestration layer

## Roadmap Ideas

- Web UI on top of `video_gen/` library
- Batch scheduler for large runs
- More providers: Pika, Luma, etc.
- Presets/prompt templates library
- Rich model metadata and dynamic discovery
