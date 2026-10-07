"""
Author: Sean Froning
Created Date: 8.24.2026
Operations pertaining to Callback persistence
"""

from psycopg2.extras import execute_values
from typing import List, Optional
from fiery_python import db_pool, logging
from fiery_python import (
    PoolFetch,
    MODEL_DB_PAGE_SIZE,
    ModelArtifact,
    ModelMetric,
)
from ..queries.select_model_artifact import QUERY as SELECT_ARTIFACT
from ..queries.upsert_model_artifact import QUERY as UPSERT_ARTIFACT
from ..queries.upsert_model_metrics import (
    QUERY as UPSERT_METRICS,
    TEMPLATE as UPSERT_METRICS_TEMPLATE,
)

logger = logging.get_logger(__name__)


class CallbackPersistService:
    """Persist artifact, metrics"""

    @staticmethod
    def select_artifact(artifact_id: str) -> Optional[ModelArtifact]:
        row = db_pool.run(
            SELECT_ARTIFACT,
            (artifact_id,),
            fetch=PoolFetch.ONE,
            error_event="fetch_model_artifact_failed",
        )
        if not row:
            logger.warning("fetch_model_artifact_empty", artifact_id=artifact_id)
            return None
        return ModelArtifact(
            id=artifact_id,
            tier=row.get("tier"),
            role=row.get("role"),
            stage=row.get("stage"),
            precision=row.get("precision"),
            architecture=row.get("architecture"),
            param_count=row.get("param_count"),
            sparsity=row.get("sparsity"),
            storage_path=row.get("storage_path"),
            signature=row.get("signature"),
            signed_at=row.get("signed_at"),
            promoted=row.get("promoted"),
            promoted_at=row.get("promoted_at"),
            mlflow_run_id=row.get("mlflow_run_id"),
            hf_repo_id=row.get("hf_repo_id"),
            hf_revision=row.get("hf_revision"),
            session_id=row.get("session_id"),
            parent_id=row.get("parent_id"),
        )

    @staticmethod
    def upsert_artifact(artifact: ModelArtifact) -> None:
        db_pool.run(
            UPSERT_ARTIFACT,
            artifact.prepare_for_storage(include_id=True),
        )

    @staticmethod
    def upsert_metrics(metrics: List[ModelMetric]) -> None:
        insert_values = [
            metric.prepare_for_storage(include_id=False) for metric in metrics
        ]
        with db_pool.get_cursor() as cursor:
            execute_values(
                cursor,
                UPSERT_METRICS.as_string(cursor),
                insert_values,
                template=UPSERT_METRICS_TEMPLATE.as_string(cursor),
                page_size=MODEL_DB_PAGE_SIZE,
            )
