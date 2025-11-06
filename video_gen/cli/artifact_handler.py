"""
Artifact management CLI handlers.

This module handles the CLI operations for listing and downloading video artifacts.
"""

import sys
from typing import List, Optional

from ..artifact_manager import ArtifactManager


class ArtifactCLIHandler:
    """Handles CLI commands for artifact management."""
    
    def __init__(self):
        """Initialize the artifact CLI handler."""
        self.artifact_manager = ArtifactManager()
    
    def handle_list_artifacts(self, argv: List[str]) -> None:
        """Handle --list-artifacts command with optional filtering."""
        # Parse filtering options
        provider_filter = self._extract_flag_value(argv, '--provider')
        status_filter = self._extract_flag_value(argv, '--status')
        
        # Print artifacts table with filters
        self.artifact_manager.print_artifacts_table(
            provider=provider_filter,
            status=status_filter
        )
        sys.exit(0)
    
    def handle_download(self, argv: List[str]) -> None:
        """Handle --download TASK_ID command with optional parameters."""
        # Find task ID
        download_idx = self._find_flag_index(argv, '--download')
        if download_idx == -1 or download_idx + 1 >= len(argv):
            print("Error: --download requires a task ID")
            sys.exit(1)
        
        task_id = argv[download_idx + 1]
        
        # Parse optional parameters
        output_path = self._extract_flag_value(argv, '--output')
        force = '--force' in argv
        
        # Download the artifact
        try:
            success = self.artifact_manager.download_artifact(
                task_id=task_id,
                output_path=output_path,
                force=force
            )
            if success:
                print(f"✅ Downloaded: {output_path or 'default location'}")
            else:
                print(f"❌ Download failed for task {task_id}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Download error: {e}")
            sys.exit(1)
        
        sys.exit(0)
    
    def _extract_flag_value(self, argv: List[str], flag: str) -> Optional[str]:
        """Extract the value following a flag, if present."""
        flag_idx = self._find_flag_index(argv, flag)
        if flag_idx != -1 and flag_idx + 1 < len(argv):
            next_arg = argv[flag_idx + 1]
            # Make sure the next argument isn't another flag
            if not next_arg.startswith('-'):
                return next_arg
        return None
    
    def _find_flag_index(self, argv: List[str], flag: str) -> int:
        """Find the index of a flag in argv, return -1 if not found."""
        try:
            return argv.index(flag)
        except ValueError:
            return -1