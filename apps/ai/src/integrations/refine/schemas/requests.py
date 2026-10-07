"""
Author: Sean Froning
Created Date: 8.22.2026
Request models for Refine
"""

from pydantic import BaseModel, AfterValidator
from typing import Annotated
from fiery_python import SchemaUtils


class RefineRequest(BaseModel):
    """Request model for running refine job"""

    contract_id: Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    max_samples: int = 5
