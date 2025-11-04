# Logs Directory

This directory contains log files generated during video generation operations.

## Log File

- **File**: `video_gen.log`
- **Level**: DEBUG (captures all operations)
- **Rotation**: 10MB max size, keeps 5 backup files (`.log.1`, `.log.2`, etc.)
- **Format**: `YYYY-MM-DD HH:MM:SS - video_gen - LEVEL - message`

## What Gets Logged

### DEBUG Level
- API client initialization with configuration
- API request details and parameters
- Image encoding and upload progress
- File operations and validations
- Retry attempt details

### INFO Level
- Major operation starts (video generation, file uploads)
- Successful completions
- Progress milestones
- Model and backend selection

### WARNING Level
- Retry attempts due to rate limiting
- Service unavailability (503)
- Non-fatal errors
- Fallback operations

### ERROR Level
- Authentication failures (401)
- API errors
- File not found errors
- Configuration issues

## Viewing Logs

```bash
# View entire log
cat video_gen.log

# Follow in real-time
tail -f video_gen.log

# View last 100 lines
tail -100 video_gen.log

# Search for errors
grep ERROR video_gen.log

# Search for specific backend
grep "Veo-3" video_gen.log
grep "Sora-2" video_gen.log
grep "RunwayML" video_gen.log

# View with timestamps
grep "2025-11-03 21:" video_gen.log
```

## Log Rotation

When `video_gen.log` reaches 10MB, it is automatically rotated:
- `video_gen.log` → Current log file
- `video_gen.log.1` → Previous log file
- `video_gen.log.2` → Older log file
- ... up to `video_gen.log.5`

The oldest log file (`.log.5`) is deleted when a new rotation occurs.

## Privacy Note

Log files may contain:
- API endpoints and request parameters
- File paths from your system
- Prompt text
- Error messages with system details

**Do not share log files publicly** without reviewing and redacting sensitive information.
