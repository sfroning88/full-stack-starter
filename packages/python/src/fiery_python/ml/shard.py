"""
Author: Sean Froning
Created Date: 8.20.2026
Web dataset packing for transformed deformation samples
"""

import io
import json
import tarfile
import numpy as np
from typing import Any, Dict, List, Tuple

_PHASE_SUFFIX = "phase.npy"
_LABEL_SUFFIX = "label.json"


class Shard:
    """Deterministic tar of (key, phase array, label) samples"""

    @staticmethod
    def _add_bytes(tar: tarfile.TarFile, name: str, body: bytes) -> None:
        """Append one tar member"""
        info = tarfile.TarInfo(name=name)
        info.size = len(body)
        info.mtime = 0
        info.uid = 0
        info.gid = 0
        info.uname = ""
        info.gname = ""
        tar.addfile(info, io.BytesIO(body))

    @classmethod
    def _add_npy(cls, tar: tarfile.TarFile, name: str, array: np.ndarray) -> None:
        """Serialize array and save down"""
        buf = io.BytesIO()
        np.save(buf, array, allow_pickle=False)
        cls._add_bytes(tar, name, buf.getvalue())

    @classmethod
    def write(cls, samples: List[Tuple[str, np.ndarray, Dict[str, Any]]]) -> bytes:
        """Pack samples into web dataset tar; return bytes"""
        keys = [key for key, _, _ in samples]
        if any(not key for key in keys):
            raise ValueError("missing required sample key")
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate sample key")
        ordered = sorted(samples, key=lambda sample: sample[0])
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            for key, phase, label in ordered:
                cls._add_npy(
                    tar,
                    f"{key}.{_PHASE_SUFFIX}",
                    phase,
                )
                cls._add_bytes(
                    tar,
                    f"{key}.{_LABEL_SUFFIX}",
                    json.dumps(label, sort_keys=True, separators=(",", ":")).encode(
                        "utf-8"
                    ),
                )
        return buf.getvalue()

    @classmethod
    def read(cls, body: bytes) -> List[Tuple[str, np.ndarray, Dict[str, Any]]]:
        """Unpack tar bytes; group by key; order by key"""
        members: Dict[str, Dict[str, bytes]] = {}
        with tarfile.open(fileobj=io.BytesIO(body), mode="r") as tar:
            for info in tar.getmembers():
                if not info.isfile():
                    continue
                fileobj = tar.extractfile(info)
                if fileobj is None:
                    continue
                if info.name.endswith(f".{_PHASE_SUFFIX}"):
                    suffix = _PHASE_SUFFIX
                elif info.name.endswith(f".{_LABEL_SUFFIX}"):
                    suffix = _LABEL_SUFFIX
                else:
                    continue
                key = info.name[: -(len(suffix) + 1)]
                members.setdefault(key, {})[suffix] = fileobj.read()
        samples = []
        for key in sorted(members):
            files = members[key]
            phase = np.load(io.BytesIO(files[_PHASE_SUFFIX]), allow_pickle=False)
            label = json.loads(files[_LABEL_SUFFIX].decode("utf-8"))
            samples.append((key, phase, label))
        return samples

    @staticmethod
    def write_manifest(payload: Dict[str, Any]) -> bytes:
        """JSON bytes for manifest (shard_count, sample_count, keys)"""
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
