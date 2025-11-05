"""
Command-line argument parsing for video generation with multiple providers.

Handles complex shell wildcard expansion scenarios and argument validation
for both Sora-2 and Veo-3 providers.
"""

import sys
from typing import Dict, Any, Optional

from .config import get_available_providers, print_available_models, print_available_providers, VideoProvider


# Supported provider Names
PROVIDER_OPENAI = 'openai'
PROVIDER_AZURE = 'azure'
PROVIDER_GOOGLE = 'google'
PROVIDER_RUNWAY = 'runway'
SUPPORTED_PROVIDERS = [PROVIDER_OPENAI, PROVIDER_AZURE, PROVIDER_GOOGLE, PROVIDER_RUNWAY]

# Minimum prompts required for stitching mode
MIN_STITCH_PROMPTS = 2


class SoraArgumentParser:
    def parse_arguments(self, argv=None):
        """
        Parse command-line arguments using custom logic.
        Returns a dictionary of parsed arguments.
        """
        if argv is None:
            argv = sys.argv[1:]

        # Handle --help
        if '-h' in argv or '--help' in argv:
            print(self.help_text)
            sys.exit(0)

        # Handle --list-providers
        if '--list-providers' in argv:
            self._handle_list_providers()

        # Handle --list-models
        if '--list-models' in argv:
            self._handle_list_models(argv)

        # Parse all arguments
        result = self._parse_all_arguments(argv)

        # Validate and finalize
        self._validate_and_finalize(result)
        
        return result
    
    def _parse_all_arguments(self, argv):
        """Parse all command-line arguments into result dictionary."""
        result = self._default_result_dict()
        i = 0
        while i < len(argv):
            arg = argv[i]
            i = self._handle_option(arg, argv, i, result)
            i += 1
        return result
    
    def _validate_and_finalize(self, result):
        """Validate arguments and finalize prompt handling."""
        self._validate_providers(result['provider'])
        
        if result['stitch']:
            self._validate_stitching(result)
        else:
            self._handle_prompt_conversion(result)
            self._validate_prompt_provided(result)
    
    def _handle_prompt_conversion(self, result):
        """Convert prompts list to single prompt for non-stitch mode."""
        if not result['prompts'] or result['prompt']:
            return
        
        if len(result['prompts']) == 1:
            result['prompt'] = result['prompts'][0]
            self._validate_prompt_not_empty(result['prompt'])
            # Normalize: clear prompts when using single prompt in non-stitch mode
            result['prompts'] = []
        elif len(result['prompts']) > 1:
            raise ValueError(f"Multiple prompts require --stitch mode.\nFound {len(result['prompts'])} prompts but --stitch not enabled.\nTip: Add --stitch flag or use only one -p argument")
    
    def _validate_prompt_not_empty(self, prompt):
        """Validate that prompt is not empty."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.\nTip: Check that your prompt file exists and contains text if using $(cat filename)")
    
    def _validate_prompt_provided(self, result):
        """Ensure prompt is provided for non-stitch mode."""
        if not result['prompt']:
            raise ValueError("No prompt provided.\nTip: Provide a prompt as positional argument or use -p flag\nExample: ./image2video.py 'Your prompt here'\n         ./image2video.py -p 'Your prompt here'")

    def _default_result_dict(self):
        return {
            'images': [],
            'prompt': None,
            'prompts': [],
            'provider': 'openai',
            'width': 1280,
            'height': 720,
            'fps': 24,
            'duration': 8,
            'seed': None,
            'model': None,
            'output': None,
            'stitch': False,
            'resume': False,
            'delay': 10,
            'out-paths': [],
            'google-login': False,
            'google-login-browser': False,
            'google-clear-cache': False,
        }

    def _handle_option(self, arg, args, i, result):
        """Route argument to appropriate handler."""
        # Complex argument handlers
        if arg in ['-i', '--images']:
            return self._parse_images_arg(args, i, result)
        if arg in ['--provider']:
            return self._parse_provider_arg(args, i, result)
        if arg in ['-p', '--prompts']:
            return self._parse_prompts_arg(args, i, result)
        
        # Simple option handlers
        if arg in ['--width', '--height', '--fps', '--duration', '--seed', '--delay']:
            return self._parse_int_option(arg, args, i, result)
        if arg in ['-m', '--model', '-o', '--output']:
            return self._parse_string_option(arg, args, i, result)
        
        # Boolean flags
        if self._handle_boolean_flag(arg, result):
            return i
        
        # Special handlers
        if arg == '--out-paths':
            return self._parse_out_paths(args, i, result)
        
        # Positional prompt
        if self._is_positional_prompt(arg, result):
            result['prompt'] = arg
            return i
        
        # Unknown flag/option - error out
        if arg.startswith('-'):
            raise ValueError(
                f"Unknown argument: {arg}\n"
                "Tip: Use -h or --help to see all available options"
            )
        
        return i
    
    def _handle_boolean_flag(self, arg, result):
        """Handle boolean flag arguments."""
        boolean_flags = {
            '--stitch': 'stitch',
            '--resume': 'resume',
            '--google-login': 'google-login',
            '--google-login-browser': 'google-login-browser',
            '--google-clear-cache': 'google-clear-cache'
        }
        if arg in boolean_flags:
            result[boolean_flags[arg]] = True
            return True
        return False
    
    def _parse_out_paths(self, args, i, result):
        """Parse --out-paths argument."""
        i += 1
        while i < len(args) and not args[i].startswith('-'):
            result['out-paths'].append(args[i])
            i += 1
        return i - 1
    
    def _is_positional_prompt(self, arg, result):
        """Check if argument is a positional prompt."""
        return not arg.startswith('-') and not result['prompt'] and not result['prompts']
    """
    Custom command-line argument parser that handles shell wildcard expansion
    and provider selection for video generation.
    
    This implements a custom argument parser instead of using argparse
    because we need to handle a specific shell expansion scenario where:
    `./script.py -i ~/path/*.jpg "prompt text"`
    expands to:
    `./script.py -i file1.jpg file2.jpg file3.jpg "prompt text"`
    
    Standard argparse can't distinguish between the expanded files and the prompt
    in this scenario, so we use custom logic to intelligently separate them.
    """
    
    def __init__(self):
        """Initialize the argument parser."""
        self.available_providers = get_available_providers()
        self.help_text = self._generate_help_text()
    
    def _handle_list_providers(self) -> None:
        """Handle --list-providers flag and exit."""
        print_available_providers()
        sys.exit(0)
    
    def _handle_list_models(self, args: list) -> None:
        """Handle --list-models flag and exit."""
        providers_to_show = self._find_providers_for_list_models(args)
        print_available_models(providers_to_show)
        sys.exit(0)
    
    def _find_providers_for_list_models(self, args: list) -> str:
        """Find which providers to show models for."""
        list_models_idx = args.index('--list-models')
        
        # Check if providers name follows --list-models
        if list_models_idx + 1 < len(args) and args[list_models_idx + 1] in SUPPORTED_PROVIDERS:
            return args[list_models_idx + 1]
        
        # Otherwise, scan for --providers flag
        return self._find_providers_flag_value(args)
    
    def _find_providers_flag_value(self, args: list) -> Optional[str]:
        """Extract provider value from --provider, --provider, or -b flag."""
        for flag in ['--provider']:
            if flag in args:
                try:
                    providers_idx = args.index(flag)
                    if providers_idx + 1 < len(args):
                        return args[providers_idx + 1]
                except (ValueError, IndexError):
                    pass
        return None
    
    def _validate_providers(self, provider: str) -> None:
        """Validate that providers is supported and available."""
        if provider not in SUPPORTED_PROVIDERS:
            provider_str = "', '".join(SUPPORTED_PROVIDERS)
            raise ValueError(
                f"Unsupported provider '{provider}'. Use '{provider_str}'\n"
                "Tip: Use --list-models to see available models for each provider"
            )
        if provider not in self.available_providers:
            raise ValueError(
                f"provider '{provider}' is not available (missing API credentials)\n"
                f"Available providers: {', '.join(self.available_providers)}\n"
                "Tip: Use --list-models to see configuration requirements"
            )
    
    def _validate_stitching(self, result: Dict[str, Any]) -> None:
        """Validate stitching mode requirements."""
        if not result['prompts'] or len(result['prompts']) < MIN_STITCH_PROMPTS:
            raise ValueError(
                f"Stitching mode (--stitch) requires at least {MIN_STITCH_PROMPTS} prompts via -p/--prompts\n"
                "Example: --stitch -p 'Prompt 1' 'Prompt 2' 'Prompt 3'"
            )
    
    def _parse_provider_arg(self, args: list, i: int, result: Dict[str, Any]) -> int:
        """Parse provider argument with validation."""
        provider = self._parse_string_arg(args, i, '--provider')
        self._validate_providers(provider)
        result['provider'] = provider
        return i + 1
    
    def _parse_int_option(self, arg: str, args: list, i: int, result: Dict[str, Any]) -> int:
        """Parse integer option arguments."""
        key = arg.lstrip('-')
        result[key] = self._parse_int_arg(args, i, arg)
        return i + 1
    
    def _parse_string_option(self, arg: str, args: list, i: int, result: Dict[str, Any]) -> int:
        """Parse string option arguments."""
        key_map = {'-m': 'model', '--model': 'model', '-o': 'output', '--output': 'output'}
        key = key_map[arg]
        result[key] = self._parse_string_arg(args, i, arg)
        return i + 1
    
    def _parse_images_arg(self, args: list, i: int, result: Dict[str, Any]) -> int:
        """Parse -i/--images argument."""
        i += 1
        collected = []
        
        while i < len(args) and not args[i].startswith('-'):
            collected.append(args[i])
            i += 1
        
        if collected:
            last_arg = collected[-1]
            if self._looks_like_file(last_arg):
                result['images'].extend(collected)
            else:
                result['images'].extend(collected[:-1])
                if not result['prompt']:
                    result['prompt'] = last_arg
        
        return i - 1
    
    def _parse_prompts_arg(self, args: list, i: int, result: Dict[str, Any]) -> int:
        """Parse -p/--prompts argument."""
        i += 1
        while i < len(args) and not args[i].startswith('-'):
            result['prompts'].append(args[i])
            i += 1
        return i - 1
    
    def _looks_like_file(self, arg: str) -> bool:
        """
        Determine if an argument looks like a file path.
        
        Args:
            arg: Argument to check
            
        Returns:
            True if the argument looks like a file path
        """
        return (
            # Has a file extension (but not too many dots)
            ('.' in arg and arg.count('.') <= 2) or
            # Has common image extensions
            arg.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')) or
            # Has path separators but no newlines (files vs multi-line prompts)
            ('/' in arg and '\n' not in arg)
        )
    
    def _parse_int_arg(self, args: list, index: int, option_name: str) -> int:
        """Parse an integer argument with error handling."""
        if index + 1 >= len(args):
            raise ValueError(f"{option_name} requires a value")
        try:
            return int(args[index + 1])
        except ValueError:
            raise ValueError(f"{option_name} requires an integer value")
    
    def _parse_string_arg(self, args: list, index: int, option_name: str) -> str:
        """Parse a string argument with error handling."""
        if index + 1 >= len(args):
            raise ValueError(f"{option_name} requires a value")
        return args[index + 1]
    
    def _generate_help_text(self) -> str:
        """Generate comprehensive help text."""
        available_str = f"Available providers: {', '.join(self.available_providers)}" if self.available_providers else "No providers available (check API credentials)"
        
        return f"""usage: image2video.py [-h] [-i IMAGES ...] [--provider PROVIDER] [--width WIDTH] [--height HEIGHT]
                      [--fps FPS] [--duration DURATION] [--seed SEED] [-o OUTPUT]
                      [--stitch] [-p PROMPTS ...] prompt

Generate videos using AI models (Sora-2, Veo-3, or RunwayML) with text prompts and optional image references

positional arguments:
  prompt                Text prompt describing the video to generate (single clip mode)
                        Can also use -p/--prompt flag for single prompts

options:
  -h, --help            Show this help message and exit
  --list-providers      List all video generation providers with their availability status
  --list-models [PROVIDER]
                        List available models for all providers or a specific one
                        Example: --list-models runway
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
  -o, --output OUTPUT   Output video file path (default: <provider>_output.mp4)
  
Veo 3.1 Stitching Mode (Multi-Clip):
  --stitch              Enable seamless multi-clip stitching (Veo 3.1 only)
                        Requires 2+ prompts via -p and --provider google (or runway)
                        Example: --stitch -p 'Clip 1' 'Clip 2' 'Clip 3'
  --resume              Resume stitching from where it left off (skips existing clips)
                        Useful when generation was interrupted or credits ran out
                        Automatically detects completed clips and continues from next
  --delay SECONDS       Seconds to wait between generating clips (default: 10)
                        Helps avoid rate limiting. Set to 0 to disable.
                        Recommended: 10-30 seconds for heavy use

Google Authentication:
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
                        Removes token.pickle file from google_provider directory

provider Requirements:
  Sora-2 (OpenAI):      Set OPENAI_API_KEY environment variable (API key)
  Azure Sora:           Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT
                        Get credentials from: https://ai.azure.com/
  Veo-3:                Option 1: Use --google-login flag (automatic gcloud or OAuth)
                        Option 2: Set GOOGLE_API_KEY manually via gcloud:
                          export GOOGLE_API_KEY="$(gcloud auth application-default print-access-token)"
                        See VEO_AUTH_GUIDE.md for detailed authentication setup
  RunwayML:             Set RUNWAY_API_KEY environment variable (optional: RUNWAY_MODEL)

Examples:
  # List all providers and their availability
  image2video.py --list-providers
  
  # List available models for all providers
  image2video.py --list-models
  
  # List models for specific provider
  image2video.py --list-models runway
  
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
"""