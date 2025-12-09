"""
This module bundles the external LLM dependency (e.g., the OpenAI client)
to ensure it is available for all AI-related modules without circular imports.
"""
import os
from openai import OpenAI
from typing import Optional

# Initialize the OpenAI client. The base_url and api_key are configured
# to use the local environment variables or the user's provided key.
# This client is intended to be used by the AIModelRouter.

def get_llm_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Returns an OpenAI client instance.
    If an API key is provided, it uses that key. Otherwise, it defaults
    to the environment variable OPENAI_API_KEY.
    """
    key = api_key if api_key else os.environ.get("OPENAI_API_KEY")
    
    if not key:
        # Fallback for local testing or if the user hasn't set a key
        # The AIModelRouter should handle the actual key management.
        return None 

    # Assuming the user's key is a standard OpenAI key
    return OpenAI(api_key=key)

# The AIModelRouter should be updated to use this function to get the client.
# This ensures the LLM dependency is correctly bundled and accessible.
