from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from backend.auth import get_current_user
from backend.ai_commands_extended import handle_ai_command
from backend.database import chat_messages_collection
from backend.models import ChatMessage

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

@router.post("/chat", response_model=ChatMessage)
async def ai_chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
    """
    The main AI ChatOps endpoint. Handles user messages, executes AI commands,
    and returns the AI's response.
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # 1. Handle the AI command and get the response
    ai_response_text = await handle_ai_command(user_id, request.message, request.context)

    # 2. Save the user message
    user_message = ChatMessage(
        user_id=user_id,
        sender="user",
        content=request.message,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    await chat_messages_collection.insert_one(user_message.dict())

    # 3. Save the AI response
    ai_message = ChatMessage(
        user_id=user_id,
        sender="ai",
        content=ai_response_text,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    await chat_messages_collection.insert_one(ai_message.dict())

    return ai_message

@router.get("/history", response_model=List[ChatMessage])
async def get_chat_history(user_id: str = Depends(get_current_user)):
    """Retrieve the last 50 chat messages for the user."""
    history = await chat_messages_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(50).to_list(50)
    return history
