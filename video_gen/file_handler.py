"""
File handling utilities for Sora video generation.

Handles file uploads, MIME type detection, and path processing.
"""

import mimetypes
import glob
from pathlib import Path
from typing import List, Iterable, Union

try:
    from openai import OpenAI
except ImportError:
    # Will be handled at runtime
    OpenAI = None

from .config import SoraConfig
from .logger import get_library_logger


class FileHandler:
    """Handles file operations for Sora video generation."""
    
    def __init__(self, config: SoraConfig, openai_client):
        """
        Initialize file handler.
        
        Args:
            config: Sora configuration
            openai_client: OpenAI client instance
        """
        self.config = config
        self.logger = get_library_logger()
        self.client = openai_client
    
    def guess_file_purpose(self, mime_type: str) -> str:
        """
        Determine the appropriate OpenAI file purpose based on MIME type.
        
        OpenAI requires different 'purpose' values when uploading files:
        - 'vision': For image files used in vision tasks (Sora image references)
        - 'assistants': Generic purpose for other file types
        
        Args:
            mime_type: The MIME type of the file (e.g., 'image/png', 'text/plain')
            
        Returns:
            The appropriate purpose string for OpenAI file upload
        """
        if any(mime_type.startswith(prefix) for prefix in self.config.supported_image_mime_prefixes):
            return "vision"
        return "assistants"
    
    def upload_files(self, file_paths: Iterable[Union[str, Path]]) -> List[str]:
        """
        Upload multiple files to OpenAI and return their file IDs.
        
        Args:
            file_paths: An iterable of file paths to upload
            
        Returns:
            A list of OpenAI file IDs corresponding to the uploaded files
            
        Raises:
            FileNotFoundError: If any input file doesn't exist
            ValueError: If MIME type cannot be determined for any file
        """
        file_ids: List[str] = []
        file_paths_list = list(file_paths)
        
        self.logger.info(f"Uploading {len(file_paths_list)} files to OpenAI")
        
        for path in file_paths_list:
            path_obj = Path(path)
            
            # Validate file exists
            if not path_obj.exists():
                self.logger.error(f"File not found: {path_obj}")
                raise FileNotFoundError(f"Input file not found: {path_obj}")
            
            # Determine MIME type for proper handling
            mime_type, _ = mimetypes.guess_type(str(path_obj))
            if not mime_type:
                self.logger.error(f"Could not determine MIME type: {path_obj}")
                raise ValueError(f"Could not determine MIME type for {path_obj}")
            
            # Get appropriate upload purpose
            purpose = self.guess_file_purpose(mime_type)
            self.logger.debug(f"Uploading {path_obj.name} (mime={mime_type}, purpose={purpose})")
            
            # Upload file to OpenAI with error handling
            try:
                with path_obj.open("rb") as file_handle:
                    uploaded = self.client.files.create(file=file_handle, purpose=purpose)
                file_ids.append(uploaded.id)
                self.logger.info(f"Uploaded {path_obj.name} -> {uploaded.id}")
            except Exception as e:
                self._handle_upload_error(e, path_obj.name)
        
        self.logger.info(f"All {len(file_ids)} files uploaded successfully")
        return file_ids
    
    def _handle_upload_error(self, error: Exception, filename: str) -> None:
        """Handle file upload errors with user-friendly messages."""
        from .exceptions import AuthenticationError
        import openai
        
        error_str = str(error).lower()
        
        # Handle SSL/Connection errors
        if "ssl" in error_str or "certificate" in error_str or isinstance(error, (openai.APIConnectionError,)):
            print("\n" + "="*60)
            print("🔒 SSL/Connection Error")
            print("="*60)
            print(f"Failed to upload '{filename}' due to connection issues.")
            print("\n💡 Quick fixes:")
            print("   • Check your internet connection")
            print("   • Try running: pip install --upgrade certifi")
            print("   • If using corporate network, check proxy settings")
            print("   • Temporarily try a different network (mobile hotspot)")
            print("="*60)
            raise AuthenticationError("SSL/Connection error during file upload")
        
        # Handle authentication errors
        elif isinstance(error, openai.AuthenticationError) or "authentication" in error_str:
            print("\n" + "="*60)
            print("🔑 Authentication Error")
            print("="*60)
            print(f"Failed to upload '{filename}' - invalid API key.")
            print("\n💡 Check your OpenAI API key:")
            print("   • Verify OPENAI_API_KEY is set correctly")
            print("   • Ensure the key hasn't expired")
            print("   • Visit: https://platform.openai.com/api-keys")
            print("="*60)
            raise AuthenticationError("Invalid OpenAI API key")
        
        # Handle rate limiting
        elif isinstance(error, openai.RateLimitError) or "rate limit" in error_str:
            print("\n" + "="*60)
            print("⏳ Rate Limit Error")
            print("="*60)
            print(f"Upload rate limited for '{filename}'. Please wait and try again.")
            print("="*60)
            raise error
        
        # Handle other OpenAI errors
        elif hasattr(error, 'response') or isinstance(error, openai.APIError):
            print(f"\n❌ API error uploading '{filename}': {error}")
            raise error
        
        # Handle unexpected errors
        else:
            print(f"\n❌ Unexpected error uploading '{filename}': {error}")
            raise error
    
    @staticmethod
    def expand_image_paths(image_args: Union[List[str], str, None]) -> List[str]:
        """
        Parse and expand image file paths from various input formats.
        
        This function handles multiple input formats for specifying image files:
        - List of file paths (from command-line argument parsing)
        - Comma-delimited string (backward compatibility)
        - Wildcard patterns (*, ?) which get expanded using glob
        
        Args:
            image_args: Either a list of strings or a single comma-delimited string
                       containing file paths and/or wildcard patterns
                       
        Returns:
            A list of resolved file paths with wildcards expanded
        """
        if not image_args:
            return []
        
        paths = []
        
        # Handle both list of arguments and single comma-delimited string
        if isinstance(image_args, list):
            raw_paths = image_args
        else:
            # Split by comma and strip whitespace (backward compatibility mode)
            raw_paths = [p.strip() for p in image_args.split(',') if p.strip()]
        
        for path in raw_paths:
            if '*' in path or '?' in path:
                # Expand wildcard patterns using glob
                expanded = glob.glob(path)
                if expanded:
                    paths.extend(expanded)
            else:
                # Regular file path - add as-is
                paths.append(path)
        
        return paths