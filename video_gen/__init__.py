"""
Multi-Backend Video Generator Package

A modular Python package for generating videos using multiple AI backends:
- Sora-2 (OpenAI direct and Azure AI Foundry)
- Veo-3 (Google Vertex AI)
- RunwayML (Gen-4 models)

Architecture:
- Provider-based modular design with clear vendor separation
- All provider code isolated in providers/*_provider/ directories
- Consistent naming prevents package shadowing issues

Core Modules:
- providers/: Backend-specific implementations (openai_provider, azure_provider, 
  google_provider, runway_provider)
- config: Configuration and environment setup for all backends
- file_handler: File upload and path management utilities
- arg_parser: Advanced CLI argument parsing with shell expansion handling
- video_generator: Main orchestration and backend routing
- logger: Centralized logging infrastructure

Provider Modules:
- providers/openai_provider: OpenAI Sora-2 API client with retry logic
- providers/azure_provider: Azure AI Foundry Sora-2 client
- providers/google_provider: Google Veo-3 client with OAuth2 browser auth
- providers/runway_provider: RunwayML Gen-4 API client
"""

__version__ = "2.1.0"
__author__ = "Generated with assistance from GitHub Copilot"

from .video_generator import generate_video_with_sora2, generate_video_with_veo3, generate_video_with_runway, generate_video
from .config import SoraConfig, Veo3Config, RunwayConfig, get_available_models, get_default_model, print_available_models
from .logger import init_library_logger, get_library_logger

__all__ = [
    'generate_video_with_sora2', 
    'generate_video_with_veo3',
    'generate_video_with_runway',
    'generate_video',
    'SoraConfig', 
    'Veo3Config',
    'RunwayConfig',
    'get_available_models',
    'get_default_model',
    'print_available_models',
    'init_library_logger',
    'get_library_logger'
]