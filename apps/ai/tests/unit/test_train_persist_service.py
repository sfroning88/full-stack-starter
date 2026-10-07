"""
Author: Sean Froning
Created Date: 8.23.2026
Unit tests for TrainPersistService
"""

from unittest.mock import patch

import pytest
from fiery_python import (
    PoolFetch,
    TrainingHyperparameterDistill,
    TrainingHyperparameterLora,
    TrainingHyperparameterPretrain,
    TrainingHyperparameterPrune,
    TrainingHyperparameterQuantize,
    TrainingOptimizer,
    TrainingPrecision,
    TrainingPruningCriterion,
    TrainingQuantizeMethod,
    TrainingRateSchedule,
    TrainingSession,
    TrainingSignal,
    TrainingSparsitySchedule,
    TrainingStage,
    TrainingStatus,
    TrainingTargetModules,
)
from integrations.train.services.persist_service import TrainPersistService


def _session(**overrides) -> TrainingSession:
    payload = {
        "id": "sess-1",
        "signal": TrainingSignal.DEFORMATION,
        "stage": TrainingStage.LORA,
        "status": TrainingStatus.PENDING,
        "samples": 10,
        "seed": 42,
        "hyperparameter_lora_id": "lora-1",
        "contract_id": "contract-1",
        "version_id": "ver-1",
    }
    payload.update(overrides)
    return TrainingSession(**payload)


def test_select_version_maps_row():
    row = {
        "transform_hash": "abc",
        "manifest_path": "contract-1/abc/manifest.json",
        "shard_count": 2,
        "sample_count": 10,
        "status": TrainingStatus.COMPLETED.value,
        "contract_id": "contract-1",
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        version = TrainPersistService.select_version("ver-1")
    assert run.call_args.args[1] == ("ver-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert version.id == "ver-1"
    assert version.transform_hash == "abc"
    assert version.shard_count == 2
    assert version.status is TrainingStatus.COMPLETED
    assert version.contract_id == "contract-1"


def test_select_version_returns_none_when_empty():
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert TrainPersistService.select_version("ver-1") is None


def test_select_pretrain_maps_row():
    row = {
        "epochs": 50,
        "batch_size": 32,
        "learning_rate": 0.001,
        "optimizer": TrainingOptimizer.ADAMW.value,
        "weight_decay": "0.01",
        "lr_schedule": TrainingRateSchedule.COSINE.value,
        "seed": 42,
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        pretrain = TrainPersistService.select_pretrain("pretrain-1")
    assert run.call_args.args[1] == ("pretrain-1",)
    assert pretrain.id == "pretrain-1"
    assert pretrain.epochs == 50
    assert pretrain.optimizer is TrainingOptimizer.ADAMW
    assert pretrain.lr_schedule is TrainingRateSchedule.COSINE


def test_select_lora_maps_row():
    row = {
        "rank": 8,
        "alpha": 16,
        "dropout": 0.1,
        "epochs": 10,
        "learning_rate": 0.0003,
        "target_modules_id": "mod-1",
        "query": True,
        "key": False,
        "value": True,
        "output": False,
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        lora, modules = TrainPersistService.select_lora("lora-1")
    assert run.call_args.args[1] == ("lora-1",)
    assert run.call_args.kwargs["fetch"] is PoolFetch.ONE
    assert lora.id == "lora-1"
    assert lora.rank == 8
    assert lora.target_modules_id == "mod-1"
    assert modules.id == "mod-1"
    assert modules.query is True
    assert modules.key is False


def test_select_distill_maps_row():
    row = {
        "temperature": 4.0,
        "alpha": "0.7",
        "epochs": 30,
        "batch_size": 64,
        "learning_rate": 0.001,
        "student_architecture": "seismic_cnn_student",
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        distill = TrainPersistService.select_distill("distill-1")
    assert run.call_args.args[1] == ("distill-1",)
    assert distill.id == "distill-1"
    assert distill.temperature == 4.0
    assert distill.student_architecture == "seismic_cnn_student"


def test_select_prune_maps_row():
    row = {
        "target_sparsity": "0.7",
        "iterations": 5,
        "sparsity_schedule": TrainingSparsitySchedule.LINEAR.value,
        "finetune_epochs_per_iter": 3,
        "pruning_criterion": TrainingPruningCriterion.L1_MAGNITUDE.value,
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        prune = TrainPersistService.select_prune("prune-1")
    assert run.call_args.args[1] == ("prune-1",)
    assert prune.id == "prune-1"
    assert prune.iterations == 5
    assert prune.sparsity_schedule is TrainingSparsitySchedule.LINEAR
    assert prune.pruning_criterion is TrainingPruningCriterion.L1_MAGNITUDE


def test_select_quantize_maps_row():
    row = {
        "method": TrainingQuantizeMethod.PTQ.value,
        "precision": TrainingPrecision.INT8.value,
        "calibration_samples": 100,
        "accuracy_drop_threshold": "0.02",
        "qat_epochs": 5,
        "qat_learning_rate": 0.001,
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        quantize = TrainPersistService.select_quantize("quantize-1")
    assert run.call_args.args[1] == ("quantize-1",)
    assert quantize.id == "quantize-1"
    assert quantize.method is TrainingQuantizeMethod.PTQ
    assert quantize.precision is TrainingPrecision.INT8


@pytest.mark.parametrize(
    "select_fn,row_id",
    [
        (TrainPersistService.select_pretrain, "pretrain-1"),
        (TrainPersistService.select_lora, "lora-1"),
        (TrainPersistService.select_distill, "distill-1"),
        (TrainPersistService.select_prune, "prune-1"),
        (TrainPersistService.select_quantize, "quantize-1"),
    ],
)
def test_select_hyperparameter_returns_none_when_empty(select_fn, row_id):
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert select_fn(row_id) is None


def test_select_session_maps_row():
    row = {
        "signal": TrainingSignal.DEFORMATION.value,
        "stage": TrainingStage.LORA.value,
        "status": TrainingStatus.PENDING.value,
        "samples": 10,
        "seed": 42,
        "git_sha": "abc123",
        "git_url": None,
        "started_at": None,
        "finished_at": None,
        "error_message": None,
        "hyperparameter_pretrain_id": None,
        "hyperparameter_lora_id": "lora-1",
        "hyperparameter_distill_id": None,
        "hyperparameter_prune_id": None,
        "hyperparameter_quantize_id": None,
        "contract_id": "contract-1",
        "version_id": "ver-1",
    }
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=row,
    ) as run:
        session = TrainPersistService.select_session("sess-1")
    assert run.call_args.args[1] == ("sess-1",)
    assert session.id == "sess-1"
    assert session.signal is TrainingSignal.DEFORMATION
    assert session.stage is TrainingStage.LORA
    assert session.status is TrainingStatus.PENDING
    assert session.hyperparameter_lora_id == "lora-1"
    assert session.version_id == "ver-1"


def test_select_session_returns_none_when_empty():
    with patch(
        "integrations.train.services.persist_service.db_pool.run",
        return_value=None,
    ):
        assert TrainPersistService.select_session("sess-1") is None


@pytest.mark.parametrize(
    "stage,fk,fn_name,select_attr,row",
    [
        (
            TrainingStage.PRETRAIN,
            "hyperparameter_pretrain_id",
            "pretrain_teacher",
            "select_pretrain",
            TrainingHyperparameterPretrain(id="pretrain-1"),
        ),
        (
            TrainingStage.LORA,
            "hyperparameter_lora_id",
            "lora_screener",
            "select_lora",
            (
                TrainingHyperparameterLora(id="lora-1", target_modules_id="mod-1"),
                TrainingTargetModules(id="mod-1"),
            ),
        ),
        (
            TrainingStage.DISTILL,
            "hyperparameter_distill_id",
            "distill_student",
            "select_distill",
            TrainingHyperparameterDistill(
                id="distill-1", student_architecture="seismic_cnn_student"
            ),
        ),
        (
            TrainingStage.PRUNE,
            "hyperparameter_prune_id",
            "prune_student",
            "select_prune",
            TrainingHyperparameterPrune(id="prune-1"),
        ),
        (
            TrainingStage.QUANTIZE,
            "hyperparameter_quantize_id",
            "quantize_student",
            "select_quantize",
            TrainingHyperparameterQuantize(id="quantize-1"),
        ),
    ],
)
def test_select_hyperparameters_packs_stage_slot(stage, fk, fn_name, select_attr, row):
    session = _session(stage=stage, **{fk: "hp-1"})
    with patch(
        f"integrations.train.services.persist_service.TrainPersistService.{select_attr}",
        return_value=row,
    ):
        packed, spawned = TrainPersistService.select_hyperparameters(session)
    assert spawned == fn_name
    pretrain, screener, distill, prune, quantize = packed
    slots = {
        TrainingStage.PRETRAIN: pretrain,
        TrainingStage.LORA: screener,
        TrainingStage.DISTILL: distill,
        TrainingStage.PRUNE: prune,
        TrainingStage.QUANTIZE: quantize,
    }
    assert slots[stage] == row
    assert sum(slot is not None for slot in packed) == 1


def test_select_hyperparameters_returns_none_packed_when_missing():
    session = _session(hyperparameter_lora_id=None)
    packed, fn_name = TrainPersistService.select_hyperparameters(session)
    assert packed is None
    assert fn_name == "lora_screener"


def test_upsert_pretrain_passes_storage_dict():
    pretrain = TrainingHyperparameterPretrain()
    with patch("integrations.train.services.persist_service.db_pool.run") as run:
        TrainPersistService.upsert_pretrain(pretrain)
    assert run.call_args.args[1]["epochs"] == 50
    assert run.call_args.args[1]["optimizer"] == TrainingOptimizer.ADAMW.value


def test_upsert_lora_runs_modules_then_lora():
    modules = TrainingTargetModules()
    lora = TrainingHyperparameterLora(target_modules_id=modules.deterministic_id())
    with patch("integrations.train.services.persist_service.db_pool.run") as run:
        TrainPersistService.upsert_lora(lora, modules)
    assert run.call_count == 2
    assert run.call_args_list[0].args[1]["query"] is True
    assert run.call_args_list[1].args[1]["rank"] == 8
    assert run.call_args_list[1].args[1]["target_modules_id"] == modules.id


def test_upsert_distill_passes_storage_dict():
    distill = TrainingHyperparameterDistill(student_architecture="seismic_cnn_student")
    with patch("integrations.train.services.persist_service.db_pool.run") as run:
        TrainPersistService.upsert_distill(distill)
    assert run.call_args.args[1]["temperature"] == 4.0
    assert run.call_args.args[1]["student_architecture"] == "seismic_cnn_student"


def test_upsert_prune_passes_storage_dict():
    prune = TrainingHyperparameterPrune()
    with patch("integrations.train.services.persist_service.db_pool.run") as run:
        TrainPersistService.upsert_prune(prune)
    assert run.call_args.args[1]["iterations"] == 5
    assert (
        run.call_args.args[1]["pruning_criterion"]
        == TrainingPruningCriterion.L1_MAGNITUDE.value
    )


def test_upsert_quantize_passes_storage_dict():
    quantize = TrainingHyperparameterQuantize()
    with patch("integrations.train.services.persist_service.db_pool.run") as run:
        TrainPersistService.upsert_quantize(quantize)
    assert run.call_args.args[1]["method"] == TrainingQuantizeMethod.PTQ.value
    assert run.call_args.args[1]["precision"] == TrainingPrecision.INT8.value


def test_upsert_session_passes_storage_dict():
    session = TrainingSession(
        id="11111111-1111-1111-1111-111111111111",
        signal=TrainingSignal.DEFORMATION,
        stage=TrainingStage.LORA,
        status=TrainingStatus.PENDING,
        samples=10,
        seed=42,
        contract_id="22222222-2222-2222-2222-222222222222",
        version_id="33333333-3333-3333-3333-333333333333",
    )
    with patch("integrations.train.services.persist_service.db_pool.run") as run:
        TrainPersistService.upsert_session(session)
    run.assert_called_once()
    params = run.call_args.args[1]
    assert params["id"] == session.id
    assert params["signal"] == TrainingSignal.DEFORMATION.value
    assert params["stage"] == TrainingStage.LORA.value
    assert params["status"] == TrainingStatus.PENDING.value
    assert params["contract_id"] == session.contract_id
