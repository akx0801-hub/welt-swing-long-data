#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = "PROVENANCE_P0_V1"
REQUIRED_FIELDS = (
    "Artifact_ID",
    "Snapshot_ID",
    "Source_ID",
    "Source_Authority",
    "Source_AsOf",
    "Retrieved_At",
    "Content_Hash",
    "Schema_Version",
    "Population_or_Domain",
    "Currentness_Status",
    "Evidence_Strength",
)
SOURCE_AUTHORITIES = frozenset({
    "AUTHORITATIVE",
    "PRIMARY_EVIDENCE",
    "CROSSCHECK",
    "RESEARCH_ONLY",
})
CURRENTNESS_STATES = frozenset({
    "CURRENT",
    "STALE",
    "UNKNOWN",
    "SUPERSEDED",
    "HISTORICAL",
})
EVIDENCE_STRENGTHS = frozenset({
    "STRONG",
    "MEDIUM",
    "WEAK",
    "INSUFFICIENT",
})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")


class ValidationResult(dict):
    @property
    def ok(self) -> bool:
        return self.get("result") == "PASS"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _slug(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-")
    token = re.sub(r"-+", "-", token)
    if not token:
        raise ValueError("empty slug")
    return token.upper()


def _parse_source_asof(value: str) -> tuple[str, date | datetime]:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Source_AsOf must be non-empty")
    text = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        parsed = date.fromisoformat(text)
        return parsed.strftime("%Y%m%d"), parsed
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Source_AsOf datetime must include timezone")
    normalized = parsed.astimezone(timezone.utc)
    return normalized.strftime("%Y%m%dT%H%M%SZ"), normalized


def _parse_retrieved_at(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Retrieved_At must be non-empty")
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Retrieved_At must include timezone")
    return parsed.astimezone(timezone.utc)


def build_snapshot_id(population_or_domain: str, source_id: str, source_asof: str, schema_version: str) -> str:
    asof_token, _ = _parse_source_asof(source_asof)
    return "WS-PROV-{}-{}-{}-{}".format(
        _slug(population_or_domain),
        _slug(source_id),
        asof_token,
        _slug(schema_version),
    )


def _fail(code: str, detail: str = "") -> ValidationResult:
    result = ValidationResult(result="FAIL", reason_code=code)
    if detail:
        result["detail"] = detail
    return result


def validate_manifest(
    manifest: dict,
    repo_root: Path,
    *,
    allowed_source_ids: Iterable[str] | None = None,
) -> ValidationResult:
    if not isinstance(manifest, dict):
        return _fail("MANIFEST_NOT_OBJECT")

    missing = [field for field in REQUIRED_FIELDS if field not in manifest or manifest[field] in (None, "")]
    if missing:
        return _fail("MISSING_FIELD", ",".join(missing))

    extras = sorted(set(manifest) - set(REQUIRED_FIELDS))
    if extras:
        return _fail("UNSUPPORTED_FIELD", ",".join(extras))

    if manifest["Schema_Version"] != SCHEMA_VERSION:
        return _fail("UNSUPPORTED_SCHEMA_VERSION", str(manifest["Schema_Version"]))

    if manifest["Source_Authority"] not in SOURCE_AUTHORITIES:
        return _fail("INVALID_ENUM", "Source_Authority")
    if manifest["Currentness_Status"] not in CURRENTNESS_STATES:
        return _fail("INVALID_ENUM", "Currentness_Status")
    if manifest["Evidence_Strength"] not in EVIDENCE_STRENGTHS:
        return _fail("INVALID_ENUM", "Evidence_Strength")

    source_id = manifest["Source_ID"]
    if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
        return _fail("SOURCE_REFERENCE_INVALID", "Source_ID syntax")
    if allowed_source_ids is not None and source_id not in set(allowed_source_ids):
        return _fail("SOURCE_REFERENCE_INVALID", source_id)

    try:
        _parse_source_asof(manifest["Source_AsOf"])
    except (TypeError, ValueError):
        return _fail("INVALID_TIMESTAMP", "Source_AsOf")
    try:
        _parse_retrieved_at(manifest["Retrieved_At"])
    except (TypeError, ValueError):
        return _fail("INVALID_TIMESTAMP", "Retrieved_At")

    content_hash = manifest["Content_Hash"]
    if not isinstance(content_hash, str) or not SHA256_RE.fullmatch(content_hash):
        return _fail("INVALID_SHA256", "Content_Hash")

    try:
        expected_snapshot = build_snapshot_id(
            manifest["Population_or_Domain"],
            source_id,
            manifest["Source_AsOf"],
            manifest["Schema_Version"],
        )
    except (TypeError, ValueError):
        return _fail("SNAPSHOT_ID_INVALID", "cannot derive")
    if manifest["Snapshot_ID"] != expected_snapshot:
        return _fail("SNAPSHOT_ID_INVALID", expected_snapshot)

    artifact_id = manifest["Artifact_ID"]
    if not isinstance(artifact_id, str) or not artifact_id.strip():
        return _fail("MISSING_FIELD", "Artifact_ID")
    artifact_rel = Path(artifact_id)
    if artifact_rel.is_absolute() or ".." in artifact_rel.parts:
        return _fail("ARTIFACT_ID_INVALID", artifact_id)
    artifact = (repo_root / artifact_rel).resolve()
    root = repo_root.resolve()
    if root not in artifact.parents and artifact != root:
        return _fail("ARTIFACT_ID_INVALID", artifact_id)
    if not artifact.is_file():
        return _fail("ARTIFACT_NOT_FOUND", artifact_id)

    actual_hash = sha256_file(artifact)
    if actual_hash != content_hash:
        return _fail("HASH_MISMATCH", f"expected={content_hash};actual={actual_hash}")

    return ValidationResult(
        result="PASS",
        reason_code="OK",
        Artifact_ID=artifact_id,
        Snapshot_ID=manifest["Snapshot_ID"],
        Content_Hash=actual_hash,
    )


def validate_manifest_file(
    manifest_path: Path,
    repo_root: Path,
    *,
    allowed_source_ids: Iterable[str] | None = None,
) -> ValidationResult:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _fail("MANIFEST_NOT_FOUND", str(manifest_path))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _fail("MANIFEST_INVALID_JSON", str(manifest_path))
    return validate_manifest(manifest, repo_root, allowed_source_ids=allowed_source_ids)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a WELT-SWING provenance/currentness snapshot P0 sidecar.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--allowed-source-id", action="append", default=None)
    args = parser.parse_args()

    result = validate_manifest_file(
        args.manifest,
        args.repo_root,
        allowed_source_ids=args.allowed_source_id,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
