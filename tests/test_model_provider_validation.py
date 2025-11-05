#!/usr/bin/env python3
"""
Test the model validation feature that catches provider/model mismatches.
"""
import unittest
from video_gen.video_generator import _validate_model_for_provider
from video_gen.logger import get_library_logger


class TestModelValidation(unittest.TestCase):
    """Test model/provider validation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = get_library_logger()
    
    def test_valid_openai_model(self):
        """Test that valid OpenAI models pass validation."""
        # Should not raise
        _validate_model_for_provider("sora-2", "openai", self.logger)
    
    def test_valid_azure_model(self):
        """Test that valid Azure models pass validation."""
        # Should not raise
        _validate_model_for_provider("sora-2", "azure", self.logger)
    
    def test_valid_google_model(self):
        """Test that valid Google models pass validation."""
        # Should not raise
        _validate_model_for_provider("veo-3.1-fast-generate-preview", "google", self.logger)
    
    def test_valid_runway_model(self):
        """Test that valid Runway models pass validation."""
        # Should not raise
        _validate_model_for_provider("gen4", "runway", self.logger)
    
    def test_google_model_with_openai_provider_fails(self):
        """Test that using Google model with OpenAI provider raises helpful error."""
        with self.assertRaises(ValueError) as ctx:
            _validate_model_for_provider("veo-3.1-fast-generate-preview", "openai", self.logger)
        
        error_msg = str(ctx.exception)
        self.assertIn("veo-3.1-fast-generate-preview", error_msg)
        self.assertIn("not available for provider 'openai'", error_msg)
        self.assertIn("google", error_msg)
        self.assertIn("Use --provider", error_msg)
    
    def test_openai_model_with_google_provider_fails(self):
        """Test that using OpenAI model with Google provider raises helpful error."""
        with self.assertRaises(ValueError) as ctx:
            _validate_model_for_provider("sora-2", "google", self.logger)
        
        error_msg = str(ctx.exception)
        self.assertIn("sora-2", error_msg)
        self.assertIn("not available for provider 'google'", error_msg)
        # Should suggest either openai or azure
        self.assertTrue("openai" in error_msg or "azure" in error_msg)
    
    def test_runway_model_with_openai_provider_fails(self):
        """Test that using Runway model with OpenAI provider raises helpful error."""
        with self.assertRaises(ValueError) as ctx:
            _validate_model_for_provider("gen4", "openai", self.logger)
        
        error_msg = str(ctx.exception)
        self.assertIn("gen4", error_msg)
        self.assertIn("not available for provider 'openai'", error_msg)
        self.assertIn("runway", error_msg)
    
    def test_invalid_model_for_any_provider_fails(self):
        """Test that completely invalid model raises helpful error."""
        with self.assertRaises(ValueError) as ctx:
            _validate_model_for_provider("nonexistent-model-xyz", "openai", self.logger)
        
        error_msg = str(ctx.exception)
        self.assertIn("nonexistent-model-xyz", error_msg)
        self.assertIn("not", error_msg.lower())
        # Should list available models for the provider
        self.assertIn("Available models", error_msg)


if __name__ == "__main__":
    unittest.main()
