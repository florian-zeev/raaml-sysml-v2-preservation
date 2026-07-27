from __future__ import annotations

import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from typing import Any
import zipfile

from .secure_xml import UnsafeXmlError, preflight_xml
from .sources import load_lock


class AdapterError(RuntimeError):
    pass


MAX_ARCHIVE_MEMBERS = 100_000
MAX_ARCHIVE_EXPANDED_BYTES = 1024 * 1024 * 1024


def _jdk_platform() -> tuple[str, Path]:
    machine = platform.machine().lower()
    if sys.platform == "darwin" and machine in {"arm64", "aarch64"}:
        return (
            "OpenJDK21U-jdk_aarch64_mac_hotspot_21.0.11_10.tar.gz",
            Path("Contents/Home"),
        )
    if sys.platform.startswith("linux") and machine in {"x86_64", "amd64"}:
        return (
            "OpenJDK21U-jdk_x64_linux_hotspot_21.0.11_10.tar.gz",
            Path("."),
        )
    raise AdapterError(
        f"no pinned JDK for platform {sys.platform}/{platform.machine()}"
    )


def tool_paths(repository_root: Path) -> dict[str, Path]:
    cache = repository_root / "tooling" / "cache"
    _, java_home_suffix = _jdk_platform()
    java_home = Path(
        os.environ.get(
            "RAAML_JAVA_HOME",
            cache / "temurin-21" / java_home_suffix,
        )
    )
    distribution = Path(
        os.environ.get(
            "RAAML_SYSML_DISTRIBUTION",
            cache / "sysml-0.59.0" / "sysml",
        )
    )
    return {
        "java": java_home / "bin" / "java",
        "javac": java_home / "bin" / "javac",
        "jar": distribution / "jupyter-sysml-kernel-0.59.0-all.jar",
        "library": distribution / "sysml.library",
        "source": repository_root
        / "tooling"
        / "java"
        / "src"
        / "org"
        / "raaml"
        / "preservation"
        / "ToolAdapter.java",
        "classes": repository_root / "tooling" / "java" / "build",
    }


def build_adapter(repository_root: Path) -> dict[str, Any]:
    paths = tool_paths(repository_root)
    for name in ("javac", "jar", "source"):
        if not paths[name].is_file():
            raise AdapterError(f"required {name} is missing: {paths[name]}")
    output = paths["classes"]
    package_output = output / "org" / "raaml" / "preservation"
    package_output.mkdir(parents=True, exist_ok=True)
    process = subprocess.run(
        [
            str(paths["javac"]),
            "-cp",
            str(paths["jar"]),
            "-d",
            str(output),
            str(paths["source"]),
        ],
        cwd=repository_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if process.returncode != 0:
        raise AdapterError(
            f"adapter compilation failed ({process.returncode}): "
            f"{process.stderr.strip()}"
        )
    return {
        "schemaVersion": "0.1.0",
        "command": "tooling build-adapters",
        "ok": True,
        "summary": {"checked": 1, "failed": 0},
        "diagnostics": [],
    }


def bootstrap_tooling(repository_root: Path) -> dict[str, Any]:
    source_cache = repository_root / "sources" / "cache"
    tool_cache = repository_root / "tooling" / "cache"
    tool_cache.mkdir(parents=True, exist_ok=True)
    jdk_archive, java_home_suffix = _jdk_platform()
    installs = (
        (
            source_cache / "jupyter-sysml-kernel-0.59.0.zip",
            tool_cache / "sysml-0.59.0",
            "zip",
            Path("sysml/jupyter-sysml-kernel-0.59.0-all.jar"),
        ),
        (
            source_cache / jdk_archive,
            tool_cache / "temurin-21",
            "tar",
            java_home_suffix / "bin" / "java",
        ),
    )
    installed = 0
    for archive, destination, archive_kind, required in installs:
        if destination.joinpath(required).is_file():
            continue
        if destination.exists():
            raise AdapterError(f"incomplete tool installation exists: {destination}")
        if not archive.is_file():
            raise AdapterError(
                f"verified archive is missing: {archive}; acquire it, then run sources verify"
            )
        with tempfile.TemporaryDirectory(dir=tool_cache) as temporary:
            temporary_path = Path(temporary)
            if archive_kind == "zip":
                _extract_zip_safely(archive, temporary_path)
                extracted = temporary_path
            else:
                _extract_tar_safely(archive, temporary_path)
                roots = [path for path in temporary_path.iterdir()]
                if len(roots) != 1 or not roots[0].is_dir():
                    raise AdapterError(f"unexpected JDK archive layout: {archive}")
                extracted = roots[0]
            if not extracted.joinpath(required).is_file():
                raise AdapterError(f"archive is missing required path {required}: {archive}")
            os.replace(extracted, destination)
        installed += 1
    report = build_adapter(repository_root)
    report["command"] = "tooling bootstrap"
    report["installed"] = installed
    return report


def _extract_zip_safely(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        expanded_bytes = 0
        if len(bundle.infolist()) > MAX_ARCHIVE_MEMBERS:
            raise AdapterError(
                f"archive has more than {MAX_ARCHIVE_MEMBERS} members: {archive}"
            )
        for member in bundle.infolist():
            _validate_archive_member_name(member.filename)
            unix_mode = member.external_attr >> 16
            if not member.is_dir() and unix_mode & 0o170000 == 0o120000:
                raise AdapterError(f"unsafe zip member: {member.filename}")
            expanded_bytes += member.file_size
            if expanded_bytes > MAX_ARCHIVE_EXPANDED_BYTES:
                raise AdapterError(
                    "archive expands beyond "
                    f"{MAX_ARCHIVE_EXPANDED_BYTES} bytes: {archive}"
                )
        bundle.extractall(destination)


def _extract_tar_safely(archive: Path, destination: Path) -> None:
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise AdapterError(
                f"archive has more than {MAX_ARCHIVE_MEMBERS} members: {archive}"
            )
        expanded_bytes = 0
        for member in members:
            _validate_archive_member_name(member.name)
            if member.issym() or member.islnk() or member.isdev():
                raise AdapterError(f"unsafe tar member: {member.name}")
            if not (member.isfile() or member.isdir()):
                raise AdapterError(f"unsupported tar member: {member.name}")
            expanded_bytes += member.size
            if expanded_bytes > MAX_ARCHIVE_EXPANDED_BYTES:
                raise AdapterError(
                    "archive expands beyond "
                    f"{MAX_ARCHIVE_EXPANDED_BYTES} bytes: {archive}"
                )
        bundle.extractall(destination, filter="data")


def _validate_archive_member_name(name: str) -> None:
    portable_name = name.replace("\\", "/")
    member_path = Path(portable_name)
    if (
        not name
        or member_path.is_absolute()
        or ".." in member_path.parts
        or portable_name.startswith("/")
        or (
            len(portable_name) >= 2
            and portable_name[0].isalpha()
            and portable_name[1] == ":"
        )
    ):
        raise AdapterError(f"unsafe archive member: {name}")


def run_adapter(
    repository_root: Path,
    mode: str,
    input_path: Path,
) -> dict[str, Any]:
    paths = tool_paths(repository_root)
    class_file = (
        paths["classes"]
        / "org"
        / "raaml"
        / "preservation"
        / "ToolAdapter.class"
    )
    for name in ("java", "jar"):
        if not paths[name].is_file():
            raise AdapterError(f"required {name} is missing: {paths[name]}")
    if not class_file.is_file():
        raise AdapterError("adapter classes are missing; run tooling build-adapters")
    if not input_path.is_file() or input_path.is_symlink():
        raise AdapterError(f"input must be a regular non-symlink file: {input_path}")

    arguments = [mode, str(input_path)]
    if mode == "v2":
        if not paths["library"].is_dir():
            raise AdapterError(f"SysML library is missing: {paths['library']}")
        arguments.append(str(paths["library"]))
    elif mode == "v1":
        lock = load_lock(repository_root / "standards.lock.json")
        authoritative = {
            artifact["authoritativeUrl"] for artifact in lock["artifacts"]
        }
        allowed = frozenset(
            authoritative
            | {
                url.replace("https://www.omg.org/", "http://www.omg.org/", 1)
                for url in authoritative
                if url.startswith("https://www.omg.org/")
            }
        )
        try:
            preflight_xml(
                input_path,
                allowed_remote_documents=allowed,
            )
        except UnsafeXmlError as error:
            return {
                "schemaVersion": "0.1.0",
                "adapter": "v1",
                "adapterVersion": "0.1.0",
                "command": "validate-v1",
                "ok": False,
                "input": input_path.name,
                "summary": {"checked": 1, "failed": 1},
                "diagnostics": [
                    {
                        "severity": "error",
                        "code": error.code,
                        "message": str(error),
                    }
                ],
            }
        arguments.append(str(repository_root / "sources" / "cache"))
    elif mode != "ocl":
        raise AdapterError(f"unknown adapter mode: {mode}")

    process = subprocess.run(
        [
            str(paths["java"]),
            "-Dlog4j.rootLogger=OFF",
            "-cp",
            f"{paths['classes']}{os.pathsep}{paths['jar']}",
            "org.raaml.preservation.ToolAdapter",
            *arguments,
        ],
        cwd=repository_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    report_line = next(
        (
            line
            for line in reversed(process.stdout.splitlines())
            if line.lstrip().startswith("{")
        ),
        None,
    )
    if report_line is None:
        raise AdapterError(
            f"adapter returned no JSON report ({process.returncode}): "
            f"{process.stderr.strip()}"
        )
    try:
        report = json.loads(report_line)
    except json.JSONDecodeError as error:
        raise AdapterError(f"adapter returned invalid JSON: {error}") from error
    if bool(report.get("ok")) != (process.returncode == 0):
        raise AdapterError(
            "adapter exit code and JSON status disagree: "
            f"exit={process.returncode}, ok={report.get('ok')!r}"
        )
    return report
