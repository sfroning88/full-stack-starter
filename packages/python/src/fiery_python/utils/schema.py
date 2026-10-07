"""
Author: Sean Froning
Created Date: 8.17.2026
API field validator utils
"""

import re
import uuid
from typing import Optional, Any


class SchemaUtils:
    """Field validators for API schemas"""

    @staticmethod
    def non_empty_string(string: Optional[Any]) -> str:
        """Validate that string is not empty. Raises error if empty"""
        if string is None:
            raise ValueError("Field cannot be empty")
        if not isinstance(string, str):
            raise ValueError("Field is not a string")
        trimmed = string.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty")
        return trimmed

    @staticmethod
    def valid_email(email: Optional[Any]) -> str:
        if email is None:
            raise ValueError("Field cannot be empty")
        if not isinstance(email, str):
            raise ValueError("Field is not a string")
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, email.strip()):
            raise ValueError("Not a valid email address")
        return email.strip()

    @staticmethod
    def valid_uuid(value: Optional[Any]) -> str:
        """Validate that value is an RFC 4122 UUID string"""
        if value is None:
            raise ValueError("Field cannot be empty")
        if not isinstance(value, str):
            raise ValueError("Field is not a string")
        try:
            uuid.UUID(value.strip())
        except ValueError:
            raise ValueError("Not a valid UUID")
        return value.strip()

    @staticmethod
    def positive_int(number: Optional[Any]) -> int | float:
        if number is None:
            raise ValueError("Field cannot be empty")
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise ValueError("Field is not a number")
        if number < 1:
            raise ValueError("Number is less than 1")
        return number
