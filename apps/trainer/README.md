# Fiery Trainer

FastAPI service for Fiery full stack AI/ML app.

## Local development

Run installs from **`apps/ai`** so the editable path resolves.
Use **Python 3.13** (same as **`python:3.13-slim`** in the Dockerfile).
On macOS/Homebrew this is typically `python3`.

```sh
cd apps/ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

After editing **`requirements.in`**, regenerate the lockfile:

```sh
pip install pip-tools
pip-compile -c constraints.txt -o requirements.txt requirements.in
```

**API:**

```sh
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```
