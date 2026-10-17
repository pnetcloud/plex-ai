"""Resolve, render, check and apply Plex project subagent settings. Requires Python 3.11+."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import tomllib


ROOT = Path(__file__).resolve().parents[3]
HOSTS = ("codex", "claude", "antigravity")
PROFILE_TIERS = ("basic", "plus", "pro", "pro-plus")
EFFORTS = {"minimal", "low", "medium", "high", "xhigh", "max", "ultra"}
CLAUDE_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
ANTIGRAVITY_MODELS = ("inherit", "flash_lite", "flash", "pro")
SUBCOMMANDS = {"resolve", "list", "render", "check", "apply"}
SKILL_PREFIX_RE = re.compile(
    r"^(Before substantive work, resolve and read these real installed skills "
    r"using the host active skill inventory:\s*)([^.\n]+)(\.)",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def table(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label}: expected a table")
    return value


def keys(value, allowed, label):
    unknown = value.keys() - allowed
    if unknown:
        raise ValueError(f"{label}: unknown fields {sorted(unknown)}")


def named_file(directory, name):
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(f"Invalid {directory} name: {name!r}")
    if directory == "model-profiles":
        profiles = load_model_profiles()
        if name not in profiles:
            raise ValueError(f"Unknown model-profiles {name!r}; available: {sorted(load_model_profiles())}")
        return profiles[name]
    path = ROOT / directory / f"{name}.toml"
    if path.is_symlink() or not path.is_file():
        choices = sorted(p.stem for p in (ROOT / directory).glob("*.toml"))
        raise ValueError(f"Unknown {directory} {name!r}; available: {choices}")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load_model_profiles():
    profiles = {}
    for path in sorted((ROOT / "model-profiles").glob("*.toml")):
        if path.is_symlink():
            continue
        document = tomllib.loads(path.read_text(encoding="utf-8"))
        if path.stem == "inherit":
            profiles["inherit"] = document
            continue
        keys(document, {"host", "profiles"}, str(path))
        host = document.get("host")
        if host not in HOSTS:
            raise ValueError(f"{path.name}: host must be one of {HOSTS}")
        for tier, config in table(document.get("profiles", {}), f"{path.name}.profiles").items():
            name = f"{path.stem}-{tier}"
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
                raise ValueError(f"Invalid model profile ID: {name!r}")
            profiles[name] = {host: table(config, name)}
    return profiles


def profile_sort_key(name):
    if name == "inherit":
        return (0, "", 0)
    vendor, _, tier = name.partition("-")
    order = PROFILE_TIERS.index(tier) if tier in PROFILE_TIERS else len(PROFILE_TIERS)
    return (1, vendor, order)


def settings(value, host, label):
    value = table(value, label)
    keys(value, {"model", "reasoning"}, label)
    if "model" in value:
        model = value["model"]
        if not isinstance(model, str) or not model.strip() or any(c.isspace() for c in model):
            raise ValueError(f"{label}: model must be a nonblank identifier")
        if host == "codex" and model == "inherit":
            raise ValueError(f"{label}: omit model for Codex inheritance")
        if host == "antigravity" and model not in ANTIGRAVITY_MODELS:
            raise ValueError(f"{label}: Antigravity model must be one of {ANTIGRAVITY_MODELS}")
    if "reasoning" in value and (
        not isinstance(value["reasoning"], str)
        or value["reasoning"] not in (EFFORTS if host == "codex" else CLAUDE_EFFORTS)
    ):
        raise ValueError(f"{label}: invalid reasoning level")
    return value


def host_settings(value, host, roles, label):
    value = table(value, label)
    defaults = settings({k: v for k, v in value.items() if k in {"model", "reasoning"}}, host, label)
    per_role = {}
    for role, fields in value.items():
        if role in {"model", "reasoning"}:
            continue
        if role not in roles:
            raise ValueError(f"{label}: unknown role {role!r}")
        per_role[role] = settings(fields, host, f"{label}.{role}")
    return defaults, per_role


def discover_known_roles():
    assets = ROOT / "skills/plex-setup/assets"
    codex_roles = {p.stem for p in (assets / "codex").glob("*.toml") if not p.is_symlink()}
    claude_roles = {p.stem for p in (assets / "claude").glob("*.md") if not p.is_symlink()}
    antigravity_roles = {p.stem for p in (assets / "antigravity").glob("*.md") if not p.is_symlink()}
    return codex_roles & claude_roles & antigravity_roles


def select_asset_path(process: str, host: str, role: str) -> Path:
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host!r}")
    assets = ROOT / "skills/plex-setup/assets"
    extension = "toml" if host == "codex" else "md"
    candidates = [assets / host / f"{role}.{extension}"]
    if process == "bmad":
        candidates.insert(0, assets / "bmad" / host / f"{role}.{extension}")
    for candidate in candidates:
        if candidate.is_file() and not candidate.is_symlink():
            return candidate
    raise ValueError(f"No {host} asset for {process}/{role}")


def resolve(config):
    config = table(config, "project")
    keys(config, {"team", "model_profile", "process", "roles", "skills", "max_agents", *HOSTS}, "project")
    team_name = config.get("team")
    if team_name is not None:
        if {"process", "roles", "skills"} & config.keys():
            raise ValueError("Choose team OR legacy process/roles/skills, not both")
        team = named_file("presets", team_name)
        keys(team, {"process", "roles", "skills", "max_agents"}, "team")
    else:
        team = {k: config[k] for k in ("process", "roles", "skills", "max_agents") if k in config}
    process = team.get("process", "plain")
    if process not in ("plain", "bmad"):
        raise ValueError("Unknown process")
    roles = team.get("roles")
    if not isinstance(roles, list) or not roles or any(not isinstance(r, str) for r in roles):
        raise ValueError("roles must be a nonempty list of role names")
    if len(roles) != len(set(roles)):
        raise ValueError("Duplicate roles")
    max_agents = config.get("max_agents", team.get("max_agents", 4))
    if type(max_agents) is not int or max_agents < 1:
        raise ValueError("max_agents must be a positive integer")
    known_roles = discover_known_roles()
    if set(roles) - known_roles:
        raise ValueError(f"Unknown roles: {sorted(set(roles) - known_roles)}")
    for host in HOSTS:
        for role in roles:
            select_asset_path(process, host, role)
    bindings = table(team.get("skills", {}), "skills")
    keys(bindings, set(roles), "skills")
    for role, names in bindings.items():
        if (not isinstance(names, list) or not names
                or any(not isinstance(n, str) or not n.strip() for n in names)
                or len(names) != len(set(names))):
            raise ValueError(f"skills.{role}: expected unique nonblank skill names")
    if process == "bmad":
        required = named_file("presets", "bmad")["skills"]
        for role in roles:
            if role not in required or not set(required[role]) <= set(bindings.get(role, [])):
                raise ValueError(f"Missing mandatory BMad bindings for {role}")
    profile_name = config.get("model_profile", "inherit")
    profile = named_file("model-profiles", profile_name)
    keys(profile, set(HOSTS), "model profile")
    hosts = {}
    inactive = {}
    for host in HOSTS:
        inherited = {} if host == "codex" else {"model": "inherit"}
        base, base_roles = host_settings(profile.get(host, inherited), host, known_roles, f"profile.{host}")
        local, local_roles = host_settings(config.get(host, {}), host, known_roles, host)
        hosts[host] = {
            role: {**base, **base_roles.get(role, {}), **local, **local_roles.get(role, {})}
            for role in roles
        }
        inactive[host] = sorted(local_roles.keys() - set(roles))
    return {
        "team": team_name, "model_profile": profile_name,
        "process": process, "roles": list(roles),
        "skills": {role: list(names) for role, names in bindings.items()},
        "max_agents": max_agents, "hosts": hosts, "inactive_overrides": inactive,
    }


def _inject_skill_bindings(instructions: str, role_skills: list[str]) -> str:
    if not role_skills:
        return instructions
    match = SKILL_PREFIX_RE.match(instructions)
    if match:
        existing = [item.strip() for item in match.group(2).split(",") if item.strip()]
        merged = list(existing)
        for skill in role_skills:
            if skill not in merged:
                merged.append(skill)
        return f"{match.group(1)}{', '.join(merged)}{match.group(3)}{instructions[match.end():]}"
    skill_list = ", ".join(role_skills)
    prefix = (
        "Before substantive work, resolve and read these real installed skills "
        f"using the host active skill inventory: {skill_list}. If missing or "
        "ambiguous, report the blocker; do not invent a replacement.\n\n"
    )
    return prefix + instructions


def render_role(resolved: dict, host: str, role: str) -> str:
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host!r}")
    if role not in resolved["roles"]:
        raise ValueError(f"Role {role!r} is not active in resolved configuration")
    asset_path = select_asset_path(resolved["process"], host, role)
    raw = asset_path.read_text(encoding="utf-8")
    role_skills = resolved.get("skills", {}).get(role, [])
    role_settings = resolved["hosts"][host][role]

    if host == "codex":
        parsed = tomllib.loads(raw)
        instructions = _inject_skill_bindings(parsed["developer_instructions"], role_skills)
        lines = [
            f'name = {json.dumps(parsed["name"])}',
            f'description = {json.dumps(parsed["description"])}',
        ]
        if "model" in role_settings:
            lines.append(f'model = {json.dumps(role_settings["model"])}')
        if "reasoning" in role_settings:
            lines.append(f'model_reasoning_effort = {json.dumps(role_settings["reasoning"])}')
        if "sandbox_mode" in parsed:
            lines.append(f'sandbox_mode = {json.dumps(parsed["sandbox_mode"])}')
        lines.append(f"developer_instructions = {json.dumps(instructions)}")
        rendered = "\n".join(lines) + "\n"
        tomllib.loads(rendered)
        return rendered

    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Malformed {host} role asset: {asset_path}")
    frontmatter_lines = parts[1].strip("\n").splitlines()
    body = parts[2].lstrip("\n")
    body = _inject_skill_bindings(body, role_skills)
    model_value = role_settings.get("model", "inherit")
    updated_frontmatter = []
    replaced_model = False
    for line in frontmatter_lines:
        if line.startswith("model:"):
            updated_frontmatter.append(f"model: {json.dumps(model_value)}")
            replaced_model = True
        else:
            updated_frontmatter.append(line)
    if not replaced_model:
        updated_frontmatter.append(f"model: {json.dumps(model_value)}")
    if "reasoning" in role_settings:
        updated_frontmatter.append(f"effort: {role_settings['reasoning']}")
    return "---\n" + "\n".join(updated_frontmatter) + "\n---\n\n" + body.rstrip("\n") + "\n"


def host_dotdir(host: str) -> str:
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host!r}")
    return ".agents" if host == "antigravity" else f".{host}"


def host_agents_relpath(host: str) -> str:
    return f"{host_dotdir(host)}/agents"


def host_role_relpath(host: str, role: str) -> str:
    extension = "toml" if host == "codex" else "md"
    return f"{host_agents_relpath(host)}/plex-{role}.{extension}"


def render_host_roles(resolved: dict, host: str) -> dict[str, dict]:
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host!r}")
    rendered = {}
    for role in resolved["roles"]:
        content = render_role(resolved, host, role)
        content_bytes = content.encode("utf-8")
        relpath = host_role_relpath(host, role)
        rendered[role] = {
            "role": role,
            "name": f"plex-{role}",
            "relpath": relpath,
            "content": content,
            "sha256": sha256_bytes(content_bytes),
        }
    return rendered


def list_catalog() -> dict:
    teams = {}
    for path in sorted((ROOT / "presets").glob("*.toml")):
        if not path.is_symlink():
            teams[path.stem] = tomllib.loads(path.read_text(encoding="utf-8"))
    return {"teams": teams, "model_profiles": load_model_profiles()}


def _ensure_safe_project_path(project_root: Path, relpath: str) -> Path:
    if project_root.is_symlink():
        raise ValueError(f"Project root must not be a symlink: {project_root}")
    root = project_root.resolve()
    target = root / relpath
    current = root
    for part in Path(relpath).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Refusing symlinked path inside project: {current}")
    if not target.resolve(strict=False).is_relative_to(root):
        raise ValueError(f"Path escapes project root: {relpath}")
    return target


def _validate_receipt_structure(data: dict) -> dict:
    data = table(data, "applied.json")
    keys(data, {"hosts"}, "applied.json")
    hosts_table = table(data.get("hosts", {}), "applied.json.hosts")
    keys(hosts_table, set(HOSTS), "applied.json.hosts")
    for host, record in hosts_table.items():
        record = table(record, f"applied.json.hosts.{host}")
        keys(
            record,
            {
                "host", "team", "model_profile", "process", "roles",
                "skills", "max_agents", "role_settings", "files", "source_sha256",
            },
            f"applied.json.hosts.{host}",
        )
        if record.get("host") != host:
            raise ValueError(f"applied.json.hosts.{host}: mismatched host field")
        files = table(record.get("files", {}), f"applied.json.hosts.{host}.files")
        for role, file_info in files.items():
            file_info = table(file_info, f"applied.json.hosts.{host}.files.{role}")
            keys(file_info, {"relpath", "sha256"}, f"applied.json.hosts.{host}.files.{role}")
            expected_rel = host_role_relpath(host, role)
            if file_info.get("relpath") != expected_rel:
                raise ValueError(
                    f"applied.json.hosts.{host}.files.{role}: invalid relpath {file_info.get('relpath')!r}"
                )
            digest = file_info.get("sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"applied.json.hosts.{host}.files.{role}: invalid sha256")
    return data


def _inspect_host_state(
    project_root: Path,
    host: str,
    resolved: dict | None,
    source_sha256: str | None,
    receipt_record: dict | None,
) -> dict:
    extension = "toml" if host == "codex" else "md"
    agents_rel = host_agents_relpath(host)
    conflicts = []
    try:
        _ensure_safe_project_path(project_root, host_dotdir(host))
        agents_dir = _ensure_safe_project_path(project_root, agents_rel)
    except ValueError as err:
        return {
            "host": host,
            "status": "conflict",
            "conflicts": [str(err)],
            "installed_roles": [],
            "missing_roles": [],
            "outdated_roles": [],
            "retire_roles": [],
        }

    receipt_files = receipt_record.get("files", {}) if receipt_record else {}
    existing_plex_files = {}
    if agents_dir.is_dir():
        for entry in sorted(agents_dir.glob(f"plex-*.{extension}")):
            role = entry.stem.removeprefix("plex-")
            if entry.is_symlink():
                conflicts.append(f"Symlinked role file refused: {agents_rel}/{entry.name}")
                continue
            if entry.is_file():
                existing_plex_files[role] = sha256_bytes(entry.read_bytes())

    for role, info in receipt_files.items():
        if role not in existing_plex_files:
            conflicts.append(
                f"Previously managed role file is missing: {info['relpath']}"
            )
        elif existing_plex_files[role] != info["sha256"]:
            conflicts.append(
                f"Previously managed role file was modified outside Plex: {info['relpath']}"
            )

    for role in existing_plex_files:
        if role not in receipt_files:
            conflicts.append(
                f"Unmanaged file collision: {host_role_relpath(host, role)} is not owned by .plex/applied.json"
            )

    if resolved is None:
        status = "conflict" if conflicts else ("installed" if receipt_files else "unconfigured")
        return {
            "host": host,
            "status": status,
            "conflicts": conflicts,
            "installed_roles": sorted(existing_plex_files.keys()),
            "missing_roles": [],
            "outdated_roles": [],
            "retire_roles": [],
        }

    rendered = render_host_roles(resolved, host)
    desired_roles = resolved["roles"]
    missing_roles = []
    outdated_roles = []
    installed_roles = []
    for role in desired_roles:
        target_hash = rendered[role]["sha256"]
        actual_hash = existing_plex_files.get(role)
        if actual_hash is None:
            missing_roles.append(role)
        elif actual_hash != target_hash:
            outdated_roles.append(role)
        else:
            installed_roles.append(role)

    retire_roles = sorted(set(receipt_files.keys()) - set(desired_roles))
    receipt_matches_desired = (
        receipt_record is not None
        and receipt_record.get("team") == resolved["team"]
        and receipt_record.get("model_profile") == resolved["model_profile"]
        and receipt_record.get("process") == resolved["process"]
        and receipt_record.get("roles") == resolved["roles"]
        and receipt_record.get("skills") == resolved["skills"]
        and receipt_record.get("max_agents") == resolved["max_agents"]
        and receipt_record.get("role_settings") == resolved["hosts"][host]
        and receipt_record.get("source_sha256") == source_sha256
    )

    if conflicts:
        status = "conflict"
    elif not receipt_record and not existing_plex_files:
        status = "needs_setup"
    elif missing_roles or outdated_roles or retire_roles or not receipt_matches_desired:
        status = "needs_refresh"
    else:
        status = "in_sync"

    return {
        "host": host,
        "status": status,
        "conflicts": conflicts,
        "installed_roles": installed_roles,
        "missing_roles": missing_roles,
        "outdated_roles": outdated_roles,
        "retire_roles": retire_roles,
        "effective_roles": resolved["hosts"][host],
    }


def check_project(project_root: Path, host: str | None = None) -> dict:
    project_root = Path(project_root)
    conflicts = []
    try:
        _ensure_safe_project_path(project_root, ".plex")
        preset_path = _ensure_safe_project_path(project_root, ".plex/preset.toml")
        resolved_path = _ensure_safe_project_path(project_root, ".plex/resolved.json")
        applied_path = _ensure_safe_project_path(project_root, ".plex/applied.json")
    except ValueError as err:
        return {"status": "conflict", "conflicts": [str(err)], "hosts": {}}

    resolved = None
    source_sha256 = None
    if preset_path.is_file():
        try:
            source_bytes = preset_path.read_bytes()
            source_sha256 = sha256_bytes(source_bytes)
            resolved = resolve(tomllib.loads(source_bytes.decode("utf-8")))
        except (OSError, UnicodeError, ValueError) as err:
            conflicts.append(f"Invalid .plex/preset.toml: {err}")

    snapshot_in_sync = False
    if resolved is not None:
        expected_snapshot = {**resolved, "source_sha256": source_sha256}
        if resolved_path.is_file():
            try:
                saved_snapshot = json.loads(resolved_path.read_text(encoding="utf-8"))
                if saved_snapshot == expected_snapshot:
                    snapshot_in_sync = True
                else:
                    conflicts_or_stale = "outdated"
            except (OSError, UnicodeError, ValueError) as err:
                conflicts.append(f"Invalid .plex/resolved.json: {err}")

    receipt = {"hosts": {}}
    if applied_path.is_file():
        try:
            receipt = _validate_receipt_structure(
                json.loads(applied_path.read_text(encoding="utf-8"))
            )
        except (OSError, UnicodeError, ValueError) as err:
            conflicts.append(f"Invalid .plex/applied.json: {err}")

    target_hosts = (host,) if host else HOSTS
    host_reports = {}
    for h in HOSTS:
        host_reports[h] = _inspect_host_state(
            project_root, h, resolved, source_sha256, receipt["hosts"].get(h)
        )

    all_conflicts = list(conflicts)
    for h in target_hosts:
        all_conflicts.extend(host_reports[h]["conflicts"])

    if all_conflicts:
        overall = "conflict"
    elif resolved is None:
        overall = "needs_setup"
    elif not snapshot_in_sync or any(host_reports[h]["status"] != "in_sync" for h in target_hosts):
        overall = "needs_refresh"
    else:
        overall = "in_sync"

    other_hosts_needing_refresh = [
        h for h in HOSTS
        if h not in target_hosts
        and receipt["hosts"].get(h) is not None
        and host_reports[h]["status"] != "in_sync"
    ]

    return {
        "status": overall,
        "preset_exists": preset_path.is_file(),
        "snapshot_in_sync": snapshot_in_sync,
        "resolved": ({**resolved, "source_sha256": source_sha256} if resolved else None),
        "conflicts": all_conflicts,
        "hosts": host_reports,
        "other_hosts_needing_refresh": other_hosts_needing_refresh,
    }


def _format_toml_section(table_data: dict) -> list[str]:
    lines = []
    for k, v in table_data.items():
        if not isinstance(v, dict):
            lines.append(f"{k} = {json.dumps(v)}")
    return lines


def build_preset_toml(
    existing_config: dict | None,
    team: str | None = None,
    model_profile: str | None = None,
    max_agents: int | None = None,
    reset_overrides: bool = False,
    host_overrides: dict | None = None,
) -> str:
    config = dict(existing_config) if existing_config else {}
    if reset_overrides:
        for key in ("max_agents", *HOSTS):
            config.pop(key, None)

    if team is not None:
        for legacy_key in ("process", "roles", "skills"):
            config.pop(legacy_key, None)
        config["team"] = team
    elif "team" not in config and not ({"process", "roles", "skills"} & config.keys()):
        config["team"] = "default"

    if model_profile is not None:
        config["model_profile"] = model_profile
    elif "model_profile" not in config:
        config["model_profile"] = "inherit"

    if max_agents is not None:
        config["max_agents"] = max_agents

    if host_overrides is not None:
        keys(table(host_overrides, "host overrides"), set(HOSTS), "host overrides")
        config.update(host_overrides)
    resolve(config)

    lines = []
    if "team" in config:
        lines.append(f'team = {json.dumps(config["team"])}')
    if "model_profile" in config:
        lines.append(f'model_profile = {json.dumps(config["model_profile"])}')
    if "process" in config:
        lines.append(f'process = {json.dumps(config["process"])}')
    if "roles" in config:
        lines.append(f'roles = {json.dumps(config["roles"])}')
    if "max_agents" in config:
        lines.append(f'max_agents = {json.dumps(config["max_agents"])}')

    if "skills" in config and isinstance(config["skills"], dict) and config["skills"]:
        lines.append("")
        lines.append("[skills]")
        for role, skill_list in config["skills"].items():
            lines.append(f"{role} = {json.dumps(skill_list)}")

    for host in HOSTS:
        host_table = config.get(host)
        if not isinstance(host_table, dict) or not host_table:
            continue
        scalar_lines = _format_toml_section(host_table)
        if scalar_lines:
            lines.append("")
            lines.append(f"[{host}]")
            lines.extend(scalar_lines)
        for role, role_table in host_table.items():
            if isinstance(role_table, dict) and role_table:
                lines.append("")
                lines.append(f"[{host}.{role}]")
                lines.extend(_format_toml_section(role_table))

    return "\n".join(lines) + "\n"


def _atomic_write_bytes(target: Path, data: bytes) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.is_symlink():
        raise ValueError(f"Refusing to write symlink target: {target}")
    descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.tmp-", dir=target.parent)
    temp_path = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        temp_path.replace(target)
    finally:
        temp_path.unlink(missing_ok=True)
    read_back = target.read_bytes()
    digest = sha256_bytes(read_back)
    if digest != sha256_bytes(data):
        raise ValueError(f"Atomic write verification failed for {target}")
    return digest


def _create_backup_dir(project_root: Path, host: str) -> Path:
    backups_root = _ensure_safe_project_path(project_root, ".plex/backups")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    index = 0
    while True:
        suffix = f"{timestamp}" if index == 0 else f"{timestamp}-{index}"
        candidate = backups_root / suffix / host
        if not candidate.exists() and not candidate.is_symlink():
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        index += 1


class _ApplyTransaction:
    """Roll back this run's changes without overwriting concurrent user edits."""

    def __init__(self, root, paths):
        self.root = root
        self.original = {path: self.read(path) for path in paths}
        self.expected = dict(self.original)
        self.changed = []

    def read(self, path):
        _ensure_safe_project_path(self.root, str(path.relative_to(self.root.resolve())))
        return path.read_bytes() if path.exists() else None

    def check(self):
        for path, expected in self.expected.items():
            if self.read(path) != expected:
                raise ValueError(f"Concurrent modification detected on {path.relative_to(self.root.resolve())}")

    def write(self, path, data):
        self.check()
        self.changed.append((path, data))
        result = _atomic_write_bytes(path, data)
        self.expected[path] = data
        return result

    def archive(self, path, backup):
        self.check()
        self.changed.append((path, None))
        shutil.move(str(path), str(backup))
        self.expected[path] = None

    def rollback(self):
        failures = []
        for path, written in reversed(self.changed):
            try:
                current = self.read(path)
                before = self.original[path]
                if current == before:
                    continue
                if current != written:
                    raise ValueError("concurrent edit preserved")
                if before is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_write_bytes(path, before)
            except (OSError, ValueError) as error:
                failures.append(f"{path}: {error}")
        return failures


def apply_project(project_root, host, team=None, model_profile=None, max_agents=None, reset_overrides=False,
                  host_overrides=None):
    project_root = Path(project_root)
    lock = _ensure_safe_project_path(project_root, ".plex/.apply.lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock.open("x", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
    except FileExistsError:
        raise ValueError("Another apply holds .plex/.apply.lock; inspect the owning process before recovery") from None
    try:
        return _apply_project(project_root, host, team, model_profile, max_agents, reset_overrides, host_overrides)
    finally:
        lock.unlink()


def _apply_project(
    project_root: Path,
    host: str,
    team: str | None = None,
    model_profile: str | None = None,
    max_agents: int | None = None,
    reset_overrides: bool = False,
    host_overrides: dict | None = None,
) -> dict:
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host!r}")
    project_root = Path(project_root)
    _ensure_safe_project_path(project_root, ".plex")
    preset_path = _ensure_safe_project_path(project_root, ".plex/preset.toml")
    resolved_path = _ensure_safe_project_path(project_root, ".plex/resolved.json")
    applied_path = _ensure_safe_project_path(project_root, ".plex/applied.json")
    _ensure_safe_project_path(project_root, host_dotdir(host))
    _ensure_safe_project_path(project_root, host_agents_relpath(host))

    existing_preset_bytes = preset_path.read_bytes() if preset_path.is_file() else None
    existing_resolved_bytes = resolved_path.read_bytes() if resolved_path.is_file() else None
    existing_applied_bytes = applied_path.read_bytes() if applied_path.is_file() else None
    existing_config = (
        tomllib.loads(existing_preset_bytes.decode("utf-8"))
        if existing_preset_bytes is not None
        else None
    )

    if (
        existing_preset_bytes is not None
        and team is None
        and model_profile is None
        and max_agents is None
        and not reset_overrides
        and host_overrides is None
    ):
        candidate_preset_bytes = existing_preset_bytes
    else:
        candidate_text = build_preset_toml(
            existing_config,
            team=team,
            model_profile=model_profile,
            max_agents=max_agents,
            reset_overrides=reset_overrides,
            host_overrides=host_overrides,
        )
        candidate_preset_bytes = candidate_text.encode("utf-8")

    candidate_config = tomllib.loads(candidate_preset_bytes.decode("utf-8"))
    resolved = resolve(candidate_config)
    source_sha256 = sha256_bytes(candidate_preset_bytes)
    resolved_snapshot = {**resolved, "source_sha256": source_sha256}
    candidate_resolved_bytes = (json.dumps(resolved_snapshot, indent=2, sort_keys=True) + "\n").encode("utf-8")

    receipt = {"hosts": {}}
    if existing_applied_bytes is not None:
        receipt = _validate_receipt_structure(
            json.loads(existing_applied_bytes.decode("utf-8"))
        )

    host_state = _inspect_host_state(
        project_root, host, resolved, source_sha256, receipt["hosts"].get(host)
    )
    if host_state["conflicts"]:
        raise ValueError("; ".join(host_state["conflicts"]))

    rendered_roles = render_host_roles(resolved, host)
    old_host_record = receipt["hosts"].get(host, {})
    old_files = old_host_record.get("files", {})
    retire_roles = sorted(set(old_files.keys()) - set(resolved["roles"]))

    paths = {preset_path, resolved_path, applied_path}
    for role in set(old_files) | set(rendered_roles):
        paths.add(_ensure_safe_project_path(project_root, host_role_relpath(host, role)))
    transaction = _ApplyTransaction(project_root, paths)
    for path, original in ((preset_path, existing_preset_bytes),
                           (resolved_path, existing_resolved_bytes),
                           (applied_path, existing_applied_bytes)):
        if transaction.original[path] != original:
            raise ValueError(f"Concurrent modification detected on {path.name}")
    for role, item in rendered_roles.items():
        path = _ensure_safe_project_path(project_root, item["relpath"])
        if role not in old_files and transaction.original[path] is not None:
            raise ValueError(f"Unmanaged file collision: {item['relpath']}")

    try:
        backup_dir = None

        def ensure_backup() -> Path:
            nonlocal backup_dir
            if backup_dir is None:
                backup_dir = _create_backup_dir(project_root, host)
            return backup_dir

        if existing_preset_bytes is not None and existing_preset_bytes != candidate_preset_bytes:
            if preset_path.read_bytes() != existing_preset_bytes:
                raise ValueError("Concurrent modification detected on .plex/preset.toml")
            bdir = ensure_backup()
            (bdir / "preset.toml").write_bytes(existing_preset_bytes)

        if existing_resolved_bytes is not None and existing_resolved_bytes != candidate_resolved_bytes:
            if resolved_path.read_bytes() != existing_resolved_bytes:
                raise ValueError("Concurrent modification detected on .plex/resolved.json")
            bdir = ensure_backup()
            (bdir / "resolved.json").write_bytes(existing_resolved_bytes)

        archived_roles = []
        for role in retire_roles:
            relpath = old_files[role]["relpath"]
            role_path = _ensure_safe_project_path(project_root, relpath)
            current_bytes = role_path.read_bytes()
            if sha256_bytes(current_bytes) != old_files[role]["sha256"]:
                raise ValueError(f"Concurrent modification detected on retired role {relpath}")
            bdir = ensure_backup()
            backup_target = bdir / role_path.name
            transaction.archive(role_path, backup_target)
            if sha256_bytes(backup_target.read_bytes()) != old_files[role]["sha256"]:
                raise ValueError(f"Archive verification failed for {relpath}")
            archived_roles.append(role)

        new_files_record = {}
        written_roles = []
        for role in resolved["roles"]:
            item = rendered_roles[role]
            role_path = _ensure_safe_project_path(project_root, item["relpath"])
            target_bytes = item["content"].encode("utf-8")
            if role_path.is_file():
                current_bytes = role_path.read_bytes()
                current_hash = sha256_bytes(current_bytes)
                if role in old_files and current_hash != old_files[role]["sha256"]:
                    raise ValueError(f"Concurrent modification detected on {item['relpath']}")
                if current_bytes != target_bytes:
                    bdir = ensure_backup()
                    (bdir / role_path.name).write_bytes(current_bytes)
                    verified_hash = transaction.write(role_path, target_bytes)
                    written_roles.append(role)
                else:
                    verified_hash = current_hash
            else:
                verified_hash = transaction.write(role_path, target_bytes)
                written_roles.append(role)
            new_files_record[role] = {
                "relpath": item["relpath"],
                "sha256": verified_hash,
            }

        if existing_preset_bytes != candidate_preset_bytes:
            transaction.write(preset_path, candidate_preset_bytes)
        if existing_resolved_bytes != candidate_resolved_bytes:
            transaction.write(resolved_path, candidate_resolved_bytes)

        receipt["hosts"][host] = {
            "host": host,
            "team": resolved["team"],
            "model_profile": resolved["model_profile"],
            "process": resolved["process"],
            "roles": resolved["roles"],
            "skills": resolved["skills"],
            "max_agents": resolved["max_agents"],
            "role_settings": resolved["hosts"][host],
            "source_sha256": source_sha256,
            "files": new_files_record,
        }
        receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if transaction.original[applied_path] != receipt_bytes:
            transaction.write(applied_path, receipt_bytes)
        transaction.check()

        other_hosts = {}
        other_hosts_needing_refresh = []
        for candidate_host in HOSTS:
            if candidate_host == host:
                continue
            state = _inspect_host_state(
                project_root, candidate_host, resolved, source_sha256, receipt["hosts"].get(candidate_host)
            )
            configured = receipt["hosts"].get(candidate_host) is not None
            needs_refresh = configured and state["status"] != "in_sync"
            if needs_refresh:
                other_hosts_needing_refresh.append(candidate_host)
            other_hosts[candidate_host] = {
                "host": candidate_host,
                "configured": configured,
                "needs_refresh": needs_refresh,
                "status": state["status"],
            }
        primary_other = (
            other_hosts_needing_refresh[0]
            if other_hosts_needing_refresh
            else next(
                (h for h, info in other_hosts.items() if info["configured"]),
                next(iter(other_hosts)),
            )
        )

        return {
            "status": "applied",
            "host": host,
            "team": resolved["team"],
            "model_profile": resolved["model_profile"],
            "process": resolved["process"],
            "installed_roles": list(resolved["roles"]),
            "written_roles": written_roles,
            "archived_roles": archived_roles,
            "backup_dir": (
                str(backup_dir.relative_to(project_root.resolve()))
                if backup_dir is not None
                else None
            ),
            "effective_roles": resolved["hosts"][host],
            "inactive_overrides": resolved["inactive_overrides"],
            "other_host": other_hosts[primary_other],
            "other_hosts": other_hosts,
            "other_hosts_needing_refresh": other_hosts_needing_refresh,
        }
    except (OSError, ValueError) as error:
        failures = transaction.rollback()
        if failures:
            raise ValueError(f"{error}; rollback needs recovery: {'; '.join(failures)}") from error
        raise


def _resolve_file_snapshot(config_path: Path) -> dict:
    source = config_path.read_bytes()
    result = resolve(tomllib.loads(source.decode("utf-8")))
    result["source_sha256"] = sha256_bytes(source)
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in SUBCOMMANDS and not argv[0].startswith("-"):
        argv = ["resolve", *argv]

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    resolve_parser = subparsers.add_parser("resolve", help="Resolve a preset.toml without writing files")
    resolve_parser.add_argument("config", type=Path, help="Project or candidate preset.toml")

    subparsers.add_parser("list", help="List packaged teams and model profiles")

    render_parser = subparsers.add_parser("render", help="Render native role files in memory as JSON")
    render_parser.add_argument("config", type=Path, help="Project or candidate preset.toml")
    render_parser.add_argument("--host", choices=HOSTS, required=True, help="Target host")

    check_parser = subparsers.add_parser("check", help="Check project Plex status without writing files")
    check_parser.add_argument("project", type=Path, nargs="?", default=Path("."), help="Project root")
    check_parser.add_argument("--host", choices=HOSTS, default=None, help="Optional single host to check")

    apply_parser = subparsers.add_parser("apply", help="Apply or switch Plex configuration for a host")
    apply_parser.add_argument("project", type=Path, nargs="?", default=Path("."), help="Project root")
    apply_parser.add_argument("--host", choices=HOSTS, required=True, help="Target host to configure")
    apply_parser.add_argument("--team", default=None, help="Named team preset to select")
    apply_parser.add_argument("--model-profile", default=None, help="Named model profile to select")
    apply_parser.add_argument("--max-agents", type=int, default=None, help="Optional max_agents override")
    apply_parser.add_argument(
        "--reset-overrides", action="store_true", help="Clear personal overrides in .plex/preset.toml"
    )

    args = parser.parse_args(argv)
    try:
        if args.subcommand == "resolve":
            output = _resolve_file_snapshot(args.config)
        elif args.subcommand == "list":
            output = list_catalog()
        elif args.subcommand == "render":
            snapshot = _resolve_file_snapshot(args.config)
            output = {
                "host": args.host,
                "resolved": snapshot,
                "roles": render_host_roles(snapshot, args.host),
            }
        elif args.subcommand == "check":
            output = check_project(args.project, host=args.host)
        elif args.subcommand == "apply":
            output = apply_project(
                args.project,
                host=args.host,
                team=args.team,
                model_profile=args.model_profile,
                max_agents=args.max_agents,
                reset_overrides=args.reset_overrides,
            )
        else:
            raise ValueError(f"Unknown subcommand: {args.subcommand}")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Plex configuration error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
