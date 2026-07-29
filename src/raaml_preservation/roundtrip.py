from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET

from .facts import extract_artifact_set, extract_facts, serialize_facts
from .sources import load_lock


SCHEMA_VERSION = "0.1.0"
SLICE_ID = "milestone-3-core-general-stpa"
FULL_CORPUS_ID = "milestone-4-full-corpus"
FULL_CORPUS_V2_FILENAME = "raaml-full-corpus.sysml"
FULL_ARTIFACTS = {
    "CoreRAAML.xmi",
    "CoreRAAMLLib.xmi",
    "GeneralRAAML.xmi",
    "GeneralRAAMLLib.xmi",
}
STPA_PROFILE_NAMES = {"ControlStructure", "Controller", "ControlAction"}
STPA_LIBRARY_NAMES = {"Loss"}
XMI = "http://www.omg.org/spec/XMI/20131001"
UML = "http://www.omg.org/spec/UML/20161101"
MOFEXT = "http://www.omg.org/spec/MOF/20131001"
XMI_ID = f"{{{XMI}}}id"
XMI_TYPE = f"{{{XMI}}}type"
XMI_IDREF = f"{{{XMI}}}idref"
SAFE_NAME = re.compile(r"[^A-Za-z0-9_]")

ET.register_namespace("xmi", XMI)
ET.register_namespace("uml", UML)
ET.register_namespace("mofext", MOFEXT)


class RoundTripError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def select_milestone_three_slice(canonical: dict[str, Any]) -> dict[str, Any]:
    selected = copy.deepcopy(canonical)
    selected["artifacts"] = []
    for artifact in canonical["artifacts"]:
        filename = artifact["filename"]
        if filename in FULL_ARTIFACTS:
            selected["artifacts"].append(copy.deepcopy(artifact))
            continue
        if filename == "STPA.xmi":
            item = copy.deepcopy(artifact)
            item["declarations"] = [
                declaration
                for declaration in item["declarations"]
                if declaration["name"] in STPA_PROFILE_NAMES
            ]
            selected["artifacts"].append(item)
            continue
        if filename == "STPALib.xmi":
            item = copy.deepcopy(artifact)
            item["declarations"] = [
                declaration
                for declaration in item["declarations"]
                if declaration["name"] in STPA_LIBRARY_NAMES
            ]
            kept_ids = {item["declarations"][0]["id"]}
            item["applications"] = [
                application
                for application in item["applications"]
                if application["target"]["target"] in kept_ids
            ]
            selected["artifacts"].append(item)
    selected["artifacts"].sort(key=lambda item: item["artifactId"])
    _require_slice_coverage(selected)
    _require_reference_closure(selected)
    return selected


def create_manifest(canonical_slice: dict[str, Any]) -> dict[str, Any]:
    v2_bytes = render_v2(canonical_slice).encode("utf-8")
    payload = {
        "sliceId": SLICE_ID,
        "v2Sha256": hashlib.sha256(v2_bytes).hexdigest(),
        "nativeTargets": _native_targets(canonical_slice),
        "canonicalFacts": canonical_slice,
    }
    return {
        "schemaVersion": SCHEMA_VERSION,
        "documentKind": "raaml-preservation-manifest",
        "payloadSha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
        "payload": payload,
    }


def create_full_corpus_manifest(
    canonical: dict[str, Any],
    artifact: dict[str, Any],
    v2_bytes: bytes,
) -> dict[str, Any]:
    artifact_facts = copy.deepcopy(canonical)
    artifact_facts["artifacts"] = [copy.deepcopy(artifact)]
    payload = {
        "scopeId": FULL_CORPUS_ID,
        "artifactId": artifact["artifactId"],
        "sourceFilename": artifact["filename"],
        "sourceSha256": artifact["sha256"],
        "v2Filename": FULL_CORPUS_V2_FILENAME,
        "v2Sha256": hashlib.sha256(v2_bytes).hexdigest(),
        "nativeTargets": _native_targets(
            artifact_facts,
            root_package="RaamlFullCorpus",
        ),
        "canonicalFacts": artifact_facts,
    }
    return {
        "schemaVersion": SCHEMA_VERSION,
        "documentKind": "raaml-preservation-manifest",
        "payloadSha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
        "payload": payload,
    }


def verify_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        raise RoundTripError("MANIFEST_VERSION", "unsupported manifest version")
    if manifest.get("documentKind") != "raaml-preservation-manifest":
        raise RoundTripError("MANIFEST_KIND", "unexpected manifest document kind")
    payload = manifest.get("payload")
    if not isinstance(payload, dict):
        raise RoundTripError("MANIFEST_PAYLOAD", "manifest payload is missing")
    expected = hashlib.sha256(canonical_json(payload)).hexdigest()
    if manifest.get("payloadSha256") != expected:
        raise RoundTripError(
            "MANIFEST_DIGEST",
            "manifest payload does not match payloadSha256",
        )
    if payload.get("sliceId") != SLICE_ID:
        raise RoundTripError("MANIFEST_SLICE", "unexpected slice identity")
    facts = payload.get("canonicalFacts")
    if not isinstance(facts, dict):
        raise RoundTripError("MANIFEST_FACTS", "canonical facts are missing")
    _require_slice_coverage(facts)
    _require_reference_closure(facts)
    return facts


def verify_native_targets(manifest: dict[str, Any], v2_path: Path) -> None:
    verify_manifest(manifest)
    try:
        v2_bytes = v2_path.read_bytes()
        text = v2_bytes.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise RoundTripError("V2_READ", str(error)) from error
    if hashlib.sha256(v2_bytes).hexdigest() != manifest["payload"].get("v2Sha256"):
        raise RoundTripError(
            "V2_DIGEST",
            "SysML v2 model does not match the manifest v2Sha256",
        )
    targets = manifest["payload"].get("nativeTargets")
    if not isinstance(targets, list):
        raise RoundTripError("MANIFEST_NATIVE_TARGETS", "nativeTargets is missing")
    expected_counts: dict[str, int] = {}
    for target in targets:
        line = target.get("declaration")
        if not isinstance(line, str) or not line:
            raise RoundTripError(
                "MANIFEST_NATIVE_TARGET",
                "native target declaration is invalid",
            )
        expected_counts[line] = expected_counts.get(line, 0) + 1
    actual_lines = [line.strip() for line in text.splitlines()]
    missing = [
        line
        for line, count in expected_counts.items()
        if actual_lines.count(line) != count
    ]
    if missing:
        raise RoundTripError(
            "V2_TARGET_MISSING",
            f"native v2 target count mismatch: {missing[:3]}",
        )


def forward_slice(repository_root: Path, output_dir: Path) -> dict[str, Any]:
    _, canonical = extract_facts(repository_root)
    canonical_slice = select_milestone_three_slice(canonical)
    manifest = create_manifest(canonical_slice)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "preservation-manifest.json"
    v2_path = output_dir / "raaml-milestone-3.sysml"
    manifest_path.write_bytes(
        json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    )
    v2_path.write_text(render_v2(canonical_slice), encoding="utf-8", newline="\n")
    return {
        "manifest": manifest_path,
        "v2": v2_path,
        "facts": canonical_slice,
    }


def forward_full_corpus(repository_root: Path, output_dir: Path) -> dict[str, Any]:
    _, canonical = extract_facts(repository_root)
    _require_full_corpus_coverage(canonical)
    _require_reference_closure(canonical)
    v2_text = render_full_corpus_v2(canonical)
    v2_bytes = v2_text.encode("utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    v2_path = output_dir / FULL_CORPUS_V2_FILENAME
    v2_path.write_bytes(v2_bytes)
    manifest_dir = output_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_paths = []
    for artifact in canonical["artifacts"]:
        manifest = create_full_corpus_manifest(canonical, artifact, v2_bytes)
        manifest_path = (
            manifest_dir
            / f"{Path(artifact['filename']).stem}.preservation.json"
        )
        manifest_path.write_bytes(
            json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        )
        manifest_paths.append(manifest_path)
    return {
        "manifests": manifest_paths,
        "v2": v2_path,
        "facts": canonical,
    }


def reverse_slice(
    manifest_path: Path,
    v2_path: Path,
    output_dir: Path,
) -> list[Path]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RoundTripError("MANIFEST_READ", str(error)) from error
    facts = verify_manifest(manifest)
    verify_native_targets(manifest, v2_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for artifact in facts["artifacts"]:
        path = output_dir / artifact["filename"]
        path.write_bytes(render_v1_artifact(facts, artifact))
        paths.append(path)
    return paths


def compare_reconstructed(
    repository_root: Path,
    manifest_path: Path,
    reconstructed_dir: Path,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = verify_manifest(manifest)
    descriptors = [
        {
            "id": artifact["artifactId"],
            "filename": artifact["filename"],
            "sha256": artifact["sha256"],
        }
        for artifact in expected["artifacts"]
    ]
    _, actual = extract_artifact_set(repository_root, descriptors, reconstructed_dir)
    differences = _differences(expected, actual)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "documentKind": "raaml-roundtrip-report",
        "sliceId": SLICE_ID,
        "ok": not differences,
        "summary": {
            "artifacts": len(expected["artifacts"]),
            "sourceFactsSha256": hashlib.sha256(serialize_facts(expected)).hexdigest(),
            "reconstructedFactsSha256": hashlib.sha256(
                serialize_facts(actual)
            ).hexdigest(),
            "differences": len(differences),
        },
        "differences": differences,
        "sourceFacts": expected,
        "reconstructedFacts": actual,
    }


def render_v2(facts: dict[str, Any]) -> str:
    return _render_v2_model(
        facts,
        root_package="RaamlMilestone3",
        include_preservation_metadata=False,
        include_scalar_import=False,
    )


def render_full_corpus_v2(facts: dict[str, Any]) -> str:
    return _render_v2_model(
        facts,
        root_package="RaamlFullCorpus",
        include_preservation_metadata=True,
        include_scalar_import=True,
    )


def _render_v2_model(
    facts: dict[str, Any],
    *,
    root_package: str,
    include_preservation_metadata: bool,
    include_scalar_import: bool,
) -> str:
    lines = [
        f"package {root_package} {{",
    ]
    if include_scalar_import:
        lines.append("    private import ScalarValues::*;")
    lines.append("    private occurrence def PreservedAssociationEnd;")
    if include_preservation_metadata:
        lines.extend(
            [
                "    metadata def Raaml_BaseAnnotation;",
                (
                    "    metadata def Raaml_LibraryClass "
                    ":> Raaml_BaseAnnotation;"
                ),
                (
                    "    metadata def Raaml_AssociationClass "
                    ":> Raaml_BaseAnnotation;"
                ),
                (
                    "    metadata def Raaml_LibraryAssociation "
                    ":> Raaml_BaseAnnotation;"
                ),
            ]
        )
    for artifact in facts["artifacts"]:
        package_name = _identifier(Path(artifact["filename"]).stem)
        lines.append(f"    package {package_name} {{")
        for declaration in artifact["declarations"]:
            name = _identifier(declaration["name"] or declaration["id"])
            kind = declaration["kind"]
            if kind == "Stereotype":
                specialization = (
                    " :> RaamlFullCorpus::Raaml_BaseAnnotation"
                    if include_preservation_metadata
                    else ""
                )
                lines.append(f"        metadata def {name}{specialization};")
            elif kind == "Class":
                if include_preservation_metadata:
                    lines.append(
                        "        #RaamlFullCorpus::Raaml_LibraryClass"
                    )
                lines.append(f"        occurrence def {name};")
            elif kind in {"Association", "AssociationClass"}:
                if include_preservation_metadata:
                    marker = (
                        "Raaml_AssociationClass"
                        if kind == "AssociationClass"
                        else "Raaml_LibraryAssociation"
                    )
                    lines.append(f"        #RaamlFullCorpus::{marker}")
                lines.append(f"        connection def {name} {{")
                for end_name, end_type in _association_ends(
                    facts, artifact, declaration
                ):
                    lines.append(f"            end {end_name} : {end_type};")
                lines.append("        }")
            elif kind == "Enumeration":
                lines.append(f"        enum def {name} {{")
                for literal in declaration["literals"]:
                    lines.append(f"            {_identifier(literal['name'])};")
                lines.append("        }")
            for constraint in declaration["constraints"]:
                constraint_name = _identifier(
                    f"{name}_{constraint['name'] or 'Constraint'}"
                )
                lines.append(f"        constraint def {constraint_name};")
        lines.append("    }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _native_targets(
    facts: dict[str, Any],
    *,
    root_package: str | None = None,
) -> list[dict[str, str]]:
    targets = []
    for artifact in facts["artifacts"]:
        package_name = _identifier(Path(artifact["filename"]).stem)
        for declaration in artifact["declarations"]:
            name = _identifier(declaration["name"] or declaration["id"])
            carrier = {
                "Stereotype": "metadata def",
                "Class": "occurrence def",
                "Association": "connection def",
                "AssociationClass": "connection def",
                "Enumeration": "enum def",
            }[declaration["kind"]]
            terminator = " {" if carrier in {"connection def", "enum def"} else ";"
            target = {
                "canonicalId": declaration["id"],
                "carrier": carrier,
                "declaration": f"{carrier} {name}{terminator}",
            }
            if root_package is not None:
                target["qualifiedName"] = (
                    f"{root_package}::{package_name}::{name}"
                )
            targets.append(target)
            for constraint in declaration["constraints"]:
                constraint_name = _identifier(
                    f"{name}_{constraint['name'] or 'Constraint'}"
                )
                target = {
                    "canonicalId": constraint["id"],
                    "carrier": "constraint def",
                    "declaration": f"constraint def {constraint_name};",
                }
                if root_package is not None:
                    target["qualifiedName"] = (
                        f"{root_package}::{package_name}::{constraint_name}"
                    )
                targets.append(target)
    return sorted(targets, key=lambda item: item["canonicalId"])


def _association_ends(
    facts: dict[str, Any],
    current_artifact: dict[str, Any],
    declaration: dict[str, Any],
) -> list[tuple[str, str]]:
    properties: dict[str, dict[str, Any]] = {}
    declarations: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for artifact in facts["artifacts"]:
        for candidate in artifact["declarations"]:
            declarations[candidate["id"]] = (artifact, candidate)
            for prop in candidate["properties"] + candidate["ownedEnds"]:
                properties[prop["id"]] = prop
    result = []
    used_names: set[str] = set()
    for ordinal, reference in enumerate(declaration["memberEnds"], start=1):
        prop = properties.get(reference["target"])
        if prop is None or prop["type"] is None:
            end_name = f"end{ordinal}"
            end_type = "PreservedAssociationEnd"
        else:
            end_name = _identifier(f"end_{prop['name'] or ordinal}")
            target = declarations.get(prop["type"]["target"])
            if target is None:
                end_type = "PreservedAssociationEnd"
            else:
                target_artifact, target_declaration = target
                target_name = _identifier(
                    target_declaration["name"] or target_declaration["id"]
                )
                if target_artifact["artifactId"] == current_artifact["artifactId"]:
                    end_type = target_name
                else:
                    end_type = (
                        f"{_identifier(Path(target_artifact['filename']).stem)}"
                        f"::{target_name}"
                    )
        if end_name in used_names:
            end_name = f"{end_name}{ordinal}"
        used_names.add(end_name)
        result.append((end_name, end_type))
    while len(result) < 2:
        ordinal = len(result) + 1
        result.append((f"end{ordinal}", "PreservedAssociationEnd"))
    return result


def render_v1_artifact(
    facts: dict[str, Any],
    artifact: dict[str, Any],
) -> bytes:
    context = _RenderContext(facts)
    for namespace in facts["artifacts"]:
        for item in namespace["namespaces"]:
            ET.register_namespace(item["prefix"], item["uri"])
    root = ET.Element(f"{{{XMI}}}XMI")
    package = artifact["packages"][0]
    model_tag = f"{{{UML}}}{'Profile' if package['kind'] == 'Profile' else 'Package'}"
    model = ET.SubElement(
        root,
        model_tag,
        {
            XMI_TYPE: f"uml:{package['kind']}",
            XMI_ID: context.ids[package["id"]],
            "name": package["name"],
        },
    )
    if package["uri"]["present"]:
        model.set("URI", package["uri"]["value"] or "")
    _append_comments(model, package["comments"], artifact, context, package["id"])
    for machinery in artifact["machinery"]:
        node = ET.SubElement(
            model,
            _machinery_tag(machinery["kind"]),
            {
                XMI_TYPE: _machinery_type(machinery["kind"]),
                XMI_ID: context.ids[machinery["id"]],
            },
        )
        for reference in machinery["targets"]:
            _append_reference(node, reference, artifact, context)
        _append_comments(node, machinery["comments"], artifact, context, machinery["id"])
    for declaration in artifact["declarations"]:
        node = _append_declaration(model, declaration, artifact, context)
        _append_comments(node, declaration["comments"], artifact, context, declaration["id"])
        for extension in declaration["extensions"]:
            _append_extension(model, extension, artifact, context)
    for namespace in artifact["namespaces"]:
        ET.SubElement(
            root,
            f"{{{MOFEXT}}}Tag",
            {
                XMI_TYPE: "mofext:Tag",
                XMI_ID: _digest_id(artifact["artifactId"], namespace["prefix"]),
                "name": "org.omg.xmi.nsPrefix",
                "value": namespace["prefix"],
                "element": context.ids[package["id"]],
            },
        )
    for application in artifact["applications"]:
        attrs = {
            XMI_ID: context.ids[application["id"]],
            application["targetProperty"]: context.reference_value(
                application["target"], artifact
            ),
        }
        for value in application["values"]:
            attrs[value["property"]] = " ".join(value["values"])
        ET.SubElement(
            root,
            f"{{{application['stereotypeNamespace']}}}{application['stereotypeName']}",
            attrs,
        )
    ET.indent(root, space="  ")
    return ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    ) + b"\n"


class _RenderContext:
    def __init__(self, facts: dict[str, Any]):
        self.facts = facts
        self.artifact_by_id = {
            artifact["artifactId"]: artifact for artifact in facts["artifacts"]
        }
        self.artifact_for_target: dict[str, dict[str, Any]] = {}
        self.ids: dict[str, str] = {}
        for artifact in facts["artifacts"]:
            key = Path(artifact["filename"]).stem
            for package in artifact["packages"]:
                self.ids[package["id"]] = synthetic_id(key, package["name"])
                self.artifact_for_target[package["id"]] = artifact
            for declaration in artifact["declarations"]:
                name = declaration["name"] or declaration["id"]
                self.ids[declaration["id"]] = synthetic_id(key, name)
                self.artifact_for_target[declaration["id"]] = artifact
                self._index_owned(artifact, declaration, key)
            for machinery in artifact["machinery"]:
                self.ids[machinery["id"]] = _digest_id(key, machinery["id"])
                self.artifact_for_target[machinery["id"]] = artifact
            for application in artifact["applications"]:
                self.ids[application["id"]] = _digest_id(key, application["id"])
                self.artifact_for_target[application["id"]] = artifact
        if len(set(self.ids.values())) != len(self.ids):
            raise RoundTripError("SYNTHETIC_ID_COLLISION", "synthetic ID collision")

    def _index_owned(
        self,
        artifact: dict[str, Any],
        declaration: dict[str, Any],
        key: str,
    ) -> None:
        for relation in ("properties", "ownedEnds", "extensions", "constraints", "connectors"):
            for ordinal, item in enumerate(declaration[relation], start=1):
                local = item.get("name") or item["id"]
                self.ids[item["id"]] = synthetic_owned_id(
                    key, declaration["id"], relation, local, ordinal
                )
                self.artifact_for_target[item["id"]] = artifact
                if relation == "extensions":
                    for end_ordinal, end in enumerate(item["ownedEnds"], start=1):
                        self.ids[end["id"]] = synthetic_owned_id(
                            key,
                            item["id"],
                            "ExtensionEnd",
                            end.get("name") or end["id"],
                            end_ordinal,
                        )
                        self.artifact_for_target[end["id"]] = artifact

    def reference_value(
        self,
        reference: dict[str, str],
        current_artifact: dict[str, Any],
    ) -> str:
        target = reference["target"]
        if target.startswith("external::"):
            _, rest = target.split("external::", 1)
            document, separator, fragment = rest.partition("::")
            if not separator:
                raise RoundTripError(
                    "EXTERNAL_REFERENCE_SHAPE",
                    f"invalid external identity: {target}",
                )
            if fragment == "Package::UML":
                fragment = "_0"
            return f"{document}#{fragment}"
        if target not in self.ids:
            raise RoundTripError(
                "REFERENCE_TARGET_MISSING",
                f"reference target is absent from slice: {target}",
            )
        target_artifact = self.artifact_for_target[target]
        if reference["sourceForm"] == "href":
            return (
                "https://www.omg.org/spec/RAAML/20240219/"
                f"{target_artifact['filename']}#{self.ids[target]}"
            )
        if target_artifact["artifactId"] != current_artifact["artifactId"]:
            raise RoundTripError(
                "REFERENCE_FORM_CROSS_FILE",
                f"non-href cross-file reference: {target}",
            )
        return self.ids[target]


def _append_declaration(
    model: ET.Element,
    declaration: dict[str, Any],
    artifact: dict[str, Any],
    context: _RenderContext,
) -> ET.Element:
    attrs = {
        XMI_TYPE: f"uml:{declaration['kind']}",
        XMI_ID: context.ids[declaration["id"]],
    }
    if declaration["name"] is not None:
        attrs["name"] = declaration["name"]
    if declaration["isAbstract"]["present"]:
        attrs["isAbstract"] = str(declaration["isAbstract"]["value"]).lower()
    node = ET.SubElement(model, "packagedElement", attrs)
    for reference in declaration["generalizations"]:
        relationship = ET.SubElement(
            node,
            "generalization",
            {
                XMI_TYPE: "uml:Generalization",
                XMI_ID: _digest_id(declaration["id"], "generalization", reference["target"]),
            },
        )
        _append_reference(relationship, reference, artifact, context)
    for ordinal, prop in enumerate(declaration["properties"], start=1):
        _append_property(node, "ownedAttribute", prop, artifact, context, ordinal)
    for ordinal, owned_end in enumerate(declaration["ownedEnds"], start=1):
        _append_property(node, "ownedEnd", owned_end, artifact, context, ordinal)
    for reference in declaration["memberEnds"]:
        _append_reference(node, reference, artifact, context)
    for reference in declaration["navigableOwnedEnds"]:
        _append_reference(node, reference, artifact, context)
    for literal_ordinal, literal in enumerate(declaration["literals"], start=1):
        literal_node = ET.SubElement(
            node,
            "ownedLiteral",
            {
                XMI_TYPE: "uml:EnumerationLiteral",
                XMI_ID: synthetic_owned_id(
                    Path(artifact["filename"]).stem,
                    declaration["id"],
                    "EnumerationLiteral",
                    literal["name"],
                    literal_ordinal,
                ),
                "name": literal["name"],
            },
        )
        _append_comments(
            literal_node,
            literal["comments"],
            artifact,
            context,
            f"{declaration['id']}::{literal['name']}",
        )
    for constraint in declaration["constraints"]:
        constraint_node = ET.SubElement(
            node,
            "ownedRule",
            {
                XMI_TYPE: "uml:Constraint",
                XMI_ID: context.ids[constraint["id"]],
            },
        )
        if constraint["name"] is not None:
            constraint_node.set("name", constraint["name"])
        for reference in constraint["constrainedElements"]:
            _append_reference(constraint_node, reference, artifact, context)
        specification = ET.SubElement(
            constraint_node,
            "specification",
            {
                XMI_TYPE: "uml:OpaqueExpression",
                XMI_ID: _digest_id(constraint["id"], "specification"),
            },
        )
        for body in constraint["bodyLines"]:
            ET.SubElement(specification, "body").text = body
        for language in constraint["languages"]:
            ET.SubElement(specification, "language").text = language
        _append_comments(
            constraint_node,
            constraint["comments"],
            artifact,
            context,
            constraint["id"],
        )
    for icon_ordinal, icon in enumerate(declaration["icons"], start=1):
        icon_node = ET.SubElement(
            node,
            "icon",
            {
                XMI_TYPE: "uml:Image",
                XMI_ID: synthetic_owned_id(
                    Path(artifact["filename"]).stem,
                    declaration["id"],
                    "Image",
                    "icon",
                    icon_ordinal,
                ),
                "content": icon["content"],
            },
        )
        for field in ("format", "location"):
            if icon[field]["present"]:
                icon_node.set(field, icon[field]["value"] or "")
    return node


def _append_extension(
    model: ET.Element,
    extension: dict[str, Any],
    artifact: dict[str, Any],
    context: _RenderContext,
) -> None:
    node = ET.SubElement(
        model,
        "packagedElement",
        {
            XMI_TYPE: "uml:Extension",
            XMI_ID: context.ids[extension["id"]],
        },
    )
    for reference in extension["memberEnds"]:
        _append_reference(node, reference, artifact, context)
    for reference in extension["navigableOwnedEnds"]:
        _append_reference(node, reference, artifact, context)
    for ordinal, end in enumerate(extension["ownedEnds"], start=1):
        _append_property(node, "ownedEnd", end, artifact, context, ordinal)
    _append_comments(node, extension["comments"], artifact, context, extension["id"])


def _append_property(
    owner: ET.Element,
    tag: str,
    prop: dict[str, Any],
    artifact: dict[str, Any],
    context: _RenderContext,
    ordinal: int,
) -> None:
    attrs = {
        XMI_TYPE: f"uml:{prop['kind']}",
        XMI_ID: context.ids[prop["id"]],
    }
    if prop["name"] is not None:
        attrs["name"] = prop["name"]
    for field in ("aggregation",):
        if prop[field]["present"]:
            attrs[field] = prop[field]["value"] or ""
    for field in ("isDerived", "isReadOnly", "isOrdered", "isUnique"):
        if prop[field]["present"]:
            attrs[field] = str(prop[field]["value"]).lower()
    node = ET.SubElement(owner, tag, attrs)
    if prop["type"] is not None:
        _append_reference(node, prop["type"], artifact, context)
    for relation in ("subsettedProperties", "redefinedProperties"):
        for reference in prop[relation]:
            _append_reference(node, reference, artifact, context)
    for role in ("lower", "upper", "default"):
        value = prop[role]
        if value["present"]:
            child = ET.SubElement(
                node,
                f"{role}Value",
                {
                    XMI_TYPE: value["kind"],
                    XMI_ID: _digest_id(prop["id"], role, str(ordinal)),
                },
            )
            if value["value"] is not None:
                child.set("value", value["value"])
    _append_comments(node, prop["comments"], artifact, context, prop["id"])


def _append_comments(
    owner: ET.Element,
    comments: list[dict[str, Any]],
    artifact: dict[str, Any],
    context: _RenderContext,
    owner_id: str,
) -> None:
    for ordinal, comment in enumerate(comments, start=1):
        node = ET.SubElement(
            owner,
            "ownedComment",
            {
                XMI_TYPE: "uml:Comment",
                XMI_ID: _digest_id(owner_id, "comment", str(ordinal)),
                "body": comment["body"],
            },
        )
        for reference in comment["annotatedElements"]:
            _append_reference(node, reference, artifact, context)


def _append_reference(
    owner: ET.Element,
    reference: dict[str, str],
    artifact: dict[str, Any],
    context: _RenderContext,
) -> None:
    value = context.reference_value(reference, artifact)
    role = reference["role"]
    if reference["sourceForm"] == "attribute":
        owner.set(role, value)
    elif reference["sourceForm"] == "idref":
        ET.SubElement(owner, role, {XMI_IDREF: value})
    else:
        ET.SubElement(owner, role, {"href": value})


def _require_slice_coverage(facts: dict[str, Any]) -> None:
    filenames = {artifact["filename"] for artifact in facts.get("artifacts", [])}
    required = FULL_ARTIFACTS | {"STPA.xmi", "STPALib.xmi"}
    if filenames != required:
        raise RoundTripError(
            "SLICE_ARTIFACTS",
            f"expected {sorted(required)}, got {sorted(filenames)}",
        )
    declarations = {
        declaration["name"]
        for artifact in facts["artifacts"]
        for declaration in artifact["declarations"]
    }
    required_names = {
        "Situation",
        "ControlStructure",
        "Controller",
        "ControlAction",
        "Undeveloped",
        "Loss",
    }
    missing = required_names - declarations
    if missing:
        raise RoundTripError("SLICE_DECLARATIONS", f"missing {sorted(missing)}")
    undeveloped = next(
        declaration
        for artifact in facts["artifacts"]
        for declaration in artifact["declarations"]
        if declaration["name"] == "Undeveloped"
    )
    if not undeveloped["icons"] or undeveloped["properties"][0]["name"] != "base_Element":
        raise RoundTripError(
            "SLICE_UNDEVELOPED",
            "Undeveloped must retain base_Element and its icon",
        )
    if not any(
        declaration["constraints"]
        for artifact in facts["artifacts"]
        for declaration in artifact["declarations"]
    ):
        raise RoundTripError("SLICE_OCL", "slice has no constraint")
    if not any(
        application["stereotypeName"] == "Situation"
        for artifact in facts["artifacts"]
        for application in artifact["applications"]
    ):
        raise RoundTripError("SLICE_APPLICATION", "slice has no Situation application")


def _require_full_corpus_coverage(facts: dict[str, Any]) -> None:
    locked = load_lock(
        Path(__file__).resolve().parents[2] / "standards.lock.json"
    )
    expected = {
        artifact["filename"]
        for artifact in locked["artifacts"]
        if artifact["collection"] == "raaml-1.1-definitions"
    }
    actual = {
        artifact["filename"]
        for artifact in facts.get("artifacts", [])
    }
    if len(expected) != 17 or actual != expected:
        raise RoundTripError(
            "FULL_CORPUS_ARTIFACTS",
            f"expected {sorted(expected)}, got {sorted(actual)}",
        )
    declaration_count = sum(
        len(artifact["declarations"]) for artifact in facts["artifacts"]
    )
    if declaration_count != 283:
        raise RoundTripError(
            "FULL_CORPUS_DECLARATIONS",
            f"expected 283 declarations, got {declaration_count}",
        )


def _require_reference_closure(facts: dict[str, Any]) -> None:
    known = set()
    references = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            identifier = value.get("id")
            if isinstance(identifier, str):
                known.add(identifier)
            if {"role", "sourceForm", "target"} <= set(value):
                references.append(value["target"])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(facts)
    missing = sorted(
        target
        for target in references
        if not target.startswith("external::") and target not in known
    )
    if missing:
        raise RoundTripError(
            "REFERENCE_TARGET_MISSING",
            f"slice has {len(missing)} unresolved target(s): {missing[:3]}",
        )


def _differences(expected: Any, actual: Any, path: str = "$") -> list[dict[str, Any]]:
    if type(expected) is not type(actual):
        return [{"path": path, "expected": expected, "actual": actual}]
    if isinstance(expected, dict):
        differences = []
        for key in sorted(set(expected) | set(actual)):
            if key not in expected or key not in actual:
                differences.append(
                    {
                        "path": f"{path}.{key}",
                        "expected": expected.get(key),
                        "actual": actual.get(key),
                    }
                )
            else:
                differences.extend(
                    _differences(expected[key], actual[key], f"{path}.{key}")
                )
        return differences
    if isinstance(expected, list):
        differences = []
        if len(expected) != len(actual):
            differences.append(
                {
                    "path": f"{path}.length",
                    "expected": len(expected),
                    "actual": len(actual),
                }
            )
        for index, (left, right) in enumerate(zip(expected, actual)):
            differences.extend(_differences(left, right, f"{path}[{index}]"))
        return differences
    return [] if expected == actual else [
        {"path": path, "expected": expected, "actual": actual}
    ]


def synthetic_id(artifact: str, name: str) -> str:
    return "_raaml_" + hashlib.sha256(
        f"{artifact}::{name}".encode("utf-8")
    ).hexdigest()[:40]


def synthetic_owned_id(
    artifact: str,
    owner: str,
    kind: str,
    name: str,
    ordinal: int,
) -> str:
    value = f"{artifact}::{owner}::{kind}::{name}::{ordinal}"
    return "_raaml_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:40]


def _digest_id(*parts: str) -> str:
    return "_raaml_" + hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:40]


def _identifier(value: str) -> str:
    result = SAFE_NAME.sub("_", value)
    if not result or result[0].isdigit():
        result = f"_{result}"
    return result


def _machinery_tag(kind: str) -> str:
    return {
        "MetamodelReference": "metamodelReference",
        "PackageImport": "packageImport",
        "ElementImport": "elementImport",
        "ProfileApplication": "profileApplication",
    }[kind]


def _machinery_type(kind: str) -> str:
    return {
        "MetamodelReference": "uml:PackageImport",
        "PackageImport": "uml:PackageImport",
        "ElementImport": "uml:ElementImport",
        "ProfileApplication": "uml:ProfileApplication",
    }[kind]
