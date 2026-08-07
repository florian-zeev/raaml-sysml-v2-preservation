from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Iterable


_ALLOWED_XMI_FIXTURES = {
    "fixtures/milestone-0/minimal-v1-invalid-reference.xmi",
    "fixtures/milestone-0/minimal-v1-library.xmi",
    "fixtures/milestone-0/minimal-v1-profile.xmi",
}

_ALLOWED_PLACEHOLDERS = {
    "generated/.gitkeep",
    "reports/.gitkeep",
    "sources/cache/.gitkeep",
}

_BLOCKED_PREFIXES = (
    "container-evidence/",
    "generated/",
    "release-container/",
    "release-host/",
    "reports/",
    "review-evidence/",
    "sources/cache/",
    "tooling/cache/",
    "tooling/java/build/",
    "typescript/dist/",
    "typescript/node_modules/",
)

_BLOCKED_BASENAMES = {
    "canonical-raaml-facts.json",
    "raaml-full-corpus.sysml",
    "raw-raaml-facts.json",
}

_BLOCKED_ARCHIVE_SUFFIXES = (
    ".class",
    ".emof",
    ".jar",
    ".pdf",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".zip",
)

_BLOCKED_WORKFLOW_MARKERS = (
    "actions/upload-artifact@",
    "docker push ",
    "gh release ",
    "npm publish",
    "packages: write",
)

_NPM_STAGE_WORKFLOW = ".github/workflows/publish-npm.yml"

_NPM_STAGE_REQUIRED_MARKERS = (
    'tags:\n      - "typescript-v*"',
    "contents: read",
    "id-token: write",
    "environment: npm",
    "npm stage publish --access public --tag next",
)

_REQUIRED_GITIGNORE_RULES = {
    "/container-evidence/",
    "/generated/*",
    "/release-container/",
    "/release-host/",
    "/reports/*",
    "/review-evidence/",
    "/sources/cache/*",
    "/tooling/cache/",
}


def audit_paths(paths: Iterable[str], *, scope: str) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    for raw_path in sorted(set(paths)):
        path = raw_path.removeprefix("./")
        if not path or path in _ALLOWED_PLACEHOLDERS:
            continue
        basename = path.rsplit("/", 1)[-1]
        reason: str | None = None
        if path in _ALLOWED_XMI_FIXTURES:
            continue
        if path.endswith(".xmi"):
            reason = "only the three project-authored XMI fixtures may be committed"
        elif path.endswith(".preservation.json"):
            reason = "preservation manifests derived from the official corpus are local-only"
        elif basename in _BLOCKED_BASENAMES:
            reason = "full-corpus generated evidence is local-only"
        elif any(path.startswith(prefix) for prefix in _BLOCKED_PREFIXES):
            reason = "cache, generated, report, build, or release output is local-only"
        elif path.endswith(_BLOCKED_ARCHIVE_SUFFIXES):
            reason = "standards, tool binaries, and downloaded archives are local-only"
        if reason is not None:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "PUBLICATION_PATH_BLOCKED",
                    "message": f"{scope}: {path}: {reason}",
                }
            )
    return diagnostics


def audit_workflow(
    workflow: str,
    *,
    path: str = ".github/workflows/validate.yml",
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    for marker in _BLOCKED_WORKFLOW_MARKERS:
        if marker in workflow:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "PUBLICATION_WORKFLOW_PUBLISHES_OUTPUT",
                    "message": (
                        f"{path}: workflow contains blocked publishing marker "
                        f"{marker!r}"
                    ),
                }
            )
    if "permissions:\n  contents: read\n" not in workflow:
        diagnostics.append(
            {
                "severity": "error",
                "code": "PUBLICATION_WORKFLOW_PERMISSIONS",
                "message": (
                    f"{path}: workflow must retain top-level contents: read permission"
                ),
            }
        )
    if "npm stage publish" in workflow and path != _NPM_STAGE_WORKFLOW:
        diagnostics.append(
            {
                "severity": "error",
                "code": "PUBLICATION_WORKFLOW_UNAUTHORIZED_NPM_STAGE",
                "message": f"{path}: npm staging is allowed only in {_NPM_STAGE_WORKFLOW}",
            }
        )
    if path == _NPM_STAGE_WORKFLOW:
        for marker in _NPM_STAGE_REQUIRED_MARKERS:
            if marker not in workflow:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "PUBLICATION_NPM_STAGE_CONTROL_MISSING",
                        "message": f"{path}: missing required control {marker!r}",
                    }
                )
    return diagnostics


def audit_ignore_rules(gitignore: str) -> list[dict[str, str]]:
    rules = {
        line.strip()
        for line in gitignore.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    return [
        {
            "severity": "error",
            "code": "PUBLICATION_IGNORE_RULE_MISSING",
            "message": f".gitignore is missing required rule {rule}",
        }
        for rule in sorted(_REQUIRED_GITIGNORE_RULES - rules)
    ]


def _git_output(repository_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _history_paths(repository_root: Path) -> list[str]:
    paths: list[str] = []
    for line in _git_output(
        repository_root,
        "rev-list",
        "--objects",
        "--all",
    ).splitlines():
        _object_id, separator, path = line.partition(" ")
        if separator:
            paths.append(path)
    return paths


def audit_repository(repository_root: Path) -> dict[str, Any]:
    diagnostics: list[dict[str, str]] = []
    current_paths: list[str] = []
    historical_paths: list[str] = []
    try:
        current_paths = _git_output(repository_root, "ls-files").splitlines()
        historical_paths = _history_paths(repository_root)
    except (OSError, subprocess.CalledProcessError) as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": "PUBLICATION_GIT_AUDIT_FAILED",
                "message": str(error),
            }
        )
    else:
        diagnostics.extend(audit_paths(current_paths, scope="current index"))
        diagnostics.extend(audit_paths(historical_paths, scope="Git history"))

    workflow_directory = repository_root / ".github" / "workflows"
    gitignore_path = repository_root / ".gitignore"
    workflow_paths: list[Path] = []
    try:
        workflow_paths = sorted(
            path
            for path in workflow_directory.iterdir()
            if path.suffix in {".yml", ".yaml"}
        )
        if not workflow_paths:
            raise FileNotFoundError(f"no workflows found in {workflow_directory}")
        for workflow_path in workflow_paths:
            relative_path = workflow_path.relative_to(repository_root).as_posix()
            diagnostics.extend(
                audit_workflow(
                    workflow_path.read_text(encoding="utf-8"),
                    path=relative_path,
                )
            )
        diagnostics.extend(
            audit_ignore_rules(gitignore_path.read_text(encoding="utf-8"))
        )
    except OSError as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": "PUBLICATION_POLICY_FILE_MISSING",
                "message": str(error),
            }
        )

    return {
        "schemaVersion": "0.1.0",
        "command": "publication audit",
        "ok": not diagnostics,
        "summary": {
            "checked": (
                len(current_paths)
                + len(set(historical_paths))
                + len(workflow_paths)
                + 1
            ),
            "currentTrackedPaths": len(current_paths),
            "historicalPaths": len(set(historical_paths)),
            "failed": len(diagnostics),
        },
        "diagnostics": diagnostics,
        "limitations": [
            "This automated gate audits Git paths, ignore rules, and known CI publishing mechanisms.",
            "It does not provide legal clearance for source-grounded names, facts, or examples in committed original analysis and proposal text.",
            "It cannot inspect retained GitHub Actions artifacts, releases, packages, or caches through the local Git repository.",
        ],
    }
