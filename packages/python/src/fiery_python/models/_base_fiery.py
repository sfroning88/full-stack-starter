"""
Author: Sean Froning
Created Date: 8.17.2026
Class objects for Fiery schemas
"""

import uuid
from typing import Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class BaseFiery(BaseModel):
    """Base Focus Schema Model"""

    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __init__(self, **data):
        """Create initial file class object"""
        super().__init__(**data)
        self.gen_uuid_field()

    def gen_uuid_field(self) -> None:
        """Generate a 128 bit UUID"""
        if not self.id:
            self.id = str(uuid.uuid4())

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from the row natural key; None when unavailable"""
        return None

    def prepare_for_storage(self, include_id: bool = True) -> dict:
        """Convert row to batch insertion dict"""
        derived = self.deterministic_id()
        if derived:
            self.id = derived
        skip = {"id"} if not include_id else set()

        def storage_value(value: object) -> object:
            if isinstance(value, Enum):
                return value.value
            return value

        skip = {"id"} if not include_id else set()
        return {
            name: storage_value(value)
            for name, value in self.model_dump(mode="python").items()
            if name not in skip
        }
