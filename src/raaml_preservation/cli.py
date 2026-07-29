from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest

from . import __version__
from .adapters import (
    AdapterError,
    bootstrap_tooling,
    build_adapter,
    run_adapter,
)
from .facts import (
    FactExtractionError,
    count_facts,
    extract_facts,
    serialize_facts,
)
from .roundtrip import (
    RoundTripError,
    canonical_json,
    compare_reconstructed,
    forward_slice,
    reverse_slice,
)
from .oracle import EXPECTED_TOTALS, audit_corpus
from .ocl_validation import validate_ocl_corpus
from .sources import LockError, fetch_sources, load_lock, verify_sources
from .transformation import (
    analyze_constraint_transformation_surface,
    analyze_corpus_transformation_surface,
    analyze_property_transformation_surface,
    audit_transformation_matrix,
)
from .schemas import (
    SchemaValidationError,
    validate_instance_against_schema,
    validate_schemas,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    try:
        os.fchmod(descriptor, 0o644)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _sources_verify(args: argparse.Namespace) -> int:
    try:
        report = verify_sources(
            lock_path=args.lock,
            source_dir=args.source_dir,
            collection=args.collection,
        )
    except LockError as error:
        report = {
            "schemaVersion": "0.1.0",
            "command": "sources verify",
            "ok": False,
            "summary": {"checked": 0, "failed": 1},
            "diagnostics": [
                {
                    "severity": "error",
                    "code": "LOCK_INVALID",
                    "message": str(error),
                }
            ],
        }

    _write_json_atomic(args.diagnostics, report)
    summary = report["summary"]
    if report["ok"]:
        print(
            f"Verified {summary['checked']} source artifact(s); "
            f"diagnostics: {args.diagnostics}"
        )
        return 0

    print(
        f"Source verification failed: {summary['failed']} error(s); "
        f"diagnostics: {args.diagnostics}",
        file=sys.stderr,
    )
    for diagnostic in report["diagnostics"]:
        if diagnostic["severity"] == "error":
            print(
                f"{diagnostic['code']}: {diagnostic['message']}",
                file=sys.stderr,
            )
    return 1


def _sources_fetch(args: argparse.Namespace) -> int:
    try:
        report = fetch_sources(
            lock_path=args.lock,
            source_dir=args.source_dir,
        )
    except (LockError, OSError) as error:
        report = {
            "schemaVersion": "0.1.0",
            "command": "sources fetch",
            "ok": False,
            "summary": {"checked": 0, "fetched": 0, "failed": 1},
            "diagnostics": [
                {
                    "severity": "error",
                    "code": "SOURCE_FETCH_FAILED",
                    "message": str(error),
                }
            ],
        }
    _write_json_atomic(args.diagnostics, report)
    summary = report["summary"]
    if report["ok"]:
        print(
            f"Fetched {summary['fetched']} of {summary['checked']} locked "
            f"source artifact(s); diagnostics: {args.diagnostics}"
        )
        return 0

    print(
        f"Source fetch failed: {summary['failed']} error(s); "
        f"diagnostics: {args.diagnostics}",
        file=sys.stderr,
    )
    for diagnostic in report["diagnostics"]:
        if diagnostic["severity"] == "error":
            print(
                f"{diagnostic['code']}: {diagnostic['message']}",
                file=sys.stderr,
            )
    return 1


def _path(value: str) -> Path:
    return Path(value)


def _tests_unit(args: argparse.Namespace) -> int:
    suite = unittest.defaultTestLoader.discover(
        str(REPOSITORY_ROOT / "tests"),
        pattern="test_*.py",
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failures = len(result.failures) + len(result.errors)
    report = {
        "schemaVersion": "0.1.0",
        "command": "tests unit",
        "ok": result.wasSuccessful(),
        "summary": {
            "checked": result.testsRun,
            "failed": failures,
        },
        "diagnostics": [
            {
                "severity": "error",
                "code": "UNIT_TEST_FAILURE",
                "message": test.id(),
            }
            for test, _traceback in result.failures + result.errors
        ],
    }
    _write_json_atomic(args.diagnostics, report)
    return 0 if result.wasSuccessful() else 1


def _tests_milestone_zero(args: argparse.Namespace) -> int:
    fixtures = REPOSITORY_ROOT / "fixtures" / "milestone-0"
    cases = (
        ("v2-valid", "v2", fixtures / "minimal-valid.sysml", True),
        ("v2-invalid", "v2", fixtures / "minimal-invalid.sysml", False),
        ("v1-profile", "v1", fixtures / "minimal-v1-profile.xmi", True),
        ("v1-library", "v1", fixtures / "minimal-v1-library.xmi", True),
        (
            "v1-invalid-reference",
            "v1",
            fixtures / "minimal-v1-invalid-reference.xmi",
            False,
        ),
        (
            "v1-core-profile",
            "v1",
            REPOSITORY_ROOT / "sources" / "cache" / "CoreRAAML.xmi",
            True,
        ),
        (
            "v1-core-library",
            "v1",
            REPOSITORY_ROOT / "sources" / "cache" / "CoreRAAMLLib.xmi",
            True,
        ),
        ("ocl-valid", "ocl", fixtures / "ocl-valid.txt", True),
        ("ocl-invalid", "ocl", fixtures / "ocl-invalid.txt", False),
    )
    diagnostics: list[dict[str, str]] = []
    try:
        build_adapter(REPOSITORY_ROOT)
        for name, mode, path, expected in cases:
            result = run_adapter(REPOSITORY_ROOT, mode, path)
            if bool(result["ok"]) != expected:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "MILESTONE_ZERO_EXPECTATION",
                        "message": (
                            f"{name}: expected ok={expected}, "
                            f"got {result['ok']!r}"
                        ),
                    }
                )
            if name == "v2-valid" and any(result["errorCategories"].values()):
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "V2_CATEGORY_NOT_ZERO",
                        "message": "valid v2 fixture has a nonzero error category",
                    }
                )
            if name == "ocl-valid":
                required = {"Situation", "allInstances", "closure", "from"}
                missing = required - set(result["referencedNames"])
                if missing:
                    diagnostics.append(
                        {
                            "severity": "error",
                            "code": "OCL_AST_NAME_MISSING",
                            "message": f"OCL AST names missing: {sorted(missing)}",
                        }
                    )
    except AdapterError as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": "MILESTONE_ZERO_ADAPTER",
                "message": str(error),
            }
        )
    report = {
        "schemaVersion": "0.1.0",
        "command": "tests milestone-0",
        "ok": not diagnostics,
        "summary": {"checked": len(cases), "failed": len(diagnostics)},
        "diagnostics": diagnostics,
    }
    _write_json_atomic(args.diagnostics, report)
    return 0 if report["ok"] else 1


def _tests_milestone_one(args: argparse.Namespace) -> int:
    diagnostics: list[dict[str, str]] = []
    checked = 0
    try:
        raw, canonical = extract_facts(REPOSITORY_ROOT)
        checked += 17
        validate_instance_against_schema(
            raw,
            REPOSITORY_ROOT / "schemas" / "raw-raaml-facts.schema.json",
        )
        validate_instance_against_schema(
            canonical,
            REPOSITORY_ROOT / "schemas" / "canonical-raaml-facts.schema.json",
        )
        raw_again, canonical_again = extract_facts(REPOSITORY_ROOT)
        if serialize_facts(raw) != serialize_facts(raw_again):
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "FACT_RAW_NONDETERMINISTIC",
                    "message": "two raw extractions are not byte-identical",
                }
            )
        if serialize_facts(canonical) != serialize_facts(canonical_again):
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "FACT_CANONICAL_NONDETERMINISTIC",
                    "message": "two canonical extractions are not byte-identical",
                }
            )
        actual_counts = count_facts(canonical)
        if actual_counts != EXPECTED_TOTALS:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "FACT_COUNT_MISMATCH",
                    "message": (
                        f"expected {EXPECTED_TOTALS!r}, got {actual_counts!r}"
                    ),
                }
            )
        oracle_report = audit_corpus(REPOSITORY_ROOT)
        if not oracle_report["ok"]:
            diagnostics.extend(oracle_report["diagnostics"])
        elif oracle_report["counts"] != actual_counts:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "FACT_ORACLE_DISAGREEMENT",
                    "message": "production and independent corpus counts differ",
                }
            )
        ocl_report = validate_ocl_corpus(REPOSITORY_ROOT)
        checked += ocl_report["summary"]["checked"]
        if not ocl_report["ok"]:
            diagnostics.extend(ocl_report["diagnostics"])
    except (FactExtractionError, SchemaValidationError, OSError) as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": getattr(error, "code", "MILESTONE_ONE_FAILURE"),
                "message": str(error),
            }
        )
    report = {
        "schemaVersion": "0.1.0",
        "command": "tests milestone-1",
        "ok": not diagnostics,
        "summary": {
            "checked": checked,
            "failed": len(diagnostics),
        },
        "diagnostics": diagnostics,
    }
    _write_json_atomic(args.diagnostics, report)
    return 0 if report["ok"] else 1


def _forward_command(args: argparse.Namespace) -> int:
    diagnostics: list[dict[str, str]] = []
    try:
        result = forward_slice(REPOSITORY_ROOT, args.output_dir)
        validate_instance_against_schema(
            json.loads(result["manifest"].read_text(encoding="utf-8")),
            REPOSITORY_ROOT / "schemas" / "preservation-manifest.schema.json",
        )
        validate_instance_against_schema(
            result["facts"],
            REPOSITORY_ROOT / "schemas" / "canonical-raaml-facts.schema.json",
        )
    except (FactExtractionError, RoundTripError, SchemaValidationError, OSError) as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": getattr(error, "code", "FORWARD_FAILED"),
                "message": str(error),
            }
        )
    report = {
        "schemaVersion": "0.1.0",
        "command": "forward",
        "ok": not diagnostics,
        "summary": {"checked": 1, "failed": len(diagnostics)},
        "diagnostics": diagnostics,
    }
    _write_json_atomic(args.diagnostics, report)
    return 0 if report["ok"] else 1


def _reverse_command(args: argparse.Namespace) -> int:
    diagnostics: list[dict[str, str]] = []
    checked = 0
    try:
        paths = reverse_slice(args.manifest, args.v2, args.output_dir)
        checked = len(paths)
    except (RoundTripError, OSError) as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": getattr(error, "code", "REVERSE_FAILED"),
                "message": str(error),
            }
        )
    report = {
        "schemaVersion": "0.1.0",
        "command": "reverse",
        "ok": not diagnostics,
        "summary": {"checked": checked, "failed": len(diagnostics)},
        "diagnostics": diagnostics,
    }
    _write_json_atomic(args.diagnostics, report)
    return 0 if report["ok"] else 1


def _compare_command(args: argparse.Namespace) -> int:
    diagnostics: list[dict[str, str]] = []
    comparison: dict[str, Any] | None = None
    try:
        comparison = compare_reconstructed(
            REPOSITORY_ROOT,
            args.manifest,
            args.reconstructed_dir,
        )
        if not comparison["ok"]:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "ROUNDTRIP_FACT_DIFFERENCE",
                    "message": (
                        f"{comparison['summary']['differences']} canonical "
                        "fact difference(s)"
                    ),
                }
            )
        validate_instance_against_schema(
            comparison,
            REPOSITORY_ROOT / "schemas" / "roundtrip-report.schema.json",
        )
        _write_json_atomic(args.output, comparison)
    except (FactExtractionError, RoundTripError, OSError, json.JSONDecodeError) as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": getattr(error, "code", "COMPARE_FAILED"),
                "message": str(error),
            }
        )
    report = {
        "schemaVersion": "0.1.0",
        "command": "compare",
        "ok": not diagnostics,
        "summary": {
            "checked": 1 if comparison is not None else 0,
            "failed": len(diagnostics),
        },
        "diagnostics": diagnostics,
    }
    _write_json_atomic(args.diagnostics, report)
    return 0 if report["ok"] else 1


def _tests_milestone_three(args: argparse.Namespace) -> int:
    diagnostics: list[dict[str, str]] = []
    checked = 0
    stage_reports: dict[str, Any] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="raaml-m3-") as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            reconstructed = root / "reconstructed"
            first_result = forward_slice(REPOSITORY_ROOT, first)
            second_result = forward_slice(REPOSITORY_ROOT, second)
            checked += 2
            for filename in ("preservation-manifest.json", "raaml-milestone-3.sysml"):
                if (first / filename).read_bytes() != (second / filename).read_bytes():
                    raise RoundTripError(
                        "FORWARD_NONDETERMINISTIC",
                        f"two forward runs differ for {filename}",
                    )
            stage_reports["v2"] = run_adapter(
                REPOSITORY_ROOT, "v2", first_result["v2"]
            )
            checked += 1
            if not stage_reports["v2"]["ok"]:
                raise RoundTripError("V2_VALIDATION_FAILED", "generated v2 is invalid")
            paths = reverse_slice(
                first_result["manifest"],
                first_result["v2"],
                reconstructed,
            )
            checked += len(paths)
            v1_reports = []
            for path in paths:
                result = run_adapter(
                    REPOSITORY_ROOT,
                    "v1",
                    path,
                    v1_catalog_dir=reconstructed,
                )
                v1_reports.append(result)
                checked += 1
                if not result["ok"]:
                    raise RoundTripError(
                        "V1_VALIDATION_FAILED",
                        f"reconstructed {path.name} is invalid",
                    )
            stage_reports["v1"] = v1_reports
            comparison = compare_reconstructed(
                REPOSITORY_ROOT,
                first_result["manifest"],
                reconstructed,
            )
            stage_reports["comparison"] = comparison["summary"]
            checked += 1
            if not comparison["ok"]:
                raise RoundTripError(
                    "ROUNDTRIP_FACT_DIFFERENCE",
                    f"{comparison['summary']['differences']} fact difference(s)",
                )
            validate_instance_against_schema(
                comparison,
                REPOSITORY_ROOT / "schemas" / "roundtrip-report.schema.json",
            )
            manifest = json.loads(
                first_result["manifest"].read_text(encoding="utf-8")
            )
            manifest["payload"]["canonicalFacts"]["artifacts"][0][
                "declarations"
            ][0]["name"] = "Corrupted"
            corrupt_path = root / "corrupt-manifest.json"
            _write_json_atomic(corrupt_path, manifest)
            try:
                reverse_slice(
                    corrupt_path,
                    first_result["v2"],
                    root / "corrupt-output",
                )
            except RoundTripError as error:
                if error.code != "MANIFEST_DIGEST":
                    raise
            else:
                raise RoundTripError(
                    "CORRUPT_MANIFEST_ACCEPTED",
                    "corrupt manifest was accepted",
                )
            checked += 1
            missing_v2 = root / "missing-target.sysml"
            missing_v2.write_text(
                first_result["v2"].read_text(encoding="utf-8").replace(
                    "        metadata def Situation;\n",
                    "",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            try:
                reverse_slice(
                    first_result["manifest"],
                    missing_v2,
                    root / "missing-output",
                )
            except RoundTripError as error:
                if error.code not in {"V2_DIGEST", "V2_TARGET_MISSING"}:
                    raise
            else:
                raise RoundTripError(
                    "MISSING_TARGET_ACCEPTED",
                    "manifest with removed targets was accepted",
                )
            checked += 1
            ordered = json.loads(
                first_result["manifest"].read_text(encoding="utf-8")
            )
            core_library = next(
                artifact
                for artifact in ordered["payload"]["canonicalFacts"]["artifacts"]
                if artifact["filename"] == "CoreRAAMLLib.xmi"
            )
            association = next(
                item
                for item in core_library["declarations"]
                if item["kind"] == "Association"
            )
            association["memberEnds"].reverse()
            ordered["payloadSha256"] = hashlib.sha256(
                canonical_json(ordered["payload"])
            ).hexdigest()
            ordered_path = root / "ordered-value.json"
            _write_json_atomic(ordered_path, ordered)
            ordered_output = root / "ordered-output"
            reverse_slice(
                ordered_path,
                first_result["v2"],
                ordered_output,
            )
            ordered_comparison = compare_reconstructed(
                REPOSITORY_ROOT,
                first_result["manifest"],
                ordered_output,
            )
            if ordered_comparison["ok"]:
                raise RoundTripError(
                    "ORDERED_MUTATION_UNDETECTED",
                    "ordered member-end mutation was not detected",
                )
            checked += 1
            published = {
                "schemaVersion": "0.1.0",
                "documentKind": "milestone-3-conformance-report",
                "implementationVersion": __version__,
                "sliceId": "milestone-3-core-general-stpa",
                "ok": True,
                "sourceDigests": {
                    artifact["filename"]: artifact["sha256"]
                    for artifact in first_result["facts"]["artifacts"]
                },
                "lockedInputs": {
                    artifact["id"]: {
                        "collection": artifact["collection"],
                        "filename": artifact["filename"],
                        "sha256": artifact["sha256"],
                    }
                    for artifact in load_lock(
                        REPOSITORY_ROOT / "standards.lock.json"
                    )["artifacts"]
                },
                "tools": {
                    "v2Adapter": stage_reports["v2"].get("adapterVersion"),
                    "v1Adapter": (
                        stage_reports["v1"][0].get("adapterVersion")
                        if stage_reports["v1"]
                        else None
                    ),
                },
                "summary": comparison["summary"],
                "stages": stage_reports,
            }
            _write_json_atomic(args.output, published)
    except (
        AdapterError,
        FactExtractionError,
        RoundTripError,
        SchemaValidationError,
        OSError,
    ) as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": getattr(error, "code", "MILESTONE_THREE_FAILURE"),
                "message": str(error),
            }
        )
    report = {
        "schemaVersion": "0.1.0",
        "command": "tests milestone-3",
        "ok": not diagnostics,
        "summary": {"checked": checked, "failed": len(diagnostics)},
        "diagnostics": diagnostics,
    }
    _write_json_atomic(args.diagnostics, report)
    return 0 if report["ok"] else 1


def _adapter_command(args: argparse.Namespace) -> int:
    try:
        report = run_adapter(REPOSITORY_ROOT, args.mode, args.input)
    except AdapterError as error:
        report = {
            "schemaVersion": "0.1.0",
            "command": args.command_name,
            "ok": False,
            "summary": {"checked": 0, "failed": 1},
            "diagnostics": [
                {
                    "severity": "error",
                    "code": "ADAPTER_UNAVAILABLE",
                    "message": str(error),
                }
            ],
        }
    _write_json_atomic(args.diagnostics, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def _build_adapters(args: argparse.Namespace) -> int:
    try:
        report = build_adapter(REPOSITORY_ROOT)
    except AdapterError as error:
        report = {
            "schemaVersion": "0.1.0",
            "command": "tooling build-adapters",
            "ok": False,
            "summary": {"checked": 0, "failed": 1},
            "diagnostics": [
                {
                    "severity": "error",
                    "code": "ADAPTER_BUILD_FAILED",
                    "message": str(error),
                }
            ],
        }
    _write_json_atomic(args.diagnostics, report)
    return 0 if report["ok"] else 1


def _bootstrap_tooling(args: argparse.Namespace) -> int:
    try:
        report = bootstrap_tooling(REPOSITORY_ROOT)
    except AdapterError as error:
        report = {
            "schemaVersion": "0.1.0",
            "command": "tooling bootstrap",
            "ok": False,
            "summary": {"checked": 0, "failed": 1},
            "diagnostics": [
                {
                    "severity": "error",
                    "code": "TOOLING_BOOTSTRAP_FAILED",
                    "message": str(error),
                }
            ],
        }
    _write_json_atomic(args.diagnostics, report)
    return 0 if report["ok"] else 1


def _schemas_validate(args: argparse.Namespace) -> int:
    report = validate_schemas(REPOSITORY_ROOT)
    _write_json_atomic(args.diagnostics, report)
    if not report["ok"]:
        for diagnostic in report["diagnostics"]:
            print(
                f"{diagnostic['code']}: {diagnostic['message']}",
                file=sys.stderr,
            )
    return 0 if report["ok"] else 1


def _facts_extract(args: argparse.Namespace) -> int:
    diagnostics: list[dict[str, str]] = []
    try:
        raw, canonical = extract_facts(
            REPOSITORY_ROOT,
            lock_path=args.lock,
            source_dir=args.source_dir,
        )
        validate_instance_against_schema(
            raw,
            REPOSITORY_ROOT / "schemas" / "raw-raaml-facts.schema.json",
        )
        validate_instance_against_schema(
            canonical,
            REPOSITORY_ROOT / "schemas" / "canonical-raaml-facts.schema.json",
        )
        if args.check_determinism:
            raw_again, canonical_again = extract_facts(
                REPOSITORY_ROOT,
                lock_path=args.lock,
                source_dir=args.source_dir,
            )
            if serialize_facts(raw) != serialize_facts(raw_again):
                raise FactExtractionError(
                    "FACT_RAW_NONDETERMINISTIC",
                    "two raw extractions are not byte-identical",
                )
            if serialize_facts(canonical) != serialize_facts(canonical_again):
                raise FactExtractionError(
                    "FACT_CANONICAL_NONDETERMINISTIC",
                    "two canonical extractions are not byte-identical",
                )
        _write_json_atomic(args.raw_output, raw)
        _write_json_atomic(args.canonical_output, canonical)
    except FactExtractionError as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": error.code,
                "message": str(error),
            }
        )
    except SchemaValidationError as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": "FACT_SCHEMA_INVALID",
                "message": str(error),
            }
        )
    except OSError as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": "FACT_WRITE_FAILED",
                "message": str(error),
            }
        )

    report = {
        "schemaVersion": "0.1.0",
        "command": "facts extract",
        "ok": not diagnostics,
        "summary": {
            "checked": 17 if not diagnostics else 0,
            "failed": len(diagnostics),
        },
        "diagnostics": diagnostics,
    }
    _write_json_atomic(args.diagnostics, report)
    if diagnostics:
        for diagnostic in diagnostics:
            print(
                f"{diagnostic['code']}: {diagnostic['message']}",
                file=sys.stderr,
            )
        return 1
    print(f"Raw facts: {args.raw_output}")
    print(f"Canonical facts: {args.canonical_output}")
    return 0


def _oracle_audit(args: argparse.Namespace) -> int:
    report = audit_corpus(
        REPOSITORY_ROOT,
        lock_path=args.lock,
        source_dir=args.source_dir,
    )
    _write_json_atomic(args.output, report)
    if report["ok"]:
        print(f"Corpus audit: {args.output}")
        return 0
    for diagnostic in report["diagnostics"]:
        if diagnostic["severity"] == "error":
            print(
                f"{diagnostic['code']}: {diagnostic['message']}",
                file=sys.stderr,
            )
    return 1


def _transformation_audit(args: argparse.Namespace) -> int:
    report = audit_transformation_matrix(
        REPOSITORY_ROOT,
        matrix_path=args.matrix,
        require_resolved=args.require_resolved,
    )
    _write_json_atomic(args.output, report)
    for diagnostic in report["diagnostics"]:
        if diagnostic["severity"] == "error":
            print(
                f"{diagnostic['code']}: {diagnostic['message']}",
                file=sys.stderr,
            )
    if report["ok"]:
        summary = report["summary"]
        print(
            f"Audited {summary['checked']} transformation row(s); "
            f"{summary['open']} open; report: {args.output}"
        )
        return 0
    return 1


def _transformation_surface(args: argparse.Namespace) -> int:
    try:
        report = analyze_corpus_transformation_surface(REPOSITORY_ROOT)
    except (OSError, ValueError) as error:
        print(
            f"TRANSFORMATION_SURFACE_INVALID: {error}",
            file=sys.stderr,
        )
        return 1
    _write_json_atomic(args.output, report)
    print(
        "Inventoried "
        f"{report['rootSysmlApplicationCount']} root-level SysML "
        f"application(s); report: {args.output}"
    )
    return 0


def _transformation_properties(args: argparse.Namespace) -> int:
    try:
        report = analyze_property_transformation_surface(REPOSITORY_ROOT)
    except (OSError, ValueError) as error:
        print(
            f"TRANSFORMATION_PROPERTIES_INVALID: {error}",
            file=sys.stderr,
        )
        return 1
    _write_json_atomic(args.output, report)
    print(
        f"Classified {report['propertyCount']} UML Properties; "
        f"report: {args.output}"
    )
    return 0


def _transformation_constraints(args: argparse.Namespace) -> int:
    try:
        report = analyze_constraint_transformation_surface(REPOSITORY_ROOT)
    except (OSError, ValueError) as error:
        print(
            f"TRANSFORMATION_CONSTRAINTS_INVALID: {error}",
            file=sys.stderr,
        )
        return 1
    _write_json_atomic(args.output, report)
    print(
        f"Classified {report['opaqueExpressionCount']} constraint "
        f"OpaqueExpressions; report: {args.output}"
    )
    return 0


def _validate_ocl_command(args: argparse.Namespace) -> int:
    if args.all:
        if args.input is not None:
            args.parser.error("validate-ocl accepts either INPUT or --all, not both")
        report = validate_ocl_corpus(REPOSITORY_ROOT)
        _write_json_atomic(args.diagnostics, report)
        if not report["ok"]:
            for diagnostic in report["diagnostics"]:
                if diagnostic["severity"] == "error":
                    print(
                        f"{diagnostic['code']}: {diagnostic['message']}",
                        file=sys.stderr,
                    )
            return 1
        print(
            f"Validated {report['summary']['checked']} OCL expression(s); "
            f"diagnostics: {args.diagnostics}"
        )
        return 0
    if args.input is None:
        args.parser.error("validate-ocl requires INPUT or --all")
    args.mode = "ocl"
    args.command_name = "validate-ocl"
    return _adapter_command(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="raaml")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    sources = commands.add_parser("sources", help="manage pinned standards inputs")
    source_commands = sources.add_subparsers(dest="sources_command", required=True)

    verify = source_commands.add_parser(
        "verify",
        help="verify local source bytes against standards.lock.json",
    )
    verify.add_argument(
        "--lock",
        type=_path,
        default=REPOSITORY_ROOT / "standards.lock.json",
    )
    verify.add_argument(
        "--source-dir",
        type=_path,
        default=REPOSITORY_ROOT / "sources" / "cache",
    )
    verify.add_argument("--collection")
    verify.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "sources-verify.json",
    )
    verify.set_defaults(handler=_sources_verify)

    fetch = source_commands.add_parser(
        "fetch",
        help="explicitly download every locked artifact and verify it",
    )
    fetch.add_argument(
        "--lock",
        type=_path,
        default=REPOSITORY_ROOT / "standards.lock.json",
    )
    fetch.add_argument(
        "--source-dir",
        type=_path,
        default=REPOSITORY_ROOT / "sources" / "cache",
    )
    fetch.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "sources-fetch.json",
    )
    fetch.set_defaults(handler=_sources_fetch)

    schemas = commands.add_parser("schemas", help="validate project schemas")
    schema_commands = schemas.add_subparsers(dest="schemas_command", required=True)
    validate = schema_commands.add_parser(
        "validate",
        help="validate schemas and schema-governed JSON artifacts",
    )
    validate.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "schemas-validate.json",
    )
    validate.set_defaults(handler=_schemas_validate)

    facts = commands.add_parser(
        "facts",
        help="extract and canonicalize the locked RAAML preservation facts",
    )
    fact_commands = facts.add_subparsers(dest="facts_command", required=True)
    extract = fact_commands.add_parser(
        "extract",
        help="extract raw and canonical facts from the locked corpus",
    )
    extract.add_argument(
        "--all",
        action="store_true",
        required=True,
        help="extract all 17 locked RAAML definition artifacts",
    )
    extract.add_argument(
        "--check-determinism",
        action="store_true",
        help="extract twice and require byte-identical raw and canonical output",
    )
    extract.add_argument(
        "--lock",
        type=_path,
        default=REPOSITORY_ROOT / "standards.lock.json",
    )
    extract.add_argument(
        "--source-dir",
        type=_path,
        default=REPOSITORY_ROOT / "sources" / "cache",
    )
    extract.add_argument(
        "--raw-output",
        type=_path,
        default=REPOSITORY_ROOT / "reports" / "facts" / "raw-raaml-facts.json",
    )
    extract.add_argument(
        "--canonical-output",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "facts"
        / "canonical-raaml-facts.json",
    )
    extract.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "facts-extract.json",
    )
    extract.set_defaults(handler=_facts_extract)

    forward = commands.add_parser(
        "forward",
        help="map the Milestone 3 RAAML slice to SysML v2 plus a manifest",
    )
    forward.add_argument(
        "--milestone-3",
        action="store_true",
        required=True,
        help="generate the frozen Milestone 3 vertical slice",
    )
    forward.add_argument(
        "--output-dir",
        type=_path,
        default=REPOSITORY_ROOT / "generated" / "milestone-3" / "forward",
    )
    forward.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "forward-milestone-3.json",
    )
    forward.set_defaults(handler=_forward_command)

    reverse = commands.add_parser(
        "reverse",
        help="reconstruct v1 XMI from a preservation manifest",
    )
    reverse.add_argument("--manifest", type=_path, required=True)
    reverse.add_argument("--v2", type=_path, required=True)
    reverse.add_argument(
        "--output-dir",
        type=_path,
        default=REPOSITORY_ROOT / "generated" / "milestone-3" / "reconstructed",
    )
    reverse.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "reverse-milestone-3.json",
    )
    reverse.set_defaults(handler=_reverse_command)

    compare = commands.add_parser(
        "compare",
        help="compare source and reconstructed canonical facts",
    )
    compare.add_argument("--manifest", type=_path, required=True)
    compare.add_argument("--reconstructed-dir", type=_path, required=True)
    compare.add_argument(
        "--output",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "conformance"
        / "milestone-3-comparison.json",
    )
    compare.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "compare-milestone-3.json",
    )
    compare.set_defaults(handler=_compare_command)

    oracle = commands.add_parser(
        "oracle",
        help="audit the corpus independently of production fact extraction",
    )
    oracle_commands = oracle.add_subparsers(
        dest="oracle_command",
        required=True,
    )
    audit = oracle_commands.add_parser(
        "audit",
        help="count and check preservation facts directly from XML events",
    )
    audit.add_argument(
        "--all",
        action="store_true",
        required=True,
        help="audit all 17 locked RAAML definition artifacts",
    )
    audit.add_argument(
        "--lock",
        type=_path,
        default=REPOSITORY_ROOT / "standards.lock.json",
    )
    audit.add_argument(
        "--source-dir",
        type=_path,
        default=REPOSITORY_ROOT / "sources" / "cache",
    )
    audit.add_argument(
        "--output",
        type=_path,
        default=REPOSITORY_ROOT / "reports" / "oracle" / "corpus-audit.json",
    )
    audit.set_defaults(handler=_oracle_audit)

    transformation = commands.add_parser(
        "transformation",
        help="audit the comparison with the official v1-to-v2 transformation",
    )
    transformation_commands = transformation.add_subparsers(
        dest="transformation_command",
        required=True,
    )
    transformation_audit = transformation_commands.add_parser(
        "audit",
        help="validate matrix citations against the pinned transformation model",
    )
    transformation_audit.add_argument(
        "--matrix",
        type=_path,
        default=REPOSITORY_ROOT
        / "analysis"
        / "transformation-matrix-v0.1.json",
    )
    transformation_audit.add_argument(
        "--require-resolved",
        action="store_true",
        help="fail when any matrix row remains classified open",
    )
    transformation_audit.add_argument(
        "--output",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "transformation"
        / "matrix-audit.json",
    )
    transformation_audit.set_defaults(handler=_transformation_audit)
    transformation_surface = transformation_commands.add_parser(
        "surface",
        help="inventory specialized SysML v1 mappings selected by the corpus",
    )
    transformation_surface.add_argument(
        "--output",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "transformation"
        / "corpus-surface.json",
    )
    transformation_surface.set_defaults(handler=_transformation_surface)
    transformation_properties = transformation_commands.add_parser(
        "properties",
        help="classify corpus Properties using the official rule filters",
    )
    transformation_properties.add_argument(
        "--output",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "transformation"
        / "property-surface.json",
    )
    transformation_properties.set_defaults(
        handler=_transformation_properties
    )
    transformation_constraints = transformation_commands.add_parser(
        "constraints",
        help="classify constraint expressions against the official rules",
    )
    transformation_constraints.add_argument(
        "--output",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "transformation"
        / "constraint-surface.json",
    )
    transformation_constraints.set_defaults(
        handler=_transformation_constraints
    )

    tests = commands.add_parser("tests", help="run project tests")
    test_commands = tests.add_subparsers(dest="tests_command", required=True)
    unit = test_commands.add_parser("unit", help="run dependency-free unit tests")
    unit.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "tests-unit.json",
    )
    unit.set_defaults(handler=_tests_unit)
    milestone_zero = test_commands.add_parser(
        "milestone-0",
        help="run paired foundation smoke tests through every pinned adapter",
    )
    milestone_zero.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "tests-milestone-0.json",
    )
    milestone_zero.set_defaults(handler=_tests_milestone_zero)
    milestone_one = test_commands.add_parser(
        "milestone-1",
        help="run extraction, oracle, determinism, and corpus OCL gates",
    )
    milestone_one.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "tests-milestone-1.json",
    )
    milestone_one.set_defaults(handler=_tests_milestone_one)
    milestone_three = test_commands.add_parser(
        "milestone-3",
        help="run the complete thin vertical-slice round trip",
    )
    milestone_three.add_argument(
        "--output",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "conformance"
        / "milestone-3.json",
    )
    milestone_three.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "tests-milestone-3.json",
    )
    milestone_three.set_defaults(handler=_tests_milestone_three)

    tooling = commands.add_parser("tooling", help="build pinned tool adapters")
    tooling_commands = tooling.add_subparsers(dest="tooling_command", required=True)
    build = tooling_commands.add_parser(
        "build-adapters",
        help="compile the Java adapters against the pinned distribution",
    )
    build.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "tooling-build-adapters.json",
    )
    build.set_defaults(handler=_build_adapters)
    bootstrap = tooling_commands.add_parser(
        "bootstrap",
        help="extract verified local tool archives and build adapters",
    )
    bootstrap.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "tooling-bootstrap.json",
    )
    bootstrap.set_defaults(handler=_bootstrap_tooling)

    adapter_specs = (
        ("validate-v2", "v2"),
        ("validate-v1", "v1"),
    )
    for command_name, mode in adapter_specs:
        command = commands.add_parser(command_name)
        command.add_argument("input", type=_path)
        command.add_argument(
            "--diagnostics",
            type=_path,
            default=REPOSITORY_ROOT
            / "reports"
            / "diagnostics"
            / f"{command_name}.json",
        )
        command.set_defaults(
            handler=_adapter_command,
            mode=mode,
            command_name=command_name,
        )
    validate_ocl = commands.add_parser("validate-ocl")
    validate_ocl.add_argument("input", type=_path, nargs="?")
    validate_ocl.add_argument(
        "--all",
        action="store_true",
        help="parse and resolve every OCL expression in the locked corpus",
    )
    validate_ocl.add_argument(
        "--diagnostics",
        type=_path,
        default=REPOSITORY_ROOT
        / "reports"
        / "diagnostics"
        / "validate-ocl.json",
    )
    validate_ocl.set_defaults(
        handler=_validate_ocl_command,
        parser=validate_ocl,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
