#!/usr/bin/env python3
"""Read-only structural and size validation for Plex coordinator state."""

import argparse
import json
from pathlib import Path
import sys


MAX_BYTES = 8192
MAX_ITEMS = {"queued": 8, "paused": 8, "recently_completed": 4, "decisions": 8}
ROOT_KEYS = {"version", "session_id", "primary_id", "active", *MAX_ITEMS}
OUTCOME_KEYS = {"id", "goal", "reference", "owner", "authorization", "priority",
                "next_action", "blocker", "resume_condition"}
COMPLETED_KEYS = {"id", "goal", "reference", "owner", "authorization", "priority",
                  "result_reference"}
DECISION_KEYS = {"id", "decision", "authority", "reference", "active_limit"}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def _string(value, path, errors, limit=512, required=True):
    if not isinstance(value, str):
        errors.append(f"{path} must be a string")
    elif required and not value.strip():
        errors.append(f"{path} must be non-empty")
    elif len(value) > limit:
        errors.append(f"{path} exceeds {limit} Unicode characters")


def _keys(value, required, allowed, path, errors):
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return False
    missing = required - value.keys()
    extra = value.keys() - allowed
    for key in sorted(missing):
        errors.append(f"{path}.{key} is required")
    for key in sorted(extra):
        errors.append(f"{path}.{key} is not allowed")
    return not missing and not extra


def _outcome(item, path, errors, goal_limit=512, paused=False, completed=False):
    allowed = COMPLETED_KEYS if completed else OUTCOME_KEYS
    required = allowed
    if not _keys(item, required, allowed, path, errors):
        return
    _string(item["id"], f"{path}.id", errors, limit=64)
    _string(item["goal"], f"{path}.goal", errors, limit=goal_limit)
    _string(item["reference"], f"{path}.reference", errors)
    _string(item["owner"], f"{path}.owner", errors, limit=64)
    _string(item["authorization"], f"{path}.authorization", errors)
    _string(item["priority"], f"{path}.priority", errors)
    if completed:
        _string(item["result_reference"], f"{path}.result_reference", errors)
        return
    _string(item["next_action"], f"{path}.next_action", errors, limit=256)
    _string(item["blocker"], f"{path}.blocker", errors, limit=256, required=False)
    _string(item["resume_condition"], f"{path}.resume_condition", errors,
            limit=256, required=paused)


def validate(state):
    """Return structural, lifecycle and limit errors without modifying state."""
    errors = []
    if not _keys(state, ROOT_KEYS, ROOT_KEYS, "state", errors):
        return errors
    if type(state["version"]) is not int or state["version"] != 1:
        errors.append("state.version must be integer 1")
    _string(state["session_id"], "state.session_id", errors)
    primary_id = state["primary_id"]
    if primary_id is not None:
        _string(primary_id, "state.primary_id", errors, limit=64)

    entries = {}
    open_count = 0
    primary_count = 0
    if not isinstance(state["active"], list):
        errors.append("state.active must be an array")
    else:
        for index, item in enumerate(state["active"]):
            open_count += 1
            _outcome(item, f"state.active[{index}]", errors,
                     goal_limit=1024 if isinstance(item, dict) and item.get("id") == primary_id else 512)
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                entries.setdefault(item["id"], []).append(("active", index))
                primary_count += item["id"] == primary_id

    for field, limit in MAX_ITEMS.items():
        items = state[field]
        if not isinstance(items, list):
            errors.append(f"state.{field} must be an array")
            continue
        if len(items) > limit:
            errors.append(f"state.{field} exceeds the limit of {limit}")
        if field == "decisions":
            for index, item in enumerate(items):
                path = f"state.decisions[{index}]"
                if not _keys(item, DECISION_KEYS - {"active_limit"}, DECISION_KEYS, path, errors):
                    continue
                _string(item["id"], f"{path}.id", errors, limit=64)
                _string(item["decision"], f"{path}.decision", errors)
                _string(item["authority"], f"{path}.authority", errors)
                _string(item["reference"], f"{path}.reference", errors)
                if "active_limit" in item:
                    value = item["active_limit"]
                    if type(value) is not int or value < 1:
                        errors.append(f"{path}.active_limit must be a positive integer")
                    if item.get("authority") != "user":
                        errors.append(f"{path}.active_limit requires user authority")
        else:
            for index, item in enumerate(items):
                path = f"state.{field}[{index}]"
                if field == "recently_completed":
                    _outcome(item, path, errors, completed=True)
                else:
                    open_count += 1
                    _outcome(item, path, errors, paused=field == "paused",
                             goal_limit=1024 if isinstance(item, dict) and item.get("id") == primary_id else 512)
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    entries.setdefault(item["id"], []).append((field, index))
                    if field in ("queued", "paused"):
                        primary_count += item["id"] == primary_id

    for identifier, locations in entries.items():
        if len(locations) > 1:
            errors.append(f"state item id {identifier!r} appears more than once")
    if primary_id is None:
        if open_count:
            errors.append("state.primary_id is required when unfinished work exists")
    elif primary_count != 1:
        errors.append("state.primary_id must identify exactly one active, queued or paused item")

    decisions = state["decisions"] if isinstance(state["decisions"], list) else []
    overrides = [item for item in decisions if isinstance(item, dict) and "active_limit" in item]
    active_count = len(state["active"]) if isinstance(state["active"], list) else 0
    if active_count > 2 and not overrides:
        errors.append("state.active exceeds 2 without a sufficient user active_limit override")
    if overrides and type(overrides[-1].get("active_limit")) is int \
            and active_count > overrides[-1]["active_limit"]:
        errors.append("state.active exceeds its user active_limit override")
    return errors


def validate_bytes(raw):
    """Validate UTF-8 JSON bytes, including their serialized whitespace."""
    if not isinstance(raw, (bytes, bytearray)):
        return ["state input must be bytes"]
    if len(raw) > MAX_BYTES:
        return [f"state exceeds {MAX_BYTES} UTF-8 bytes"]
    try:
        value = json.loads(bytes(raw).decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
    except (UnicodeError, ValueError, RecursionError) as error:
        return [f"invalid state JSON: {error}"]
    return validate(value)


def validate_file(path):
    """Read no more than one byte past the limit before validating a file."""
    try:
        with Path(path).open("rb") as stream:
            return validate_bytes(stream.read(MAX_BYTES + 1))
    except OSError as error:
        return [f"cannot read state: {error}"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path, help="Session state JSON file to check")
    args = parser.parse_args()
    errors = validate_file(args.state)
    print(json.dumps({"status": "invalid" if errors else "valid", "errors": errors},
                     ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
