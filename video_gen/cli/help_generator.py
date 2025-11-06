"""
Help text generation for the video generation CLI.

This module is responsible for generating comprehensive help documentation
for all CLI options and commands.
"""

from typing import List, Union
from ..config import VideoProvider

# Type alias for providers
ProviderType = Union[VideoProvider, List[VideoProvider]]


class HelpGenerator:
    """Generates help text for CLI commands and options."""
    
    def __init__(self, available_providers: ProviderType):
        """Initialize with available providers for dynamic help content."""
        if isinstance(available_providers, list):
            self.available_providers = available_providers
        else:
            self.available_providers = [available_providers]
    
    def generate_help_text(self) -> str:
        """Generate comprehensive help text."""
        available_str = self._get_available_providers_text()
        
        header = self._generate_usage_header()
        options = self._generate_options_section(available_str)
        stitching = self._generate_stitching_section()
        auth = self._generate_auth_section()
        artifacts = self._generate_artifacts_section()
        requirements = self._generate_requirements_section()
        examples = self._generate_examples_section()
        
        return f"{header}\n{options}\n{stitching}\n{auth}\n{artifacts}\n{requirements}\n{examples}"
    
    def _get_available_providers_text(self) -> str:
        """Get text describing available providers."""
        if self.available_providers:
            return f"Available providers: {', '.join(self.available_providers)}"
        return "No providers available (check API credentials)"
    
    def _generate_usage_header(self) -> str:
        """Generate the usage header and description."""
        return """usage: image2video.py [-h] [-i IMAGES ...] [--provider PROVIDER] [--width WIDTH] [--height HEIGHT]
                      [--fps FPS] [--duration DURATION] [--seed SEED] [-o OUTPUT]
                      [--stitch] [-p PROMPTS ...] prompt

Generate videos using AI models (Sora-2, Veo-3, or RunwayML) with text prompts and optional image references

positional arguments:
  prompt                Text prompt describing the video to generate (single clip mode)
                        Can also use -p/--prompt flag for single prompts"""
    
    def _generate_options_section(self, available_str: str) -> str:
        """Generate the main options section."""
        return f"""options:
  -h, --help            Show this help message and exit
  --list-providers      List all video generation providers with their availability status
  --list-models [PROVIDER]
                        List available models for all providers or a specific one
                        Example: --list-models runway
  --list-artifacts      List all generated video artifacts with metadata and download status
                        Optionally filter by: --provider PROVIDER --status STATUS
  --download TASK_ID    Download a specific video artifact by task ID
                        Optionally specify: --output PATH --force (to overwrite existing files)
  -i, --images IMAGES   Image file paths (supports multiple files and shell wildcards)
  --provider PROVIDER   Video generation provider: 'openai', 'azure', 'google', or 'runway' (default: openai)
                        {available_str}
  -p, --prompt PROMPT   Text prompt (alternative to positional argument)
                        Single prompt: -p "Your prompt here"
                        Multiple prompts for stitching: -p "Prompt 1" "Prompt 2" (requires --stitch)
  --width WIDTH         Video width in pixels (default: 1280)
  --height HEIGHT       Video height in pixels (default: 720)
  --fps FPS             Frames per second (default: 24)
  --duration DURATION   Video duration in seconds (default: 8, or per-clip if stitching)
  --seed SEED           Random seed for reproducible results (optional)
  -m, --model MODEL     Specific model to use (e.g., gen4_turbo, gen4, veo-3.1-fast-generate-preview)
                        Use --list-models to see available models per provider
  -o, --output OUTPUT   Output video file path (default: <provider>_output.mp4)"""
    
    def _generate_stitching_section(self) -> str:
        """Generate the stitching mode section."""
        return """  
Veo 3.1 Stitching Mode (Multi-Clip):
  --stitch              Enable seamless multi-clip stitching (Veo 3.1 only)
                        Requires 2+ prompts via -p and --provider google (or runway)
                        Example: --stitch -p 'Clip 1' 'Clip 2' 'Clip 3'
  --resume              Resume stitching from where it left off (skips existing clips)
                        Useful when generation was interrupted or credits ran out
                        Automatically detects completed clips and continues from next
  --delay SECONDS       Seconds to wait between generating clips (default: 10)
                        Helps avoid rate limiting. Set to 0 to disable.
                        Recommended: 10-30 seconds for heavy use"""
    
    def _generate_auth_section(self) -> str:
        """Generate the authentication section."""
        return """Google Authentication:
  --google-login        Authenticate with Google Cloud for Veo-3 provider
                        Supports two methods (tries gcloud first, falls back to OAuth):
                        1. gcloud CLI (recommended): Uses 'gcloud auth' automatically
                        2. OAuth browser: Opens browser for login (requires client_secrets.json)
                        After authentication, continue with video generation or exit
  --google-login-browser
                        Force OAuth browser authentication (skip gcloud, use browser only)
                        Requires client_secrets.json in video_gen/providers/google_provider/
                        Useful when you want to use a different Google account than gcloud
  --google-clear-cache  Clear cached OAuth credentials and exit
                        Use this to force re-authentication or switch accounts
                        Removes token.pickle file from google_provider directory"""
    
    def _generate_artifacts_section(self) -> str:
        """Generate the artifact management section."""
        return """Artifact Management:
  --list-artifacts      List all generated video artifacts with metadata
                        Shows: Task ID, Provider, Model, Status, Prompt, Created date
                        Optional filters: --provider (openai|azure|google|runway)
                                         --status (pending|completed|failed|downloaded)
  --download TASK_ID    Download a video artifact by its unique task ID
                        Downloads to artifacts/downloads/ by default
                        Optional parameters: --output PATH, --force (overwrite existing)
                        Automatically updates artifact status to 'downloaded'
                        Resumes interrupted downloads when possible"""
    
    def _generate_requirements_section(self) -> str:
        """Generate the provider requirements section."""
        return """provider Requirements:
  Sora-2 (OpenAI):      Set OPENAI_API_KEY environment variable (API key)
  Azure Sora:           Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT
                        Get credentials from: https://ai.azure.com/
  Veo-3:                Option 1: Use --google-login flag (automatic gcloud or OAuth)
                        Option 2: Set GOOGLE_API_KEY manually via gcloud:
                          export GOOGLE_API_KEY="$(gcloud auth application-default print-access-token)"
                        See VEO_AUTH_GUIDE.md for detailed authentication setup
  RunwayML:             Set RUNWAY_API_KEY environment variable (optional: RUNWAY_MODEL)"""
    
    def _generate_examples_section(self) -> str:
        """Generate the examples section."""
        return """Examples:
  # List all providers and their availability
  image2video.py --list-providers
  
  # List available models for all providers
  image2video.py --list-models
  
  # List models for specific provider
  image2video.py --list-models runway
  
  # Artifact Management
  # List all generated video artifacts
  image2video.py --list-artifacts
  
  # List artifacts by provider
  image2video.py --list-artifacts --provider runway
  
  # List artifacts by status (pending, completed, failed, downloaded)
  image2video.py --list-artifacts --status completed
  
  # Download a specific video by task ID
  image2video.py --download ce88ed9c-89c9-483f-ae46-8259c64dd180
  
  # Download with custom output path
  image2video.py --download ce88ed9c-89c9-483f-ae46-8259c64dd180 --output my_video.mp4
  
  # Force overwrite existing file
  image2video.py --download ce88ed9c-89c9-483f-ae46-8259c64dd180 --force
  
  # Text-only generation with default OpenAI Sora-2
  image2video.py "A serene mountain landscape with flowing water"
  
  # Using different providers
  image2video.py --provider azure "A serene mountain landscape with flowing water"
  image2video.py --provider google "A serene mountain landscape with flowing water"
  image2video.py --provider runway "A serene mountain landscape with flowing water"
  
  # Using shell wildcard expansion for image references
  image2video.py -i images/* "A video tour of these beautiful scenes"
  image2video.py -b google -i ~/Downloads/photos/*.jpg "Create a slideshow video"
  
  # Using specific image files with OpenAI Sora-2
  image2video.py -i image1.png image2.jpg "Dynamic sequence between these scenes"
  
  # With custom video parameters
  image2video.py "Abstract art animation" --width 1920 --height 1080 --fps 30 --duration 12
  
  # Using command substitution for complex prompts
  image2video.py -i photos/* "$(cat detailed_prompt.txt)"
  
  # Comparing providers with same prompt
  image2video.py --provider openai "Random scene" --seed 42 -o openai_video.mp4
  image2video.py --provider google "Random scene" --seed 42 -o google_video.mp4
  
  # Google Authentication (Veo-3)
  # Auto-authenticate and generate in one command (tries gcloud first)
  image2video.py --provider google --google-login -p "A serene landscape"
  
  # Force browser OAuth login (skip gcloud, use different account)
  image2video.py --provider google --google-login-browser -p "A serene landscape"
  
  # Just authenticate (for testing or to cache credentials)
  image2video.py --provider google --google-login
  
  # Clear cached OAuth credentials (force re-authentication next time)
  image2video.py --google-clear-cache
  
  # Veo 3.1 Stitching with authentication - Generate multiple clips
  image2video.py --provider google --model veo-3.1-fast-generate-preview --stitch \\
    --google-login -i foyer.png living.png kitchen.png \\
    -p "Pan right from foyer to reveal the stairs" \\
       "Dolly forward into living area, pan left to sofas" \\
       "Slow pan right to the sideboard with ornate mirror" \\
       "Dolly forward, pan left to show entry to other rooms"

Tips:
  - Use quotes around prompts to handle spaces and special characters
  - Wildcard patterns like *.jpg are expanded by the shell before reaching the script
  - For long prompts, consider storing them in a file and using $(cat prompt.txt)
  - Both providers handle synchronous and asynchronous API responses automatically
  - Stitching mode (--stitch) requires Veo 3.1 models and generates seamless multi-clip videos
  - If models are at capacity, the script will retry automatically with backoff delays
  - Use Ctrl+C to cancel during capacity retry attempts
  - Generated videos are saved in MP4 format with H.264 encoding
  - Set up API credentials for both providers to compare their outputs
  - All generated videos are automatically tracked as artifacts for later download
  - Use --list-artifacts to see all your generated videos and their status
  - Videos can be downloaded later even if generation was interrupted or failed initially
"""