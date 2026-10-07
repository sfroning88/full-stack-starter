"""
Author: Sean Froning
Created Date: 8.19.2026
Definitions for Training structures
"""

TRAINING_CONTRACT_DEFORMATION_VERSION = 3
TRAINING_CONTRACT_SEISMIC_VERSION = 3
TRAINING_DB_FETCH_SIZE = 100
TRAINING_DB_PAGE_SIZE = 1000
TRAINING_SPLIT_ENUM = ("ai", "training_split")
TRAINING_SAMPLE_SOURCE_ENUM = ("ai", "training_sample_source")
TRAINING_SIGNAL_ENUM = ("ai", "training_signal")
TRAINING_STAGE_ENUM = ("ai", "training_stage")
TRAINING_STATUS_ENUM = ("ai", "training_status")
TRAINING_PRECISION_ENUM = ("ai", "training_precision")
TRAINING_SEISMIC_LABEL_ENUM = ("ai", "training_seismic_label")
TRAINING_DEFORMATION_LABEL_ENUM = ("ai", "training_deformation_label")
TRAINING_WINDOW_ENUM = ("ai", "training_window")
TRAINING_NORMALIZE_ENUM = ("ai", "training_normalize")
TRAINING_OPTIMIZER_ENUM = ("ai", "training_optimizer")
TRAINING_RATE_SCHEDULE_ENUM = ("ai", "training_rate_schedule")
TRAINING_SPARSITY_SCHEDULE_ENUM = ("ai", "training_sparsity_schedule")
TRAINING_PRUNING_CRITERION_ENUM = ("ai", "training_pruning_criterion")
TRAINING_QUANTIZE_METHOD_ENUM = ("ai", "training_quantize_method")
TRAINING_DEFORMATION_SOURCE_TYPE_ENUM = ("ai", "training_deformation_source_type")
TRAINING_NOISE_MODEL_ENUM = ("ai", "training_noise_model")
TRAINING_DEFORMATION_CLASS_TABLE = ("ai", "training_deformation_class")
TRAINING_SEISMIC_CLASS_TABLE = ("ai", "training_seismic_class")
TRAINING_DEFORMATION_SOURCE_TABLE = ("ai", "training_deformation_source")
TRAINING_INTERFEROGRAM_TABLE = ("ai", "training_interferogram")
TRAINING_SEISMIC_EVENT_TABLE = ("ai", "training_seismic_event")
TRAINING_SEISMIC_TABLE = ("ai", "training_seismic")
TRAINING_DEFORMATION_TABLE = ("ai", "training_deformation")
TRAINING_HYPERPARAMETER_PRETRAIN_TABLE = ("ai", "training_hyperparameter_pretrain")
TRAINING_TARGET_MODULES_TABLE = ("ai", "training_target_modules")
TRAINING_HYPERPARAMETER_LORA_TABLE = ("ai", "training_hyperparameter_lora")
TRAINING_HYPERPARAMETER_DISTILL_TABLE = ("ai", "training_hyperparameter_distill")
TRAINING_HYPERPARAMETER_PRUNE_TABLE = ("ai", "training_hyperparameter_prune")
TRAINING_HYPERPARAMETER_QUANTIZE_TABLE = ("ai", "training_hyperparameter_quantize")
TRAINING_CONTRACT_TABLE = ("ai", "training_contract")
TRAINING_SESSION_TABLE = ("ai", "training_session")
