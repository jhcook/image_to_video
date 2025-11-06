"""
Artifact management for video generation results.

Provides functionality to:
- Track generated video artifacts across providers
- List available downloads
- Resume interrupted downloads
- Download specific artifacts by ID
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests

from .logger import get_library_logger


@dataclass
class VideoArtifact:
    """Represents a generated video artifact."""
    task_id: str
    provider: str
    model: str
    prompt: str
    status: str  # 'generated', 'downloaded', 'failed'
    created_at: str
    download_url: Optional[str] = None
    local_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ArtifactManager:
    """Manages video generation artifacts and downloads."""
    
    def __init__(self, artifacts_dir: str = "artifacts"):
        """
        Initialize the artifact manager.
        
        Args:
            artifacts_dir: Directory to store artifact metadata and downloads
        """
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)
        
        self.metadata_file = self.artifacts_dir / "artifacts.json"
        self.downloads_dir = self.artifacts_dir / "downloads"
        self.downloads_dir.mkdir(exist_ok=True)
        
        self.logger = get_library_logger()
        self._load_artifacts()
    
    def _load_artifacts(self) -> None:
        """Load artifacts from metadata file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.artifacts = {
                        k: VideoArtifact(**v) for k, v in data.items()
                    }
            else:
                self.artifacts = {}
        except Exception as e:
            self.logger.warning(f"Failed to load artifacts: {e}")
            self.artifacts = {}
    
    def _save_artifacts(self) -> None:
        """Save artifacts to metadata file."""
        try:
            data = {
                k: asdict(v) for k, v in self.artifacts.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save artifacts: {e}")
    
    def add_artifact(
        self,
        task_id: str,
        provider: str,
        model: str,
        prompt: str,
        download_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VideoArtifact:
        """
        Add a new video artifact.
        
        Args:
            task_id: Unique task identifier
            provider: Provider name (openai, runway, google)
            model: Model used for generation
            prompt: Generation prompt
            download_url: URL to download the video
            metadata: Additional metadata
            
        Returns:
            Created VideoArtifact
        """
        artifact = VideoArtifact(
            task_id=task_id,
            provider=provider,
            model=model,
            prompt=prompt,
            status='generated',
            created_at=datetime.now().isoformat(),
            download_url=download_url,
            metadata=metadata or {}
        )
        
        self.artifacts[task_id] = artifact
        self._save_artifacts()
        
        self.logger.info(f"Added artifact: {task_id} ({provider})")
        return artifact
    
    def update_artifact_status(
        self,
        task_id: str,
        status: str,
        local_path: Optional[str] = None
    ) -> None:
        """
        Update artifact status and local path.
        
        Args:
            task_id: Task identifier
            status: New status
            local_path: Local file path if downloaded
        """
        if task_id in self.artifacts:
            self.artifacts[task_id].status = status
            if local_path:
                self.artifacts[task_id].local_path = local_path
            self._save_artifacts()
    
    def update_download_url(self, task_id: str, download_url: str) -> None:
        """
        Update the download URL for an artifact.
        
        Args:
            task_id: Task identifier
            download_url: URL to download the video
        """
        if task_id in self.artifacts:
            self.artifacts[task_id].download_url = download_url
            self._save_artifacts()
            self.logger.info(f"Updated download URL for {task_id}")
    
    def list_artifacts(
        self,
        provider: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[VideoArtifact]:
        """
        List available artifacts with optional filtering.
        
        Args:
            provider: Filter by provider
            status: Filter by status
            
        Returns:
            List of matching artifacts
        """
        artifacts = list(self.artifacts.values())
        
        if provider:
            artifacts = [a for a in artifacts if a.provider == provider]
        
        if status:
            artifacts = [a for a in artifacts if a.status == status]
        
        # Sort by creation time (newest first)
        artifacts.sort(key=lambda a: a.created_at, reverse=True)
        return artifacts
    
    def get_artifact(self, task_id: str) -> Optional[VideoArtifact]:
        """Get artifact by task ID."""
        return self.artifacts.get(task_id)
    
    def download_artifact(
        self,
        task_id: str,
        output_path: Optional[str] = None,
        force: bool = False
    ) -> Optional[str]:
        """
        Download a video artifact.
        
        Args:
            task_id: Task identifier
            output_path: Custom output path (optional)
            force: Force re-download even if file exists
            
        Returns:
            Path to downloaded file, or None if failed
        """
        artifact = self.get_artifact(task_id)
        if not artifact:
            self.logger.error(f"Artifact not found: {task_id}")
            return None
        
        if not artifact.download_url:
            self.logger.error(f"No download URL for artifact: {task_id}")
            return None
        
        # Determine output path
        if not output_path:
            filename = f"{artifact.provider}_{task_id}_{artifact.model}.mp4"
            output_path = str(self.downloads_dir / filename)
        
        output_file = Path(output_path)
        
        # Check if already downloaded
        if output_file.exists() and not force:
            if artifact.status == 'downloaded':
                self.logger.info(f"Already downloaded: {output_path}")
                return str(output_path)
        
        # Download the file
        try:
            self.logger.info(f"Downloading {task_id} from {artifact.provider}...")
            
            # Handle provider-specific download logic
            if artifact.provider == 'openai':
                success = self._download_openai_video(artifact, output_path)
            elif artifact.provider == 'runway':
                success = self._download_runway_video(artifact, output_path)
            elif artifact.provider == 'google':
                success = self._download_google_video(artifact, output_path)
            else:
                success = self._download_generic_video(artifact, output_path)
            
            if success:
                self.update_artifact_status(task_id, 'downloaded', str(output_path))
                self.logger.info(f"✅ Downloaded: {output_path}")
                return str(output_path)
            else:
                self.logger.error(f"❌ Download failed: {task_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Download error for {task_id}: {e}")
            return None
    
    def _download_openai_video(self, artifact: VideoArtifact, output_path: str) -> bool:
        """Download OpenAI video using httpx."""
        try:
            import httpx
            import os
            
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Accept": "video/*"
            }
            
            with httpx.Client(timeout=300) as client:
                response = client.get(artifact.download_url, headers=headers)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                
                return True
                
        except Exception as e:
            self.logger.error(f"OpenAI download failed: {e}")
            return False
    
    def _download_runway_video(self, artifact: VideoArtifact, output_path: str) -> bool:
        """Download RunwayML video."""
        try:
            response = requests.get(
                artifact.download_url,
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Runway download failed: {e}")
            return False
    
    def _download_google_video(self, artifact: VideoArtifact, output_path: str) -> bool:
        """Download Google VEO video."""
        return self._download_generic_video(artifact, output_path)
    
    def _download_generic_video(self, artifact: VideoArtifact, output_path: str) -> bool:
        """Generic video download."""
        try:
            response = requests.get(
                artifact.download_url,
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Generic download failed: {e}")
            return False
    
    def print_artifacts_table(
        self,
        provider: Optional[str] = None,
        status: Optional[str] = None
    ) -> None:
        """Print a formatted table of artifacts."""
        artifacts = self.list_artifacts(provider, status)
        
        if not artifacts:
            print("No artifacts found.")
            return
        
        print("\n" + "="*100)
        print("📦 Available Video Artifacts")
        print("="*100)
        print(f"{'Task ID':<20} {'Provider':<10} {'Model':<15} {'Status':<12} {'Created':<20} {'Prompt':<30}")
        print("-"*100)
        
        for artifact in artifacts:
            created = artifact.created_at[:19].replace('T', ' ')  # Remove timezone and microseconds
            prompt = artifact.prompt[:27] + "..." if len(artifact.prompt) > 30 else artifact.prompt
            
            print(f"{artifact.task_id:<20} {artifact.provider:<10} {artifact.model:<15} "
                  f"{artifact.status:<12} {created:<20} {prompt:<30}")
        
        print("="*100)
        print(f"Total: {len(artifacts)} artifacts")
        
        # Show download instructions
        print("\n💡 Download commands:")
        print("  List all:     python -m video_gen.artifact_manager list")
        print("  Download:     python -m video_gen.artifact_manager download <task_id>")
        print("  Filter:       python -m video_gen.artifact_manager list --provider runway")


# Global artifact manager instance
_artifact_manager = None

def get_artifact_manager() -> ArtifactManager:
    """Get global artifact manager instance."""
    global _artifact_manager
    if _artifact_manager is None:
        _artifact_manager = ArtifactManager()
    return _artifact_manager


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Video artifact management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List artifacts')
    list_parser.add_argument('--provider', help='Filter by provider')
    list_parser.add_argument('--status', help='Filter by status')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download artifact')
    download_parser.add_argument('task_id', help='Task ID to download')
    download_parser.add_argument('--output', help='Output file path')
    download_parser.add_argument('--force', action='store_true', help='Force re-download')
    
    args = parser.parse_args()
    manager = get_artifact_manager()
    
    if args.command == 'list':
        manager.print_artifacts_table(args.provider, args.status)
    elif args.command == 'download':
        result = manager.download_artifact(args.task_id, args.output, args.force)
        if result:
            print(f"✅ Downloaded: {result}")
        else:
            print("❌ Download failed")
            sys.exit(1)
    else:
        parser.print_help()