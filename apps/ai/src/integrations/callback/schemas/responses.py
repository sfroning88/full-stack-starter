"""
Author: Sean Froning
Created Date: 8.24.2026
Response models for Callback
"""

from pydantic import BaseModel


class CallbackResponse(BaseModel):
    """Response model for receiving train callback"""

    artifact_id: str
    session_id: str
