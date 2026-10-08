"""
Author: Sean Froning
Created Date: 10.7.2026
Class objects for MyProject schema
"""

from typing import Optional
from ._base_my_project import BaseMyProject
from ..constants import MY_MESSAGE
from ..utils import UuidUtils


class MyClass(BaseMyProject):
    """Example MyClass"""

    message: str = MY_MESSAGE

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from message_length"""
        if not self.message:
            return None
        return UuidUtils.deterministic_uuid(len(self.message))
