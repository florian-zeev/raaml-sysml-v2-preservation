from __future__ import annotations

import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
from typing import Any

from . import __version__
from .adapters import (
    AdapterError,
    run_adapter,
    run_v1_corpus_adapter,
    stable_adapter_report,
)
from .conformance import run_adversarial_suite
from .facts import extract_facts, serialize_facts
from .ocl_validation import validate_ocl_corpus
from .oracle import audit_corpus
from .roundtrip import (
    canonical_json,
    compare_full_corpus,
    create_full_corpus_manifest,
    forward_full_corpus,
    render_full_corpus_v2,
    reverse_full_corpus,
)
from .schemas import validate_instance_against_schema, validate_schemas
from .sources import load_lock, verify_sources


RELEASE_SCHEMA_VERSION = "0.1.0"
CONTAINER_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_ID = re.compile(r"^[0-9a-f]{40}$")
RELEASE_TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")


class ReleaseError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def reproduce_release(
    repository_root: Path,
    output_dir: Path,
    *,
    container_digest: str,
    release_tag: str,
    require_clean: bool,
    supplied_commit: str | None = None,
    supplied_state: str | None = None,
) -> dict[str, Any]:
    if not CONTAINER_DIGEST.fullmatch(container_digest):
        raise ReleaseError(
            "RELEASE_CONTAINER_DIGEST",
            "container digest must be sha256 followed by 64 lowercase hex digits",
        )
    if not RELEASE_TAG.fullmatch(release_tag):
        raise ReleaseError(
            "RELEASE_TAG",
            "release tag must be a semantic version tag such as v0.9.0-rc.1",
        )
    commit, source_state = repository_identity(
        repository_root,
        supplied_commit=supplied_commit,
        supplied_state=supplied_state,
    )
    if require_clean and source_state != "clean":
        raise ReleaseError(
            "RELEASE_SOURCE_DIRTY",
            "reproduce --clean requires a clean source tree",
        )
    if output_dir.exists() or output_dir.is_symlink():
        raise ReleaseError(
            "RELEASE_OUTPUT_EXISTS",
            f"release output already exists: {output_dir}",
        )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(
            dir=output_dir.parent,
            prefix=f".{output_dir.name}.",
        )
    )
    try:
        report = _build_release(
            repository_root,
            temporary,
            container_digest=container_digest,
            release_tag=release_tag,
            commit=commit,
            source_state=source_state,
        )
        normalize_release_modes(temporary)
        os.replace(temporary, output_dir)
        return report
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def repository_identity(
    repository_root: Path,
    *,
    supplied_commit: str | None = None,
    supplied_state: str | None = None,
) -> tuple[str, str]:
    git_dir = repository_root / ".git"
    if git_dir.exists():
        commit = _git(repository_root, "rev-parse", "HEAD")
        status = _git(
            repository_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
        return commit, "clean" if not status else "dirty"

    commit = supplied_commit or os.environ.get("RAAML_VCS_REF")
    state = supplied_state or os.environ.get("RAAML_SOURCE_STATE")
    if not isinstance(commit, str) or not COMMIT_ID.fullmatch(commit):
        raise ReleaseError(
            "RELEASE_COMMIT_UNKNOWN",
            "a 40-character Git commit is required outside a Git checkout",
        )
    if state not in {"clean", "dirty"}:
        raise ReleaseError(
            "RELEASE_SOURCE_STATE_UNKNOWN",
            "source state must be supplied as clean or dirty outside Git",
        )
    return commit, state


def build_controlled_diff(
    canonical: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    baseline = copy.deepcopy(canonical)
    changed = copy.deepcopy(canonical)
    artifact = next(
        item
        for item in changed["artifacts"]
        if item["filename"] == "FTALib.xmi"
    )
    enumeration = next(
        item
        for item in artifact["declarations"]
        if item["kind"] == "Enumeration"
        and item["name"] == "HouseEventProbability"
    )
    literal = next(
        item for item in enumeration["literals"] if item["name"] == "NOT_OCCUR"
    )
    before = literal["name"]
    literal["name"] = "DOES_NOT_OCCUR"

    baseline_bytes = render_full_corpus_v2(baseline).encode("utf-8")
    changed_bytes = render_full_corpus_v2(changed).encode("utf-8")
    baseline_artifact = next(
        item
        for item in baseline["artifacts"]
        if item["artifactId"] == artifact["artifactId"]
    )
    baseline_manifest = create_full_corpus_manifest(
        baseline,
        baseline_artifact,
        baseline_bytes,
    )
    changed_manifest = create_full_corpus_manifest(
        changed,
        artifact,
        changed_bytes,
    )
    baseline_manifest_text = _json_text(baseline_manifest)
    changed_manifest_text = _json_text(changed_manifest)

    output_dir.mkdir(parents=True, exist_ok=True)
    v2_diff = "".join(
        difflib.unified_diff(
            baseline_bytes.decode("utf-8").splitlines(keepends=True),
            changed_bytes.decode("utf-8").splitlines(keepends=True),
            fromfile="baseline/raaml-full-corpus.sysml",
            tofile="changed/raaml-full-corpus.sysml",
        )
    )
    manifest_diff = "".join(
        difflib.unified_diff(
            baseline_manifest_text.splitlines(keepends=True),
            changed_manifest_text.splitlines(keepends=True),
            fromfile="baseline/FTALib.preservation.json",
            tofile="changed/FTALib.preservation.json",
        )
    )
    if not v2_diff or not manifest_diff:
        raise ReleaseError(
            "RELEASE_CONTROLLED_DIFF_EMPTY",
            "controlled change must affect both v2 text and its manifest",
        )
    (output_dir / "v2.diff").write_text(
        v2_diff,
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "manifest.diff").write_text(
        manifest_diff,
        encoding="utf-8",
        newline="\n",
    )
    report = {
        "schemaVersion": RELEASE_SCHEMA_VERSION,
        "documentKind": "raaml-controlled-diff-report",
        "scope": "illustrative-single-canonical-input-fact",
        "changedFact": {
            "artifactId": artifact["artifactId"],
            "owner": enumeration["id"],
            "kind": "EnumerationLiteral.name",
            "before": before,
            "after": literal["name"],
        },
        "summary": {
            "inputFactsChanged": 1,
            "v2DiffLines": len(v2_diff.splitlines()),
            "manifestDiffLines": len(manifest_diff.splitlines()),
        },
        "outputs": {
            "v2DiffSha256": _sha256(v2_diff.encode("utf-8")),
            "manifestDiffSha256": _sha256(
                manifest_diff.encode("utf-8")
            ),
        },
        "claimBoundary": (
            "This one controlled example demonstrates deterministic diff "
            "behavior only; it does not establish a general semantic-diff claim."
        ),
    }
    _write_json(output_dir / "report.json", report)
    return report


def build_stpa_walkthrough(
    full_corpus_v2: Path,
    example_fragment: Path,
    output_dir: Path,
    repository_root: Path,
) -> dict[str, Any]:
    corpus = full_corpus_v2.read_text(encoding="utf-8")
    fragment = example_fragment.read_text(encoding="utf-8")
    combined = corpus + "\n" + fragment
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "wheel-brake-with-raaml.sysml"
    model_path.write_text(combined, encoding="utf-8", newline="\n")
    validation = stable_adapter_report(
        run_adapter(repository_root, "v2", model_path)
    )
    _write_json(output_dir / "validation.json", validation)
    if not validation["ok"]:
        raise ReleaseError(
            "RELEASE_STPA_INVALID",
            "the STPA walkthrough does not pass the mandatory v2 validator",
        )
    return validation


def write_checksums(root: Path) -> list[dict[str, str]]:
    checksum_path = root / "SHA256SUMS"
    files = [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and path != checksum_path
    ]
    records = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256(path.read_bytes()),
        }
        for path in files
    ]
    checksum_path.write_text(
        "".join(
            f"{record['sha256']}  {record['path']}\n"
            for record in records
        ),
        encoding="utf-8",
        newline="\n",
    )
    return records


def normalize_release_modes(root: Path) -> None:
    paths = [root, *sorted(root.rglob("*"))]
    for path in paths:
        if path.is_symlink():
            raise ReleaseError(
                "RELEASE_SYMLINK",
                f"release output must not contain symbolic links: {path}",
            )
        if path.is_dir():
            path.chmod(0o755)
        elif path.is_file():
            path.chmod(0o644)


def _build_release(
    repository_root: Path,
    root: Path,
    *,
    container_digest: str,
    release_tag: str,
    commit: str,
    source_state: str,
) -> dict[str, Any]:
    lock = load_lock(repository_root / "standards.lock.json")
    schema_report = validate_schemas(repository_root)
    if not schema_report["ok"]:
        raise ReleaseError(
            "RELEASE_SCHEMAS",
            "one or more repository schemas or governed reports are invalid",
        )
    source_verification = verify_sources(
        lock_path=repository_root / "standards.lock.json",
        source_dir=repository_root / "sources" / "cache",
    )
    if not source_verification["ok"]:
        raise ReleaseError(
            "RELEASE_SOURCE_VERIFICATION",
            "one or more locked source inputs failed verification",
        )

    raw, canonical = extract_facts(repository_root)
    facts_dir = root / "reports" / "facts"
    facts_dir.mkdir(parents=True)
    (facts_dir / "raw-raaml-facts.json").write_bytes(serialize_facts(raw))
    (facts_dir / "canonical-raaml-facts.json").write_bytes(
        serialize_facts(canonical)
    )

    oracle_report = audit_corpus(repository_root)
    if not oracle_report["ok"]:
        raise ReleaseError("RELEASE_ORACLE", "independent oracle audit failed")
    _write_json(root / "reports" / "oracle" / "corpus-audit.json", oracle_report)

    ocl_report = stable_adapter_report(validate_ocl_corpus(repository_root))
    if not ocl_report["ok"]:
        raise ReleaseError("RELEASE_OCL", "OCL corpus validation failed")
    _write_json(root / "reports" / "ocl" / "corpus-validation.json", ocl_report)

    forward = forward_full_corpus(repository_root, root / "generated" / "forward")
    v2_report = stable_adapter_report(
        run_adapter(repository_root, "v2", forward["v2"])
    )
    if not v2_report["ok"]:
        raise ReleaseError("RELEASE_V2", "generated SysML v2 corpus is invalid")
    _write_json(root / "reports" / "validators" / "v2.json", v2_report)

    reconstructed = root / "generated" / "reconstructed"
    reverse_full_corpus(
        forward["manifests"][0].parent,
        forward["v2"],
        reconstructed,
    )
    v1_report = run_v1_corpus_adapter(repository_root, reconstructed)
    stable_v1 = {
        **v1_report,
        "results": [
            stable_adapter_report(item) for item in v1_report["results"]
        ],
    }
    if not stable_v1["ok"]:
        raise ReleaseError("RELEASE_V1", "reconstructed v1 corpus is invalid")
    _write_json(root / "reports" / "validators" / "v1.json", stable_v1)

    comparison = compare_full_corpus(repository_root, reconstructed)
    validate_instance_against_schema(
        comparison,
        repository_root
        / "schemas"
        / "full-corpus-comparison-report.schema.json",
    )
    _write_json(
        root / "reports" / "conformance" / "full-corpus-comparison.json",
        comparison,
    )
    if not comparison["ok"]:
        raise ReleaseError(
            "RELEASE_FACT_DIFFERENCE",
            f"{comparison['summary']['differences']} canonical difference(s)",
        )

    adversarial = run_adversarial_suite(
        repository_root,
        root / "work" / "adversarial",
        forward,
        reconstructed,
        comparison,
    )
    if any(not item["passed"] for item in adversarial):
        raise ReleaseError(
            "RELEASE_ADVERSARIAL",
            "one or more adversarial cases failed",
        )
    _write_json(
        root / "reports" / "conformance" / "adversarial-cases.json",
        {
            "schemaVersion": RELEASE_SCHEMA_VERSION,
            "documentKind": "raaml-adversarial-report",
            "ok": True,
            "summary": {
                "checked": len(adversarial),
                "failed": 0,
            },
            "cases": adversarial,
        },
    )

    diff_report = build_controlled_diff(
        canonical,
        root / "reports" / "controlled-diff",
    )
    walkthrough_report = build_stpa_walkthrough(
        forward["v2"],
        repository_root
        / "examples"
        / "stpa-walkthrough"
        / "wheel-brake.sysml",
        root / "examples" / "stpa-walkthrough",
        repository_root,
    )
    shutil.rmtree(root / "work")

    report = {
        "schemaVersion": RELEASE_SCHEMA_VERSION,
        "documentKind": "raaml-preservation-release-report",
        "implementationVersion": __version__,
        "releaseTag": release_tag,
        "git": {
            "commit": commit,
            "state": source_state,
        },
        "container": {
            "digest": container_digest,
            "targetPlatform": "linux/amd64",
        },
        "standardsLockSha256": _sha256(
            (repository_root / "standards.lock.json").read_bytes()
        ),
        "sourceHashes": {
            item["filename"]: item["sha256"]
            for item in lock["artifacts"]
        },
        "schemas": _schema_inventory(repository_root),
        "tools": {
            "python": platform.python_version(),
            "mandatoryV1Adapter": stable_v1["results"][0]["adapterVersion"],
            "mandatoryV2Adapter": v2_report["adapterVersion"],
            "oclParser": ocl_report["parser"],
            "lockedRuntimeInputs": [
                {
                    "id": item["id"],
                    "version": item["standardVersion"],
                    "sha256": item["sha256"],
                }
                for item in lock["artifacts"]
                if item["id"]
                in {
                    "sysml-v2-pilot-2026-04-distribution",
                    "temurin-jdk-21.0.11-linux-x64",
                    "temurin-jdk-21.0.11-macos-aarch64",
                }
            ],
        },
        "summary": {
            "sourceArtifacts": 17,
            "reconstructedArtifacts": 17,
            "canonicalFactsSha256": comparison["summary"][
                "sourceFactsSha256"
            ],
            "canonicalDifferences": comparison["summary"]["differences"],
            "adversarialCases": len(adversarial),
            "failedAdversarialCases": 0,
            "v1ValidationErrors": stable_v1["summary"]["failed"],
            "v2ValidationErrors": v2_report["summary"]["failed"],
            "oclExpressions": ocl_report["summary"]["checked"],
            "walkthroughValidationErrors": walkthrough_report["summary"][
                "failed"
            ],
            "controlledInputFactsChanged": diff_report["summary"][
                "inputFactsChanged"
            ],
        },
        "independentReproduction": {
            "status": "not-yet-performed",
            "statement": (
                "Reproduction has so far been performed only by the project "
                "team and automated project infrastructure."
            ),
        },
    }
    report["publishedArtifacts"] = (
        sum(1 for path in root.rglob("*") if path.is_file()) + 1
    )
    validate_instance_against_schema(
        report,
        repository_root / "schemas" / "release-report.schema.json",
    )
    _write_json(root / "RELEASE.json", report)
    records = write_checksums(root)
    if len(records) != report["publishedArtifacts"]:
        raise ReleaseError(
            "RELEASE_ARTIFACT_COUNT",
            "published artifact count changed while checksums were generated",
        )
    return report


def _schema_inventory(repository_root: Path) -> list[dict[str, str]]:
    result = []
    for path in sorted((repository_root / "schemas").glob("*.schema.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        result.append(
            {
                "filename": path.name,
                "draft": value["$schema"],
                "id": value["$id"],
                "sha256": _sha256(path.read_bytes()),
            }
        )
    return result


def _git(repository_root: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=repository_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if process.returncode != 0:
        raise ReleaseError(
            "RELEASE_GIT",
            process.stderr.strip() or "Git command failed",
        )
    return process.stdout.strip()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_text(value), encoding="utf-8", newline="\n")


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
