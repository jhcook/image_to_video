"""
Provider modules for video generation backends.

This package contains provider-specific implementations organized by vendor.
Each provider module is named with a '_provider' suffix to prevent package
shadowing issues with standard Python packages from PyPI.

Provider Modules:
- openai_provider: OpenAI Sora-2 video generation
  - Uses OpenAI's direct API
  - Supports multiple reference images
  - Configurable retry logic with exponential backoff
  
- azure_provider: Azure AI Foundry Sora-2 video generation
  - Uses Azure OpenAI service
  - Enterprise features and Azure security
  - Async job polling for long-running operations
  
- google_provider: Google Veo-3 video generation
  - Uses Google Vertex AI
  - Dual authentication (gcloud CLI + OAuth browser)
  - Supports video stitching for multi-segment generation
  - Browser-based OAuth login for easy authentication
  
- runway_provider: RunwayML Gen-4 video generation
  - Uses RunwayML's API
  - Multiple model variants (gen4, gen4_turbo)
  - Real-time polling for job status

All providers export their API client class and configuration class.
"""

# Import all providers
from .openai_provider import SoraAPIClient
from .azure_provider import AzureSoraAPIClient
from .google_provider import Veo3APIClient
from .runway_provider import RunwayGen4Client, RunwayVeoClient

__all__ = [
    'SoraAPIClient',
    'AzureSoraAPIClient',
    'Veo3APIClient',
    'RunwayGen4Client',
    'RunwayVeoClient',
]
