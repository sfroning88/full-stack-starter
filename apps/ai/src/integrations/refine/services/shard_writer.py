"""
Author: Sean Froning
Created Date: 8.28.2026
Processing functions for Shard writer
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union, assert_never
from fiery_python import error, logging
from fiery_python import (
    STORAGE_OP_VERSION,
    TRAINING_DB_FETCH_SIZE,
    BlobStorageServices,
    DatasetVersion,
    Shard,
    TrainingDeformation,
    TrainingSeismic,
    TrainingInterferogram,
    TrainingSeismicEvent,
    TrainingContract,
    TrainingSplit,
    TrainingStatus,
    Transformation,
    TransformationRejected,
)

from .persist_service import RefinePersistService
from .shard_manifest import RefineShardManifest

logger = logging.get_logger(__name__)

_FORMAT_VERSION = 1
_TARGET_SHARD_BYTES = 200 * 1024 * 1024
_LABEL_OVERHEAD = 256
_BASE_ID = "00000000-0000-0000-0000-000000000000"
_Params = Union[TrainingDeformation, TrainingSeismic]
_Sample = Union[TrainingInterferogram, TrainingSeismicEvent]


class RefineShardWriter:
    """Stream unrefined R2 and refine shards back to refined R2"""

    @classmethod
    def run(
        cls, contract: TrainingContract, version_id: str, max_samples: int = 5
    ) -> int:
        """Read unrefined samples, apply transform, store refined shards; return sample_count"""
        if not contract.id:
            raise error("Training contract missing id")
        if max_samples <= 0:
            raise ValueError("max_samples must be positive")
        if contract.deformation_id:
            params = RefinePersistService.select_deformation(contract.id)
            if not params:
                raise error("Training deformation not found")
            transform_hash = Transformation.transform_hash_deformation(params)
        elif contract.seismic_id:
            params = RefinePersistService.select_seismic(contract.id)
            if not params:
                raise error("Training seismic not found")
            transform_hash = Transformation.transform_hash_seismic(params)
        else:
            raise error("Malformed training contract")
        version = RefinePersistService.select_version(contract.id, transform_hash)
        if not version:
            raise error("Dataset version not found")
        if version.id != version_id:
            raise error("Dataset version mismatch")
        RefinePersistService.upsert_version(
            DatasetVersion(
                id=version.id,
                transform_hash=transform_hash,
                manifest_path=version.manifest_path,
                shard_count=0,
                sample_count=0,
                status=TrainingStatus.EXECUTING,
                contract_id=contract.id,
            )
        )
        manifest = RefineShardManifest(contract.id, transform_hash, params)
        sample_count = 0
        try:
            for split in TrainingSplit:
                sample_count += cls._write_split(
                    contract.id,
                    transform_hash,
                    split,
                    params,
                    manifest,
                    max_samples,
                )
            manifest_path = BlobStorageServices.put_manifest(
                contract.id, transform_hash, manifest.dumps()
            )
            RefinePersistService.upsert_version(
                DatasetVersion(
                    id=version.id,
                    transform_hash=transform_hash,
                    manifest_path=manifest_path,
                    shard_count=manifest.shard_count(),
                    sample_count=manifest.sample_count(),
                    status=TrainingStatus.COMPLETED,
                    contract_id=contract.id,
                )
            )
            return sample_count
        except Exception as err:
            RefinePersistService.upsert_version(
                DatasetVersion(
                    id=version.id,
                    transform_hash=transform_hash,
                    manifest_path=version.manifest_path,
                    shard_count=manifest.shard_count(),
                    sample_count=manifest.sample_count(),
                    status=TrainingStatus.FAILED,
                    contract_id=contract.id,
                )
            )
            logger.error(
                "refine_shard_writer_failed",
                contract_id=contract.id,
                version_id=version_id,
                deformation_id=contract.deformation_id or "None",
                seismic_id=contract.seismic_id or "None",
                error=str(err),
            )
            raise

    @classmethod
    def _write_split(
        cls,
        contract_id: str,
        transform_hash: str,
        split: TrainingSplit,
        params: _Params,
        manifest: RefineShardManifest,
        max_samples: int,
    ) -> int:
        buffer: List[Tuple[str, np.ndarray, Dict[str, Any]]] = []
        approx_bytes = 0
        shard_index = 0
        kept = 0
        after_id = _BASE_ID
        remaining = max_samples
        while remaining > 0:
            limit = min(TRAINING_DB_FETCH_SIZE, remaining)
            page: List[_Sample] = []
            if isinstance(params, TrainingDeformation):
                page.extend(
                    RefinePersistService.select_interferograms(split, after_id, limit)
                )
            elif isinstance(params, TrainingSeismic):
                page.extend(
                    RefinePersistService.select_seismic_events(split, after_id, limit)
                )
            else:
                assert_never(params)
            if not page:
                break
            for sample in page:
                remaining -= 1
                transformed = cls._transform_shard(sample, params, manifest)
                if transformed is None:
                    if remaining <= 0:
                        break
                    continue
                key, array, label = transformed
                buffer.append((key, array, label))
                approx_bytes += int(array.nbytes) + _LABEL_OVERHEAD
                kept += 1
                if approx_bytes >= _TARGET_SHARD_BYTES:
                    cls._flush_shard(
                        contract_id,
                        transform_hash,
                        split,
                        shard_index,
                        buffer,
                        manifest,
                    )
                    buffer = []
                    approx_bytes = 0
                    shard_index += 1
                if remaining <= 0:
                    break
            after_id = page[-1].id
            if not after_id:
                break
            page.clear()
        if buffer:
            cls._flush_shard(
                contract_id,
                transform_hash,
                split,
                shard_index,
                buffer,
                manifest,
            )
        return kept

    @staticmethod
    def _transform_shard(
        sample: _Sample,
        params: _Params,
        manifest: RefineShardManifest,
    ) -> Optional[Tuple[str, np.ndarray, Dict[str, Any]]]:
        if isinstance(sample, TrainingInterferogram) and isinstance(
            params, TrainingDeformation
        ):
            storage_path = sample.storage_path
        elif isinstance(sample, TrainingSeismicEvent) and isinstance(
            params, TrainingSeismic
        ):
            storage_path = sample.waveform_path
        else:
            raise error("Sample and params signal mismatch")
        if not sample.id or not storage_path:
            manifest.record_reject(sample.split, sample.label, "missing_identity")
            return None
        try:
            body = BlobStorageServices.get_unrefined(storage_path)
            array = RefinePersistService.load_npz(body)
            if isinstance(params, TrainingDeformation):
                transformed = Transformation.apply_deformation(array, params)
            elif isinstance(params, TrainingSeismic):
                if (
                    isinstance(sample, TrainingSeismicEvent)
                    and sample.sampling_hz != params.sampling_hz
                ):
                    raise TransformationRejected("sampling_hz mismatch")
                transformed = Transformation.apply_seismic(array, params)
            else:
                assert_never(params)
        except TransformationRejected as err:
            manifest.record_reject(sample.split, sample.label, str(err))
            return None
        except Exception as err:
            manifest.record_reject(sample.split, sample.label, str(err))
            return None
        manifest.record_kept(sample.split, sample.label)
        return (
            sample.id,
            transformed,
            {
                "label": sample.label.value,
                "split": sample.split.value,
                "format_version": _FORMAT_VERSION,
                "op_version": STORAGE_OP_VERSION,
            },
        )

    @staticmethod
    def _flush_shard(
        contract_id: str,
        transform_hash: str,
        split: TrainingSplit,
        shard_index: int,
        buffer: List[Tuple[str, np.ndarray, Dict[str, Any]]],
        manifest: RefineShardManifest,
    ) -> None:
        body = Shard.write(buffer)
        key = BlobStorageServices.put_shard(
            contract_id, transform_hash, split, shard_index, body
        )
        manifest.record_shard(split, key, len(buffer), len(body))
        logger.info(
            "refine_shard_flushed",
            contract_id=contract_id,
            split=split.value,
            shard_index=shard_index,
            sample_count=len(buffer),
            bytes=len(body),
        )
