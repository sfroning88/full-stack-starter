"""
Author: Sean Froning
Created Date: 8.17.2026
Deterministic uuid generation utils
"""

import json
import uuid
from typing import Any, Dict, List

_UUID_NAMESPACE = uuid.UUID("8c9b8f3e-4d2a-5f1b-9e7c-2a1d6b4f0e35")


class UuidUtils:
    """Deterministic uuid generators"""

    @staticmethod
    def deterministic_uuid(*fields: Any, namespace: uuid.UUID = _UUID_NAMESPACE) -> str:
        """Stable RFC 4122 UUIDv5 derived from the given fields (order-sensitive)"""
        if not fields:
            raise ValueError("at least one field is required")
        encoded = []
        for field in fields:
            type_name = type(field).__qualname__
            value = None if field is None else str(field)
            encoded.append((type_name, value))
        name = json.dumps(encoded, separators=(",", ":"))
        return str(uuid.uuid5(namespace, name))

    @staticmethod
    def dedupe_uuid(rows: List[Dict]) -> List[Dict]:
        by_id: Dict[str, Dict] = {}
        for row in rows:
            row_id = row.get("id")
            if not row_id:
                continue
            by_id[str(row_id)] = row
        return list(by_id.values())
