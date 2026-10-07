# Runtime Inference

Last updated: **August 2026**

## Design Choices

### Transformations

`Transformations` are re-applied on the `unrefined` cache.
Training consumes **frozen** shards.
This allows the live `contract` to match the `sidecar`.

Tradeoffs of this choice:

[+] Serving can assert `transform_hash` and `op_version` equivalence
[+] `low_coherence` frames can be `abstained` during serving time
[+] `low_snr` waveforms can be `abstained` during serving time
[-] every inference pays `cache_latency` and `transformation_latency`

### Abstentions

The `abstained_reason` is persisted:

```python
class InferenceAbstainReason(str, Enum):
    LOW_COHERENCE
    LOW_SNR
    TRANSFORM_REJECTED
    CONTRACT_MISMATCH
    LOW_CONFIDENCE
```

## Serving Service

### Model Serialization

Each `model` is retrieved from its `s3 location` as a **self-consistent artifact**.
After verification the model loads to its `key = (tier, role)` slot in `registry`.

Artifact retrieval fetches either:

- the `.safetensors` object and its `JSON sidecar` (`FP32` artifacts)
- the `bytes` package and its `JSON sidecar` (`INT8` artifacts)

The `registry` saves the model to disk in the local in-memory process.
The artifact bundle allows the model to be loaded without `training-serving skew`.

Rigorous **model lineage** tracks the complete `training_pipeline` applied:

- `hyperparameters` for that `session_id`
- `op_version` of the `Transformation` applied
- `transform_hash` of the `Transformation` equivalent
- `threshold` and `abstention_band` included in `sidecar`

### Model Warmup

Upon service start, **hot loading** prevents `cold start latency` with `lifespan`.
This allows for immediate inference from `apps/dashboard` upon startup completion.

### Model Registry

The `load_artifact` method uses `storage_path` to fetch the `.safetensors` artifact.
By default only the `last_promoted` model per `key = (tier, role)` is loaded.
A force reload can be triggered via `force = True`.

The registry relies on **hot swapping** to use the best available model:

1. Automatic webhook trigger from `apps/ai` with **winner promotion**
2. `jobs/dispatch_models_reload` as a **fail-safe** to asynchronously check

### Inference Requests

To make a single `inferences`:

```python
class InferenceSingleRequest:
    tier: ModelTier
    role: ModelRole
    interferogram_id: Optional[str] = None
    seismic_event_id: Optional[str] = None
    volcano_id: Optional[str] = None

    def validate_payload(self):
        return (
            self.interferogram_id
            XOR self.seismic_event_id
            XOR self.self.volcano_id
        )

class InferenceSingleResponse:
    result: InferenceOutcome
    artifact_id: str
    transform_hash: str
```

To cache batch `inferences`:

```python
class InferenceBatchRequest:
    tier: ModelTier
    role: ModelRole

class InferenceSingleResponse:
    job_ids: List[str]
```

After **warm loading** `run` is called to compile:

```python
class InferenceOutcome:
    artifact_id: str
    transform_hash: str
    op_version: int
    threshold_used: Decimal
    abstention_band: Decimal
    abstained: bool = False
    abstained_reason: Optional[InferenceAbstainReason] = None
    latency_ms: Optional[Decimal] = None
    inferred_at: datetime
    probabilities: Dict[str, Decimal]
    label: Optional[TrainingDeformationLabel] = None
    score: Optional[Decimal] = None
    interferogram_id: Optional[str] = None
    volcano_id: Optional[str] = None
```

### Serving Methodology

To serve the `InferenceOutcome`:

```python
def infer(key, sample):
    model, metadata = registry.get(key)
    tensor = preprocess(metadata, sample)  # or abstain
    probability = softmax(model(tensor))
    return decide(probability, metadata.preprocessing)  # threshold, band
```
