"""
Author: Sean Froning
Created Date: 8.29.2026
Processing functions for Serving orchestrator
"""

from fiery_python import error
from fiery_python import (
    BlobStorageServices,
    ModelTier,
    ModelRole,
    InferenceDeformation,
    InferenceSeismic,
)
from ..schemas import (
    InferenceSingleRequest,
    InferenceSingleResponse,
)
from ..models import InferenceOutcome
from .persist_service import InferencePersistService
from .serving_waiter import InferenceServingWaiter


class InferenceServingOrchestrator:
    """Manage the serving process and call waiter"""

    @classmethod
    def run(_cls, payload: InferenceSingleRequest) -> InferenceSingleResponse:
        key = (payload.tier, payload.role)
        if (
            key != (ModelTier.CLOUD, ModelRole.SCREENER)
            and key != (ModelTier.CLOUD, ModelRole.TEACHER)
            and key != (ModelTier.EDGE, ModelRole.STUDENT)
        ):
            raise NotImplementedError
        interferogram_id = payload.interferogram_id
        seismic_event_id = payload.seismic_event_id
        volcano_id = payload.volcano_id
        interferogram = None
        seismic_event = None
        if interferogram_id:
            interferogram = InferencePersistService.select_interferogram(
                (interferogram_id, None)
            )
        elif seismic_event_id:
            seismic_event = InferencePersistService.select_seismic_event(
                (seismic_event_id, None)
            )
        elif volcano_id:
            if key == (ModelTier.CLOUD, ModelRole.SCREENER):
                interferogram = InferencePersistService.select_interferogram(
                    (None, volcano_id)
                )
            elif key in (
                (ModelTier.CLOUD, ModelRole.TEACHER),
                (ModelTier.EDGE, ModelRole.STUDENT),
            ):
                seismic_event = InferencePersistService.select_seismic_event(
                    (None, volcano_id)
                )
            else:
                raise NotImplementedError
        else:
            raise error("No interferogram or seismic_event is selected")
        score = None
        if interferogram:
            if not interferogram.id:
                interferogram.id = interferogram.deterministic_id()
            if not interferogram.id:
                raise error("Invalid interferogram_id")
            storage_path = interferogram.storage_path
            volcano_id = interferogram.volcano_id or volcano_id
            interferogram_id = interferogram.id
            seismic_event_id = None
        elif seismic_event:
            if not seismic_event.id:
                seismic_event.id = seismic_event.deterministic_id()
            if not seismic_event.id:
                raise error("Invalid seismic_event_id")
            storage_path = seismic_event.waveform_path
            volcano_id = seismic_event.volcano_id or volcano_id
            seismic_event_id = seismic_event.id
            interferogram_id = None
        elif key == (ModelTier.CLOUD, ModelRole.SCREENER):
            raise error("No interferogram was found")
        else:
            raise error("No seismic event was found")
        body = BlobStorageServices.get_unrefined(storage_path)
        sample = InferencePersistService.load_npz(body)
        inference, probabilities = InferenceServingWaiter.run(
            key, sample, interferogram_id, seismic_event_id
        )
        if isinstance(inference, InferenceDeformation):
            InferencePersistService.upsert_deformation(inference)
            score = inference.score
        elif isinstance(inference, InferenceSeismic):
            InferencePersistService.upsert_seismic(inference)
        outcome = InferenceOutcome(
            artifact_id=inference.artifact_id,
            transform_hash=inference.transform_hash,
            op_version=inference.op_version,
            threshold_used=inference.threshold_used,
            abstention_band=inference.abstention_band,
            abstained=inference.abstained,
            abstained_reason=inference.abstained_reason,
            latency_ms=inference.latency_ms,
            inferred_at=inference.inferred_at,
            probabilities=probabilities,
            label=inference.label,
            score=score,
            interferogram_id=interferogram_id,
            seismic_event_id=seismic_event_id,
            volcano_id=volcano_id,
        )
        return InferenceSingleResponse(
            result=outcome,
            artifact_id=outcome.artifact_id,
            transform_hash=outcome.transform_hash,
        )
