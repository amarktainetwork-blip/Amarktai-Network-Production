"""
This module manages the per-user OpenAI API keys, providing a simple
interface for the AIModelRouter to get the correct key for a given user.
"""
import os
from typing import Dict, Optional

from backend.database import api_keys_collection

class OpenAIClientManager:
    """
    Manages API keys for multiple users.
    This class is a placeholder for a more robust key management system.
    """
    def __init__(self):
        self.user_api_keys: Dict[str, str] = {}

    async def load_user_keys(self):
        """Load all user API keys from the database."""
        cursor = api_keys_collection.find({"provider": "openai", "is_valid": True})
        async for key_data in cursor:
            self.user_api_keys[key_data["user_id"]] = key_data["key"]

    def get_api_key(self, user_id: str) -> Optional[str]:
        """
        Get the API key for a specific user.
        Returns the user's key or the system-wide fallback key.
        """
        return self.user_api_keys.get(user_id, os.environ.get("OPENAI_API_KEY"))

# Global instance
openai_client_manager = OpenAIClientManager()
