# Training Pipeline

Last updated: **August 2026**

## Design Choices

### Data Splits

It's important to accurately asses model capabilty on monitored `volcanoes`.
The pipeline tracks `is_held_out` on a per-volcano basis from the training data.

The **data leakage** concern here is training-on and cheating on the monitored volcanoes.
By keeping [**`SVZ`**](https://en.wikipedia.org/wiki/Andean_Volcanic_Belt#Southern_Volcanic_Zone) volcanoes `is_held_out=True`, accurate monitoring is possible.

### Seed Generation

The **training seed** is constant defined via `_TRAINING_SEED` per `TrainModalSpawn`.
The seed is persisted throughout the `spec` to the [`Modal workspace`](https://modal.com/docs/guide/workspaces).
The seed is used for model internal randomness (subsampling, bootstrapping, etc).

### LoRA Techniques

Currently the `optimizer` (`AdamW`) only adapts on parameters where `requires_grad`.
Similarly adaption only occurs on `qkv` instead of full `attention projection`.
Both of these choices help minimize the `cost` and `time` of `LoRA`.

## Training Methodology

### Spawned Jobs

Each `model TrainingSession` has its `training job` occur **asynchronously** off-worker.
This is why each job builds the `spec` from scratch for a per-job `payload`.
This is also why each transaction happens **atomically** with `caching`.

To prevent **training-serving skew**, only `unpacking` happens within the [`Modal workspace`](https://modal.com/docs/guide/workspaces).
The refinement process has already `wrapped`, `cropped`, `normalized` all shards.

Each job follows:

1. Build the `training_dataset` from the `job_spec`
2. Build the `training_job` from the `job_spec`
3. Initialize the `cuda` model
4. Apply `<method>` to the model
5. Score the model to collect `metrics`
6. Persist the model to `s3` bucket `models`
7. Best-effort `save_checkpoint` to `HuggingFace`
8. Send the `callback` to `apps/ai`
9. Best-effort `log_finished_run` with `mlflow`

Methods supported are `pretrain`, `lora`, `distill`, `prune`, `quantize`.

```python
def process(spec):
    loaders = build_loaders(spec)
    model = build_job(spec)
    model = model.to("cuda")
    train_model(model, loaders, spec)
    metrics, decision = score_model(spec, model, loaders)
    save_artifact(state_dict, sidecar, storage_path)
    signature = head_hmac(storage_path)
    send_callback(spec, payload)
```

```python
def fit(model, loader, spec):
    params = (param for param in model.parameters if requires_grad)
    # optimizer options: adam | adamw | sgd | rmsprop
    optimizer = optimizer_from_spec(params, spec)
    # scheduler options: constant | cosine | step | linear | warmup_cosine
    scheduler = scheduler_from_spec(optimizer, spec)
    return optimizer, scheduler
```

```python
def epoch(model, loader, optimizer, loss_fn, device):
    for x, y in loader:
        optimizer.zero_grad()
        loss_fn(model(x), y).backward()
        optimizer.step()
```

### CNN Pre-Training

For applying training a `from-scratch CNN`:

```python
def pretrain_cloud_teacher(model, loader, spec)
    optimizer, scheduler = fit(model, loader, spec)
    loss_fn = CrossEntropyLoss(weights)
    for _ in range(epochs):
        epoch(model, loader, optimizer, loss_fn, device)
        scheduler.step()
```

### Low-Rank Adapation

For applying `Low-Rank Adaption (LoRA)`:

```python
def lora_cloud_screener(model, loader, spec):
    params = (param for param in model.parameters if requires_grad)
    optimizer = AdamW(params, learning_rate, weight_decay)
    loss_fn = CrossEntropyLoss()
    for _ in range(epochs):
        for images, targets in loader:
            epoch(model, loader, optimizer, loss_fn, device)
```

### Knowledge Distillation

For `transfer learning` from `teacher CNN`:

```python
def distill_edge_student(pair, loader, student)
    optimizer, scheduler = fit(pair.student, loader, spec)
    teacher.eval()
    for _ in range(epochs):
        # KL(student/T || teacher/T) * T^2 * alpha + CE * (1-alpha)
        scheduler.step()
```

### Parameters Pruning

For applying `pruning` on `CNN weights and activations`:

```python
def prune_edge_student()
    optimizer, scheduler = fit(pair.student, loader, spec)
    loss_fn = CrossEntropyLoss(weights)
    previous = 0.0
    for step in range(steps):
        # prune weights
        prune.global_unstructured(convs, method, sparsity_at(step, spec))
        for _ in range(finetune_epochs):
            # preserve accuracy
            epoch(model, loader, optimizer, loss_fn, device)
        scheduler.step()
    prune.remove(convs)
```

### Weights Quantization

For applying `quantization` on `CNN weights`:

```python
def quantize_edge_student()
    exported = torch.export.export(model, (example,)).module()
    if method is PTQ:
        prepared = prepare_pt2e(exported, quantizer)
        for x, _ in calibrate:
            prepared(x)  # observe
    if method is QAT:
        prepared = prepare_qat_pt2e(exported, quantizer)
        optimizer, scheduler = fit(prepared, train, spec)
        for _ in range(qat_epochs):
            epoch(prepared, train, optimizer, CrossEntropyLoss(), device)
            scheduler.step() # train
    return convert_pt2e(prepared)
```

### Artifact Persistence

The trained `model` (`.safetensors`) is persisted with a JSON sidecar (`decision`, `lora`, `spec`) to `s3`.
`ModelStorageServices.save_artifact` writes weights plus sidecar; `head_hmac` is taken on the weights key.
The `model` is logged via `model ModelArtifact` and queried by the `model_registry`.

After successful `s3` write `save_checkpoint` the same bytes to `HuggingFace`.
Store `checkpoints` under repos `HF_MODEL_NAMESPACE/<registered_name>`.
On `/callback/train` best-effort log the `mlflow_run` and update experiment.

### Artifact Verification

First, artifacts received in `/callback/train` check for **Body MAC:**

```python
secret = ModelStorageServices._artifact_hmac_secret()
canonical = json.dumps(
    {
        "architecture",
        "abstention_band",
        "nonce",
        "op_version",
        "param_count",
        "precision",
        "role",
        "session_id",
        "signature",
        "sparsity",
        "storage_path",
        "threshold",
        "tier",
        "transform_hash",
    },
    separators=(",", ":"),
    sort_keys=True,
)
expected = hmac.new(
    secret, canonical.encode("utf-8"), hashlib.sha256
).hexdigest()
if not hmac.compare_digest(expected, request_hmac):
    raise error
```

Second, artifacts received in `/callback/train` check for **Object HEAD:**

```python
stored = ModelStorageServices.head_hmac(storage_path)
if not hmac.compare_digest(stored, signature):
    raise error
```

### Schema Versioning

The `training_contract` is logged by database versioning:

- **`model TrainingContract`** records each `job_spec` to be trained with hyperparameters
- **`model TrainingSession`** records each `spawned_job` to avoid duplicate jobs
- **`model ModelArtifact`** records each individual `model` artifact metadata

This creates an **indisputable and reproducible** in-code control of each `session`.

### Challenger Promotion

Via **CRON Job** any new `challengers` are evaluated for promotion over an `incumbent`.
The promotion can occur per `MODEL_REGISTRY_SLOT` from `/api/ml/promote`:

```python
MODEL_REGISTRY_SLOTS = [
    (CLOUD, SCREENER),
    (CLOUD, TEACHER),
    (EDGE, STUDENT),
]
```

First, the challenger must pass the `gate_check`:

```python
if not incumbent or challenger_metric_scores > incumbent_metric_scores:
    promote(challenger)
```

Models are scored within the [`Modal workspace`](https://modal.com/docs/guide/workspaces).

Depending on the `MODEL_REGISTRY_SLOT`, different metrics are checked:

```python
match MODEL_REGISTRY_SLOT:
    case (CLOUD, SCREENER):
        _screener_gate # RECALL, PRECISION, FALSE_POSITIVE_RATE, ABSTENTION_RATE
    case (CLOUD, TEACHER):
        _teacher_gate # MACRO_F1_SCORE
    case (EDGE, STUDENT):
        _student_gate # ACCURACY
```

Second, the challenger must pass the `budget_check`:

```python
if challenger is CLOUD:
    return passed = True
if (
    flash_kb < flash_budget_kb
    and peak_ram_kb < peak_ram_budget_kb
    and macs < macs_budget
):
    return passed = True
return passed = False
```

The logged `model ModelBudget` is persisted to record each individual evaluation.
After successful promote the `mlflow_run` is `aliased` to the registered version.
