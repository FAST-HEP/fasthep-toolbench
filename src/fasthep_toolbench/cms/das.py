from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fasthep_toolbench.command import CommandResult, run_command
from fasthep_toolbench.model import ToolAvailability

DASGOCLIENT_SPEC = {
    "name": "cms.dasgoclient",
    "kind": "external_tool",
    "version": "1.0",
    "availability": {
        "executable": "dasgoclient",
    },
    "install": {
        "method": "github_release",
        "repo": "dmwm/dasgoclient",
        "asset": "dasgoclient",
        "target": ".fasthep/bin/dasgoclient",
    },
    "params": {
        "query": {"type": "string", "required": True},
        "format": {"type": "string", "default": "json"},
        "timeout": {"type": "number", "default": 60},
        "x509_proxy": {"type": "string"},
    },
    "result": {
        "kind": "json",
    },
}


def run_dasgoclient(
    *,
    query: str,
    format: str | None = "json",
    timeout: float | str = 60,
    x509_proxy: str | None = None,
    availability: ToolAvailability | None = None,
) -> CommandResult:
    executable = (
        availability.path
        if availability is not None and availability.path is not None
        else "dasgoclient"
    )
    command = [
        executable,
        "--query",
        query,
    ]
    if format:
        command.extend(["--format", format])
    if x509_proxy is None:
        return run_command(command, timeout=float(timeout))
    return run_command(command, timeout=float(timeout), env=_das_env(x509_proxy))


@dataclass(frozen=True)
class DatasetListEntry:
    dataset: str
    kind: str
    group: str | None
    line: int


def discover_das_datasets(
    *,
    list_dir: Path,
    output_dir: Path,
    era: str,
    version: str,
    x509_proxy: Path | None = None,
    timeout: float = 60,
    runner: Callable[..., CommandResult] = run_dasgoclient,
) -> dict[str, Path]:
    """Discover DAS metadata and file lists from pyRAT-style DATA/MC lists."""
    list_dir = Path(list_dir)
    output_dir = Path(output_dir)
    discovery_dir = output_dir / "discovery"
    discovery_dir.mkdir(parents=True, exist_ok=True)

    entries = [
        *read_dataset_list(list_dir / "DATA.txt", kind="data"),
        *read_dataset_list(list_dir / "MC.txt", kind="mc"),
    ]
    x509_proxy_value = str(x509_proxy) if x509_proxy is not None else None
    dataset_records: list[dict[str, Any]] = []
    file_records: list[dict[str, Any]] = []

    for entry in entries:
        parent_result = _run_das_json(
            runner,
            f"parent dataset={entry.dataset}",
            timeout=timeout,
            x509_proxy=x509_proxy_value,
        )
        parent = _first_name(parent_result["payload"])
        dataset_records.append(
            _record_for(
                entry,
                era=era,
                version=version,
                parent=parent,
                result=_run_das_json(
                    runner,
                    f"dataset dataset={entry.dataset}",
                    timeout=timeout,
                    x509_proxy=x509_proxy_value,
                ),
            )
        )
        file_result = _run_das_text(
            runner,
            f"file dataset={entry.dataset}",
            timeout=timeout,
            x509_proxy=x509_proxy_value,
        )
        file_records.append(_file_record_for(entry, result=file_result))

    paths = {
        "datasets": discovery_dir / "datasets.json",
        "files": discovery_dir / "files.json",
        "cross_sections": discovery_dir / "cross_sections.json",
        "combined": discovery_dir / "combined.json",
    }
    datasets_doc = _document(
        era=era,
        version=version,
        list_dir=list_dir,
        records_key="datasets",
        records=dataset_records,
    )
    cross_sections_doc = _cross_sections_document(
        era=era,
        version=version,
        records=dataset_records,
    )
    combined_doc = _combined_document(
        era=era,
        version=version,
        datasets=dataset_records,
        files=file_records,
        cross_sections=cross_sections_doc["cross_sections"],
    )
    _write_json(paths["datasets"], datasets_doc)
    _write_json(paths["files"], file_records)
    _write_json(paths["cross_sections"], cross_sections_doc)
    _write_json(paths["combined"], combined_doc)
    return paths


def read_dataset_list(path: Path, *, kind: str) -> list[DatasetListEntry]:
    """Read a legacy dataset list, preserving comment sections as groups."""
    entries: list[DatasetListEntry] = []
    group: str | None = None
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            group = _comment_group(line) or group
            continue
        entries.append(
            DatasetListEntry(
                dataset=line,
                kind=kind,
                group=group,
                line=line_number,
            )
        )
    return entries


def _das_env(x509_proxy: str | None) -> dict[str, str] | None:
    if x509_proxy is None:
        return None
    env = dict(os.environ)
    env["X509_USER_PROXY"] = x509_proxy
    return env


def _run_das_json(
    runner: Callable[..., CommandResult],
    query: str,
    *,
    timeout: float,
    x509_proxy: str | None,
) -> dict[str, Any]:
    result = runner(
        query=query,
        format="json",
        timeout=timeout,
        x509_proxy=x509_proxy,
    )
    payload: Any = []
    parse_error: str | None = None
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
    status = "resolved" if result.ok and parse_error is None else "error"
    return {
        "status": status,
        "query": query,
        "payload": payload,
        "command": result.command,
        "exit_code": result.exit_code,
        "stderr": result.stderr,
        "timed_out": result.timed_out,
        "parse_error": parse_error,
    }


def _run_das_text(
    runner: Callable[..., CommandResult],
    query: str,
    *,
    timeout: float,
    x509_proxy: str | None,
) -> dict[str, Any]:
    result = runner(
        query=query,
        format=None,
        timeout=timeout,
        x509_proxy=x509_proxy,
    )
    files = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]
    return {
        "status": "resolved" if result.ok else "error",
        "query": query,
        "files": files,
        "command": result.command,
        "exit_code": result.exit_code,
        "stderr": result.stderr,
        "timed_out": result.timed_out,
    }


def _record_for(
    entry: DatasetListEntry,
    *,
    era: str,
    version: str,
    parent: str | None,
    result: Mapping[str, Any],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "dataset": entry.dataset,
        "parent": parent,
        "era": era,
        "tier": _dataset_tier(entry.dataset),
        "version": version,
        "kind": entry.kind,
        "group": entry.group,
        "source_line": entry.line,
        "status": result["status"],
        "das": result["payload"],
        "query": result["query"],
        "command": result["command"],
        "exit_code": result["exit_code"],
        "stderr": result["stderr"],
        "timed_out": result["timed_out"],
    }
    if result["parse_error"]:
        record["parse_error"] = result["parse_error"]
    if extra:
        record.update(extra)
    return record


def _file_record_for(
    entry: DatasetListEntry,
    *,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    record = {
        "dataset": entry.dataset,
        "files": result["files"],
    }
    if result["status"] != "resolved":
        record["status"] = result["status"]
        record["query"] = result["query"]
        record["command"] = result["command"]
        record["exit_code"] = result["exit_code"]
        record["stderr"] = result["stderr"]
        record["timed_out"] = result["timed_out"]
    return record


def _document(
    *,
    era: str,
    version: str,
    list_dir: Path,
    records_key: str,
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "version": "1.0",
        "source": "cms.dasgoclient",
        "era": era,
        "dataset_version": version,
        "inputs": {
            "data": str(list_dir / "DATA.txt"),
            "mc": str(list_dir / "MC.txt"),
        },
        records_key: list(records),
    }


def _cross_sections_document(
    *,
    era: str,
    version: str,
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "version": "1.0",
        "source": "xsdb",
        "status": "placeholder",
        "note": "Cross-section enrichment is intentionally deferred.",
        "era": era,
        "dataset_version": version,
        "cross_sections": [
            {
                "dataset": record["dataset"],
                "kind": record["kind"],
                "group": record.get("group"),
                "xs_pb": None,
                "status": (
                    "missing" if record["kind"] == "mc" else "not_applicable"
                ),
            }
            for record in records
        ],
    }


def _combined_document(
    *,
    era: str,
    version: str,
    datasets: Sequence[Mapping[str, Any]],
    files: Sequence[Mapping[str, Any]],
    cross_sections: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    files_by_dataset = {record["dataset"]: record for record in files}
    xs_by_dataset = {record["dataset"]: record for record in cross_sections}
    samples = []
    for index, record in enumerate(datasets):
        file_record = files_by_dataset.get(record["dataset"], {})
        xs_record = xs_by_dataset.get(record["dataset"], {})
        samples.append(
            {
                "dataset": record["dataset"],
                "parent": record.get("parent"),
                "era": era,
                "tier": record.get("tier"),
                "version": version,
                "kind": record["kind"],
                "group": record.get("group"),
                "status": {
                    "dataset": record.get("status"),
                    "files": file_record.get(
                        "status",
                        "resolved" if file_record else "missing",
                    ),
                    "cross_section": xs_record.get("status", "missing"),
                },
                "file_count": len(file_record.get("files", [])),
                "uri_policy": {
                    "global_xrootd": "root://cms-xrd-global.cern.ch//{path}",
                },
                "files": [
                    {
                        "path": path,
                        "uris": {
                            "global_xrootd": (
                                "root://cms-xrd-global.cern.ch//" + path
                            ),
                        },
                    }
                    for path in file_record.get("files", [])
                ],
                "refs": {
                    "dataset": f"datasets.json#/datasets/{index}",
                    "files": f"files.json#/files/{index}",
                    "cross_section": (
                        f"cross_sections.json#/cross_sections/{index}"
                    ),
                },
            }
        )
    return {
        "version": "1.0",
        "era": era,
        "dataset_version": version,
        "status": "partial",
        "note": "FAST-HEP-facing merge shape; xsdb enrichment is deferred.",
        "samples": samples,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _dataset_tier(dataset: str) -> str | None:
    parts = dataset.strip("/").split("/")
    return parts[2] if len(parts) >= 3 else None


def _comment_group(line: str) -> str | None:
    group = line.strip("#").strip()
    return group or None


def _names(payload: Any) -> list[str]:
    return list(dict.fromkeys(_named_values(payload)))


def _first_name(payload: Any) -> str | None:
    return next(iter(_named_values(payload)), None)


def _named_values(payload: Any) -> Iterable[str]:
    if isinstance(payload, Mapping):
        name = payload.get("name")
        if isinstance(name, str):
            yield name
        for value in payload.values():
            yield from _named_values(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _named_values(item)
