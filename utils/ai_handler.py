import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time

class APIError(Exception):
    """Custom exception for API errors"""
    pass

class AIHandler:
    """Centralized AI handler with retry logic and error handling."""
    
    def __init__(self, api_key, model_name="gemini-2.5-flash"):
        """
        Initialize the AI handler with API key and model.
        
        Args:
            api_key: Google AI API key
            model_name: Model to use (default: gemini-2.5-flash for higher rate limits)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APIError, Exception)),
        reraise=True
    )
    def generate_content(self, prompt):
        """
        Generate content with automatic retry on rate limit or server errors.
        
        Args:
            prompt: Text prompt for generation
            
        Returns:
            GenerateContentResponse object
            
        Raises:
            APIError: If all retries fail
        """
        try:
            response = self.model.generate_content(prompt)
            return response
        except Exception as e:
            error_str = str(e)
            # Check for rate limit or server errors
            if "429" in error_str or "Resource exhausted" in error_str:
                raise APIError(f"Rate limit exceeded: {error_str}")
            elif "500" in error_str or "503" in error_str:
                raise APIError(f"Server error: {error_str}")
            else:
                # Re-raise other exceptions
                raise
    
    def generate_with_fallback(self, prompt, fallback_value=None):
        """
        Generate content with a fallback value if all retries fail.
        
        Args:
            prompt: Text prompt for generation
            fallback_value: Value to return if generation fails
            
        Returns:
            Response text or fallback_value
        """
        try:
            response = self.generate_content(prompt)
            return response.text
        except Exception as e:
            # print(f"AI generation failed after retries: {e}")
            return fallback_value if fallback_value else f"Error: {str(e)}"
