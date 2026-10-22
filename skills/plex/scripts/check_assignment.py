#!/usr/bin/env python3
"""Validate a Plex assignment from stdin against an already checked snapshot.

Usage: python3 check_assignment.py --resolved <root>/.plex/resolved.json < assignment.json
Read-only structural validation; does not establish authority or semantic readiness.
"""

import argparse
import json
from pathlib import Path
import sys


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def string_list(value):
    return isinstance(value, list) and all(nonempty(item) for item in value)


def validate(assignment, snapshot):
    errors = []
    if not isinstance(snapshot, dict) or not string_list(snapshot.get("roles")) or not snapshot["roles"]:
        return ["snapshot.roles must be a non-empty list of role names"]
    configured_budget = snapshot.get("subagent_token_budget", 0)
    if type(configured_budget) is not int or configured_budget < 0:
        errors.append("snapshot.subagent_token_budget must be a non-negative integer")
    if not isinstance(assignment, dict):
        return ["assignment must be an object"]
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
    if mode == "goal":
        if "token_budget" in execution:
            budget = execution["token_budget"]
            if type(budget) is not int or budget < 0:
                errors.append("goal token_budget must be a non-negative integer; 0 means no Plex-set limit")
        elif type(configured_budget) is int and configured_budget > 0:
            errors.append("goal must include the configured snapshot.subagent_token_budget")
    elif "token_budget" in execution:
        errors.append("token_budget applies only to goal assignments")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolved", type=Path, required=True, help="Already checked .plex/resolved.json")
    args = parser.parse_args()
    try:
        snapshot = json.loads(args.resolved.read_text(encoding="utf-8"))
        assignment = json.load(sys.stdin)
        errors = validate(assignment, snapshot)
    except (OSError, ValueError) as error:
        errors = [f"cannot read assignment or snapshot: {error}"]
    print(json.dumps({"status": "invalid" if errors else "valid", "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
