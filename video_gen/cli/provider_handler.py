"""
Provider-specific argument parsing utilities.

This module handles provider detection and model-related argument parsing.
"""

import sys
from typing import List, Optional, cast

from ..config import print_available_models, print_available_providers, VideoProvider


# Supported provider Names
PROVIDER_OPENAI = 'openai'
PROVIDER_AZURE = 'azure'
PROVIDER_GOOGLE = 'google'
PROVIDER_RUNWAY = 'runway'
SUPPORTED_PROVIDERS = [PROVIDER_OPENAI, PROVIDER_AZURE, PROVIDER_GOOGLE, PROVIDER_RUNWAY]


class ProviderHandler:
    """Handles provider-specific CLI operations."""
    
    def handle_list_providers(self) -> None:
        """Handle --list-providers command."""
        print_available_providers()
        sys.exit(0)
    
    def handle_list_models(self, args: List[str]) -> None:
        """Handle --list-models command with optional provider filtering."""
        provider_str = self._find_providers_for_list_models(args)
        # Convert string to VideoProvider type if valid, otherwise use None for all providers
        provider = cast(VideoProvider, provider_str) if provider_str in SUPPORTED_PROVIDERS else None
        print_available_models(provider)
        sys.exit(0)
    
    def _find_providers_for_list_models(self, args: List[str]) -> Optional[str]:
        """Find which provider to show models for, or None for all providers."""
        # Check if there's a provider specified after --list-models
        list_models_idx = args.index('--list-models')
        
        # Check if next argument is a provider name
        if list_models_idx + 1 < len(args) and args[list_models_idx + 1] in SUPPORTED_PROVIDERS:
            provider = args[list_models_idx + 1]
            # Type cast to VideoProvider since we validated it's in SUPPORTED_PROVIDERS
            return provider
        
        # Check if --provider flag is present elsewhere
        return self._find_providers_flag_value(args)
    
    def _find_providers_flag_value(self, args: List[str]) -> Optional[str]:
        """Find the value of --provider flag if present."""
        for flag in ['--provider', '-b']:  # -b is legacy alias
            if flag in args:
                try:
                    providers_idx = args.index(flag)
                    if providers_idx + 1 < len(args):
                        return args[providers_idx + 1]
                except ValueError:
                    continue
        return None
    
    def validate_provider(self, provider: str) -> None:
        """Validate that a provider is supported."""
        if provider not in SUPPORTED_PROVIDERS:
            supported_list = ', '.join(SUPPORTED_PROVIDERS)
            raise ValueError(f"Unsupported provider '{provider}'. Supported: {supported_list}")
    
    def get_default_provider(self) -> str:
        """Get the default provider."""
        return PROVIDER_OPENAI