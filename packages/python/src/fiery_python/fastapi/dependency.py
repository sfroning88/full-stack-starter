"""
Author: Sean Froning
Created Date: 8.17.2026
Route API protections for auth
"""

import os
import secrets
from typing import Optional
from fastapi import Header
from .error import error


class _Dependency:
    """Basic auth function"""

    async def get_token_header(self, auth_token: Optional[str] = Header(None)):
        expected_token = os.environ.get("AUTH_TOKEN")
        if (
            not auth_token
            or not expected_token
            or not secrets.compare_digest(auth_token, expected_token)
        ):
            raise error("auth token invalid", status_code=403)


dependency = _Dependency()
