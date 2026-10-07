#!/usr/bin/env python3
"""
Author: Sean Froning
Created Date: 9.21.2026
Setup mlflow db
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url
from mlflow.store.tracking.sqlalchemy_store import SqlAlchemyStore

load_dotenv(Path(__file__).resolve().parents[1] / ".env", interpolate=False)

MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI")
if not MLFLOW_TRACKING_URI or not isinstance(MLFLOW_TRACKING_URI, str):
    raise EnvironmentError("misconfigured MLFLOW_TRACKING_URI")

try:
    import mlflow

    mlflow.doctor()
except ImportError:
    raise ImportError("missing mlflow install")

_TEMP_ARTIFACTS = "file:///tmp/mlflow-artifacts"


def _verify_sql_alchemy_parse() -> None:
    try:
        print(make_url(MLFLOW_TRACKING_URI))
    except Exception as err:
        print(f"Error: {err}")
        sys.exit(1)


def main() -> None:
    _verify_sql_alchemy_parse()
    print("Running mlflow setup command")
    try:
        # env = os.environ.copy()
        # env["PGOPTIONS"] = "-c search_path=mlflow"
        os.environ["PGOPTIONS"] = "-c search_path=mlflow"
        SqlAlchemyStore(
            db_uri=MLFLOW_TRACKING_URI,
            default_artifact_root=_TEMP_ARTIFACTS,
        )
        # subprocess.run(
        # ["mlflow", "db", "upgrade", MLFLOW_TRACKING_URI],
        # check=True,
        # env=env,
        # )
    except Exception as err:
        print(f"Error: {err}")
        sys.exit(1)
    print("Finished setting up mlflow")


if __name__ == "__main__":
    main()
