from __future__ import annotations

import argparse
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
from .sources import LockError, fetch_sources, verify_sources
from .schemas import validate_schemas


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
    return 0 if report["ok"] else 1


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
        ("validate-ocl", "ocl"),
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
