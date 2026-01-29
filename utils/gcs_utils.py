"""
Compatibility wrapper for `utils.gcs_utils`.

The project root contains `gcs_utils.py` with `GCSHelper`.
Some scripts (e.g. `test_config.py`) expect a `GCSClient` class with a few helpers.
We provide a thin adapter on top of `GCSHelper` / google-cloud-storage client.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from google.cloud import storage

from gcs_utils import GCSHelper


@dataclass
class GCSClient:
    """Minimal GCS client adapter expected by `test_config.py`."""

    credentials_path: str
    project_id: str

    def __post_init__(self) -> None:
        # We rely on GOOGLE_APPLICATION_CREDENTIALS being set by Settings.
        # If it's not set, google-cloud-storage will fall back to default credentials.
        self.client = storage.Client(project=self.project_id)

    @staticmethod
    def _parse_gcs_uri(gcs_uri: str) -> Tuple[str, str]:
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        bucket_and_path = gcs_uri[5:]
        parts = bucket_and_path.split("/", 1)
        bucket = parts[0]
        blob = parts[1] if len(parts) > 1 else ""
        return bucket, blob

    def file_exists(self, gcs_uri: str) -> bool:
        bucket_name, blob_name = self._parse_gcs_uri(gcs_uri)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()

    def get_file_info(self, gcs_uri: str) -> Dict[str, object]:
        bucket_name, blob_name = self._parse_gcs_uri(gcs_uri)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.reload()  # fetch metadata

        created: Optional[datetime] = getattr(blob, "time_created", None)
        created_str = (
            created.astimezone(timezone.utc).isoformat() if isinstance(created, datetime) else ""
        )

        return {
            "size": int(getattr(blob, "size", 0) or 0),
            "content_type": getattr(blob, "content_type", "") or "",
            "created": created_str,
        }


__all__ = ["GCSHelper", "GCSClient"]

