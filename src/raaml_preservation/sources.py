from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


LOCK_SCHEMA_VERSION = "0.1.0"
MAX_LOCK_BYTES = 5 * 1024 * 1024
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_ARTIFACT_FIELDS = {
    "id",
    "collection",
    "standard",
    "standardVersion",
    "kind",
    "normativeStatus",
    "omgFileId",
    "authoritativeUrl",
    "filename",
    "byteSize",
    "sha256",
    "redistribution",
}


class LockError(ValueError):
    pass


def _require_nonempty_string(value: Any, field: str, artifact_id: str) -> str:
    if not isinstance(value, str) or not value:
        raise LockError(f"{artifact_id}: {field} must be a non-empty string")
    return value


def _validate_filename(filename: Any, artifact_id: str) -> str:
    filename = _require_nonempty_string(filename, "filename", artifact_id)
    if filename in {".", ".."}:
        raise LockError(f"{artifact_id}: filename is not a file name")
    if Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise LockError(f"{artifact_id}: filename must not contain a path")
    return filename


def _validate_artifact(artifact: Any, index: int) -> dict[str, Any]:
    if not isinstance(artifact, dict):
        raise LockError(f"artifacts[{index}] must be an object")
    artifact_id = artifact.get("id", f"artifacts[{index}]")
    artifact_id = _require_nonempty_string(artifact_id, "id", str(artifact_id))

    missing = sorted(REQUIRED_ARTIFACT_FIELDS - artifact.keys())
    if missing:
        raise LockError(f"{artifact_id}: missing fields: {', '.join(missing)}")

    for field in (
        "collection",
        "standard",
        "standardVersion",
        "kind",
        "normativeStatus",
        "omgFileId",
    ):
        _require_nonempty_string(artifact[field], field, artifact_id)

    authoritative_url = _require_nonempty_string(
        artifact["authoritativeUrl"],
        "authoritativeUrl",
        artifact_id,
    )
    parsed_url = urlparse(authoritative_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise LockError(f"{artifact_id}: authoritativeUrl must be an HTTPS URL")

    _validate_filename(artifact["filename"], artifact_id)

    byte_size = artifact["byteSize"]
    if not isinstance(byte_size, int) or isinstance(byte_size, bool) or byte_size < 0:
        raise LockError(f"{artifact_id}: byteSize must be a non-negative integer")

    sha256 = artifact["sha256"]
    if not isinstance(sha256, str) or not SHA256_PATTERN.fullmatch(sha256):
        raise LockError(f"{artifact_id}: sha256 must be 64 lowercase hex digits")

    redistribution = artifact["redistribution"]
    if not isinstance(redistribution, dict):
        raise LockError(f"{artifact_id}: redistribution must be an object")
    if redistribution.get("status") not in {
        "unreviewed",
        "not-redistributable",
        "redistributable",
    }:
        raise LockError(f"{artifact_id}: invalid redistribution.status")
    if not isinstance(redistribution.get("committed"), bool):
        raise LockError(f"{artifact_id}: redistribution.committed must be boolean")
    return artifact


def load_lock(path: Path) -> dict[str, Any]:
    try:
        file_stat = path.stat()
    except FileNotFoundError as error:
        raise LockError(f"lock file does not exist: {path}") from error
    if file_stat.st_size > MAX_LOCK_BYTES:
        raise LockError(f"lock file exceeds {MAX_LOCK_BYTES} bytes")
    if path.is_symlink():
        raise LockError("lock file must not be a symbolic link")

    try:
        with path.open("r", encoding="utf-8") as handle:
            lock = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LockError(f"cannot read lock file: {error}") from error

    if not isinstance(lock, dict):
        raise LockError("lock root must be an object")
    if lock.get("schemaVersion") != LOCK_SCHEMA_VERSION:
        raise LockError(
            f"schemaVersion must be {LOCK_SCHEMA_VERSION!r}, "
            f"got {lock.get('schemaVersion')!r}"
        )
    if lock.get("status") not in {"partial", "complete"}:
        raise LockError("status must be 'partial' or 'complete'")

    artifacts = lock.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise LockError("artifacts must be a non-empty array")

    validated = [_validate_artifact(item, index) for index, item in enumerate(artifacts)]
    ids = [item["id"] for item in validated]
    filenames = [item["filename"] for item in validated]
    if len(ids) != len(set(ids)):
        raise LockError("artifact ids must be unique")
    if len(filenames) != len(set(filenames)):
        raise LockError("artifact filenames must be unique")
    return lock


def _hash_regular_file(path: Path) -> tuple[int, str]:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ValueError(f"cannot open without following links: {error}") from error

    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("source is not a regular file")
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return file_stat.st_size, digest.hexdigest()
    finally:
        os.close(descriptor)


def verify_sources(
    *,
    lock_path: Path,
    source_dir: Path,
    collection: str | None = None,
) -> dict[str, Any]:
    lock = load_lock(lock_path)
    artifacts = lock["artifacts"]
    if collection is not None:
        artifacts = [
            artifact
            for artifact in artifacts
            if artifact["collection"] == collection
        ]
        if not artifacts:
            raise LockError(f"collection not found in lock: {collection}")

    diagnostics: list[dict[str, Any]] = []
    checked = 0

    if source_dir.is_symlink():
        diagnostics.append(
            {
                "severity": "error",
                "code": "SOURCE_ROOT_SYMLINK",
                "message": "source directory must not be a symbolic link",
            }
        )
    elif not source_dir.is_dir():
        diagnostics.append(
            {
                "severity": "error",
                "code": "SOURCE_ROOT_MISSING",
                "message": "source directory does not exist or is not a directory",
            }
        )
    else:
        for artifact in artifacts:
            filename = artifact["filename"]
            candidate = source_dir / filename
            checked += 1
            if candidate.is_symlink():
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "SOURCE_SYMLINK",
                        "artifactId": artifact["id"],
                        "filename": filename,
                        "message": "source artifact must not be a symbolic link",
                    }
                )
                continue
            if not candidate.exists():
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "SOURCE_MISSING",
                        "artifactId": artifact["id"],
                        "filename": filename,
                        "message": "source artifact is missing",
                    }
                )
                continue
            try:
                actual_size, actual_sha256 = _hash_regular_file(candidate)
            except ValueError as error:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "SOURCE_UNSAFE",
                        "artifactId": artifact["id"],
                        "filename": filename,
                        "message": str(error),
                    }
                )
                continue

            if actual_size != artifact["byteSize"]:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "SOURCE_SIZE_MISMATCH",
                        "artifactId": artifact["id"],
                        "filename": filename,
                        "message": (
                            f"expected {artifact['byteSize']} bytes, "
                            f"got {actual_size}"
                        ),
                    }
                )
            if actual_sha256 != artifact["sha256"]:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "SOURCE_HASH_MISMATCH",
                        "artifactId": artifact["id"],
                        "filename": filename,
                        "message": (
                            f"expected SHA-256 {artifact['sha256']}, "
                            f"got {actual_sha256}"
                        ),
                    }
                )

    failed = sum(item["severity"] == "error" for item in diagnostics)
    return {
        "schemaVersion": "0.1.0",
        "command": "sources verify",
        "ok": failed == 0,
        "selection": {
            "collection": collection,
            "lockStatus": lock["status"],
        },
        "summary": {
            "checked": checked,
            "failed": failed,
        },
        "diagnostics": diagnostics,
    }


def fetch_sources(*, lock_path: Path, source_dir: Path) -> dict[str, Any]:
    lock = load_lock(lock_path)
    if source_dir.is_symlink():
        raise LockError("source directory must not be a symbolic link")
    source_dir.mkdir(parents=True, exist_ok=True)
    diagnostics: list[dict[str, Any]] = []
    checked = 0
    fetched = 0

    for artifact in lock["artifacts"]:
        checked += 1
        destination = source_dir / artifact["filename"]
        if destination.exists():
            try:
                size, digest = _hash_regular_file(destination)
            except ValueError as error:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "SOURCE_UNSAFE",
                        "artifactId": artifact["id"],
                        "message": str(error),
                    }
                )
                continue
            if size == artifact["byteSize"] and digest == artifact["sha256"]:
                continue
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "SOURCE_EXISTS_UNVERIFIED",
                    "artifactId": artifact["id"],
                    "message": "refusing to overwrite an existing unverified file",
                }
            )
            continue

        descriptor, temporary_name = tempfile.mkstemp(
            dir=source_dir,
            prefix=f".{artifact['filename']}.",
            suffix=".download",
        )
        try:
            digest = hashlib.sha256()
            downloaded = 0
            request = Request(
                artifact["authoritativeUrl"],
                headers={"User-Agent": "raaml-sysml-v2-preservation/0.1"},
            )
            with (
                os.fdopen(descriptor, "wb") as output,
                urlopen(request, timeout=30) as response,
            ):
                final_url = urlparse(response.geturl())
                if final_url.scheme != "https":
                    raise LockError(
                        f"{artifact['id']}: download redirected away from HTTPS"
                    )
                while block := response.read(1024 * 1024):
                    downloaded += len(block)
                    if downloaded > artifact["byteSize"]:
                        raise LockError(
                            f"{artifact['id']}: download exceeds locked byte size"
                        )
                    digest.update(block)
                    output.write(block)
                output.flush()
                os.fsync(output.fileno())
            if downloaded != artifact["byteSize"]:
                raise LockError(
                    f"{artifact['id']}: expected {artifact['byteSize']} bytes, "
                    f"downloaded {downloaded}"
                )
            if digest.hexdigest() != artifact["sha256"]:
                raise LockError(f"{artifact['id']}: downloaded SHA-256 does not match")
            os.replace(temporary_name, destination)
            fetched += 1
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise

    failed = sum(item["severity"] == "error" for item in diagnostics)
    return {
        "schemaVersion": "0.1.0",
        "command": "sources fetch",
        "ok": failed == 0,
        "summary": {"checked": checked, "fetched": fetched, "failed": failed},
        "diagnostics": diagnostics,
    }
