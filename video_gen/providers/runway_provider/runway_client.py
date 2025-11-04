"""Deprecated module: use gen4_client.py instead.

This file remains temporarily to avoid import errors in downstream code. It
simply re-exports RunwayAPIClient from gen4_client and will be removed in a
subsequent cleanup. Please switch imports to:

    from video_gen.providers.runway_provider.gen4_client import RunwayAPIClient
"""

from .gen4_client import RunwayAPIClient  # re-export
