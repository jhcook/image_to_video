"""
Common retry utilities for API clients.

Provides shared retry logic with exponential backoff to avoid code duplication
across provider implementations.
"""

import time
import random
import logging
from typing import Protocol


class RetryConfig(Protocol):
    """Protocol for config objects that support retry settings."""
    retry_base_delay: int
    retry_max_delay: int
    retry_jitter_percent: float


def calculate_retry_delay(
    retry_count: int,
    base_delay: int = 30,
    max_delay: int = 300,
    jitter_percent: float = 0.2
) -> float:
    """
    Calculate exponential backoff delay with jitter.
    
    Args:
        retry_count: Current retry attempt number (1-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        jitter_percent: Percentage of jitter to add (±)
        
    Returns:
        Calculated delay in seconds with jitter applied
    """
    # Exponential backoff with cap at attempt 4 (2^4 = 16x base)
    delay = min(
        base_delay * (2 ** min(retry_count - 1, 4)),
        max_delay
    )
    
    # Add random jitter to avoid thundering herd
    jitter = delay * jitter_percent * (random.random() - 0.5)
    actual_delay = max(1, delay + jitter)
    
    return actual_delay


def handle_capacity_retry(
    retry_count: int,
    config: RetryConfig,
    logger: logging.Logger
) -> None:
    """
    Handle capacity retry with exponential backoff and user cancellation.
    
    Args:
        retry_count: Current retry attempt number
        config: Configuration object with retry settings
        logger: Logger instance for output
        
    Raises:
        RuntimeError: If user cancels during backoff (Ctrl+C)
    """
    actual_delay = calculate_retry_delay(
        retry_count,
        config.retry_base_delay,
        config.retry_max_delay,
        config.retry_jitter_percent
    )
    
    logger.info(f"Waiting {actual_delay:.1f}s before retry {retry_count}...")
    
    try:
        time.sleep(actual_delay)
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        raise RuntimeError("Operation cancelled by user")
