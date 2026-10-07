"""
Author: Sean Froning
Created Date: 9.22.2026
Centralized observability with sentry
"""

from typing import Any, Optional, Dict
from urllib.parse import urlparse
import sentry_sdk
from sentry_sdk.integrations.rq import RqIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from ..constants import SENTRY_HEALTH_PATHS
from .config import config


class _Observability:
    """Centralized observability configuration with sentry"""

    def __init__(self) -> None:
        self._configured = False

    def _resolve_credentials(
        self,
    ) -> Optional[tuple[str, str, float, Optional[str], Optional[str]]]:
        """Read dsn, environment, and trace config for this instance"""
        dsn = config.get("SENTRY_DSN")
        environment = "local"
        sample_rate = 0.0
        release = config.get("RENDER_GIT_COMMIT")
        domain = config.get("JOB_DOMAIN")
        if not dsn or not isinstance(dsn, str):
            return None
        if (
            config.get("SENTRY_ENVIRONMENT")
            and isinstance(config.get("SENTRY_ENVIRONMENT"), str)
            and str(config.get("SENTRY_ENVIRONMENT")).strip() in ("prod", "local")
        ):
            environment = str(config.get("SENTRY_ENVIRONMENT")).strip()
        elif config.get_log_format() == "json":
            environment = "prod"
        try:
            sample_rate = float(config.get("SENTRY_TRACES_SAMPLE_RATE"))
        except (TypeError, ValueError):
            pass
        if release is not None:
            release = str(release).strip()
        if domain is not None:
            domain = str(domain).strip()
        return (
            dsn,
            environment,
            sample_rate,
            release,
            domain,
        )

    @staticmethod
    def drop_health_routes(
        event: Dict[str, Any], _hint: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        url = (event.get("request") or {}).get("url") or ""
        request_path = urlparse(url).path
        if request_path in SENTRY_HEALTH_PATHS:
            return None
        return event

    def configure_sentry(self, service: Optional[str] = None) -> None:
        if self._configured:
            return
        cfg = self._resolve_credentials()
        if cfg is None:
            return
        dsn, environment, sample_rate, release, domain = cfg
        service_name = service or domain or "unknown"
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=sample_rate,
            send_default_pii=False,
            trace_propagation_targets=[],
            before_send=self.drop_health_routes,
            before_send_transaction=self.drop_health_routes,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                RqIntegration(),
            ],
        )
        sentry_sdk.set_tag("service", service_name)
        self._configured = True

    def bind_event_context(self, **fields: str) -> None:
        if not self._configured:
            return
        for key, value in fields.items():
            sentry_sdk.set_tag(key, str(value))

    def bind_request_context(
        self, *, correlation_id: str, path: Optional[str] = None
    ) -> None:
        if not self._configured:
            return
        sentry_sdk.set_tag("correlation_id", correlation_id)
        if path is not None:
            sentry_sdk.set_tag("path", path)


observability = _Observability()
