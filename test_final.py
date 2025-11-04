#!/usr/bin/env python3

import argparse
import glob
from typing import List

def parse_image_paths(image_args) -> List[str]:
    """Parse image arguments and expand wildcards."""
    if not image_args:
        return []
    
    paths = []
    
    # Handle both list of arguments and single comma-delimited string for backward compatibility
    if isinstance(image_args, list):
        raw_paths = image_args
    else:
        # Split by comma and strip whitespace (backward compatibility)
        raw_paths = [p.strip() for p in image_args.split(',') if p.strip()]
    
    for path in raw_paths:
        if '*' in path or '?' in path:
            # Expand wildcards
            expanded = glob.glob(path)
            if not expanded:
                print(f"Warning: No files found matching pattern: {path}")
            else:
                paths.extend(expanded)
        else:
            # Regular path
            paths.append(path)
    
    return paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "prompt",
        help="Text prompt describing the video to generate"
    )
    
    parser.add_argument(
        "additional_images",
        nargs="*",
        help="Additional image files"
    )
    
    parser.add_argument(
        "-i", "--images",
        nargs="*",
        default=[],
        help="Image file paths"
    )
    
    args = parser.parse_args()
    
    # Parse image paths from -i option and expand wildcards
    image_paths = parse_image_paths(args.images)
    
    # Add any additional positional image arguments
    if args.additional_images:
        image_paths.extend(args.additional_images)
    
    print(f"Prompt: {args.prompt}")
    print(f"Images from -i: {args.images}")
    print(f"Additional images: {args.additional_images}")
    print(f"Combined image paths: {image_paths}")