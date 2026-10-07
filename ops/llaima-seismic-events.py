#!/usr/bin/env python3
"""
Author: Sean Froning
Created Date: 8.28.2026
Ops function for Llaima seismic events
"""

import os
from pathlib import Path
from typing import Dict, List
import h5py
import numpy as np
from dotenv import load_dotenv
from datasets import ClassLabel, Dataset, DatasetDict, Features, Sequence, Value

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

_SOURCE_DIR = Path.home() / "Downloads" / "llaima-seismic-events"
_OUTPUT_DIR = Path.home() / "Downloads" / "llaima-hf"
_HF_REPO = "sfroning88/Llaima"
_SEED = 42
_SAMPLING_HZ = 100
_STATION = "LAV"
_FILE_LABEL = (
    ("vt.hdf5", "vt"),
    ("lp.hdf5", "lp"),
    ("tr.hdf5", "tr"),
    ("tc.hdf5", "tc"),
)
_LABEL_NAMES = ["vt", "lp", "tr", "tc"]
_FEATURES = Features(
    {
        "waveform": Sequence(Value("float32")),
        "label": ClassLabel(names=_LABEL_NAMES),
        "station": Value("string"),
        "sampling_hz": Value("int32"),
        "duration_s": Value("float32"),
    }
)
_DATASET_CARD = """\
---
license: cc-by-nc-3.0
task_categories:
  - audio-classification
pretty_name: Llaima seismic events
---

# Llaima seismic events

Derived from Canário et al., Mendeley Data `10.17632/dv8nwdd36k.1` (version 1).
Traces are LAV / Z-vertical, 100 Hz, 60 s (`6000` samples), already bandpass-filtered
1–10 Hz and scaled into `[1, 2]` in the archive. Splits are stratified on `label`
with seed `42` (70 / 15 / 15).

Cite the original paper and DOI. This Hub copy is for reproducible ingest only.
"""


def _iter_file_waveforms(path: Path) -> np.ndarray:
    with h5py.File(path, "r") as handle:
        names: List[str] = []

        def collect(name: str, obj: object) -> None:
            if isinstance(obj, h5py.Dataset):
                names.append(name)

        handle.visititems(collect)
        if len(names) != 1:
            raise RuntimeError(f"{path.name} expected one dataset, found {names}")
        array = np.asarray(handle[names[0]], dtype=np.float32)
    array = np.squeeze(array)
    if array.ndim != 2:
        raise RuntimeError(
            f"{path.name} expected (N, T) after squeeze, got {array.shape}"
        )
    return array


def _load_rows(source_dir: Path) -> Dict[str, List[object]]:
    waveforms: List[List[float]] = []
    labels: List[str] = []
    stations: List[str] = []
    sampling: List[int] = []
    durations: List[float] = []
    for filename, label in _FILE_LABEL:
        path = source_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"missing {path}")
        traces = _iter_file_waveforms(path)
        for trace in traces:
            waveforms.append(trace.tolist())
            labels.append(label)
            stations.append(_STATION)
            sampling.append(_SAMPLING_HZ)
            durations.append(float(len(trace) / _SAMPLING_HZ))
    return {
        "waveform": waveforms,
        "label": labels,
        "station": stations,
        "sampling_hz": sampling,
        "duration_s": durations,
    }


def _stratified_splits(dataset: Dataset) -> DatasetDict:
    first = dataset.train_test_split(
        test_size=0.30,
        seed=_SEED,
        stratify_by_column="label",
    )
    second = first["test"].train_test_split(
        test_size=0.50,
        seed=_SEED,
        stratify_by_column="label",
    )
    return DatasetDict(
        {
            "train": first["train"],
            "validation": second["train"],
            "test": second["test"],
        }
    )


def _print_counts(splits: DatasetDict) -> None:
    for name, split in splits.items():
        counts = {label: 0 for label in _LABEL_NAMES}
        for label in split["label"]:
            counts[_LABEL_NAMES[int(label)]] += 1
        print(f"{name}: {len(split)} {counts}")


def main() -> None:
    if not _SOURCE_DIR.is_dir():
        raise FileNotFoundError(f"missing source directory {_SOURCE_DIR}")
    rows = _load_rows(_SOURCE_DIR)
    dataset = Dataset.from_dict(rows, features=_FEATURES)
    splits = _stratified_splits(dataset)
    _print_counts(splits)
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (_OUTPUT_DIR / "README.md").write_text(_DATASET_CARD, encoding="utf-8")
    splits.save_to_disk(str(_OUTPUT_DIR / "dataset"))
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN not configured")
    splits.push_to_hub(
        _HF_REPO, token=token, commit_message="Add stratified Llaima waveforms"
    )
    print(f"saved {_OUTPUT_DIR / 'dataset'}")
    print(f"pushed {_HF_REPO}")


if __name__ == "__main__":
    main()
