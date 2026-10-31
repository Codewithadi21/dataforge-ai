"""Explicit, read-only synchronization of the upstream public DataPulse metrics export.

This reads ONE fixed public JSON asset. It does not download arbitrary paths,
follow user supplied URLs, execute upstream code, or modify the upstream repo.
"""
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Callable
import requests

from dataforge.assistant.engine import DataForgeEngine

URL = ("https://api.github.com/repos/Codewithadi21/"
       "aegis-real-time-supply-chain-ai/contents/"
       "datapulse-ai/examples/verified_synthetic_results.json?ref=main")
FIELDS = {"rows", "test_rows", "prediction_flips", "prediction_flip_rate",
          "baseline_auc", "changed_auc", "baseline_false_negatives",
          "changed_false_negatives", "schema_checks_passed_after_shift",
          "semantic_checks_passed_after_shift"}


def refresh_public_repo_snapshot(engine: DataForgeEngine,
                                 get: Callable | None = None) -> dict:
    fetch = get or requests.get
    try:
        result = fetch(URL, timeout=12, headers={"Accept":"application/vnd.github+json"})
        result.raise_for_status()
        raw = result.content
        if len(raw) > 65_536:
            raise ValueError("Oversized GitHub response")
        envelope = json.loads(raw)
        if envelope.get("encoding") != "base64" or not isinstance(envelope.get("content"), str):
            raise ValueError("Unexpected GitHub content format")
        decoded = base64.b64decode(envelope["content"], validate=False)
        if len(decoded) > 16_384:
            raise ValueError("Oversized DataPulse metrics")
        payload = json.loads(decoded)
        if not isinstance(payload, dict) or not FIELDS <= payload.keys():
            raise ValueError("Missing required metrics")
        ints = ("rows", "test_rows", "prediction_flips", "baseline_false_negatives", "changed_false_negatives")
        for key in ints:
            if type(payload[key]) is not int or not 0 <= payload[key] <= 10_000_000:
                raise ValueError("Invalid integer metric")
        if not 0 < payload["test_rows"] <= payload["rows"] or payload["prediction_flips"] > payload["test_rows"]:
            raise ValueError("Inconsistent replay metrics")
        for key in ("prediction_flip_rate", "baseline_auc", "changed_auc"):
            val=payload[key]
            if isinstance(val,bool) or not isinstance(val,(float,int)) or not math.isfinite(val) or not 0 <= val <= 1:
                raise ValueError("Invalid float metric")
        if abs(payload["prediction_flip_rate"]-payload["prediction_flips"]/payload["test_rows"]) > 0.00015:
            raise ValueError("Replay rate and count mismatch")
        for key in ("schema_checks_passed_after_shift", "semantic_checks_passed_after_shift"):
            if type(payload[key]) is not bool:
                raise ValueError("Invalid schema or semantic flag")
        adapter=engine.registry.get("datapulse-repo-snapshot")
        record=adapter.get_incident("DP-REPO-SYN-001")
        if not record:
            raise ValueError("Pinned incident missing")
        record["metrics"]={
            "source_rows":payload["rows"],"paired_cohort_size":payload["test_rows"],
            "prediction_flip_count":payload["prediction_flips"],
            "prediction_flip_rate":payload["prediction_flip_rate"],
            "baseline_auc":payload["baseline_auc"],"changed_auc":payload["changed_auc"],
            "baseline_false_negatives":payload["baseline_false_negatives"],
            "changed_false_negatives":payload["changed_false_negatives"],
            "schema_check_passed":payload["schema_checks_passed_after_shift"],
            "semantic_check_passed":payload["semantic_checks_passed_after_shift"],
        }
        adapter._incidents=[record]
        return {"status":"fetched_and_validated","source":"public_DataPulse_GitHub_file",
                "source_blob_sha":envelope.get("sha"),
                "sha256":hashlib.sha256(decoded).hexdigest(),
                "fetched_at_utc":datetime.now(timezone.utc).isoformat(),
                "synthetic":True,"live_bigquery":False}
    except Exception as exc:
        return {"status":"failed_pinned_snapshot_unchanged", "error_type":type(exc).__name__,
                "synthetic":True,"live_bigquery":False}
