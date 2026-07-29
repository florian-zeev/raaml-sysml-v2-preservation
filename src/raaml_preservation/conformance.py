from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Callable

from .facts import (
    FactExtractionError,
    canonicalize_facts,
    extract_artifact_set,
    extract_facts,
)
from .roundtrip import (
    RoundTripError,
    canonical_json,
    compare_full_corpus,
    render_v1_artifact,
    reverse_full_corpus,
)
from .schemas import SchemaValidationError, validate_instance_against_schema
from .secure_xml import UnsafeXmlError, XmlLimits, preflight_xml


class ConformanceError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def run_adversarial_suite(
    repository_root: Path,
    workspace: Path,
    forward: dict[str, Any],
    reconstructed_dir: Path,
    comparison: dict[str, Any],
) -> list[dict[str, Any]]:
    raw, canonical = extract_facts(repository_root)
    cases: list[dict[str, Any]] = []

    def witness(case_id: str, requirement: str, detail: str, condition: bool) -> None:
        if not condition:
            raise ConformanceError(case_id, detail)
        cases.append(
            {
                "id": case_id,
                "requirement": requirement,
                "kind": "positive-witness",
                "expectedDiagnostic": None,
                "observedDiagnostic": None,
                "detail": detail,
                "passed": True,
            }
        )

    def rejected(
        case_id: str,
        requirement: str,
        expected_code: str,
        action: Callable[[], None],
    ) -> None:
        try:
            action()
        except (
            ConformanceError,
            FactExtractionError,
            RoundTripError,
            SchemaValidationError,
            UnsafeXmlError,
        ) as error:
            observed = getattr(error, "code", "SCHEMA_VALIDATION_ERROR")
            if observed != expected_code:
                raise ConformanceError(
                    case_id,
                    f"expected {expected_code}, observed {observed}: {error}",
                ) from error
        else:
            raise ConformanceError(
                case_id,
                f"expected rejection with {expected_code}",
            )
        cases.append(
            {
                "id": case_id,
                "requirement": requirement,
                "kind": "negative-fixture",
                "expectedDiagnostic": expected_code,
                "observedDiagnostic": expected_code,
                "detail": f"rejected with {expected_code}",
                "passed": True,
            }
        )

    declarations = [
        declaration
        for artifact in canonical["artifacts"]
        for declaration in artifact["declarations"]
    ]
    owned_by_name: dict[str, set[str]] = {}
    for declaration in declarations:
        for item in declaration["properties"] + declaration["ownedEnds"]:
            if item["name"] is not None:
                owned_by_name.setdefault(item["name"], set()).add(item["id"])
    witness(
        "duplicate-local-names-distinct",
        "duplicate local names under different owners",
        "owner-qualified identities keep repeated owned names distinct",
        any(len(identities) > 1 for identities in owned_by_name.values()),
    )

    duplicate_constraints = [
        constraint["id"]
        for declaration in declarations
        for constraint in declaration["constraints"]
        if constraint["name"] == "ClientIsSituation"
    ]
    witness(
        "duplicate-constraint-names-distinct",
        "duplicate constraint names under different owners",
        "the two ClientIsSituation constraints have distinct identities",
        len(duplicate_constraints) == 2
        and len(set(duplicate_constraints)) == 2,
    )

    ambiguous = copy.deepcopy(raw)
    ambiguous_property = next(
        item
        for artifact in ambiguous["artifacts"]
        for declaration in artifact["declarations"]
        for item in declaration["properties"]
        if item["name"] is not None
    )
    duplicate = copy.deepcopy(ambiguous_property)
    duplicate["sourceHandle"] += "-duplicate"
    owner = next(
        declaration
        for artifact in ambiguous["artifacts"]
        for declaration in artifact["declarations"]
        if ambiguous_property in declaration["properties"]
    )
    owner["properties"].append(duplicate)
    rejected(
        "ambiguous-same-owner-siblings",
        "same-kind same-name siblings under one owner",
        "FACT_OWNED_ID_COLLISION",
        lambda: canonicalize_facts(ambiguous),
    )

    artifact_for_identity = {
        declaration["id"]: artifact["filename"]
        for artifact in canonical["artifacts"]
        for declaration in artifact["declarations"]
    }
    cross_artifact = [
        (artifact["filename"], reference["target"])
        for artifact in canonical["artifacts"]
        for declaration in artifact["declarations"]
        for reference in declaration["generalizations"]
        if artifact_for_identity.get(reference["target"]) not in {
            None,
            artifact["filename"],
        }
    ]
    witness(
        "cross-artifact-generalizations",
        "cross-profile and cross-library generalizations",
        "cross-artifact generalizations survive the exact comparison",
        bool(cross_artifact) and comparison["ok"],
    )

    fta_and = next(
        item
        for item in declarations
        if item["kind"] == "Stereotype"
        and item["name"] == "AND"
        and item["id"].startswith("raaml-1.1-fta-profile::")
    )
    fta_gate = next(
        item
        for item in declarations
        if item["id"] == fta_and["generalizations"][0]["target"]
    )
    witness(
        "inherited-versus-local-bases",
        "inherited versus locally owned base properties",
        "FTA AND inherits Gate bases without receiving local base properties",
        not any(
            (item["name"] or "").startswith("base_")
            for item in fta_and["properties"]
        )
        and any(
            (item["name"] or "").startswith("base_")
            for item in fta_gate["properties"]
        ),
    )

    raw_references = [
        value["sourceValue"]
        for artifact in raw["artifacts"]
        for value in _walk_dicts(artifact)
        if isinstance(value.get("sourceValue"), str)
    ]
    witness(
        "uri-variants",
        "URI variants",
        "the corpus exercises both HTTP support URIs and HTTPS RAAML URIs",
        any(value.startswith("http://www.omg.org/") for value in raw_references)
        and any(
            value.startswith("https://www.omg.org/spec/RAAML/")
            for value in raw_references
        ),
    )

    multi = copy.deepcopy(canonical)
    association = next(
        declaration
        for artifact in multi["artifacts"]
        for declaration in artifact["declarations"]
        if declaration["kind"] == "Association"
        and len(declaration["memberEnds"]) == 2
    )
    for reference in association["memberEnds"]:
        reference["sourceForm"] = "idref"
    association["memberEnds"].append(copy.deepcopy(association["memberEnds"][0]))
    association_artifact = next(
        artifact
        for artifact in multi["artifacts"]
        if association in artifact["declarations"]
    )
    rendered_multi = render_v1_artifact(multi, association_artifact)
    witness(
        "multi-ended-association",
        "multi-ended associations",
        "the renderer emits all three ordered member-end references",
        rendered_multi.count(b"<memberEnd") == 3,
    )

    witness(
        "properties-versus-ports",
        "Properties versus Ports",
        "267 Properties and 65 Ports remain distinct after reconstruction",
        comparison["sourceCounts"]["properties"] == 267
        and comparison["sourceCounts"]["ports"] == 65
        and comparison["sourceCounts"] == comparison["reconstructedCounts"],
    )
    connectors = [
        connector
        for declaration in declarations
        for connector in declaration["connectors"]
    ]
    witness(
        "connector-role-and-part-with-port",
        "connector roles and partWithPort references",
        "94 ordered connectors, including partWithPort references, compare exactly",
        len(connectors) == 94
        and any(
            end["partWithPort"] is not None
            for connector in connectors
            for end in connector["ends"]
        )
        and comparison["ok"],
    )

    changed_dir = workspace / "changed-default-presence"
    shutil.copytree(reconstructed_dir, changed_dir)
    changed_path = next(
        path
        for path in sorted(changed_dir.glob("*.xmi"))
        if re.search(r'isAbstract="(?:true|false)"', path.read_text())
    )
    text = changed_path.read_text(encoding="utf-8")
    changed_path.write_text(
        re.sub(
            r'isAbstract="(true|false)"',
            lambda match: (
                'isAbstract="false"'
                if match.group(1) == "true"
                else 'isAbstract="true"'
            ),
            text,
            count=1,
        ),
        encoding="utf-8",
        newline="\n",
    )
    changed_comparison = compare_full_corpus(repository_root, changed_dir)
    witness(
        "absent-versus-explicit-values",
        "absent versus explicitly present defaults",
        "changing one explicit presence/value fact changes the canonical digest",
        not changed_comparison["ok"]
        and changed_comparison["summary"]["differences"] > 0,
    )

    for role, requirement in (
        ("lower", "absent versus explicitly present multiplicities"),
        ("default", "absent versus explicitly present defaults"),
    ):
        changed_dir = workspace / f"removed-{role}-value"
        shutil.copytree(reconstructed_dir, changed_dir)
        tag = f"{role}Value"
        changed_path = next(
            path
            for path in sorted(changed_dir.glob("*.xmi"))
            if f"<{tag}" in path.read_text(encoding="utf-8")
        )
        text = changed_path.read_text(encoding="utf-8")
        changed_text, substitutions = re.subn(
            rf"\s*<{tag}\b[^>]*/>",
            "",
            text,
            count=1,
        )
        if substitutions != 1:
            raise ConformanceError(
                f"absent-versus-explicit-{role}",
                f"could not remove one explicit {tag}",
            )
        changed_path.write_text(
            changed_text,
            encoding="utf-8",
            newline="\n",
        )
        changed_comparison = compare_full_corpus(
            repository_root,
            changed_dir,
        )
        witness(
            f"absent-versus-explicit-{role}",
            requirement,
            f"removing one explicit {tag} changes the canonical facts",
            not changed_comparison["ok"]
            and changed_comparison["summary"]["differences"] > 0,
        )

    missing_dir = workspace / "missing-manifest"
    shutil.copytree(forward["manifests"][0].parent, missing_dir)
    next(iter(sorted(missing_dir.glob("*.preservation.json")))).unlink()
    rejected(
        "missing-manifest",
        "missing manifests",
        "FULL_CORPUS_MANIFEST_COUNT",
        lambda: reverse_full_corpus(
            missing_dir,
            forward["v2"],
            workspace / "missing-output",
        ),
    )

    altered_dir = workspace / "altered-manifest"
    shutil.copytree(forward["manifests"][0].parent, altered_dir)
    altered_path = next(iter(sorted(altered_dir.glob("*.preservation.json"))))
    altered = json.loads(altered_path.read_text(encoding="utf-8"))
    altered["payload"]["sourceFilename"] = "changed.xmi"
    altered_path.write_text(
        json.dumps(altered, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    rejected(
        "altered-manifest",
        "altered manifests",
        "MANIFEST_DIGEST",
        lambda: reverse_full_corpus(
            altered_dir,
            forward["v2"],
            workspace / "altered-output",
        ),
    )

    mismatch_dir = workspace / "mismatched-manifest"
    shutil.copytree(forward["manifests"][0].parent, mismatch_dir)
    mismatch_path = next(iter(sorted(mismatch_dir.glob("*.preservation.json"))))
    mismatch = json.loads(mismatch_path.read_text(encoding="utf-8"))
    mismatch["payload"]["sourceSha256"] = "0" * 64
    mismatch["payloadSha256"] = hashlib.sha256(
        canonical_json(mismatch["payload"])
    ).hexdigest()
    mismatch_path.write_text(
        json.dumps(mismatch, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    rejected(
        "mismatched-manifest",
        "mismatched manifests",
        "MANIFEST_SOURCE_DIGEST",
        lambda: reverse_full_corpus(
            mismatch_dir,
            forward["v2"],
            workspace / "mismatch-output",
        ),
    )

    invalid_manifest = json.loads(
        forward["manifests"][0].read_text(encoding="utf-8")
    )
    del invalid_manifest["payloadSha256"]
    rejected(
        "schema-invalid-manifest",
        "schema-invalid manifests",
        "SCHEMA_VALIDATION_ERROR",
        lambda: validate_instance_against_schema(
            invalid_manifest,
            repository_root / "schemas" / "preservation-manifest.schema.json",
        ),
    )

    unresolved = copy.deepcopy(raw)
    unresolved_reference = next(
        declaration["generalizations"][0]
        for artifact in unresolved["artifacts"]
        for declaration in artifact["declarations"]
        if declaration["generalizations"]
        and declaration["generalizations"][0]["form"] != "href"
    )
    unresolved_reference["sourceValue"] = "_missing_target"
    rejected(
        "unresolved-local-reference",
        "unresolved local references",
        "FACT_REFERENCE_UNRESOLVED",
        lambda: canonicalize_facts(unresolved),
    )

    unresolved_external = copy.deepcopy(raw)
    external_reference = next(
        reference
        for artifact in unresolved_external["artifacts"]
        for reference in _walk_dicts(artifact)
        if reference.get("form") == "href"
        and isinstance(reference.get("sourceValue"), str)
        and reference["sourceValue"].startswith(("http://", "https://"))
    )
    document = external_reference["sourceValue"].split("#", 1)[0]
    external_reference["sourceValue"] = f"{document}#_missing_external_target"
    rejected(
        "unresolved-external-reference",
        "unresolved external references",
        "FACT_EXTERNAL_ID_UNRESOLVED",
        lambda: canonicalize_facts(unresolved_external),
    )

    unsupported_dir = workspace / "unsupported"
    unsupported_dir.mkdir()
    descriptor = next(
        artifact
        for artifact in canonical["artifacts"]
        if artifact["filename"] == "CoreRAAML.xmi"
    )
    unsupported_text = (
        repository_root / "sources" / "cache" / descriptor["filename"]
    ).read_text(encoding="utf-8")
    unsupported_text = unsupported_text.replace(
        'xmi:type="uml:Property"',
        'xmi:type="uml:Operation"',
        1,
    )
    (unsupported_dir / descriptor["filename"]).write_text(
        unsupported_text,
        encoding="utf-8",
    )
    rejected(
        "unsupported-property-kind",
        "constructs deliberately outside v0.1",
        "FACT_PROPERTY_KIND",
        lambda: extract_artifact_set(
            repository_root,
            [
                {
                    "id": descriptor["artifactId"],
                    "filename": descriptor["filename"],
                    "sha256": descriptor["sha256"],
                }
            ],
            unsupported_dir,
        ),
    )

    security_payloads = [
        (
            "xml-dtd",
            "DTDs",
            b'<!DOCTYPE root [<!ENTITY x "expanded">]><root>&x;</root>',
            "XML_DTD_FORBIDDEN",
            XmlLimits(),
        ),
        (
            "xml-external-entity",
            "external entities",
            b'<!DOCTYPE root [<!ENTITY x SYSTEM "file:///etc/passwd">]><root>&x;</root>',
            "XML_DTD_FORBIDDEN",
            XmlLimits(),
        ),
        (
            "xml-xinclude",
            "XInclude",
            b'<root xmlns:x="http://www.w3.org/2001/XInclude">'
            b'<x:include href="file:///etc/passwd"/></root>',
            "XML_XINCLUDE_FORBIDDEN",
            XmlLimits(),
        ),
        (
            "xml-network-reference",
            "implicit network retrieval",
            b'<root href="https://example.invalid/model.xmi#id"/>',
            "XML_REMOTE_REFERENCE_UNPINNED",
            XmlLimits(),
        ),
        (
            "xml-file-reference",
            "implicit file retrieval",
            b'<root href="file:///etc/passwd"/>',
            "XML_FILE_REFERENCE_FORBIDDEN",
            XmlLimits(),
        ),
        (
            "xml-path-traversal",
            "path traversal",
            b'<root href="../outside.xmi#id"/>',
            "XML_PATH_TRAVERSAL",
            XmlLimits(),
        ),
        (
            "xml-depth-limit",
            "excessive XML depth",
            b"<a><b><c/></b></a>",
            "XML_DEPTH_LIMIT",
            XmlLimits(depth=2),
        ),
        (
            "xml-attribute-limit",
            "excessive XML attributes",
            b'<root a="1" b="2"/>',
            "XML_ATTRIBUTE_COUNT_LIMIT",
            XmlLimits(attributes_per_element=1),
        ),
        (
            "xml-attribute-size-limit",
            "excessive XML attribute size",
            b'<root attribute="large"/>',
            "XML_ATTRIBUTE_SIZE_LIMIT",
            XmlLimits(attribute_bytes=8),
        ),
        (
            "xml-input-limit",
            "excessive XML input size",
            b"<root/>",
            "XML_INPUT_LIMIT",
            XmlLimits(input_bytes=4),
        ),
        (
            "xml-text-limit",
            "excessive XML text",
            b"<root>large</root>",
            "XML_TEXT_LIMIT",
            XmlLimits(text_bytes=4),
        ),
        (
            "xml-entity-expansion",
            "entity-expansion and resource-exhaustion attempts",
            (
                b'<!DOCTYPE root [<!ENTITY a "1234567890">'
                b'<!ENTITY b "&a;&a;&a;&a;">]><root>&b;</root>'
            ),
            "XML_DTD_FORBIDDEN",
            XmlLimits(),
        ),
        (
            "xml-malformed",
            "malformed XML",
            b"<root>",
            "XML_MALFORMED",
            XmlLimits(),
        ),
    ]
    security_dir = workspace / "security"
    security_dir.mkdir()
    for case_id, requirement, payload, code, limits in security_payloads:
        path = security_dir / f"{case_id}.xmi"
        path.write_bytes(payload)
        rejected(
            case_id,
            requirement,
            code,
            lambda path=path, limits=limits: preflight_xml(
                path,
                limits=limits,
            ),
        )

    symlink_target = security_dir / "symlink-target.xmi"
    symlink_target.write_bytes(b"<root/>")
    symlink = security_dir / "symlink.xmi"
    symlink.symlink_to(symlink_target)
    rejected(
        "xml-symlink",
        "symlink escape",
        "XML_SYMLINK",
        lambda: preflight_xml(symlink),
    )

    collision_output = workspace / "collision-output"
    rejected(
        "injected-id-collision",
        "injected ID collisions",
        "SYNTHETIC_ID_COLLISION",
        lambda: reverse_full_corpus(
            forward["manifests"][0].parent,
            forward["v2"],
            collision_output,
            hash_provider=lambda _value: "0" * 64,
        ),
    )
    witness(
        "collision-no-partial-output",
        "collision rejection before output",
        "the injected collision writes no partial output directory",
        not collision_output.exists(),
    )

    icon_lengths = [
        len(icon["content"])
        for declaration in declarations
        for icon in declaration["icons"]
    ]
    witness(
        "large-icon-payload",
        "large icon payloads",
        "the largest 7,215-character icon payload compares exactly",
        max(icon_lengths) == 7215 and comparison["ok"],
    )

    return sorted(cases, key=lambda item: item["id"])


def _walk_dicts(value: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if isinstance(value, dict):
        result.append(value)
        for child in value.values():
            result.extend(_walk_dicts(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(_walk_dicts(child))
    return result
