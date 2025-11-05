#!/usr/bin/env python3

"""
Multi-Backend Video Generator CLI

A modular command-line interface for generating videos using multiple AI backends:
- Sora-2 (OpenAI)
- Veo-3 (Google)
- Runway (Runway ML)

This script uses a modular architecture for better maintainability and testability.

Usage:
    ./image2video.py "Your prompt here"
    ./image2video.py -i images/*.jpg "Create a video tour"
    ./image2video.py --backend veo3 "Generate with Google Veo-3"
    ./image2video.py --backend runway "Generate with Runway ML"
    
For detailed usage information, run:
    ./image2video.py --help
"""

import re
from collections import defaultdict
from pathlib import Path

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the package to the path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from video_gen.config import create_config_for_backend, get_available_backends
from video_gen.video_generator import generate_video
from video_gen.file_handler import FileHandler
from video_gen.arg_parser import SoraArgumentParser
from video_gen.logger import init_library_logger


def _check_backends_and_display_header():
    """Check available backends and display application header."""
    print("🎬 Multi-Backend Video Generator")
    print("=" * 50)
    
    available_backends = get_available_backends()
    if not available_backends:
        print("❌ No video generation backends are available!")
        print("   Please set up API credentials:")
        print("   - For Sora-2: export OPENAI_API_KEY=your_key")
        print("   - For Veo-3: export GOOGLE_API_KEY=your_key")
        print("   - For Runway: export RUNWAY_API_KEY=your_key")
        sys.exit(1)
    
    print(f"📋 Available backends: {', '.join(available_backends)}")
    return available_backends


def _process_images_and_display_config(args, config):
    """Process image paths and display configuration."""
    backend = args['backend']
    prompt = args['prompt']
    images = args['images']
    stitch = args.get('stitch', False)
    
    print(f"🎯 Using backend: {backend}")
    
    # In stitch mode, prompt is None and prompts list is used instead
    if not stitch:
        if prompt is not None:
            print(f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        else:
            print("📝 No prompt provided.")
    
    file_paths = []
    if images:
        file_handler = FileHandler(config, None)
        file_paths = file_handler.expand_image_paths(images)
        print(f"🖼️  Found {len(file_paths)} image file(s)")
    
    print("\n📋 Configuration:")
    print(f"   Backend: {backend}")
    print(f"   Dimensions: {args['width']}x{args['height']} @ {args['fps']}fps")
    print(f"   Duration: {args['duration']} seconds")
    if args['seed']:
        print(f"   Seed: {args['seed']} (reproducible)")
    
    if not stitch:
        print(f"   Output: {args['output']}")
    
    if file_paths:
        print(f"\n🖼️  Using {len(file_paths)} image reference(s):")
        for i, path in enumerate(file_paths, 1):
            print(f"   {i:2d}. {path}")
    else:
        print("\n📝 Text-only generation (no image references)")
    
    print("\n🚀 Starting video generation...")
    print("=" * 50)
    
    return file_paths, backend, prompt


def _handle_exceptions(e):
    """Handle and display appropriate error messages for different exception types."""
    error_msg = str(e)
    
    # Check if it's an authentication/credential error
    if "Authentication failed" in error_msg or "API credentials" in error_msg or "API key" in error_msg:
        print(f"❌ {error_msg}")
        sys.exit(1)
    
    # Configuration errors
    if isinstance(e, ValueError):
        print(f"❌ Configuration error: {e}")
        print("   Check your environment variables and API credentials")
        sys.exit(1)
    
    # File errors
    elif isinstance(e, FileNotFoundError):
        print(f"❌ File error: {e}")
        print("   Check that all image files exist and are accessible")
        sys.exit(1)
    
    # Generic errors with troubleshooting tips
    else:
        print(f"❌ Unexpected error: {e}")
        print("\nTroubleshooting tips:")
        print("- Check your API credentials are valid and have model access")
        print("- Verify all image files exist and are valid formats")
        print("- Try again later if the service is at capacity")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _handle_google_cache_clearing():
    """Handle Google credential cache clearing."""
    from video_gen.providers.google_provider.auth import clear_cached_credentials
    print("🧹 Clearing Google OAuth cached credentials...")
    clear_cached_credentials()
    print("\n💡 Next time you use --google-login or --google-login-browser,")
    print("   you'll be prompted to authenticate again.")
    sys.exit(0)


def _handle_google_authentication(args):
    """Handle Google authentication flow (gcloud or OAuth)."""
    if args.get('backend') != 'veo3':
        return
    
    if not (args.get('google-login') or args.get('google-login-browser')):
        return
    
    from video_gen.providers.google_provider.auth import get_google_credentials
    
    # Determine which method to use
    force_browser = args.get('google-login-browser')
    message = "🔑 Authenticating with Google Cloud (browser OAuth)..." if force_browser else "🔑 Authenticating with Google Cloud..."
    print(message)
    
    try:
        # use_gcloud=False forces browser OAuth, use_gcloud=True tries gcloud first
        creds = get_google_credentials(use_gcloud=not force_browser)
        # Set the token as environment variable for this session
        os.environ['GOOGLE_API_KEY'] = creds.token
        print("✅ Google authentication complete.")
        
        # Continue with video generation if prompt(s) provided, otherwise exit
        if not args.get('prompt') and not args.get('prompts'):
            print("💡 Credentials set for this session (valid for ~1 hour)")
            print("   You can now run video generation commands.")
            sys.exit(0)
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)


def _parse_arguments():
    """Parse command-line arguments and handle early exits."""
    parser = SoraArgumentParser()
    try:
        return parser.parse_arguments()
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)


def _route_to_workflow(args, config, file_paths):
    """Route to appropriate workflow (stitching or normal mode)."""
    backend = args['backend']
    prompt = args['prompt']
    model = args.get('model')
    
    # Resolve model from args or config default
    if not model and backend == "runway":
        # Get default model from config (which reads RUNWAY_MODEL env var)
        model = getattr(config, 'default_model', None)
    
    # Check if stitching mode is enabled
    # Support both veo3 backend and runway backend with veo models
    is_veo_model = (backend == "veo3") or (backend == "runway" and model and model.startswith("veo"))
    
    if is_veo_model and args.get("stitch"):
        _run_stitching_mode(args, config, file_paths, backend)
    else:
        _run_normal_mode(args, config, file_paths, backend, prompt)


def main():
    """Main entry point for the CLI application."""
    # Initialize logging (writes to logs/ directory and console)
    init_library_logger(verbose=True, log_to_file=True)
    
    # Parse arguments first (handles --help and --list-models before checking credentials)
    args = _parse_arguments()

    # Handle Google credential cache clearing
    if args.get('google-clear-cache'):
        _handle_google_cache_clearing()

    # Google authentication flow (gcloud or OAuth)
    _handle_google_authentication(args)
    
    _check_backends_and_display_header()
    
    try:
        # args already parsed above, now create config
        config = create_config_for_backend(args['backend'])
        config.validate()

        file_paths, _, _ = _process_images_and_display_config(args, config)

        _route_to_workflow(args, config, file_paths)

    except KeyboardInterrupt:
        print("\n👋 Video generation cancelled by user")
        sys.exit(130)
    except RuntimeError as e:
        if "Operation cancelled by user" in str(e):
            print("👋 Video generation cancelled by user")
            sys.exit(130)
        else:
            raise
    except Exception as e:
        _handle_exceptions(e)


def _build_image_keyword_groups(file_paths):
    """Build image keyword groups and a compiled regex for prompt filename matching.
    Returns (image_groups, all_keywords, keyword_pattern).
    """
    image_groups = defaultdict(list)
    all_keywords = set()

    for img_path in file_paths:
        filename = Path(img_path).stem.lower()
        keyword = re.sub(r'\d+$', '', filename)  # Remove trailing numbers
        if keyword:
            image_groups[keyword].append(img_path)
            all_keywords.add(keyword)

    keyword_pattern = None
    if all_keywords:
        alternation = "|".join(sorted((re.escape(k) for k in all_keywords), key=len, reverse=True))
        keyword_pattern = re.compile(rf"(?:^|_)({alternation})(?=$|_|\d)")
    return image_groups, all_keywords, keyword_pattern


def _match_by_filename(prompt_item, keyword_pattern, image_groups):
    """Try matching images based on keyword found in prompt filename (tuple input)."""
    if not isinstance(prompt_item, tuple) or keyword_pattern is None:
        return []
    _, prompt_filename = prompt_item
    m = keyword_pattern.search(Path(prompt_filename).stem.lower())
    if m:
        key = m.group(1)
        return image_groups.get(key, [])
    return []


def _match_by_prompt_text(prompt, all_keywords, image_groups):
    """Match images by searching known keywords inside the prompt text."""
    matches = []
    prompt_lower = prompt.lower() if isinstance(prompt, str) else ""
    for key in all_keywords:
        if key in prompt_lower:
            matches.extend(image_groups[key])
    return matches


def _match_images_for_prompt(prompt_item, image_groups, all_keywords, keyword_pattern, file_paths):
    """Match images for a single prompt using filename and text matching strategies."""
    prompt = prompt_item[0] if isinstance(prompt_item, tuple) else prompt_item
    matched_images = _match_by_filename(prompt_item, keyword_pattern, image_groups)
    if not matched_images:
        matched_images = _match_by_prompt_text(prompt, all_keywords, image_groups)
    if not matched_images:
        matched_images = file_paths[:]
    return matched_images


def _distribute_images_to_clips(file_paths, prompts, image_groups_spec=None):
    """
    Intelligently distribute reference images among clips.
    
    Supports three methods:
    1. Manual groups via spec (preferred): [[img1, img2], [img3, img4], ...]
    2. Filename pattern matching: Groups by keywords in filenames
    3. Prompt filename matching: Matches prompt filenames (fr_foyer1.txt) with image names
    
    Args:
        file_paths: List of image file paths
        prompts: List of prompt strings (one per clip) or list of tuples (prompt, filename)
        image_groups_spec: Optional list of lists specifying exact image groups per clip
        
    Returns:
        List of image lists, one per clip
        
    Examples:
        # Method 1: Manual specification
        --image-groups "foyer1.png,foyer2.png" "living1.png,living2.png" "kitchen1.png"
        
        # Method 2: Automatic keyword matching (filename-based)
        Images: foyer1.png, living1.png, kitchen1.png
        Auto-groups by: foyer*, living*, kitchen*
        
        # Method 3: Prompt filename matching
        Prompts from: fr_foyer1.txt, fr_living1.txt
        Matches images: foyer*.png, living*.png
    """
    if not file_paths or not prompts:
        return None
    
    # Method 1: Manual specification (if provided)
    if image_groups_spec:
        return _validate_and_log_distribution(image_groups_spec, prompts)
    
    image_groups, all_keywords, keyword_pattern = _build_image_keyword_groups(file_paths)
    
    # Method 3: Try matching prompt filenames with image keywords
    result = []
    for prompt_item in prompts:
        matched_images = _match_images_for_prompt(
            prompt_item, image_groups, all_keywords, keyword_pattern, file_paths
        )
        result.append(matched_images)
    
    return _validate_and_log_distribution(result, prompts)


def _validate_and_log_distribution(image_lists, prompts):
    """Log the image distribution for user visibility."""
    print("\n📸 Image distribution per clip:")
    for i, (prompt_item, images) in enumerate(zip(prompts, image_lists), 1):
        # Handle tuple prompts
        prompt = prompt_item[0] if isinstance(prompt_item, tuple) else prompt_item
        prompt_preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
        
        img_count = len(images)
        img_names = [Path(img).stem for img in images[:3]]
        img_preview = ", ".join(img_names)
        if img_count > 3:
            img_preview += f", ... ({img_count} total)"
        
        print(f"   Clip {i}: {img_count} images ({img_preview})")
        print(f"           Prompt: {prompt_preview}")
    print()
    
    return image_lists


def _run_stitching_mode(args, config, file_paths, backend):
    """Run Veo 3.1 stitching flow with multiple prompts/clips.
    
    Supports both Google Veo (veo3 backend) and RunwayML Veo (runway backend with veo* models).
    """
    from video_gen.video_generator import generate_video_sequence_with_veo3_stitching

    prompts = args["prompts"]  # List of prompts for each clip
    model = args["model"] or config.default_model

    # Intelligently distribute images among clips based on filename patterns
    file_paths_list = _distribute_images_to_clips(file_paths, prompts) if file_paths else None
    out_paths = args.get("out_paths")
    resume = args.get("resume", False)
    
    # Determine provider name for display
    provider_name = "Google Veo 3.1" if backend == "veo3" else f"RunwayML {model}"

    print(f"\n🎬 Stitching Mode: Generating {len(prompts)} clips with seamless transitions")
    print(f"   Provider: {provider_name}")
    print(f"   Model: {model}")
    print(f"   Each clip: {args['width']}x{args['height']}, {args['duration']}s")
    print(f"   Reference images: {len(file_paths)} per clip" if file_paths else "   No reference images")
    if resume:
        print("   Resume: ✅ Enabled (will skip existing clips)")
    print("\n📝 Prompts:")
    for i, p in enumerate(prompts, 1):
        print(f"   {i}. {p[:80]}{'...' if len(p) > 80 else ''}")
    print()

    outputs = generate_video_sequence_with_veo3_stitching(
        prompts=prompts,
        file_paths_list=file_paths_list,
        width=args["width"],
        height=args["height"],
        duration_seconds=args["duration"],
        seed=args["seed"],
        out_paths=out_paths,
        config=config,
        model=model,
        delay_between_clips=args["delay"],
        backend=backend,
        resume=resume
    )
    print("=" * 50)
    print(f"🎉 Success! {len(outputs)} stitched clips generated:")
    for i, path in enumerate(outputs, 1):
        print(f"   {i}. {path}")
    print("\n💡 Tip: Concatenate clips with ffmpeg:")
    print(f"   ffmpeg -i \"concat:{'|'.join(outputs)}\" -c copy final_stitched.mp4")


def _run_normal_mode(args, config, file_paths, backend, prompt):
    """Run the standard single-video generation flow."""
    output_path = generate_video(
        prompt=prompt,
        file_paths=file_paths,
        backend=backend,
        model=args['model'],
        width=args['width'],
        height=args['height'],
        fps=args['fps'],
        duration_seconds=args['duration'],
        seed=args['seed'],
        out_path=args['output'],
        config=config
    )
    print("=" * 50)
    print(f"🎉 Success! Video generated: {output_path}")


if __name__ == "__main__":
    main()
