#!/usr/bin/env python3
"""Index explicitly selected Codex JSONL files/roots without emitting message text.

Standard library only, Python 3.9+. Output is local metadata, not a semantic audit.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys

MAX_LINE_BYTES = 8 * 1024 * 1024
SAMPLE_LIMIT = 8
USAGE_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens",
                "reasoning_output_tokens", "total_tokens")


def recorded_path(value):
    """Compare recorded paths lexically, without resolving them on this host."""
    if not isinstance(value, str):
        return None
    path = PureWindowsPath(value) if PureWindowsPath(value).drive else PurePosixPath(value)
    return path if path.is_absolute() and ".." not in path.parts else None


def association(cwds, project):
    if project is None:
        return "not_requested"
    target = recorded_path(project)
    for value in cwds:
        candidate = recorded_path(value)
        if candidate is not None and type(candidate) is type(target):
            if candidate == target or target in candidate.parents:
                return "cwd_match"
    # Other cwd values are not proof of exclusion: tools can use explicit paths.
    return "needs_review"


def index_file(path, project=None):
    result = {"path": str(path), "inspection_depth": "metadata_only",
              "session_ids": [], "cwds": [], "lines": 0,
              "event_counts": {}, "sample_lines": {}, "issue_count": 0, "issues": []}
    counts = Counter()
    digest = hashlib.sha256()

    def issue(kind, line=None):
        result["issue_count"] += 1
        if len(result["issues"]) < SAMPLE_LIMIT:
            result["issues"].append({"kind": kind, "line": line})

    try:
        before = path.stat()
        with path.open("rb") as stream:
            while True:
                raw = stream.readline(MAX_LINE_BYTES + 1)
                if not raw:
                    break
                result["lines"] += 1
                line = result["lines"]
                digest.update(raw)
                if len(raw) > MAX_LINE_BYTES:
                    while not raw.endswith(b"\n"):
                        raw = stream.readline(MAX_LINE_BYTES + 1)
                        if not raw:
                            break
                        digest.update(raw)
                    issue("oversized_line", line)
                    continue
                try:
                    event = json.loads(raw.decode("utf-8-sig" if line == 1 else "utf-8"))
                except (UnicodeError, ValueError, RecursionError):
                    issue("invalid_json_or_encoding", line)
                    continue
                if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                    issue("unsupported_event_shape", line)
                    continue
                kind = event["type"]
                payload = event.get("payload")
                if not isinstance(payload, dict):
                    issue("unsupported_payload_shape", line)
                    continue
                # Fixed categories prevent transcript content leaking through type fields.
                if kind in ("session_meta", "turn_context", "compacted"):
                    category = kind
                elif kind == "event_msg":
                    subtype = payload.get("type")
                    category = "event_msg." + (subtype if subtype in (
                        "user_message", "agent_message", "token_count", "task_started",
                        "task_complete") else "other")
                elif kind == "response_item":
                    subtype = payload.get("type")
                    category = "response_item." + (subtype if subtype in (
                        "message", "function_call", "function_call_output",
                        "custom_tool_call", "custom_tool_call_output", "reasoning") else "other")
                else:
                    category = "unknown"
                    issue("unknown_event_type", line)
                counts[category] += 1
                samples = result["sample_lines"].setdefault(category, [])
                if len(samples) < SAMPLE_LIMIT:
                    samples.append(line)
                if kind in ("session_meta", "turn_context"):
                    cwd = payload.get("cwd")
                    if isinstance(cwd, str) and cwd not in result["cwds"]:
                        result["cwds"].append(cwd)
                if kind == "session_meta":
                    session_id = payload.get("id")
                    if isinstance(session_id, str) and session_id not in result["session_ids"]:
                        result["session_ids"].append(session_id)
                if category == "event_msg.token_count":
                    info = payload.get("info")
                    total = info.get("total_token_usage") if isinstance(info, dict) else None
                    if isinstance(total, dict):
                        values = {key: total[key] for key in USAGE_FIELDS
                                  if type(total.get(key)) is int and total[key] >= 0}
                        if values:
                            result["last_reported_total_usage"] = {"line": line, **values}
        after = path.stat()
        result["sha256"] = digest.hexdigest()
        result["size_bytes"] = after.st_size
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            issue("changed_during_read")
    except OSError as exc:
        issue(type(exc).__name__)
    result["event_counts"] = dict(counts)
    if not result["session_ids"]:
        issue("missing_session_identity")
    result["project_association"] = association(result["cwds"], project)
    result["parse_complete"] = result["issue_count"] == 0
    return result


def build_manifest(inputs, project=None):
    files = set()
    exclusions = []

    def consider(path):
        if path.is_symlink():
            exclusions.append({"path": str(path), "reason": "symlink_not_followed"})
        elif path.is_file() and path.suffix.lower() == ".jsonl":
            files.add(path.absolute())
        else:
            exclusions.append({"path": str(path), "reason": "unsupported_or_missing"})

    for value in inputs:
        root = Path(value).expanduser().absolute()
        if root.is_symlink() or not root.is_dir():
            consider(root)
            continue

        def walk_error(exc):
            exclusions.append({"path": str(exc.filename), "reason": type(exc).__name__})

        for folder, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
            for name in sorted(dirs):
                child = Path(folder) / name
                if child.is_symlink():
                    consider(child)
                    dirs.remove(name)
            dirs.sort()
            for name in sorted(names):
                consider(Path(folder) / name)
    sessions = [index_file(path, project) for path in sorted(files)]
    hashes = {}
    ids = {}
    for session in sessions:
        if session["parse_complete"]:
            sha = session["sha256"]
            if sha in hashes:
                session["exact_duplicate_of"] = hashes[sha]
            else:
                hashes[sha] = session["path"]
        for sid in session["session_ids"]:
            ids.setdefault(sid, []).append(session)
    for copies in ids.values():
        if len({item.get("sha256") for item in copies}) > 1:
            for item in copies:
                item["same_id_different_content"] = True
    return {"schema_version": 1, "project": project, "files_indexed": len(sessions),
            "semantic_audit_complete": False, "sessions": sessions, "excluded": exclusions}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Explicitly permitted JSONL files or roots")
    parser.add_argument("--project", help="Absolute recorded project path; cwd matches only")
    args = parser.parse_args(argv)
    if args.project is not None and recorded_path(args.project) is None:
        parser.error("--project must be an absolute path without '..'")
    manifest = build_manifest(args.paths, args.project)
    json.dump(manifest, sys.stdout, indent=2, ensure_ascii=True)
    print()
    # Incomplete data must not silently pass an automated coverage check.
    return 0 if manifest["sessions"] and not manifest["excluded"] and all(
        item["parse_complete"] for item in manifest["sessions"]) else 1


if __name__ == "__main__":
    sys.exit(main())
