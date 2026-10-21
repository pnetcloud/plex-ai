"""Resolve, render, check and apply Plex project or user subagent settings. Requires Python 3.11+."""

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
INTERACTIONS = ("interactive", "balanced", "auto")
PROFILE_TIERS = ("basic", "plus", "pro", "pro-plus")
EFFORTS = {"minimal", "low", "medium", "high", "xhigh", "max", "ultra"}
CLAUDE_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
ANTIGRAVITY_NATIVE_MODELS = ("inherit", "flash_lite", "flash", "pro")
ANTIGRAVITY_MODELS = (
    *ANTIGRAVITY_NATIVE_MODELS,
    "claude-sonnet-5-5-low", "claude-sonnet-5-5-medium", "claude-sonnet-5-5-high",
    "claude-opus-5-5-low", "claude-opus-5-5-medium", "claude-opus-5-5-high",
    "gemini-3.8-flash-low", "gemini-3.8-flash-medium", "gemini-3.8-flash-high",
    "gemini-4-argon-low", "gemini-4-argon-medium", "gemini-4-argon-high",
)
SUBCOMMANDS = {"resolve", "list", "render", "check", "apply"}
SKILL_PREFIX_RE = re.compile(
    r"^(Before substantive work, resolve and read these real installed skills "
    r"using the host active skill inventory:\s*)([^.\n]+)(\.)",
    re.MULTILINE,
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


def named_file(directory, name, team_name=None):
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(f"Invalid {directory} name: {name!r}")
    if directory == "profiles":
        profiles = load_model_profiles(team_name)
        if name not in profiles:
            raise ValueError(f"Unknown profiles {name!r}; available: {sorted(profiles)}")
        return profiles[name]
    path = ROOT / "teams" / name / "team.toml"
    if path.is_symlink() or not path.is_file():
        choices = sorted(p.parent.name for p in (ROOT / "teams").glob("*/team.toml"))
        raise ValueError(f"Unknown {directory} {name!r}; available: {choices}")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load_model_profiles(team_name):
    named_file("teams", team_name)
    profiles = {}
    for path in sorted((ROOT / "teams" / team_name / "profiles").glob("*.toml")):
        if path.is_symlink():
            continue
        document = tomllib.loads(path.read_text(encoding="utf-8"))
        if path.stem == "inherit":
            profiles["inherit"] = document
            continue
        keys(document, {"host", "profiles", "coordinator"}, str(path))
        host = document.get("host")
        if host not in HOSTS:
            raise ValueError(f"{path.name}: host must be one of {HOSTS}")
        configs = table(document.get("profiles", {}), f"{path.name}.profiles")
        recommendations = table(document.get("coordinator", {}), f"{path.name}.coordinator")
        keys(recommendations, set(configs), f"{path.name}.coordinator")
        for tier, config in configs.items():
            name = f"{path.stem}-{tier}"
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
                raise ValueError(f"Invalid model profile ID: {name!r}")
            profiles[name] = {host: table(config, name)}
            if tier in recommendations:
                profiles[name]["coordinator"] = {
                    host: settings(recommendations[tier], host, f"{name}.coordinator")}
    for tier in PROFILE_TIERS:
        sources = {"codex": f"openai-{tier}", "claude": f"anthropic-{tier}",
                   "antigravity": f"google-{tier}"}
        if all(name in profiles and host in profiles[name] for host, name in sources.items()):
            profiles[tier] = {host: profiles[name][host] for host, name in sources.items()}
            profiles[tier]["coordinator"] = {
                host: profiles[name]["coordinator"][host]
                for host, name in sources.items() if "coordinator" in profiles[name]}
    return profiles


def profile_sort_key(name):
    if name == "inherit":
        return (0, "", 0)
    if name in PROFILE_TIERS:
        return (1, "", PROFILE_TIERS.index(name))
    for tier in sorted(PROFILE_TIERS, key=len, reverse=True):
        suffix = f"-{tier}"
        if name.endswith(suffix):
            vendor = name[: -len(suffix)]
            return (1, vendor, PROFILE_TIERS.index(tier))
    vendor, _, tier = name.partition("-")
    return (1, vendor, len(PROFILE_TIERS))


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
    return {role for path in (ROOT / "teams").glob("*/team.toml")
            if not path.is_symlink()
            for role in tomllib.loads(path.read_text(encoding="utf-8"))["roles"]}


def select_asset_path(process: str, role: str, team_name=None) -> Path:
    team_name = team_name or ("bmad" if process == "bmad" else "pnet")
    candidate = ROOT / "teams" / team_name / "agents" / f"{role}.md"
    if candidate.is_file() and not any(path.is_symlink() for path in (candidate, *candidate.parents) if path != ROOT):
        return candidate
    raise ValueError(f"No agent source for team {team_name}/{role}")


def load_role(process: str, role: str, team_name=None) -> dict:
    path = select_asset_path(process, role, team_name)
    raw = path.read_text(encoding="utf-8")
    header, separator, body = raw.removeprefix("+++\n").partition("\n+++\n")
    if not raw.startswith("+++\n") or not separator or not body.strip():
        raise ValueError(f"Malformed agent source: {path}")
    data = tomllib.loads(header)
    keys(data, {"name", "description", "access", "web", "delegation"}, str(path))
    if data.get("name") != f"plex-{role}":
        raise ValueError(f"Invalid agent name: {path}")
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        raise ValueError(f"Missing agent description: {path}")
    if not isinstance(data.get("access"), str) or data["access"] not in {"read-only", "workspace-write"}:
        raise ValueError(f"Invalid agent access: {path}")
    for field in ("web", "delegation"):
        if type(data.get(field)) is not bool:
            raise ValueError(f"{path}: {field} must be a boolean")
    if data["delegation"] and data["access"] == "read-only":
        raise ValueError(f"Read-only agents cannot delegate: {path}")
    return {**data, "instructions": body.lstrip("\n")}


def resolve(config):
    config = table(config, "project")
    keys(config, {"team", "model_profile", "process", "roles", "skills", "max_agents", "interaction", *HOSTS}, "project")
    team_name = config.get("team")
    if team_name == "default":
        team_name = "pnet"
    if team_name is not None:
        if {"process", "roles", "skills"} & config.keys():
            raise ValueError("Choose team OR legacy process/roles/skills, not both")
        team = named_file("teams", team_name)
        keys(team, {"process", "roles", "skills", "workflows", "max_agents", "interaction"}, "team")
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
    interaction = config.get("interaction", team.get("interaction", "balanced"))
    if not isinstance(interaction, str) or interaction not in INTERACTIONS:
        raise ValueError(f"interaction must be one of {INTERACTIONS}")
    known_roles = discover_known_roles()
    if set(roles) - known_roles:
        raise ValueError(f"Unknown roles: {sorted(set(roles) - known_roles)}")
    for role in roles:
        load_role(process, role, team_name)
    bindings = table(team.get("skills", {}), "skills")
    keys(bindings, set(roles), "skills")
    for role, names in bindings.items():
        if (not isinstance(names, list) or not names
                or any(not isinstance(n, str) or not n.strip() for n in names)
                or len(names) != len(set(names))):
            raise ValueError(f"skills.{role}: expected unique nonblank skill names")
    workflows = table(team.get("workflows", {}), "workflows")
    keys(workflows, set(roles), "workflows")
    for role, entries in workflows.items():
        label = f"workflows.{role}"
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"{label}: expected a nonempty list of workflow entries")
        seen = set()
        for entry in entries:
            entry = table(entry, label)
            keys(entry, {"skill", "description", "operation"}, label)
            skill = entry.get("skill")
            if not isinstance(skill, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill):
                raise ValueError(f"{label}: invalid workflow skill")
            description = entry.get("description")
            if not isinstance(description, str) or not description.strip():
                raise ValueError(f"{label}: expected a nonblank description")
            operation = entry.get("operation")
            if "operation" in entry and (not isinstance(operation, str)
                    or not re.fullmatch(r"[A-Z][A-Z0-9_-]*", operation)):
                raise ValueError(f"{label}: invalid menu operation code")
            identity = (skill, operation)
            if identity in seen:
                raise ValueError(f"{label}: duplicate workflow operation {identity}")
            seen.add(identity)
    if process == "bmad":
        required = named_file("teams", "bmad")["skills"]
        for role in roles:
            if role not in required or not set(required[role]) <= set(bindings.get(role, [])):
                raise ValueError(f"Missing mandatory BMad bindings for {role}")
    profile_name = config.get("model_profile", "inherit")
    profile_team = team_name or ("bmad" if process == "bmad" else "pnet")
    profile = named_file("profiles", profile_name, profile_team)
    keys(profile, {*HOSTS, "coordinator"}, "model profile")
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
        "coordinator": profile.get("coordinator", {}),
        "process": process, "roles": list(roles),
        "skills": {role: list(names) for role, names in bindings.items()},
        "workflows": {role: [dict(entry) for entry in entries] for role, entries in workflows.items()},
        "interaction": interaction,
        "max_agents": max_agents, "hosts": hosts, "inactive_overrides": inactive,
    }


def _inject_skill_bindings(instructions: str, role_skills: list[str]) -> str:
    if not role_skills:
        return instructions
    match = SKILL_PREFIX_RE.search(instructions)
    if match:
        existing = [item.strip() for item in match.group(2).split(",") if item.strip()]
        merged = list(existing)
        for skill in role_skills:
            if skill not in merged:
                merged.append(skill)
        return f"{instructions[:match.start()]}{match.group(1)}{', '.join(merged)}{match.group(3)}{instructions[match.end():]}"
    skill_list = ", ".join(role_skills)
    prefix = (
        "Before substantive work, resolve and read these real installed skills "
        f"using the host active skill inventory: {skill_list}. If missing or "
        "ambiguous, report the blocker; do not invent a replacement.\n\n"
    )
    return prefix + instructions


def toml_multiline(value: str) -> str:
    body = "\n".join(json.dumps(line, ensure_ascii=False)[1:-1].replace("\x7f", "\\u007f")
                     for line in value.split("\n"))
    return '\"\"\"\n' + body + '\"\"\"'


def render_role(resolved: dict, host: str, role: str) -> str:
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host!r}")
    if role not in resolved["roles"]:
        raise ValueError(f"Role {role!r} is not active in resolved configuration")
    source = load_role(resolved["process"], role, resolved.get("team"))
    instructions = _inject_skill_bindings(source["instructions"], resolved.get("skills", {}).get(role, []))
    role_settings = resolved["hosts"][host][role]

    if host == "codex":
        lines = [
            f'name = {json.dumps(source["name"])}',
            f'description = {json.dumps(source["description"])}',
        ]
        if "model" in role_settings:
            lines.append(f'model = {json.dumps(role_settings["model"])}')
        if "reasoning" in role_settings:
            lines.append(f'model_reasoning_effort = {json.dumps(role_settings["reasoning"])}')
        lines.append(f'sandbox_mode = {json.dumps(source["access"])}')
        lines.append(f"developer_instructions = {toml_multiline(instructions)}")
        rendered = "\n".join(lines) + "\n"
        tomllib.loads(rendered)
        return rendered

    model_value = role_settings.get("model", "inherit")
    if host == "antigravity" and model_value not in ANTIGRAVITY_NATIVE_MODELS:
        raise ValueError(
            f"Antigravity role {role!r}: native model routing does not support {model_value!r}; "
            "choose a supported tier or explicitly choose inherit for the current session model. "
            "No model substitution was applied."
        )
    lines = [f'name: {source["name"]}', f'description: {json.dumps(source["description"])}']
    # Preserve the native tool restrictions; omitting Claude tools inherits host permissions.
    tools = ["Read", "Glob", "Grep"]
    if host == "claude" and source["access"] == "read-only":
        if source["web"]:
            tools += ["WebSearch", "WebFetch"]
        tool_line = "tools: " + ", ".join(tools)
    elif host == "antigravity":
        tools = ["send_message", "view_file", "grep_search", "find_by_name", "list_dir"]
        if source["web"]:
            tools += ["read_url_content", "search_web"]
        if source["access"] == "workspace-write":
            tools += ["schedule", "multi_replace_file_content", "replace_file_content",
                      "write_to_file", "run_command", "manage_task", "notebook_edit"]
        if source["delegation"]:
            tools += ["define_subagent", "invoke_subagent", "manage_subagents"]
        tool_line = "tools:\n" + "\n".join(f"  - {tool}" for tool in tools)
    else:
        tool_line = None
    lines.append(f"model: {json.dumps(model_value)}")
    if tool_line:
        lines.append(tool_line)
    if host == "claude" and not source["delegation"]:
        lines.append("disallowedTools: Agent")
    if "reasoning" in role_settings:
        lines.append(f"effort: {role_settings['reasoning']}")
    return "---\n" + "\n".join(lines) + "\n---\n\n" + instructions.rstrip("\n") + "\n"


def host_dotdir(host: str) -> str:
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host!r}")
    return ".agents" if host == "antigravity" else f".{host}"


def user_root(host: str) -> Path:
    if host == "codex":
        return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().absolute()
    if host == "claude":
        return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")).expanduser().absolute()
    if host == "antigravity":
        return Path.home() / ".gemini"
    raise ValueError(f"Unknown host: {host}")


def installation_root(project: Path, host: str, scope: str) -> Path:
    if scope not in {"project", "user"}:
        raise ValueError(f"Unknown scope: {scope}")
    return user_root(host) if scope == "user" else Path(project)


def host_agents_relpath(host: str, scope="project") -> str:
    if scope == "user":
        return "config/agents" if host == "antigravity" else "agents"
    return f"{host_dotdir(host)}/agents"


def host_role_relpath(host: str, role: str, scope="project") -> str:
    extension = "toml" if host == "codex" else "md"
    return f"{host_agents_relpath(host, scope)}/plex-{role}.{extension}"


def render_host_roles(resolved: dict, host: str, scope="project") -> dict[str, dict]:
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host!r}")
    rendered = {}
    for role in resolved["roles"]:
        content = render_role(resolved, host, role)
        content_bytes = content.encode("utf-8")
        relpath = host_role_relpath(host, role, scope)
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
    for path in sorted((ROOT / "teams").glob("*/team.toml")):
        if not path.is_symlink():
            teams[path.parent.name] = tomllib.loads(path.read_text(encoding="utf-8"))
    return {"teams": teams, "model_profiles": {name: load_model_profiles(name) for name in teams}}


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


PLEX_START = b"<!-- plex:managed:start -->"
PLEX_END = b"<!-- plex:managed:end -->"
LEGACY_PLEX_MARKERS = (b"<!-- plex:start -->", b"<!-- plex:end -->")


def instruction_block(dev=False) -> bytes:
    block = (ROOT / "skills/plex-setup/assets/AGENTS.md.template").read_bytes().removesuffix(b"\n")
    if dev:
        extra = (ROOT / "skills/plex-setup/assets/AGENTS.dev.md.template").read_bytes().strip()
        block = block.replace(PLEX_END, b"\n" + extra + b"\n" + PLEX_END)
    if instruction_span(block) != (0, len(block)):
        raise ValueError("AGENTS.md.template must contain exactly one complete Plex block and no outside text")
    return block


def instruction_span(data: bytes):
    pairs = [(start, end) for start, end in ((PLEX_START, PLEX_END), LEGACY_PLEX_MARKERS)
             if start in data or end in data]
    if not pairs:
        return None
    if len(pairs) != 1:
        raise ValueError("Mixed legacy and managed Plex instruction markers")
    start_marker, end_marker = pairs[0]
    if data.count(start_marker) != 1 or data.count(end_marker) != 1:
        raise ValueError("Duplicate or unbalanced Plex instruction markers")
    start, end = data.index(start_marker), data.index(end_marker)
    if end < start:
        raise ValueError("Reversed Plex instruction markers")
    return start, end + len(end_marker)


def instruction_relpath(root: Path, host: str, scope: str) -> str:
    if host == "codex":
        names = ["AGENTS.override.md", "AGENTS.md"]
        if scope == "project":
            fallbacks = []
            for config in (user_root(host) / "config.toml", root / ".codex/config.toml"):
                if config.is_file():
                    fallbacks = tomllib.loads(config.read_text()).get("project_doc_fallback_filenames", fallbacks)
            if not isinstance(fallbacks, list) or not all(isinstance(n, str) and n and Path(n).name == n and n not in {".", ".."} and "\\" not in n for n in fallbacks):
                raise ValueError("Invalid project_doc_fallback_filenames; instruction target is ambiguous")
            names.extend(fallbacks)
        default = "AGENTS.md"
    elif host == "claude":
        names = ["CLAUDE.md"] if scope == "user" else ["CLAUDE.md", ".claude/CLAUDE.md"]
        default = "CLAUDE.md"
    else:
        names = ["GEMINI.md"] if scope == "user" else ["GEMINI.md", "AGENTS.md"]
        default = "GEMINI.md"
    for name in names:
        path = _ensure_safe_project_path(root, name)
        if path.is_file() and path.read_bytes().strip():
            return name
    return default


def plan_instructions(root: Path, host: str, scope: str, record=None, dev=None) -> dict:
    relpath = instruction_relpath(root, host, scope)
    path = _ensure_safe_project_path(root, relpath)
    before = path.read_bytes() if path.exists() else None
    data = before or b""
    span = instruction_span(data)
    current = data[slice(*span)] if span else None
    if dev is None:
        dev = host == "codex" and scope == "project" and _ensure_safe_project_path(root, ".plex/dev.json").is_file()
    block = instruction_block(dev=dev)
    if record:
        if record["relpath"] != relpath:
            raise ValueError("Managed Plex instructions are masked by another instruction file")
        if current is None or sha256_bytes(current) != record["sha256"]:
            raise ValueError("Managed Plex instruction block was modified or removed; outside text is preserved")
    elif current is not None and current != block:
        raise ValueError("Unowned Plex instruction block differs; review it before installation")
    if span:
        after = data[:span[0]] + block + data[span[1]:]
    else:
        separator = b"" if not data or data.endswith(b"\n\n") else (b"\n" if data.endswith(b"\n") else b"\n\n")
        after = data + separator + block + b"\n"
    return {"path": path, "before": before, "after": after,
            "record": {"relpath": relpath, "sha256": sha256_bytes(block)}}


def plan_codex_routing(root, scope, record=None):
    """Expose native role selection without adopting or replacing personal settings."""
    relpath = "config.toml" if scope == "user" else ".codex/config.toml"
    path = _ensure_safe_project_path(root, relpath)
    before = path.read_bytes() if path.exists() else None
    text = (before or b"").decode("utf-8")
    start, end = "# plex-routing:start\n", "# plex-routing:end\n"
    span = None
    if start.strip() in text or end.strip() in text:
        if text.count(start) != 1 or text.count(end) != 1 or text.index(end) < text.index(start):
            raise ValueError("Invalid Plex routing markers; config preserved")
        span = (text.index(start), text.index(end) + len(end))
    if record:
        if record["relpath"] != relpath or span is None or sha256_bytes(text[slice(*span)].encode()) != record["sha256"]:
            raise ValueError("Managed Codex routing changed or missing; config preserved")
    elif span is not None:
        raise ValueError("Unmanaged Plex routing block; config preserved")
    config = tomllib.loads(text)
    features = table(config.get("features", {}), "Codex features")
    native = table(features.get("multi_agent_v2", {}), "Codex multi_agent_v2")
    required = {"hide_spawn_agent_metadata": False, "tool_namespace": "agents"}
    for key, value in required.items():
        if key in native and (type(native[key]) is not type(value) or native[key] != value):
            raise ValueError(f"Codex features.multi_agent_v2.{key} conflicts with Plex role selection; personal setting preserved")
    missing = {key: value for key, value in required.items() if key not in native}
    if missing:
        if record:
            raise ValueError("Managed Codex routing is incomplete; config preserved")
        block = start + "".join(f"{key} = {json.dumps(value)}\n" for key, value in missing.items()) + end
        header = re.search(r"(?m)^\[features\.multi_agent_v2\][ \t]*(?:#[^\n]*)?(?:\n|$)", text)
        if "multi_agent_v2" in features:
            if header is None:
                raise ValueError("Codex routing uses inline or quoted tables; configure native role selection explicitly, config preserved")
            text = text[:header.end()] + ("" if header.group().endswith("\n") else "\n") + block + text[header.end():]
        else:
            # Keep the table header outside ownership so later personal keys retain their scope on uninstall.
            text += ("" if not text or text.endswith("\n") else "\n") + "\n[features.multi_agent_v2]\n" + block
        record = {"relpath": relpath, "sha256": sha256_bytes(block.encode())}
        parsed = tomllib.loads(text)["features"]["multi_agent_v2"]
        if any(parsed.get(key) != value for key, value in required.items()):
            raise ValueError("Codex routing did not render correctly")
    return {"path": path, "before": before, "after": text.encode() if text else before, "record": record}


def _validate_receipt_structure(data: dict, scope="project") -> dict:
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
                "skills", "max_agents", "role_settings", "files", "source_sha256", "instructions", "routing",
            },
            f"applied.json.hosts.{host}",
        )
        if record.get("host") != host:
            raise ValueError(f"applied.json.hosts.{host}: mismatched host field")
        if "instructions" in record:
            instruction = table(record["instructions"], "instructions")
            keys(instruction, {"relpath", "sha256"}, "instructions")
            relpath = instruction.get("relpath")
            if not isinstance(relpath, str) or Path(relpath).is_absolute() or ".." in Path(relpath).parts:
                raise ValueError("Invalid managed instruction path")
            if not isinstance(instruction.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", instruction["sha256"]):
                raise ValueError("Invalid managed instruction block hash")
        if "routing" in record:
            routing = table(record["routing"], "routing")
            keys(routing, {"relpath", "sha256"}, "routing")
            expected = "config.toml" if scope == "user" else ".codex/config.toml"
            if host != "codex" or routing.get("relpath") != expected or not isinstance(routing.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", routing["sha256"]):
                raise ValueError("Invalid managed Codex routing receipt")
        files = table(record.get("files", {}), f"applied.json.hosts.{host}.files")
        for role, file_info in files.items():
            if not isinstance(role, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", role):
                raise ValueError("Invalid managed role name")
            file_info = table(file_info, f"applied.json.hosts.{host}.files.{role}")
            keys(file_info, {"relpath", "sha256"}, f"applied.json.hosts.{host}.files.{role}")
            expected_rel = host_role_relpath(host, role, scope)
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
    scope="project",
    archive_agents=None,
) -> dict:
    extension = "toml" if host == "codex" else "md"
    agents_rel = host_agents_relpath(host, scope)
    conflicts = []
    try:
        if scope == "project":
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
    instructions_stale = False
    if receipt_record and receipt_record.get("instructions"):
        try:
            plan = plan_instructions(project_root, host, scope, receipt_record["instructions"])
            instructions_stale = plan["before"] != plan["after"]
        except (OSError, ValueError) as error:
            conflicts.append(str(error))
    routing_stale = False
    if host == "codex" and (resolved is not None or receipt_record):
        try:
            routing = plan_codex_routing(project_root, scope, (receipt_record or {}).get("routing"))
            routing_stale = routing["before"] != routing["after"]
        except (OSError, ValueError) as error:
            conflicts.append(str(error))
    existing_plex_files = {}
    if agents_dir.is_dir():
        for entry in sorted(agents_dir.glob(f"plex-*.{extension}")):
            if host == "codex" and f"{agents_rel}/{entry.name}" in (archive_agents or {}):
                continue
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
                f"Unmanaged file collision: {host_role_relpath(host, role, scope)} is not owned by .plex/applied.json"
            )

    rendered = {}
    if resolved is not None:
        try:
            rendered = render_host_roles(resolved, host, scope)
        except ValueError as error:
            conflicts.append(str(error))
            resolved = None

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
    elif missing_roles or outdated_roles or retire_roles or not receipt_matches_desired or instructions_stale or routing_stale:
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


def check_project(project_root: Path, host: str | None = None, scope="project") -> dict:
    if scope in {"user", "auto"} and host not in HOSTS:
        raise ValueError("User/auto scope requires a host")
    project_root = Path(project_root)
    if scope == "auto":
        local_roles = project_root / host_agents_relpath(host)
        scope = "project" if (project_root / ".plex").exists() or any(local_roles.glob("plex-*")) else "user"
    project_root = installation_root(project_root, host, scope)
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
            except (OSError, UnicodeError, ValueError) as err:
                conflicts.append(f"Invalid .plex/resolved.json: {err}")

    receipt = {"hosts": {}}
    if applied_path.is_file():
        try:
            receipt = _validate_receipt_structure(
                json.loads(applied_path.read_text(encoding="utf-8")), scope
            )
        except (OSError, UnicodeError, ValueError) as err:
            conflicts.append(f"Invalid .plex/applied.json: {err}")

    target_hosts = (host,) if host else HOSTS
    host_reports = {}
    for h in HOSTS:
        if scope == "user" and h != host:
            host_reports[h] = {"status": "unconfigured", "conflicts": []}
            continue
        host_reports[h] = _inspect_host_state(
            project_root, h, resolved, source_sha256, receipt["hosts"].get(h), scope
        )

    for h in HOSTS:
        host_reports[h]["configured"] = receipt["hosts"].get(h) is not None

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
        "scope": scope,
        "root": str(project_root.absolute()),
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
    interaction: str | None = None,
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
        config["team"] = "pnet"

    if config.get("team") == "default":
        config["team"] = "pnet"

    if model_profile is not None:
        config["model_profile"] = model_profile
    elif "model_profile" not in config:
        config["model_profile"] = "inherit"

    if max_agents is not None:
        config["max_agents"] = max_agents

    if interaction is not None:
        config["interaction"] = interaction

    if host_overrides is not None:
        keys(table(host_overrides, "host overrides"), set(HOSTS), "host overrides")
        config.update(host_overrides)
    config.setdefault("interaction", resolve(config)["interaction"])

    lines = []
    if "team" in config:
        lines.append(f'team = {json.dumps(config["team"])}')
    if "model_profile" in config:
        lines.append(f'model_profile = {json.dumps(config["model_profile"])}')
    if "interaction" in config:
        lines.append(f'interaction = {json.dumps(config["interaction"])}')
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


def other_codex_agents(root, roles, scope="project"):
    """Return other agent paths and hashes; None means manual cleanup is required."""
    directory = host_agents_relpath("codex", scope)
    folder = _ensure_safe_project_path(root, directory)
    receipt_path = _ensure_safe_project_path(root, ".plex/applied.json")
    receipt = _validate_receipt_structure(json.loads(receipt_path.read_text()), scope) if receipt_path.is_file() else {"hosts": {}}
    protected = {host_role_relpath("codex", role, scope) for role in roles}
    protected.update(item["relpath"] for item in receipt["hosts"].get("codex", {}).get("files", {}).values())
    config = _ensure_safe_project_path(root, "config.toml" if scope == "user" else ".codex/config.toml")
    registrations = tomllib.loads(config.read_text()).get("agents", {}) if config.is_file() else {}
    if not isinstance(registrations, dict):
        raise ValueError("Invalid Codex agent registrations; preserved")
    referenced = {str((config.parent / Path(item["config_file"]).expanduser()).resolve())
                  for item in registrations.values() if isinstance(item, dict) and isinstance(item.get("config_file"), str)}
    result = {}
    for path in sorted(folder.glob("*.toml")):
        relpath = f"{directory}/{path.name}"
        if relpath in protected or not (path.is_symlink() or path.is_file()):
            continue
        result[relpath] = (None if path.is_symlink() or str(path.resolve()) in referenced
                           else sha256_bytes(path.read_bytes()))
    return result


def apply_project(project_root, host, team=None, model_profile=None, max_agents=None, reset_overrides=False,
                  host_overrides=None, scope="project", instructions=False, interaction=None, archive_agents=None):
    project_root = installation_root(Path(project_root), host, scope)
    lock = _ensure_safe_project_path(project_root, ".plex/.apply.lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock.open("x", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
    except FileExistsError:
        raise ValueError("Another apply holds .plex/.apply.lock; inspect the owning process before recovery") from None
    try:
        return _apply_project(project_root, host, team, model_profile, max_agents, reset_overrides, host_overrides, scope, instructions, interaction, archive_agents)
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
    scope="project",
    instructions=False,
    interaction: str | None = None,
    archive_agents: dict | None = None,
) -> dict:
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host!r}")
    project_root = Path(project_root)
    _ensure_safe_project_path(project_root, ".plex")
    preset_path = _ensure_safe_project_path(project_root, ".plex/preset.toml")
    resolved_path = _ensure_safe_project_path(project_root, ".plex/resolved.json")
    applied_path = _ensure_safe_project_path(project_root, ".plex/applied.json")
    if scope == "project":
        _ensure_safe_project_path(project_root, host_dotdir(host))
    _ensure_safe_project_path(project_root, host_agents_relpath(host, scope))

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
        and "interaction" in existing_config
        and team is None
        and model_profile is None
        and max_agents is None
        and interaction is None
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
            interaction=interaction,
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
            json.loads(existing_applied_bytes.decode("utf-8")), scope
        )

    archive_agents = archive_agents or {}
    if archive_agents:
        if host != "codex":
            raise ValueError("Agent cleanup is supported only for Codex")
        available = other_codex_agents(project_root, resolved["roles"], scope)
        if any(digest is None or path not in available or available[path] != digest for path, digest in archive_agents.items()):
            raise ValueError("Other Codex agents changed after preview; review and retry")
    host_state = _inspect_host_state(
        project_root, host, resolved, source_sha256, receipt["hosts"].get(host), scope, archive_agents
    )
    if host_state["conflicts"]:
        raise ValueError("; ".join(host_state["conflicts"]))

    rendered_roles = render_host_roles(resolved, host, scope)
    old_host_record = receipt["hosts"].get(host, {})
    old_files = old_host_record.get("files", {})
    instruction_plan = (plan_instructions(project_root, host, scope, old_host_record.get("instructions"))
                        if instructions else None)
    routing_plan = plan_codex_routing(project_root, scope, old_host_record.get("routing")) if host == "codex" else None
    retire_roles = sorted(set(old_files.keys()) - set(resolved["roles"]))

    paths = {preset_path, resolved_path, applied_path}
    paths.update(_ensure_safe_project_path(project_root, path) for path in archive_agents)
    if instruction_plan:
        paths.add(instruction_plan["path"])
    for role in set(old_files) | set(rendered_roles):
        paths.add(_ensure_safe_project_path(project_root, host_role_relpath(host, role, scope)))
    if routing_plan:
        paths.add(routing_plan["path"])
    transaction = _ApplyTransaction(project_root, paths)
    if routing_plan and transaction.original[routing_plan["path"]] != routing_plan["before"]:
        raise ValueError("Codex config changed after planning; review and retry")
    if instruction_plan and transaction.original[instruction_plan["path"]] != instruction_plan["before"]:
        raise ValueError("Instruction file changed after planning; review and retry")
    for path, original in ((preset_path, existing_preset_bytes),
                           (resolved_path, existing_resolved_bytes),
                           (applied_path, existing_applied_bytes)):
        if transaction.original[path] != original:
            raise ValueError(f"Concurrent modification detected on {path.name}")
    for role, item in rendered_roles.items():
        path = _ensure_safe_project_path(project_root, item["relpath"])
        if role not in old_files and transaction.original[path] is not None:
            raise ValueError(f"Unmanaged file collision: {item['relpath']}")

    for relpath, digest in archive_agents.items():
        path = _ensure_safe_project_path(project_root, relpath)
        if transaction.original[path] is None or sha256_bytes(transaction.original[path]) != digest:
            raise ValueError("Other Codex agents changed after preview; review and retry")

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

        for relpath, digest in archive_agents.items():
            path = _ensure_safe_project_path(project_root, relpath)
            target = ensure_backup() / "other-agents" / path.name
            target.parent.mkdir(exist_ok=True)
            transaction.archive(path, target)
            if sha256_bytes(target.read_bytes()) != digest:
                raise ValueError(f"Archive verification failed for {relpath}")

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

        if instruction_plan and instruction_plan["before"] != instruction_plan["after"]:
            if instruction_plan["before"] is not None:
                bdir = ensure_backup()
                (bdir / "instructions.before.md").write_bytes(instruction_plan["before"])
            transaction.write(instruction_plan["path"], instruction_plan["after"])

        if routing_plan and routing_plan["before"] != routing_plan["after"]:
            if routing_plan["before"] is not None:
                (ensure_backup() / "config.before.toml").write_bytes(routing_plan["before"])
            transaction.write(routing_plan["path"], routing_plan["after"])

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
        if routing_plan and routing_plan["record"]:
            receipt["hosts"][host]["routing"] = routing_plan["record"]
        instruction_record = instruction_plan["record"] if instruction_plan else old_host_record.get("instructions")
        if instruction_record:
            receipt["hosts"][host]["instructions"] = instruction_record
            for other in receipt["hosts"].values():
                if other.get("instructions", {}).get("relpath") == instruction_record["relpath"]:
                    other["instructions"] = instruction_record
        receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if transaction.original[applied_path] != receipt_bytes:
            transaction.write(applied_path, receipt_bytes)
        transaction.check()

        other_hosts = {}
        other_hosts_needing_refresh = []
        for candidate_host in HOSTS:
            if candidate_host == host:
                continue
            if scope == "user":
                other_hosts[candidate_host] = {"host": candidate_host, "configured": False, "needs_refresh": False, "status": "unconfigured"}
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
            "scope": scope,
            "root": str(project_root.absolute()),
            "host": host,
            "team": resolved["team"],
            "model_profile": resolved["model_profile"],
            "process": resolved["process"],
            "installed_roles": list(resolved["roles"]),
            "written_roles": written_roles,
            "archived_roles": archived_roles,
            "archived_other_agents": list(archive_agents),
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


def uninstall_project(project_root, host, scope="project", dry_run=False):
    """Remove unchanged receipt-owned roles/blocks; retain preferences and shared plugins."""
    root = installation_root(Path(project_root), host, scope)
    receipt_path = _ensure_safe_project_path(root, ".plex/applied.json")
    if not receipt_path.is_file():
        return {"status": "unconfigured", "host": host, "scope": scope, "removed_roles": []}
    lock = _ensure_safe_project_path(root, ".plex/.apply.lock")
    if not dry_run:
        try:
            with lock.open("x", encoding="utf-8") as stream:
                stream.write(str(os.getpid()))
        except FileExistsError:
            raise ValueError("Another apply/uninstall holds .plex/.apply.lock") from None
    try:
        before_receipt = receipt_path.read_bytes()
        receipt = _validate_receipt_structure(json.loads(before_receipt), scope)
        record = receipt["hosts"].get(host)
        if record is None:
            return {"status": "unconfigured", "host": host, "scope": scope, "removed_roles": []}
        remaining = {name: item for name, item in receipt["hosts"].items() if name != host}
        roles = {}
        for role, info in record.get("files", {}).items():
            path = _ensure_safe_project_path(root, info["relpath"])
            if not path.is_file() or sha256_bytes(path.read_bytes()) != info["sha256"]:
                raise ValueError(f"Managed role changed or missing; preserved: {info['relpath']}")
            roles[path] = info["sha256"]
        instruction_path = None
        instruction_before = instruction_after = None
        info = record.get("instructions")
        if info:
            path = _ensure_safe_project_path(root, info["relpath"])
            data = path.read_bytes() if path.is_file() else b""
            span = instruction_span(data)
            if span is None or sha256_bytes(data[span[0]:span[1]]) != info["sha256"]:
                raise ValueError("Managed instruction block changed or missing; preserved")
            shared = any(other.get("instructions", {}).get("relpath") == info["relpath"] for other in remaining.values())
            if not shared:
                instruction_path, instruction_before = path, data
                instruction_after = data[:span[0]] + data[span[1]:]
        routing_plan = None
        if record.get("routing"):
            routing_plan = plan_codex_routing(root, scope, record["routing"])
            text = routing_plan["before"].decode("utf-8")
            start = text.index("# plex-routing:start\n")
            end = text.index("# plex-routing:end\n") + len("# plex-routing:end\n")
            routing_plan["after"] = (text[:start] + text[end:]).encode()
        snapshot = _ensure_safe_project_path(root, ".plex/resolved.json")
        paths = {receipt_path, *roles}
        if instruction_path:
            paths.add(instruction_path)
        if not remaining and snapshot.is_file():
            paths.add(snapshot)
        if routing_plan:
            paths.add(routing_plan["path"])
        transaction = _ApplyTransaction(root, paths)
        if transaction.original[receipt_path] != before_receipt:
            raise ValueError("Concurrent receipt change; retry uninstall")
        for path, digest in roles.items():
            if sha256_bytes(transaction.original[path] or b"") != digest:
                raise ValueError(f"Concurrent role change: {path}")
        if instruction_path and transaction.original[instruction_path] != instruction_before:
            raise ValueError("Concurrent instruction change; retry uninstall")
        if routing_plan and transaction.original[routing_plan["path"]] != routing_plan["before"]:
            raise ValueError("Concurrent Codex config change; retry uninstall")
        result = {"status": "planned" if dry_run else "uninstalled", "host": host, "scope": scope,
                  "root": str(root), "removed_roles": list(record.get("files", {})),
                  "instruction_block_removed": instruction_path is not None, "routing_settings_removed": routing_plan is not None, "backup_dir": None}
        if dry_run:
            return result
        backup = _create_backup_dir(root, host)
        result["backup_dir"] = str(backup.relative_to(root.resolve()))
        try:
            (backup / "applied.before.json").write_bytes(before_receipt)
            if instruction_path:
                (backup / "instructions.before.md").write_bytes(instruction_before)
                transaction.write(instruction_path, instruction_after)
            if routing_plan:
                (backup / "config.before.toml").write_bytes(routing_plan["before"])
                transaction.write(routing_plan["path"], routing_plan["after"])
            for path, digest in roles.items():
                transaction.archive(path, backup / path.name)
                if sha256_bytes((backup / path.name).read_bytes()) != digest:
                    raise ValueError(f"Backup verification failed: {path.name}")
            if remaining:
                transaction.write(receipt_path, (json.dumps({"hosts": remaining}, indent=2, sort_keys=True) + "\n").encode())
            else:
                transaction.archive(receipt_path, backup / "applied.json")
                if snapshot in paths:
                    transaction.archive(snapshot, backup / "resolved.json")
        except (OSError, ValueError, KeyboardInterrupt) as error:
            failures = transaction.rollback()
            if failures:
                raise ValueError(f"{error}; rollback needs recovery: {'; '.join(failures)}") from error
            raise
        return result
    finally:
        if not dry_run:
            lock.unlink()


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
    apply_parser.add_argument("--interaction", choices=INTERACTIONS, help="Interaction mode; preserve current selection if omitted")
    apply_parser.add_argument("--max-agents", type=int, default=None, help="Optional max_agents override")
    apply_parser.add_argument(
        "--reset-overrides", action="store_true", help="Clear personal overrides in .plex/preset.toml"
    )

    render_parser.add_argument("--scope", choices=("project", "user"), default="project")
    check_parser.add_argument("--scope", choices=("project", "user", "auto"), default="auto")
    apply_parser.add_argument("--scope", choices=("project", "user"), default="project")
    apply_parser.add_argument("--instructions", action="store_true", help="Also add/update the managed Plex block in the native instruction file")
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
                "roles": render_host_roles(snapshot, args.host, args.scope),
            }
        elif args.subcommand == "check":
            output = check_project(args.project, host=args.host, scope=("project" if args.host is None and args.scope == "auto" else args.scope))
        elif args.subcommand == "apply":
            output = apply_project(
                args.project,
                host=args.host,
                team=args.team,
                model_profile=args.model_profile,
                max_agents=args.max_agents,
                interaction=args.interaction,
                reset_overrides=args.reset_overrides,
                scope=args.scope,
                instructions=args.instructions,
            )
        else:
            raise ValueError(f"Unknown subcommand: {args.subcommand}")
    except (OSError, UnicodeError, ValueError) as error:
        label = "ERROR"
        if sys.stderr.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb":
            label = "\033[1;31mERROR\033[0m"
        print(f"[{label}] Plex configuration error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
