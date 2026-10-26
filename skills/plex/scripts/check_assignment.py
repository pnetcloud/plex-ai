#!/usr/bin/env python3
"""Validate a Plex assignment or response against an already checked snapshot.

Usage: python3 check_assignment.py --resolved <root>/.plex/resolved.toml < assignment.md
Add --assignment <current-assignment.md> to validate a response on stdin.
Markdown is the handoff format; legacy JSON remains readable.
Read-only structural validation; does not establish authority or semantic readiness.
"""

import argparse
import json
import re
import tomllib
from pathlib import Path
import sys


def _sections(lines, level):
    """Split fixed headings, preserving headings inside fenced evidence."""
    result, current, fence = {}, None, None
    for line in lines:
        marker = re.match(r"^(`{3,}|~{3,})(.*)$", line)
        if marker:
            token, rest = marker.groups()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not rest.strip():
                fence = None
        heading = None if fence or marker else re.fullmatch(r"(#{1,6}) (.+)", line)
        if heading and len(heading[1]) == level:
            current = heading[2]
            if current in result:
                raise ValueError(f"duplicate heading: {current}")
            result[current] = []
        elif heading and len(heading[1]) < level:
            raise ValueError(f"unexpected heading: {line}")
        elif current is not None:
            result[current].append(line)
        elif line.strip():
            raise ValueError(f"expected a level-{level} heading: {line}")
    if fence:
        raise ValueError("unclosed Markdown fence")
    return result


def _bullets(lines):
    result = []
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("- ") and line[2:].strip():
            result.append(line[2:])
        elif line.startswith("  ") and result:
            result[-1] += "\n" + line[2:]
        else:
            raise ValueError(f"expected a '- ' list item or indented continuation: {line}")
    return result


def _fields(lines, allowed, lists=()):
    values, current = {}, None
    for line in lines:
        if not line.strip():
            continue
        match = re.fullmatch(r"- \*\*([a-z_]+):\*\*(?: (.*))?", line)
        if match:
            current, value = match.groups()
            if current not in allowed or current in values:
                raise ValueError(f"unknown or duplicate field: {current}")
            values[current] = [value] if value else []
        elif line.startswith("  ") and current:
            values[current].append(line[2:])
        else:
            raise ValueError(f"expected a bold field or indented continuation: {line}")
    return {key: _bullets(value) if key in lists else "\n".join(value)
            for key, value in values.items()}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_contract(text):
    """Decode the documented Markdown grammar into the existing validation schema."""
    text = text.strip()
    if not text.startswith("#"):
        return json.loads(text, object_pairs_hook=_unique_object)
    lines = text.splitlines()
    if lines[0] not in ("# Plex assignment", "# Plex response"):
        raise ValueError("expected '# Plex assignment' or '# Plex response'")
    response = lines[0] == "# Plex response"
    start = next((i for i, line in enumerate(lines[1:], 1) if line.startswith("## ")), len(lines))
    result = _fields(lines[1:start], {"assignment", "revision", "role", "status"} if response
                     else {"assignment", "revision", "role", "readiness"})
    if not {"assignment", "revision"} <= result.keys():
        raise ValueError("Markdown contracts require assignment and revision")
    if "revision" in result:
        if not re.fullmatch(r"[1-9][0-9]*", result["revision"]):
            raise ValueError("revision must be a positive integer")
        result["revision"] = int(result["revision"])
    sections = _sections(lines[start:], 2)
    strings = {"Summary": "summary", "Next": "next", "Notes": "notes"} if response else {
        "Reference": "reference", "Outcome": "outcome"}
    lists = {"Evidence": "evidence", "Artifacts": "artifacts"} if response else {
        "Inputs": "inputs", "Dependencies": "dependencies"}
    objects = {"Request": ({"kind", "question", "attempted", "recommendation"}, {"attempted"}),
               "Blocker": ({"constraint", "evidence", "resume"}, {"evidence"})} if response else {
        "Execution": ({"mode", "reason"}, set())}
    for title, body in sections.items():
        if title in strings:
            result[strings[title]] = "\n".join(body).strip()
        elif title in lists:
            result[lists[title]] = _bullets(body)
        elif title in objects:
            result[title.lower()] = _fields(body, *objects[title])
        elif not response and title in {"Writable paths", "Excluded paths"}:
            result.setdefault("scope", {})["write" if title == "Writable paths" else "exclude"] = _bullets(body)
        elif title == ("Criteria" if response else "Acceptance"):
            items = []
            for index, fields in _sections(body, 3).items():
                if not re.fullmatch(r"[1-9][0-9]*", index):
                    raise ValueError("criterion headings must be positive integer indexes")
                item = _fields(fields, {"state", "evidence"} if response else {"criterion", "check"},
                               {"evidence"} if response else set())
                if response:
                    item["index"] = int(index)
                elif int(index) != len(items) + 1:
                    raise ValueError("acceptance indexes must be consecutive from 1")
                items.append(item)
            result["criteria" if response else "acceptance"] = items
        else:
            raise ValueError(f"unknown section: {title}")
    return result


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def string_list(value):
    return isinstance(value, list) and all(nonempty(item) for item in value)


def validate(assignment, snapshot):
    errors = []
    if not isinstance(snapshot, dict) or not string_list(snapshot.get("roles")) or not snapshot["roles"]:
        return ["snapshot.roles must be a non-empty list of role names"]
    if not isinstance(assignment, dict):
        return ["assignment must be an object"]
    if "assignment" in assignment or "revision" in assignment:
        errors.extend(validate_identity(assignment))
    for field in ("outcome", "reference"):
        if not nonempty(assignment.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if assignment.get("role") not in [f"plex-{role}" for role in snapshot["roles"]]:
        errors.append("role must be an exact native plex-<role> in snapshot.roles")
    for field in ("inputs", "dependencies"):
        if not string_list(assignment.get(field)):
            errors.append(f"{field} must be a list of non-empty references (may be empty)")
    scope = assignment.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object with write and exclude lists")
    else:
        for field in ("write", "exclude"):
            if not string_list(scope.get(field)):
                errors.append(f"scope.{field} must be a list of non-empty paths (may be empty)")
    acceptance = assignment.get("acceptance")
    if not isinstance(acceptance, list) or not 1 <= len(acceptance) <= 5:
        errors.append("acceptance must contain 1 to 5 observable criteria")
    else:
        for index, item in enumerate(acceptance):
            if not isinstance(item, dict) or not all(nonempty(item.get(key)) for key in ("criterion", "check")):
                errors.append(f"acceptance[{index}] requires non-empty criterion and check")
    execution = assignment.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution must be an object with mode and reason")
        return errors
    mode = execution.get("mode")
    if mode not in ("normal", "plan", "goal"):
        errors.append("execution.mode must be normal, plan or goal")
    if not nonempty(execution.get("reason")):
        errors.append("execution.reason must explain the manager's choice")
    readiness = assignment.get("readiness")
    if readiness not in ("ready", "needs-specialist", "blocked"):
        errors.append("readiness must be ready, needs-specialist or blocked")
    elif readiness == "blocked" or (mode != "plan" and readiness != "ready"):
        errors.append("only a plan assignment may resolve needs-specialist; blocked work cannot launch")
    return errors


def validate_identity(value):
    errors = []
    if not nonempty(value.get("assignment")):
        errors.append("assignment must be a non-empty task label")
    if type(value.get("revision")) is not int or value["revision"] < 1:
        errors.append("revision must be a positive integer")
    return errors


def validate_response(response, assignment, snapshot):
    """Check response structure and identity, not evidence truth or progress history."""
    errors = validate(assignment, snapshot)
    if errors:
        return ["assignment: " + error for error in errors]
    errors = validate_identity(assignment)
    if errors:
        return ["assignment: " + error for error in errors]
    if not isinstance(response, dict):
        return ["response must be an object"]
    errors = validate_identity(response)
    for field in ("assignment", "revision", "role"):
        if response.get(field) != assignment[field]:
            errors.append(f"{field} must match the current assignment")
    if not nonempty(response.get("summary")):
        errors.append("summary must be a non-empty string")
    status = response.get("status")
    if status not in ("progress", "needs-decision", "blocked", "completed"):
        errors.append("status must be progress, needs-decision, blocked or completed")
    if status in ("progress", "needs-decision") and not nonempty(response.get("next")):
        errors.append("next must describe the next step")
    if status == "progress":
        if not string_list(response.get("evidence")) or not response["evidence"]:
            errors.append("progress requires non-empty evidence of a new result or observation")
    if status == "needs-decision":
        request = response.get("request")
        if not isinstance(request, dict):
            errors.append("needs-decision requires a request object")
        else:
            if request.get("kind") not in ("context", "scope", "technical", "permission"):
                errors.append("request.kind must be context, scope, technical or permission")
            for field in ("question", "recommendation"):
                if not nonempty(request.get(field)):
                    errors.append(f"request.{field} must be non-empty")
            if not string_list(request.get("attempted")) or not request["attempted"]:
                errors.append("request.attempted must contain observations or safe checks already made")
    if status == "blocked":
        blocker = response.get("blocker")
        if not isinstance(blocker, dict):
            errors.append("blocked requires a blocker object")
        else:
            for field in ("constraint", "resume"):
                if not nonempty(blocker.get(field)):
                    errors.append(f"blocker.{field} must be non-empty")
            if not string_list(blocker.get("evidence")) or not blocker["evidence"]:
                errors.append("blocker.evidence must be non-empty")
    if "artifacts" in response or status == "completed":
        if not string_list(response.get("artifacts")):
            errors.append("artifacts must be a list of references (may be empty)")
    if "criteria" in response or status == "completed":
        criteria = response.get("criteria")
        if not isinstance(criteria, list):
            errors.append("criteria must be a list")
        else:
            seen = set()
            for item in criteria:
                if not isinstance(item, dict):
                    errors.append("each criterion result must be an object")
                    continue
                index = item.get("index")
                if type(index) is not int or not 1 <= index <= len(assignment["acceptance"]):
                    errors.append("criterion index must identify an acceptance criterion (1-based)")
                elif index in seen:
                    errors.append("criterion indexes must be unique")
                else:
                    seen.add(index)
                state = item.get("state")
                if state not in ("passed", "failed", "pending"):
                    errors.append("criterion state must be passed, failed or pending")
                evidence = item.get("evidence")
                if not string_list(evidence) or (state != "pending" and not evidence):
                    errors.append("criterion evidence must be a list, non-empty for passed/failed")
                if status == "completed" and state != "passed":
                    errors.append("completed requires every criterion to pass")
            if status == "completed" and seen != set(range(1, len(assignment["acceptance"]) + 1)):
                errors.append("completed must cover every acceptance criterion")
    for field, allowed in (("request", "needs-decision"), ("blocker", "blocked")):
        if field in response and status != allowed:
            errors.append(f"{field} is only valid with status {allowed}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolved", type=Path, required=True, help="Already checked .plex/resolved.toml")
    parser.add_argument("--assignment", type=Path,
                        help="Validate a response from stdin against this current Markdown or legacy JSON assignment")
    args = parser.parse_args()
    try:
        path = args.resolved
        if not path.exists() and path.stem == "resolved":
            path = path.with_suffix(".toml" if path.suffix == ".json" else ".json")
        raw = path.read_text(encoding="utf-8")
        snapshot = tomllib.loads(raw) if path.suffix == ".toml" else json.loads(raw)
        value = read_contract(sys.stdin.read())
        if args.assignment:
            assignment = read_contract(args.assignment.read_text(encoding="utf-8"))
            errors = validate_response(value, assignment, snapshot)
        else:
            errors = validate(value, snapshot)
    except (OSError, ValueError) as error:
        errors = [f"cannot read assignment or snapshot: {error}"]
    print(json.dumps({"status": "invalid" if errors else "valid", "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
