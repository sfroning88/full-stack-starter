"""
Author: Sean Froning
Created Date: 8.17.2026
App Error handling for FastAPI App
"""

from typing import Any, Dict, Optional, Union


class _Error(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Union[Dict[str, Any], list]] = None,
        error_type: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details
        self.error_type = error_type or self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.error_type,
            "message": self.message,
            "code": self.status_code,
            "details": self.details,
        }


error = _Error
