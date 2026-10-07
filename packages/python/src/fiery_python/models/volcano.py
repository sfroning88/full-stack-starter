"""
Author: Sean Froning
Created Date: 8.19.2026
Class objects for Volcano schema
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from ._base_fiery import BaseFiery
from ..enums import (
    VolcanoZone,
    VolcanoActivitySource,
    VolcanoAlertLevel,
)
from ..utils import UuidUtils


class Volcano(BaseFiery):
    """Normalized Volcano"""

    gvp_number: Optional[int] = None
    name: str
    country: str
    zone: VolcanoZone
    latitude: Decimal
    longitude: Decimal
    elevation_m: int
    volcanic_class: Optional[str] = None
    is_glaciated: bool = False
    is_instrumented: bool = False
    is_held_out: bool = False
    image_path: Optional[str] = None

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (gvp_number or country, name, zone, name)"""
        if self.gvp_number is not None:
            return UuidUtils.deterministic_uuid(self.gvp_number)
        if not self.country or not self.name or not self.zone:
            return None
        return UuidUtils.deterministic_uuid(self.country, self.name, self.zone.value)


class VolcanoActivity(BaseFiery):
    """Normalized Volcano Activity"""

    source: VolcanoActivitySource
    started_at: Optional[date] = None
    ended_at: Optional[date] = None
    vei: Optional[int] = None
    alert_level: Optional[VolcanoAlertLevel] = None
    is_confirmed: bool = True
    volcano_id: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from activity identity fields"""
        if not self.volcano_id or not self.source:
            return None
        alert = self.alert_level.value if self.alert_level else None
        return UuidUtils.deterministic_uuid(
            self.volcano_id,
            self.source.value,
            self.started_at,
            self.ended_at,
            self.vei,
            alert,
        )
