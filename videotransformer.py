#!/usr/bin/env python3
"""
Video Transformer CLI - Transform and edit videos using AI models

A command-line tool for applying AI-powered transformations to video files.
Supports various video editing models and providers.

Examples:
    ./videotransformer.py --video input_video.mp4 -p "Transform this into an animated cartoon"
    ./videotransformer.py --video video.mp4 -p "Change the lighting to golden hour" -v
    ./videotransformer.py --video input.mp4 -p "Add falling snow to this scene"
"""

import argparse
import os
import sys
from pathlib import Path

# Add the project root to the Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project modules
from video_gen.logger import init_library_logger
from video_gen.config import RunwayConfig
from video_gen.exceptions import AuthenticationError
from video_gen.providers.runway_aleph_functions import edit_video_with_runway_aleph


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="videotransformer.py",
        description="Transform and edit videos using AI-powered video editing models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic style transformation
  videotransformer.py --video input.mp4 -p "Transform into anime style"

  # Lighting and mood changes
  videotransformer.py --video sunset.mp4 -p "Change to dramatic stormy weather"

  # Custom output path with verbose output
  videotransformer.py --video input.mp4 -p "Make it look cyberpunk" -o cyberpunk.mp4 -v

Configuration:
  Set RUNWAY_API_KEY environment variable
  Get your API key from: https://app.runwayml.com/settings/api-keys
        """
    )

    parser.add_argument(
        "--video",
        required=True,
        help="Path to input video file to transform (required)"
    )

    parser.add_argument(
        "-p", "--prompt",
        required=True,
        help="Text prompt describing the transformation to apply"
    )

    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Output video width in pixels (default: 1280)"
    )

    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Output video height in pixels (default: 720)"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        choices=range(2, 31),
        metavar="[2-30]",
        help="Output video duration in seconds, 2-30 (default: 5)"
    )

    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducible results (optional)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output video file path (default: auto-generated)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output for detailed processing information"
    )

    return parser


def validate_video_file(video_path: str) -> None:
    """Validate that the video file exists and has a supported extension."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Check for common video extensions
    video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm')
    if not video_path.lower().endswith(video_exts):
        print(f"⚠️  Warning: '{video_path}' doesn't have a common video extension")
        print(f"   Supported formats: {', '.join(video_exts)}")


def check_credentials_and_display_header() -> RunwayConfig:
    """Check API credentials and display application header."""
    print("🎬 AI Video Transformer")
    print("==================================================")

    config = RunwayConfig.from_environment()
    if config.api_key:
        print("✅ API credentials found")
    else:
        print("❌ API credentials not found")
        print("   Please set RUNWAY_API_KEY environment variable")
        print("   Get your API key from: https://app.runwayml.com/settings/api-keys")
        sys.exit(1)

    return config


def display_transformation_info(args: argparse.Namespace) -> None:
    """Display transformation configuration."""
    print("\n🎯 Video Transformation:")
    print(f"   Input Video: {args.video}")
    prompt_preview = args.prompt[:80] + "..." if len(args.prompt) > 80 else args.prompt
    print(f"   Transformation: {prompt_preview}")

    print("\n📋 Configuration:")
    print(f"   Dimensions: {args.width}x{args.height}")
    print(f"   Duration: {args.duration} seconds")
    if args.seed:
        print(f"   Seed: {args.seed} (reproducible)")
    if args.output:
        print(f"   Output: {args.output}")
    else:
        print("   Output: Auto-generated filename")


def handle_exceptions(e: Exception) -> None:
    """Handle and display appropriate error messages for different exception types."""
    if isinstance(e, AuthenticationError):
        print("\n❌ Authentication Error:")
        print(f"   {e}")
        print("   Please check your API key configuration.")
        sys.exit(1)
    elif isinstance(e, FileNotFoundError):
        print("\n❌ File Error:")
        print(f"   {e}")
        print("   Please check that the input video file exists and is accessible.")
        sys.exit(1)
    elif "400 Client Error" in str(e) or "Bad Request" in str(e):
        print("\n❌ Invalid Request:")
        print("   The video transformation request was rejected by the server.")
        print("   This could be due to:")
        print("   • Unsupported video format or resolution")
        print("   • Video file is corrupted or unreadable")
        print("   • Prompt contains unsupported content")
        print("   • Video duration exceeds service limits")
        print("   • Invalid transformation parameters")
        print(f"\n   Technical details: {e}")
        print("\n   Suggestions:")
        print("   • Try a different video file (MP4 recommended)")
        print("   • Ensure video is under 30 seconds")
        print("   • Simplify your transformation prompt")
        print("   • Check video resolution (1280x720 recommended)")
        sys.exit(1)
    elif isinstance(e, ValueError):
        if "API key" in str(e) or "credentials" in str(e):
            print("\n❌ Configuration Error:")
            print(f"   {e}")
            print("   Please set up your API credentials.")
            sys.exit(1)
        else:
            print("\n❌ Input Error:")
            print(f"   {e}")
            sys.exit(1)
    elif "insufficient credits" in str(e).lower():
        print("\n💳 Insufficient Credits:")
        print(f"   {e}")
        print("   Please add credits to your account:")
        print("   https://app.runwayml.com/account/billing")
        sys.exit(1)
    elif "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
        print("\n⏱️  Rate Limit Exceeded:")
        print(f"   {e}")
        print("   Please wait a moment and try again.")
        sys.exit(1)
    else:
        print("\n❌ Unexpected Error:")
        print(f"   {e}")
        print("   Please check your input and try again.")
        print("   If the problem persists, please report this issue.")
        sys.exit(1)


def main() -> None:
    """Main entry point for the AI video transformer CLI."""
    try:
        # Parse arguments
        parser = create_parser()
        args = parser.parse_args()

        # Validate video file
        validate_video_file(args.video)

        # Initialize logging based on verbose flag
        init_library_logger(verbose=args.verbose, log_to_file=True)

        if args.verbose:
            print("🔧 Verbose mode enabled - showing detailed processing information")

        # Check credentials and display header
        config = check_credentials_and_display_header()

        # Display transformation info
        display_transformation_info(args)

        if args.verbose:
            print("\n📋 Detailed Configuration:")
            print(f"   Video file: {args.video}")
            print(f"   Prompt: {args.prompt}")
            print(f"   Dimensions: {args.width}x{args.height}")
            print(f"   Duration: {args.duration} seconds")
            if args.seed:
                print(f"   Seed: {args.seed}")
            print(f"   Output: {args.output or 'Auto-generated'}")

        print("\n🚀 Starting video transformation with AI...")
        print("   This may take several minutes depending on video length and complexity.")

        # Perform the video transformation
        output_path = edit_video_with_runway_aleph(
            prompt=args.prompt,
            video_path=args.video,
            width=args.width,
            height=args.height,
            duration_seconds=args.duration,
            seed=args.seed,
            out_path=args.output,
            config=config
        )

        print("\n✅ Video transformation completed successfully!")
        print(f"   Output saved to: {output_path}")

        # Display file size info if possible
        try:
            output_size = os.path.getsize(output_path)
            size_mb = output_size / (1024 * 1024)
            print(f"   File size: {size_mb:.1f} MB")

            if args.verbose:
                # Additional verbose information
                input_size = os.path.getsize(args.video)
                input_size_mb = input_size / (1024 * 1024)
                print(f"   Input file size: {input_size_mb:.1f} MB")
                print(f"   Size ratio: {size_mb/input_size_mb:.2f}x")
        except Exception:
            pass

        print("\n🎬 Your transformed video is ready!")

    except KeyboardInterrupt:
        print("\n👋 Video transformation cancelled by user")
        sys.exit(130)
    except Exception as e:
        handle_exceptions(e)


if __name__ == "__main__":
    main()