"""Gemini (Generative Language) client wrapper.

Handles authentication via environment variable ``GEMINI_API_KEY``.
Wraps the Google Generative AI Python SDK and provides simple generate_content
helper with basic retry/backoff.

NOTE: Requires ``google-generativeai`` package.
"""

from __future__ import annotations

import os
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

API_KEY_ENV = "GEMINI_API_KEY"


class GeminiClient:
    """A client for interacting with the Gemini API using the google-generativeai SDK."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        """Initializes the Gemini client.

        Args:
            api_key: The API key for the Gemini API. If not provided, it will
              be read from the GEMINI_API_KEY environment variable.
            model: The Gemini model to use. If not provided, it will default
              to 'gemini-1.5-flash'.
        """
        self.api_key = api_key or os.environ.get(API_KEY_ENV)
        if not self.api_key:
            raise RuntimeError(f"Environment variable {API_KEY_ENV} is required for Gemini access")

        # Configure the API key
        genai.configure(api_key=self.api_key)
        
        # Set the model name - use current available models
        self.model_name = model or "gemini-1.5-flash"
        
        # Initialize the model
        try:
            self.model = genai.GenerativeModel(self.model_name)
            print(f"✅ Gemini client initialized with model: {self.model_name}")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini model '{self.model_name}': {e}")
            # Try fallback models in order of preference
            fallback_models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.5-flash"]
            
            for fallback_model in fallback_models:
                try:
                    self.model_name = fallback_model
                    self.model = genai.GenerativeModel(self.model_name)
                    print(f"✅ Fallback to model: {self.model_name}")
                    break
                except Exception as e2:
                    print(f"❌ Fallback model '{fallback_model}' also failed: {e2}")
                    continue
            else:
                raise RuntimeError(f"Failed to initialize any Gemini model. Last error: {e}")

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    def generate_content(self, *, prompt: str, **kwargs: Any) -> str:
        """Generate text content using Gemini model with retries."""
        try:
            print(f"🤖 Calling Gemini API with model: {self.model_name}")
            response = self.model.generate_content(prompt, **kwargs)
            
            if not response.text:
                raise RuntimeError("Gemini API returned empty response")
                
            print(f"✅ Gemini API call successful, response length: {len(response.text)} characters")
            return response.text
            
        except Exception as err:
            print(f"❌ Gemini API call failed: {err}")
            # Provide more specific error information
            error_msg = f"Gemini API call failed with model '{self.model_name}': {err}"
            raise RuntimeError(error_msg) from err 