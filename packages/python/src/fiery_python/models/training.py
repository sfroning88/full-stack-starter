"""
Author: Sean Froning
Created Date: 8.19.2026
Class objects for Training schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field
from ._base_fiery import BaseFiery
from ..enums import (
    TrainingSplit,
    TrainingSampleSource,
    TrainingSignal,
    TrainingStage,
    TrainingStatus,
    TrainingPrecision,
    TrainingSeismicLabel,
    TrainingDeformationLabel,
    TrainingWindow,
    TrainingNormalize,
    TrainingOptimizer,
    TrainingRateSchedule,
    TrainingSparsitySchedule,
    TrainingPruningCriterion,
    TrainingQuantizeMethod,
    TrainingDeformationSourceType,
    TrainingNoiseModel,
)
from ..utils import UuidUtils


class TrainingDeformationClass(BaseFiery):
    """Normalized Training Deformation Class"""

    deformation: bool = True
    seismic: bool = True

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (deformation, seismic)"""
        return UuidUtils.deterministic_uuid(self.deformation, self.seismic)


class TrainingSeismicClass(BaseFiery):
    """Normalized Training Seismic Class"""

    vt: bool = True
    lp: bool = True
    tr: bool = True
    tc: bool = True

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (vt, lp, tr, tc)"""
        return UuidUtils.deterministic_uuid(self.vt, self.lp, self.tr, self.tc)


class TrainingDeformationSource(BaseFiery):
    """Normalized Training Deformation Source"""

    source: TrainingDeformationSourceType
    latitude: Decimal
    longitude: Decimal
    depth_km: Decimal
    volume_change_m3: Optional[Decimal] = None
    pressure_change_pa: Optional[Decimal] = None
    strike_deg: Optional[Decimal] = None
    dip_deg: Optional[Decimal] = None
    length_km: Optional[Decimal] = None
    width_km: Optional[Decimal] = None
    rake_deg: Optional[Decimal] = None
    slip_m: Optional[Decimal] = None
    opening_m: Optional[Decimal] = None
    poissons_ratio: Decimal = Decimal("0.25")
    shear_modulus_pa: Optional[Decimal] = None
    los_incidence_deg: Decimal
    los_heading_deg: Decimal
    wavelength_m: Decimal
    noise_model: TrainingNoiseModel = Field(default=TrainingNoiseModel.NONE)

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (source, latitude, longitude, depth_km)"""
        return UuidUtils.deterministic_uuid(
            self.source.value, self.latitude, self.longitude, self.depth_km
        )


class TrainingInterferogram(BaseFiery):
    """Normalized Training Interferogram"""

    source: TrainingSampleSource
    split: TrainingSplit
    label: TrainingDeformationLabel
    frame_id: Optional[str] = None
    primary_at: Optional[date] = None
    secondary_at: Optional[date] = None
    coherence_mean: Optional[Decimal] = None
    is_augmented: bool = False
    storage_path: str
    deformation_source_id: Optional[str] = None
    volcano_id: Optional[str] = None

    def deterministic_id(self) -> Optional[str]:
        """Stable id from (deformation_source_id or storage_path)"""
        if self.deformation_source_id:
            return UuidUtils.deterministic_uuid(self.deformation_source_id)
        if not self.storage_path:
            return None
        return UuidUtils.deterministic_uuid(self.storage_path)


class TrainingSeismicEvent(BaseFiery):
    """Normalized Training Seismic Event"""

    source: TrainingSampleSource
    split: TrainingSplit
    label: TrainingSeismicLabel
    station: str = "LAV"
    recorded_at: datetime
    duration_s: Decimal
    sampling_hz: int
    waveform_path: str
    spectrogram_path: Optional[str] = None
    volcano_id: Optional[str] = None

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (waveform_path)"""
        if not self.waveform_path:
            return None
        return UuidUtils.deterministic_uuid(self.waveform_path)


class TrainingSeismic(BaseFiery):
    """Normalized Training Seismic"""

    nfft: int
    hop: int
    window: TrainingWindow
    window_s: Decimal
    sampling_hz: int
    mel_bins: int
    bandpass_low_hz: Decimal
    bandpass_high_hz: Decimal
    normalize: TrainingNormalize
    snr_min: Decimal
    class_id: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (nfft, hop, window, normalize, class_id)"""
        return UuidUtils.deterministic_uuid(
            self.nfft, self.hop, self.window.value, self.normalize, self.class_id
        )


class TrainingDeformation(BaseFiery):
    """Normalized Training Deformation"""

    patch_px: int
    wrap_rad: Decimal
    normalize: TrainingNormalize
    coherence_min: Decimal
    class_id: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (patch_px, normalize, class_id)"""
        return UuidUtils.deterministic_uuid(
            self.patch_px, self.normalize.value, self.class_id
        )


class TrainingHyperparameterPretrain(BaseFiery):
    """Normalized Training Hyperparameter Pretrain"""

    epochs: int = 50
    batch_size: int = 32
    learning_rate: float = 0.001
    optimizer: TrainingOptimizer = Field(default=TrainingOptimizer.ADAMW)
    weight_decay: Decimal = Decimal("0.01")
    lr_schedule: TrainingRateSchedule = Field(default=TrainingRateSchedule.COSINE)
    seed: int = 42

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (learning_rate, seed, optimizer)"""
        return UuidUtils.deterministic_uuid(
            self.learning_rate, self.seed, self.optimizer.value
        )


class TrainingTargetModules(BaseFiery):
    """Normalized Training Target Modules"""

    query: bool = True
    key: bool = False
    value: bool = True
    output: bool = False

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (query, key, value, output)"""
        return UuidUtils.deterministic_uuid(
            self.query, self.key, self.value, self.output
        )


class TrainingHyperparameterLora(BaseFiery):
    """Normalized Training Hyperparameter LoRA"""

    rank: int = 8
    alpha: int = 16
    dropout: float = 0.1
    epochs: int = 10
    learning_rate: float = 0.0003
    target_modules_id: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (rank, alpha, target_modules_id)"""
        if not self.target_modules_id:
            return None
        return UuidUtils.deterministic_uuid(
            self.rank, self.alpha, self.target_modules_id
        )


class TrainingHyperparameterDistill(BaseFiery):
    """Normalized Training Hyperparameter Distill"""

    temperature: float = 4.0
    alpha: Decimal = Decimal("0.7")
    epochs: int = 30
    batch_size: int = 64
    learning_rate: float = 0.001
    student_architecture: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (temperature, alpha, student_architecture)"""
        if not self.student_architecture:
            return None
        return UuidUtils.deterministic_uuid(
            self.temperature, self.alpha, self.student_architecture
        )


class TrainingHyperparameterPrune(BaseFiery):
    """Normalized Training Hyperparameter Prune"""

    target_sparsity: Decimal = Decimal("0.7")
    iterations: int = 5
    sparsity_schedule: TrainingSparsitySchedule = Field(
        default=TrainingSparsitySchedule.LINEAR
    )
    finetune_epochs_per_iter: int = 3
    pruning_criterion: TrainingPruningCriterion = Field(
        default=TrainingPruningCriterion.L1_MAGNITUDE
    )

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (target_sparsity, pruning_criterion)"""
        return UuidUtils.deterministic_uuid(
            self.target_sparsity, self.pruning_criterion.value
        )


class TrainingHyperparameterQuantize(BaseFiery):
    """Normalized Training Hyperparameter Quantize"""

    method: TrainingQuantizeMethod = Field(default=TrainingQuantizeMethod.PTQ)
    precision: TrainingPrecision = Field(default=TrainingPrecision.INT8)
    calibration_samples: int = 100
    accuracy_drop_threshold: Decimal = Decimal("0.02")
    qat_epochs: int = 5
    qat_learning_rate: float = 0.001

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (method, precision)"""
        return UuidUtils.deterministic_uuid(self.method.value, self.precision.value)


class TrainingContract(BaseFiery):
    """Normalized Training Contract"""

    signal: TrainingSignal
    notes: Optional[str] = None
    version: int = 1
    seismic_id: Optional[str] = None
    deformation_id: Optional[str] = None

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (signal, version)"""
        return UuidUtils.deterministic_uuid(self.signal.value, self.version)


class TrainingSession(BaseFiery):
    """Normalized Training Session"""

    signal: TrainingSignal
    stage: TrainingStage
    status: TrainingStatus
    samples: int
    seed: int
    git_sha: Optional[str] = None
    git_url: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    hyperparameter_pretrain_id: Optional[str] = None
    hyperparameter_lora_id: Optional[str] = None
    hyperparameter_distill_id: Optional[str] = None
    hyperparameter_prune_id: Optional[str] = None
    hyperparameter_quantize_id: Optional[str] = None
    contract_id: str
    version_id: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (contract_id, version_id, stage, seed)"""
        if not self.contract_id or not self.version_id:
            return None
        return UuidUtils.deterministic_uuid(
            self.contract_id, self.version_id, self.stage.value, self.seed
        )
