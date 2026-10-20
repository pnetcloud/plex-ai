#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["questionary==2.1.1"]
# ///
"""Interactive Plex installer. Arrow-key menus via uv + questionary; no model calls."""

import sys

if sys.version_info < (3, 11):
    sys.exit("Plex setup requires Python 3.11 or newer.")

sys.dont_write_bytecode = True

import argparse
import copy
from contextlib import contextmanager, nullcontext
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import tomllib


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "plex_config", ROOT / "skills/plex-setup/scripts/resolve_config.py"
)
CONFIG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIG)


MENU_STYLE = [
    ("qmark", "fg:#06b6d4"),
    ("pointer", "fg:#06b6d4 bold"),
    ("selected", "fg:#22c55e noreverse"),
    ("highlighted", "fg:default bg:default noreverse"),
    ("text", "fg:default bg:default noreverse"),
    ("answer", "fg:#06b6d4"),
    ("instruction", "fg:#808080"),
]


def heading(text):
    color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    print(f"\n\033[1;36m{text}\033[0m" if color else f"\n{text}", flush=True)


def choose(label, choices, default):
    ui = terminal_ui()
    if ui:
        labels = {"__default__": "Default", "__manual__": "Other model…", "__done__": "Done",
                  "inherit": "Inherit session settings", "custom": "Custom",
                  "basic": "Basic", "plus": "Plus", "pro": "Pro", "pro-plus": "Pro+",
                  "refresh": "Update only", "configure": "Reconfigure"}
        if label == "Model profile":
            for name in choices:
                if name in CONFIG.PROFILE_TIERS:
                    continue
                for tier in sorted(CONFIG.PROFILE_TIERS, key=len, reverse=True):
                    if name.endswith(f"-{tier}"):
                        vendor = name[: -(len(tier) + 1)]
                        title = {
                            "openai": "OpenAI",
                            "anthropic": "Anthropic",
                            "google": "Google",
                            "google-anthropic": "Google-Anthropic",
                        }.get(vendor, vendor.title())
                        labels[name] = f"{title} · " + ("Pro+" if tier == "pro-plus" else tier.title())
                        break
        return ui.select(label, choices=[ui.Choice(
            [("class:text", labels.get(name, name) if label == "Model profile" else f"{labels.get(name, name)}  {detail}")],
            value=name, description=detail if label == "Model profile" else None)
                                        for name, detail in choices.items()], default=default,
                         pointer="›", style=ui.Style(MENU_STYLE)).unsafe_ask()
    heading(label)
    names = list(choices)
    for index, name in enumerate(names, 1):
        print(f"  {index}. {name:<16} {choices[name]}")
    while True:
        answer = input(f"Choice [{default}]: ").strip() or default
        if answer.isdigit() and 1 <= int(answer) <= len(names):
            answer = names[int(answer) - 1]
        if answer in choices:
            return answer
        print("Choose a listed name or number.")


def choose_clients():
    choices = {"codex": "OpenAI Codex", "claude": "Anthropic Claude Code",
               "antigravity": "Google Antigravity"}
    ui = terminal_ui()
    if ui:
        return ui.checkbox(
            "Clients",
            choices=[ui.Choice([("class:text", title)], value=name, checked=name == "codex")
                     for name, title in choices.items()],
            pointer="›", style=ui.Style(MENU_STYLE),
            instruction="↑/↓ move · Space select · Enter continue",
            validate=lambda selected: bool(selected) or "Select at least one client.",
        ).unsafe_ask()
    heading("Clients (choose one or more)")
    names = list(choices)
    for index, name in enumerate(names, 1):
        print(f"  {index}. {choices[name]}")
    while True:
        answer = input("Names or numbers separated by commas [codex]: ").strip() or "codex"
        selected = [part.strip() for part in answer.split(",")]
        selected = [names[int(item) - 1] if item.isdigit() and 1 <= int(item) <= len(names) else item
                    for item in selected]
        if selected and all(item in choices for item in selected):
            return list(dict.fromkeys(selected))
        print("Select at least one listed client, for example 1,2.")


def terminal_ui():
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import questionary
            return questionary
        except ImportError:
            pass
    return None


def ask_text(label, default=""):
    ui = terminal_ui()
    if ui:
        return ui.text(label, default=default).unsafe_ask()
    return input(f"{label} [{default}]: ").strip() or default


def model_catalog(host, project):
    if host == "claude":
        return {name: {} for name in ("sonnet", "opus", "haiku", "fable", "inherit")}
    if host == "antigravity":
        return {name: {} for name in CONFIG.ANTIGRAVITY_NATIVE_MODELS}
    print("\nReading the active Codex model catalog…", flush=True)
    try:
        result = subprocess.run(["codex", "debug", "models"], cwd=project,
                                capture_output=True, text=True, timeout=15)
        if result.returncode:
            raise ValueError("catalog unavailable")
        return {item["slug"]: item for item in json.loads(result.stdout)["models"]
                if item.get("visibility", "list") == "list"}
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        print("Codex catalog unavailable. Using packaged suggestions; availability is unverified.")
        models = {}
        for profiles in CONFIG.list_catalog()["model_profiles"].values():
            for profile in profiles.values():
                settings = profile.get(host, {})
                for value in (settings, *(v for v in settings.values() if isinstance(v, dict))):
                    if value.get("model"):
                        models[value["model"]] = {}
        return models


def customize_roles(config, host, project):
    config = copy.deepcopy(config)
    resolved = CONFIG.resolve(config)
    models = model_catalog(host, project)
    print(f"\nCustom overrides on {resolved['model_profile']}. Default uses profile/project settings.")
    print("Model availability depends on your provider and account.")
    host_config = config.setdefault(host, {})
    while True:
        effective = CONFIG.resolve(config)["hosts"][host]
        roles = {role: f"{value.get('model', 'session model')} / {value.get('reasoning', 'session reasoning')}"
                 for role, value in effective.items()}
        roles["__done__"] = "Return to the installation plan"
        role = choose("Agent settings", roles, "__done__")
        if role == "__done__":
            break
        values = host_config.setdefault(role, {})
        baseline = copy.deepcopy(config)
        baseline[host].pop(role, None)
        defaults = CONFIG.resolve(baseline)["hosts"][host][role]
        choices = {"__default__": f"Profile/project default ({defaults.get('model', 'session model')})"}
        choices.update({name: item.get("description", "") for name, item in models.items()})
        current = values.get("model", "__default__")
        if current not in choices:
            choices[current] = "Current project model"
        if host != "antigravity":
            choices["__manual__"] = "Enter a model ID for your provider"
        selected = choose(f"plex-{role} · Model", choices, current)
        if selected == "__manual__":
            selected = ask_text("Model ID", values.get("model", ""))
            CONFIG.settings({"model": selected}, host, role)
        if selected == "__default__":
            values.pop("model", None)
        else:
            values["model"] = selected
        effective_model = values.get("model", defaults.get("model"))
        supported = models.get(effective_model, {}).get("supported_reasoning_levels")
        allowed = CONFIG.EFFORTS if host == "codex" else CONFIG.CLAUDE_EFFORTS
        efforts = [item["effort"] for item in supported if item.get("effort") in allowed] if supported is not None else [
            effort for effort in ("minimal", "low", "medium", "high", "xhigh", "max", "ultra") if effort in allowed]
        choices = {"__default__": f"Profile/project default ({defaults.get('reasoning', 'session reasoning')})"}
        descriptions = {item["effort"]: item.get("description", "") for item in supported or []}
        choices.update({effort: descriptions.get(effort, "") for effort in efforts})
        current = values.get("reasoning", "__default__")
        if current not in choices:
            print(f"  Previous reasoning {current!r} is not listed for this model; choose a supported level.")
            current = "__default__"
        selected = choose(f"plex-{role} · Reasoning", choices, current)
        if selected == "__default__":
            values.pop("reasoning", None)
        else:
            values["reasoning"] = selected
    CONFIG.resolve(config)
    return {host: host_config}


def host_cli(host):
    return "agy" if host == "antigravity" else host


def build_plugin(host):
    """Export reviewed public files; native caches need a self-contained package."""
    if host not in CONFIG.HOSTS:
        raise ValueError(f"Unknown host: {host}")
    files = {}
    prefix = f"plugins/{host}/"
    for line in (ROOT / ".gitignore").read_text().splitlines():
        if not line.startswith("!/") or line.endswith("/"):
            continue
        pattern = Path(line[2:])
        if pattern.is_absolute() or ".." in pattern.parts:
            raise ValueError(f"Invalid public package path: {pattern}")
        for source in ROOT.glob(str(pattern)):
            name = source.relative_to(ROOT).as_posix()
            if name.startswith(prefix):
                target = name[len(prefix):]
            elif source.relative_to(ROOT).parts[0] in ("skills", "teams") or name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
                target = name
            else:
                continue
            if source.is_symlink() or not source.resolve().is_relative_to(ROOT) or not source.is_file():
                raise ValueError(f"Missing or unsafe public package file: {name}")
            files[target] = source.read_bytes()
    required = {f".{host}-plugin/plugin.json", "skills/plex/SKILL.md",
                "skills/plex-setup/scripts/resolve_config.py",
                "skills/plex-setup/assets/AGENTS.md.template", "teams/pnet/team.toml",
                "teams/pnet/profiles/inherit.toml",
                "teams/pnet/coordinator.md", "teams/bmad/coordinator.md"}
    if not required <= files.keys():
        raise ValueError("Missing or unsafe public package files: incomplete plugin")
    package = ROOT / ".build/plugins" / host
    if package.is_symlink() or package.parent.is_symlink() or (ROOT / ".build").is_symlink():
        raise ValueError(f"Build directory must not be a symlink: {package}")
    if package.exists():
        actual = {p.relative_to(package).as_posix(): p.read_bytes()
                  for p in package.rglob("*") if p.is_file()}
        if actual == files:
            return package
    package.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=package.parent) as temp:
        staged = Path(temp) / "package"
        for name, content in files.items():
            target = staged / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        previous = Path(temp) / "previous"
        if package.exists():
            package.rename(previous)
        try:
            staged.rename(package)
        except OSError:
            if previous.exists():
                previous.rename(package)
            raise
    return package


def plugin_commands(host, scope="project"):
    package = ROOT / ".build/plugins" / host
    if host == "codex":
        return [
            ["codex", "plugin", "marketplace", "add", str(ROOT), "--json"],
            ["codex", "plugin", "add", "pnet-plex@pnet-plex", "--json"],
        ]
    if host == "antigravity":
        return [
            ["agy", "plugin", "install", str(package)],
        ]
    return [
        ["claude", "plugin", "marketplace", "add", str(ROOT)],
        ["claude", "plugin", "install", "pnet-plex@pnet-plex", "--scope", "user"],
    ]


def run(command, project):
    result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=120)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise ValueError(f"{shlex.join(command)}\n{detail}")
    return result.stdout


def command_destination(*, keep_existing=False):
    destination = Path.home() / ".local/bin/plex"
    if destination.is_symlink() and destination.resolve() in {ROOT / "setup.py", ROOT / "setup.sh"}:
        return destination
    if destination.exists() or destination.is_symlink():
        if keep_existing:
            print(f"Keeping existing command: {destination}. Setup continues without replacing it.")
            print(f"To use this checkout directly: {ROOT / 'setup.sh'}")
            return None
        raise ValueError(f"Command already exists; left unchanged: {destination}. Use --no-command to keep it.")
    return destination


def install_command():
    destination = command_destination()
    source = ROOT / "setup.sh"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() and destination.resolve() == ROOT / "setup.py":
        destination.unlink()  # Upgrade this checkout's previous shortcut.
    if not destination.is_symlink():
        destination.symlink_to(source)
    print(f"Command ready: {destination}\nRun plex from any project directory.")
    if str(destination.parent) not in os.environ.get("PATH", "").split(os.pathsep):
        print('Add this to your shell configuration: export PATH="$HOME/.local/bin:$PATH"')


# This official skills revision includes PO; the plugin marketplace still lags it.
BMAD_SKILLS_SOURCE = "https://github.com/bmad-code-org/BMAD-METHOD/tree/495ef6e0996d07b23359cc4d6c73a1aa2f3ba5ad/skills"
SKILLS_CLI = "skills@1.7.4"
BMAD_AGENTS = {"codex": "codex", "claude": "claude-code", "antigravity": "antigravity"}


class BMadNotInstalled(ValueError):
    pass


def bmad_plugin_inventory(project, host):
    data = json.loads(run([host_cli(host), "plugin", "list", "--json"], project))
    entries = data.get("installed") if host == "codex" and isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ValueError(f"Unsupported {host} plugin inventory for BMad discovery")
    return [item for item in entries if isinstance(item, dict)]


def bmad_plugin_id(item, host):
    return (f"{item.get('name')}@{item.get('marketplaceName')}" if host == "codex"
            else item.get("id"))


def bmad_required_skills():
    team = CONFIG.named_file("teams", "bmad")
    names = {"bmad", "bmod-method", "bmod-core-tools"}
    names.update(name for bindings in team["skills"].values() for name in bindings)
    names.update(entry["skill"] for entries in team["workflows"].values() for entry in entries)
    return sorted(names)


def bmad_install_commands(host):
    return [["npx", "--yes", SKILLS_CLI, "add", BMAD_SKILLS_SOURCE, "--global",
             "--agent", BMAD_AGENTS[host], "--skill", *bmad_required_skills(), "--yes"]]


def bmad_user_skills(host):
    if host == "codex":
        return Path.home() / ".agents/skills"
    if host == "antigravity":
        return Path.home() / ".gemini/antigravity/skills"
    return CONFIG.user_root(host) / "skills"


def install_bmad_dependencies(project, host):
    if not shutil.which("npx"):
        raise ValueError("Installing official BMad skills requires Node.js/npm (npx). Install them and retry.")
    print("Installing the selected official BMad skills for this user. Existing selected "
          "user skill files may be replaced; other projects share them. Installed plugins "
          "are not changed. These changes remain after cancellation or later failure.")
    for command in bmad_install_commands(host):
        print("  " + shlex.join(command))
        run(command, project)
    root = bmad_user_skills(host)
    missing = [name for name in bmad_required_skills() if not (root / name / "SKILL.md").is_file()]
    if missing:
        raise ValueError(f"Official BMad installation is incomplete: {', '.join(missing)}")


BMAD_RUNTIME_SCRIPTS = ("resolve_config.py", "resolve_customization.py", "render_skill.py")


def bmad_runtime_ready(project):
    return all((project / "_bmad/scripts" / name).is_file() for name in BMAD_RUNTIME_SCRIPTS)


def find_bmad_skill(project, host, explicit=None):
    def usable(path):
        return (all((path / name).is_file() for name in
                    ("SKILL.md", "scripts/setup.py", "assets/config.template.toml"))
                and any((path / name).is_file() for name in ("module-manifest.toml", "bmod.toml")))

    if explicit is not None:
        path = explicit.expanduser().resolve()
        if not usable(path):
            raise ValueError(f"Not a BMad setup skill: {path}")
        return path
    # Prefer project skills, then user skills; do not scan arbitrary cached versions.
    for roots in ((project / ".agents/skills", project / CONFIG.host_dotdir(host) / "skills"),
                  (bmad_user_skills(host), Path.home() / ".agents/skills", CONFIG.user_root(host) / "skills")):
        candidates = {root.resolve() / "bmad" for root in roots if usable(root / "bmad")}
        if len(candidates) == 1:
            return candidates.pop()
        if candidates:
            raise ValueError("Multiple BMad setup skills found; select one with --bmad-skill PATH")
    if host in {"codex", "claude"}:
        candidates = set()
        for item in bmad_plugin_inventory(project, host):
            identity = bmad_plugin_id(item, host)
            if identity != "bmad-toolbox@bmad" or not item.get("enabled") or item.get("errors"):
                continue
            if host == "codex" and not item.get("installed"):
                continue
            if host == "claude" and item.get("scope") != "user":
                continue
            version = item.get("version")
            if not isinstance(version, str) or version in {"", ".", ".."} or "/" in version or "\\" in version:
                raise ValueError("Invalid BMad plugin inventory path")
            path = CONFIG.user_root(host) / "plugins/cache/bmad/bmad-toolbox" / version / "skills/bmad"
            if host == "claude" and isinstance(item.get("installPath"), str):
                path = Path(item["installPath"]) / "skills/bmad"
            if usable(path):
                candidates.add(path.resolve())
        if len(candidates) == 1:
            return candidates.pop()
        if candidates:
            raise ValueError("Multiple enabled BMad Toolbox copies; select one with --bmad-skill PATH")
    raise BMadNotInstalled(
        "BMad setup skill is not available. Install the official BMad Toolbox for your client, "
        "or rerun with --install-bmad to install the required official user skills and initialize this project.\n"
        "For an existing installation, use --bmad-skill PATH; or choose team pnet without BMad."
    )


def plan_bmad_init(project, host, explicit, interactive):
    if not shutil.which("uv"):
        raise ValueError("BMad setup requires uv. Install uv, then rerun setup.")
    skill = find_bmad_skill(project, host, explicit)
    command = ["uv", "run", "--no-cache", str(skill / "scripts/setup.py"),
               "--project-root", str(project), "--skill", str(skill)]
    questions = json.loads(run([*command, "--list-config-questions"], project))
    if not isinstance(questions, list):
        raise ValueError("Unsupported BMad setup question response")
    answers = {}
    for question in questions:
        if not isinstance(question, dict) or any(not isinstance(question.get(key), str)
                for key in ("module", "key", "prompt", "default")):
            raise ValueError("Malformed BMad setup question")
        identity = (question["module"], question["key"])
        if identity in answers:
            raise ValueError("Duplicate BMad setup question")
        if interactive:
            answer = ask_text(question["prompt"], question["default"])
        else:
            answer = question["default"]
            print(f"  BMad default: {question['prompt']} = {answer}")
        answers[identity] = answer
    return {"command": command, "answers": answers, "skill": skill}


def initialize_bmad(project, plan):
    # Let the official setup own materialization and preservation of BMad config.
    with tempfile.TemporaryDirectory(prefix="plex-bmad-answers-") as temp:
        command = list(plan["command"])
        if plan["answers"]:
            sections = {}
            for (module, key), value in plan["answers"].items():
                sections.setdefault(module, []).append(f"{json.dumps(key)} = {json.dumps(value)}")
            text = "\n\n".join(f"[modules.{json.dumps(module)}]\n" + "\n".join(values)
                                 for module, values in sections.items()) + "\n"
            answers_path = Path(temp) / "answers.toml"
            answers_path.write_text(text)
            command += ["--module-answers", str(answers_path)]
        run(command, project)
    if not bmad_runtime_ready(project):
        raise ValueError("Official BMad setup did not produce the required runtime; inspect its output before retrying")
    print("  BMad runtime initialized by its official setup. It remains if a later Plex step fails.")


def verify_plugin(host, project):
    data = json.loads(run([host_cli(host), "plugin", "list", "--json"], project))
    entries = data.get("installed", []) if host == "codex" and isinstance(data, dict) else data
    if not isinstance(entries, list):
        raise ValueError("The host returned an unsupported plugin inventory format")
    for item in entries:
        if not isinstance(item, dict):
            continue
        matches = (item.get("id") == "pnet-plex@pnet-plex" and item.get("scope") == "user"
                   if host == "claude" else item.get("name") == "pnet-plex")
        if matches and item.get("enabled") is True and not item.get("errors"):
            return
    raise ValueError("Plex plugin is not installed and enabled for this host/project; inspect the host's plugin settings")


def select_target(args, interactive):
    if args.scope is None:
        args.scope = choose("Installation scope", {
            "project": "Team for one project (recommended); shared plugin stays user-wide",
            "user": "Default team for all projects of this user/client profile",
        }, "project") if interactive else "project"
    if args.project is None:
        if args.scope == "project":
            default_project = "" if Path.cwd().resolve() == ROOT else str(Path.cwd())
            while True:
                selected_project = ask_text("Project directory", default_project).strip()
                if selected_project:
                    args.project = Path(selected_project)
                    break
                print("Enter your target project directory; the Plex source checkout is not selected automatically.")
        else:
            args.project = Path.cwd()
    project = args.project.expanduser().absolute()
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    return project


def setup_clients(args, clients, interactive):
    if args.model_profile is not None and args.model_profile not in ("inherit", *CONFIG.PROFILE_TIERS):
        raise ValueError("For multiple clients choose one shared profile: inherit, basic, plus, pro or pro-plus")
    if not args.roles_only and not args.dry_run:
        missing = [host_cli(client) for client in clients if not shutil.which(host_cli(client))]
        if missing:
            raise ValueError(f"Missing client CLI: {', '.join(missing)}. Install it or use --roles-only.")
    project = select_target(args, interactive)
    print("One profile is shared by all clients. Each installation has a plan to confirm; stopping preserves completed clients.")
    completed = []
    setup_mode = None
    instruction_choices = {}
    for client in clients:
        heading(f"Configure client: {client}")
        options = ["--host", client, "--scope", args.scope, "--project", str(project)]
        for flag, value in (("--team", args.team), ("--model-profile", args.model_profile),
                            ("--max-agents", args.max_agents), ("--interaction", args.interaction)):
            if value is not None:
                options.extend([flag, str(value)])
        for flag, enabled in (("--roles-only", args.roles_only), ("--dry-run", args.dry_run),
                              ("--yes", args.yes), ("--no-command", not args.command)):
            if enabled:
                options.append(flag)
        if args.install_bmad:
            options.append("--install-bmad")
        if args.init_bmad:
            options.append("--init-bmad")
        if args.bmad_skill is not None:
            options.extend(["--bmad-skill", str(args.bmad_skill)])
        if args.instructions is not None:
            options.append("--instructions" if args.instructions else "--no-instructions")
        selection = {}
        status = main(options, shared_profile=True, selection=selection, setup_mode=setup_mode)
        if status or selection.get("cancelled"):
            print(f"Stopped at {client}. Completed clients: {', '.join(completed) or 'none'}. Rerun to continue.")
            return status
        completed.append(client)
        setup_mode = selection["setup_mode"]
        instruction_choices[client] = selection["instructions"]
        if args.team is None:
            args.team = selection["team"]
        if args.max_agents is None:
            args.max_agents = selection["max_agents"]
        if args.interaction is None:
            args.interaction = selection["interaction"]
        if args.model_profile is None:
            args.model_profile = selection["model_profile"]
    if not args.dry_run:
        # All selected clients must acknowledge the final shared configuration.
        for client in clients:
            CONFIG.apply_project(project, client, scope=args.scope, instructions=instruction_choices[client])
        for client in clients:
            if CONFIG.check_project(project, client, args.scope)["status"] != "in_sync":
                raise ValueError(f"Final check failed for client {client}; rerun setup")
        print(f"All selected clients are in sync: {', '.join(completed)}.")
    return 0


DEV_PLUGIN = "pnet-plex@pnet-plex"
DEV_BLOCK = ('# plex-dev:start\n[plugins."pnet-plex@pnet-plex"]\nenabled = false\n# plex-dev:end\n')
DEV_SKILLS = ("plex", "plex-setup")


def plan_dev(project, enabled):
    """Plan only owned links and a repo-local plugin override; never touch user config."""
    project = project.resolve()
    receipt = CONFIG._ensure_safe_project_path(project, ".plex/dev.json")
    config = CONFIG._ensure_safe_project_path(project, ".codex/config.toml")
    CONFIG._ensure_safe_project_path(project, ".agents/skills")
    before = receipt.read_bytes() if receipt.exists() else None
    record = json.loads(before) if before is not None else None
    if record is not None and (not isinstance(record, dict) or set(record) != {"source", "config_block"}
                               or not isinstance(record["source"], str) or not Path(record["source"]).is_absolute()
                               or type(record["config_block"]) is not bool):
        raise ValueError("Invalid .plex/dev.json; inspect before changing development mode")
    config_before = config.read_bytes() if config.exists() else None
    text = (config_before or b"").decode("utf-8")
    settings = tomllib.loads(text)
    plugins = settings.get("plugins", {})
    if not isinstance(plugins, dict) or (DEV_PLUGIN in plugins and not isinstance(plugins[DEV_PLUGIN], dict)):
        raise ValueError("Invalid project plugin settings; preserved")
    if record and record["config_block"] and text.count(DEV_BLOCK) != 1:
        raise ValueError("Managed Plex dev plugin override changed; preserved")
    links = []
    for name in DEV_SKILLS:
        path = project / ".agents/skills" / name
        old = str(Path(record["source"]) / "skills" / name) if record else None
        actual = os.readlink(path) if path.is_symlink() else None
        if (old is not None and actual != old) or (old is None and (path.exists() or path.is_symlink())):
            raise ValueError(f"Foreign or modified development skill preserved: {path}")
        target = str(ROOT / "skills" / name) if enabled else None
        if enabled and not (Path(target) / "SKILL.md").is_file():
            raise ValueError(f"Development source is incomplete: {target}")
        links.append((path, actual, target))
    if enabled:
        owned_block = record["config_block"] if record else False
        plugin = plugins.get(DEV_PLUGIN)
        if not record and plugin is None:
            text += ("" if not text or text.endswith("\n\n") else "\n" if text.endswith("\n") else "\n\n") + DEV_BLOCK
            owned_block = True
        if tomllib.loads(text).get("plugins", {}).get(DEV_PLUGIN, {}).get("enabled") is not False:
            raise ValueError('Set [plugins."pnet-plex@pnet-plex"] enabled = false in project .codex/config.toml before --dev; existing override preserved')
        after = (json.dumps({"source": str(ROOT), "config_block": owned_block}, indent=2) + "\n").encode()
    else:
        if record and record["config_block"]:
            text = text.replace(DEV_BLOCK, "", 1)
        after = None
    config_after = text.encode() if text else None
    return {"project": project, "enabled": enabled, "links": links,
            "files": {config: (config_before, config_after), receipt: (before, after)}}


@contextmanager
def apply_dev(plan):
    """Undo dev changes if role application fails, preserving concurrent edits."""
    changed = []
    def link_value(path):
        CONFIG._ensure_safe_project_path(plan["project"], str(path.parent.relative_to(plan["project"])))
        if path.is_symlink():
            return os.readlink(path)
        if path.exists():
            raise ValueError(f"Foreign development skill preserved: {path}")
        return None
    def set_link(path, target):
        if path.is_symlink():
            path.unlink()
        if target is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(target, target_is_directory=True)
    transaction = CONFIG._ApplyTransaction(plan["project"], plan["files"])
    try:
        for path, (before, after) in plan["files"].items():
            if transaction.original[path] != before:
                raise ValueError(f"Development settings changed after preview: {path}")
        for path, before, after in plan["links"]:
            if link_value(path) != before:
                raise ValueError(f"Development skill changed after preview: {path}")
        for path, before, after in plan["links"]:
            if before != after:
                if link_value(path) != before:
                    raise ValueError(f"Development skill changed during apply: {path}")
                changed.append((path, before, after))
                set_link(path, after)
        for path, (before, after) in plan["files"].items():
            if before == after:
                continue
            if after is None:
                transaction.check()
                transaction.changed.append((path, None))
                path.unlink()
                transaction.expected[path] = None
            else:
                transaction.write(path, after)
        yield
    except (OSError, ValueError, KeyboardInterrupt):
        failures = transaction.rollback()
        for path, before, after in reversed(changed):
            try:
                if link_value(path) != after:
                    raise ValueError("concurrent edit preserved")
                set_link(path, before)
            except (OSError, ValueError) as error:
                failures.append(f"{path}: {error}")
        if failures:
            raise ValueError("Development rollback needs recovery: " + "; ".join(failures))
        raise


def plex_status(project, clients, scope=None):
    version = json.loads((ROOT / "plugins/codex/.codex-plugin/plugin.json").read_text())["version"]
    reports = []
    for client in clients:
        report = CONFIG.check_project(project, client, scope or "auto")
        state = report.get("hosts", {}).get(client, {})
        configured = state.get("configured", False)
        plugin = "not_checked"
        dev_source = None
        dev_receipt = CONFIG._ensure_safe_project_path(project.resolve(), ".plex/dev.json")
        if configured and client == "codex" and report.get("scope") == "project" and dev_receipt.is_file():
            try:
                plan_dev(project, True)
                dev_source = json.loads(dev_receipt.read_text())["source"]
                for name in DEV_SKILLS:
                    if not (Path(dev_source) / "skills" / name / "SKILL.md").is_file():
                        raise ValueError(f"Development source missing: {dev_source}")
                if not (Path(dev_source) / "teams").is_dir():
                    raise ValueError(f"Development team resources missing: {dev_source}")
                plugin = "development"
            except (OSError, ValueError) as error:
                plugin = str(error)
        elif configured:
            if not shutil.which(host_cli(client)):
                plugin = "cli_missing"
            else:
                try:
                    verify_plugin(client, project)
                    plugin = "enabled"
                except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                    plugin = str(error)
        resolved = report.get("resolved") or {}
        reports.append({"client": client, "scope": report.get("scope", scope or "auto"),
                        "root": report.get("root"), "configured": configured,
                        "status": report["status"] if configured or report.get("conflicts") else "unconfigured",
                        "team": resolved.get("team"), "profile": resolved.get("model_profile"),
                        "roles": state.get("installed_roles", []), "plugin": plugin, "dev_source": dev_source,
                        "conflicts": report.get("conflicts", [])})
    return {"version": version, "source": str(ROOT), "clients": reports}


def maintenance(args):
    project = (args.project or Path.cwd()).expanduser().absolute()
    clients = list(dict.fromkeys(([args.host] if args.host else []) + (args.clients or []))) or list(CONFIG.HOSTS)
    if args.action == "status":
        result = plex_status(project, clients, args.scope)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Plex {result['version']}\nSource: {result['source']}")
            for item in result["clients"]:
                print(f"\n{item['client']} ({item['scope']}): {item['status']}")
                print(f"  Team/profile: {item['team'] or '—'} / {item['profile'] or '—'}; plugin: {item['plugin']}")
                print(f"  Root: {item['root']}; native roles: {len(item['roles'])}")
                if item["dev_source"]:
                    print(f"  Development source: {item['dev_source']}")
                for conflict in item["conflicts"]:
                    print(f"  Conflict: {conflict}")
            print("\nConfiguration/plugin checks only; runtime model routing is not verified.")
        return int(any(item["conflicts"] or item["configured"] and
                       (item["status"] != "in_sync" or item["plugin"] not in {"enabled", "development"})
                       for item in result["clients"]))
    scope = args.scope or "project"
    dev_plan = (plan_dev(project, False) if scope == "project" and "codex" in clients
                and CONFIG._ensure_safe_project_path(project.resolve(), ".plex/dev.json").is_file() else None)
    plans = [CONFIG.uninstall_project(project, client, scope, dry_run=True) for client in clients]
    if dev_plan:
        for plan in plans:
            if plan["host"] == "codex":
                plan["remove_dev_links_and_override"] = True
    if args.dry_run:
        print(json.dumps(plans, indent=2))
        return 0
    if not args.yes:
        if not sys.stdin.isatty():
            raise ValueError("Use uninstall --dry-run to preview or uninstall --yes to confirm")
        for plan in plans:
            print(f"{plan['host']} ({scope}): {len(plan['removed_roles'])} owned roles")
        if input("Remove these Plex roles and owned instruction blocks? [y/N] ").strip().lower() not in {"y", "yes"}:
            print("Uninstall cancelled.")
            return 0
    results = []
    for client in clients:
        with apply_dev(dev_plan) if dev_plan and client == "codex" else nullcontext():
            results.append(CONFIG.uninstall_project(project, client, scope))
    print(json.dumps(results, indent=2))
    if not args.json:
        print("Shared plugins, source checkout, preset preferences and backups were retained.")
    return 0


def main(argv=None, *, shared_profile=False, selection=None, setup_mode=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=("setup", "status", "update", "uninstall"), default="setup")
    parser.add_argument("--json", action="store_true", help="Machine-readable status")
    parser.add_argument("--release", help="Published tag for update; defaults to newest published release")
    parser.add_argument("--development", action="store_true", help="Explicitly update to main")
    parser.add_argument("--project", type=Path, help="Existing target project directory")
    parser.add_argument("--client", dest="clients", action="append", choices=CONFIG.HOSTS,
                        help="Client to configure; repeat to select several")
    parser.add_argument("--host", choices=CONFIG.HOSTS, help="Compatibility alias for one --client")
    parser.add_argument("--scope", choices=("project", "user"), help="Role installation scope; default: project (recommended)")
    parser.add_argument("--instructions", action=argparse.BooleanOptionalAction, default=None,
                        help="Add/update the managed Plex block in the native instruction file (default: enabled)")
    parser.add_argument("--team", help="Work mode (role set); preserve current selection if omitted")
    parser.add_argument("--model-profile", help="Model profile; preserve current selection if omitted")
    parser.add_argument("--interaction", choices=CONFIG.INTERACTIONS,
                        help="Interaction mode: interactive, balanced (default), auto; preserve saved selection")
    parser.add_argument("--max-agents", type=int, help="Shared limit of concurrent Plex assignments (positive integer)")
    parser.add_argument("--install-bmad", action="store_true", help="Install the selected official BMad user skills; may replace selected skill files; project scope also initializes runtime")
    parser.add_argument("--init-bmad", action="store_true", help="Initialize missing project runtime using installed official BMad setup; --yes accepts module defaults")
    parser.add_argument("--bmad-skill", type=Path, help="Installed bmad setup skill directory; otherwise discover supported installed sources")
    parser.add_argument("--dev", action=argparse.BooleanOptionalAction, default=None,
                        help="Codex project: link this checkout as local Plex skills; --no-dev restores shared plugin discovery")
    parser.add_argument("--roles-only", action="store_true", help="Configure roles without installing the plugin")
    parser.add_argument("--command", action=argparse.BooleanOptionalAction, default=True,
                        help="Create ~/.local/bin/plex during full installation (default: enabled)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show planned commands and roles without writes")
    mode.add_argument("--install-command", action="store_true", help="Link this checkout as ~/.local/bin/plex")
    parser.add_argument("--yes", action="store_true", help="Apply without prompts; requires --client and --project for project scope")
    args = parser.parse_args(argv)
    if args.dev is not None and args.install_command:
        parser.error("--dev configures a project, not the user-wide command shortcut")
    if args.dev is not None and args.action != "setup":
        parser.error("--dev/--no-dev apply to setup; status and uninstall detect development mode automatically")
    if args.action in {"status", "uninstall", "update"}:
        try:
            if args.action == "update":
                spec = importlib.util.spec_from_file_location("plex_releases", ROOT / "skills/plex-setup/scripts/releases.py")
                release = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(release)
                forwarded = list(argv)
                forwarded.remove("update")
                return release.main(["--checkout", str(ROOT), *forwarded])
            return maintenance(args)
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            print(f"Plex {args.action} stopped: {error}", file=sys.stderr)
            return 1
        except (EOFError, KeyboardInterrupt):
            print("Plex maintenance interrupted; inspect the last reported state.", file=sys.stderr)
            return 130
    if args.release or args.development:
        parser.error("--release and --development require plex update")
    if args.team == "default":
        args.team = "pnet"
    interactive = sys.stdin.isatty() and not args.yes
    if not args.install_command and not interactive and (args.host is None and not args.clients or (args.project is None and args.scope != "user")):
        parser.error("Unattended runs require --project and --client (or --scope user)")
    if not args.install_command and not interactive and not (args.yes or args.dry_run):
        parser.error("Use --yes to apply, or --dry-run to preview without prompts")

    plugin_started = False
    host_overrides = None
    try:
        if args.install_command:
            install_command()
            return 0
        heading("pNet Plex  /  Setup")
        if args.dev:
            print("Development setup: this checkout supplies project-local Plex skills. No model calls.")
        else:
            print("One setup: shared Plex plugin + your selected team. No model calls.")
            print("The plugin supplies shared skills; team scope controls where roles and instructions are written.")
        clients = list(dict.fromkeys(([args.host] if args.host else []) + (args.clients or [])))
        if args.clients or not args.host or args.model_profile in CONFIG.PROFILE_TIERS:
            shared_profile = True
        if not clients:
            clients = choose_clients()
        if args.dev is not None and (clients != ["codex"] or args.scope == "user" or args.instructions is False):
            raise ValueError("--dev/--no-dev require one Codex client, project scope and managed instructions")
        if len(clients) > 1:
            return setup_clients(args, clients, interactive)
        args.host = clients[0]

        project = select_target(args, interactive)
        if args.dev is not None and args.scope != "project":
            raise ValueError("--dev/--no-dev require project scope")
        dev_receipt = CONFIG._ensure_safe_project_path(project, ".plex/dev.json") if args.scope == "project" else None
        dev_enabled = args.host == "codex" and (args.dev if args.dev is not None else bool(dev_receipt and dev_receipt.exists()))
        dev_plan = plan_dev(project, dev_enabled) if args.host == "codex" and args.scope == "project" and (dev_enabled or dev_receipt.exists()) else None
        if dev_enabled and args.instructions is False:
            raise ValueError("Development mode requires the managed AGENTS.md block")

        # Fail before configuration menus when the required host is unavailable.
        if not dev_enabled and not args.roles_only and not args.dry_run and not shutil.which(host_cli(args.host)):
            raise ValueError(f"{host_cli(args.host)} CLI not found. Install it or use --roles-only.")
        shortcut = command_destination(keep_existing=True) if not dev_enabled and not args.roles_only and args.command else None
        config_root = CONFIG.installation_root(project, args.host, args.scope)

        # Reuse the core path checks before reading or planning any managed file.
        preset = CONFIG._ensure_safe_project_path(config_root, ".plex/preset.toml")
        source_bytes = preset.read_bytes() if preset.is_file() else None
        existing = tomllib.loads(source_bytes.decode("utf-8")) if source_bytes is not None else None
        if existing is not None:
            CONFIG.resolve(existing)
        receipt_path = CONFIG._ensure_safe_project_path(config_root, ".plex/applied.json")
        receipt = CONFIG._validate_receipt_structure(json.loads(receipt_path.read_text()), args.scope) if receipt_path.is_file() else {"hosts": {}}
        installed = receipt["hosts"].get(args.host)
        if installed and interactive and setup_mode is None:
            changing = any(value is not None for value in (
                args.team, args.model_profile, args.interaction, args.max_agents, args.instructions, args.dev))
            setup_mode = choose("Existing Plex installation", {
                "refresh": "Update managed files; keep saved settings (explicit CLI overrides still apply)",
                "configure": "Reconfigure team, profile, interaction and concurrency",
            }, "configure" if changing else "refresh")
        if installed and not interactive and setup_mode is None:
            setup_mode = "refresh"
        configure_interactively = interactive and setup_mode != "refresh"
        if installed and setup_mode == "refresh" and args.instructions is None:
            args.instructions = dev_enabled or bool(installed.get("instructions"))
        def saved_profile(config):
            return config.get("model_profile", "inherit")

        def build_candidate(profile, **overrides):
            return CONFIG.build_preset_toml(
                existing, args.team, profile, interaction=args.interaction,
                **overrides,
            )

        catalog = CONFIG.list_catalog()
        if configure_interactively:
            if args.team is None:
                choices = {
                    name: ("Standalone" if name == "pnet" else "Requires BMad skills + project runtime")
                    + ": " + ", ".join(catalog["teams"][name]["roles"])
                    for name in sorted(catalog["teams"], key=lambda name: (name != "pnet", name))
                }
                current = CONFIG.resolve(existing)["team"] if existing else "pnet"
                if current is None:
                    choices["keep-custom"] = "Keep the current custom team"
                    current = "keep-custom"
                selected = choose("Work mode", choices, current)
                args.team = None if selected in {"keep-custom", current} and existing else selected
        preview_profile = args.model_profile
        if configure_interactively and preview_profile is None and existing:
            selected_team = args.team or CONFIG.resolve(existing)["team"] or (
                "bmad" if existing.get("process") == "bmad" else "pnet")
            if saved_profile(existing) not in catalog["model_profiles"][selected_team]:
                print("The saved model profile is unavailable in the selected team. Choose a profile below.")
                preview_profile = "inherit"
        candidate = build_candidate(preview_profile, max_agents=args.max_agents)
        team_config = tomllib.loads(candidate)
        bmad_init = None
        if CONFIG.resolve(team_config)["process"] == "bmad" and args.install_bmad and not args.dry_run:
            plugin_started = True
            install_bmad_dependencies(project, args.host)
        if (CONFIG.resolve(team_config)["process"] == "bmad" and args.scope == "project"
                and not args.dry_run and not bmad_runtime_ready(project)):
            action = "init" if args.init_bmad or args.install_bmad else None
            if action is None and interactive:
                action = choose("BMad project runtime is missing or incomplete", {
                    "init": "Initialize with installed official BMad setup (no model calls)",
                    **({"pnet": "Use pnet without BMad"} if setup_mode != "refresh" else {}),
                    "cancel": "Cancel without changes",
                }, "init")
            if action == "cancel":
                if selection is not None:
                    selection["cancelled"] = True
                print("Cancelled. No changes.")
                return 0
            if action == "pnet":
                args.team = "pnet"
                candidate = build_candidate(preview_profile, max_agents=args.max_agents)
                team_config = tomllib.loads(candidate)
            elif action == "init":
                try:
                    bmad_init = plan_bmad_init(project, args.host, args.bmad_skill, interactive)
                except BMadNotInstalled:
                    if not interactive or args.install_bmad:
                        raise
                    print("Official BMad setup is missing. Install the selected user skills; this may replace selected skill files and affects other projects. Existing plugins remain unchanged.")
                    if choose("Install required official BMad skills for this user?", {
                        "yes": "Install the team skill set, then initialize this project",
                        "no": "Cancel; keep user skills and project unchanged",
                    }, "yes") != "yes":
                        if selection is not None:
                            selection["cancelled"] = True
                        return 0
                    plugin_started = True
                    install_bmad_dependencies(project, args.host)
                    bmad_init = plan_bmad_init(project, args.host, args.bmad_skill, interactive)
            else:
                raise ValueError(
                    "BMad runtime is missing or incomplete. No changes made.\n"
                    "Rerun with --init-bmad to initialize it using installed official BMad setup, "
                    "or run the official bmad skill's 'bmad setup' in this project.\n"
                    "Choose team pnet to use Plex without BMad."
                )
        if configure_interactively:
            if args.model_profile is None:
                choices = {}
                profile_team = team_config.get("team") or ("bmad" if team_config.get("process") == "bmad" else "pnet")
                for name in sorted(catalog["model_profiles"][profile_team], key=CONFIG.profile_sort_key):
                    if shared_profile and name not in ("inherit", *CONFIG.PROFILE_TIERS):
                        continue
                    if not shared_profile and name in CONFIG.PROFILE_TIERS:
                        continue
                    if name != "inherit" and args.host not in catalog["model_profiles"][profile_team][name]:
                        continue
                    settings = CONFIG.resolve({**team_config, "model_profile": name, **{h: {} for h in CONFIG.HOSTS}})
                    if name != "inherit" and not any(
                        v.get("model", "inherit") != "inherit" or "reasoning" in v
                        for v in settings["hosts"][args.host].values()
                    ):
                        continue
                    groups = {}
                    for role, values in settings["hosts"][args.host].items():
                        model = values.get("model", "inherit")
                        label = "user/session default model and reasoning" if model == "inherit" else model
                        if values.get("reasoning"):
                            label += " / " + values["reasoning"]
                        groups.setdefault(label, []).append(role)
                    choices[name] = "; ".join(f"{', '.join(roles)}: {label}" for label, roles in groups.items())
                print("\nProfile defaults for this team and client; existing project overrides still apply.")
                if not shared_profile:
                    choices["custom"] = "Choose model and reasoning for each agent"
                current_profile = saved_profile(existing) if existing else "inherit"
                current = current_profile
                if current not in choices:
                    current = next((tier for tier in sorted(CONFIG.PROFILE_TIERS, key=len, reverse=True)
                                    if current_profile.endswith(f"-{tier}") and tier in choices), "inherit") if shared_profile else "custom"
                if not shared_profile and any(isinstance(v, dict) and v for v in team_config.get(args.host, {}).values()):
                    current = "custom"
                selected = choose(
                    "Model profile", choices, current,
                )
                if selected == "custom":
                    host_overrides = customize_roles(team_config, args.host, project)
                    if preview_profile is not None:
                        args.model_profile = preview_profile
                else:
                    args.model_profile = None if existing and selected == current_profile else selected
        candidate = build_candidate(args.model_profile,
                                             max_agents=args.max_agents, host_overrides=host_overrides)
        resolved = CONFIG.resolve(tomllib.loads(candidate))
        if (shared_profile and resolved["model_profile"] not in ("inherit", *CONFIG.PROFILE_TIERS)
                and not (setup_mode == "refresh" and existing
                         and resolved["model_profile"] == saved_profile(existing))):
            raise ValueError("Choose one shared profile: inherit, basic, plus, pro or pro-plus; client-specific profiles remain available through legacy --host setup")
        if configure_interactively and args.interaction is None:
            args.interaction = choose("Interaction mode", {
                "interactive": "Ask about meaningful choices; collaborate step by step",
                "balanced": "Resolve routine choices; ask only for consequential decisions (recommended)",
                "auto": "Do not wait for answers; report blockers and continue independent work",
            }, resolved["interaction"])
            candidate = build_candidate(args.model_profile,
                                        max_agents=args.max_agents, host_overrides=host_overrides)
            resolved = CONFIG.resolve(tomllib.loads(candidate))
        if configure_interactively and args.max_agents is None:
            print("\nOne shared limit for concurrent Plex assignments across all roles. Client limits still apply.")
            while True:
                answer = ask_text("Parallel agents", str(resolved["max_agents"])).strip()
                try:
                    limit = int(answer)
                    if limit > 0:
                        break
                except ValueError:
                    pass
                print("Enter a positive whole number.")
            args.max_agents = limit
            candidate = build_candidate(args.model_profile,
                                                 max_agents=limit, host_overrides=host_overrides)
            resolved = CONFIG.resolve(tomllib.loads(candidate))
        rendered = CONFIG.render_host_roles(resolved, args.host, args.scope)
        if not args.roles_only and not args.dry_run and args.host == "codex" and os.environ.get("CODEX_HOME"):
            profile = Path(os.environ["CODEX_HOME"]).expanduser()
            if not profile.is_dir():
                raise ValueError(f"CODEX_HOME directory does not exist: {profile}. Create the test profile directory first.")
        state = CONFIG.check_project(project, args.host, args.scope)
        if state["conflicts"]:
            raise ValueError("\n".join(state["conflicts"]))

        refresh_clients = [args.host]
        if shared_profile and args.scope == "project":
            receipt_path = CONFIG._ensure_safe_project_path(config_root, ".plex/applied.json")
            receipt = CONFIG._validate_receipt_structure(json.loads(receipt_path.read_text())) if receipt_path.is_file() else {"hosts": {}}
            for client in receipt["hosts"]:
                if client != args.host:
                    if state["hosts"][client]["conflicts"]:
                        raise ValueError("; ".join(state["hosts"][client]["conflicts"]))
                    refresh_clients.append(client)

        instruction_path = CONFIG.instruction_relpath(config_root, args.host, args.scope) if args.instructions is not False else None
        if args.instructions is None:
            args.instructions = True
        instruction_plan = None
        if args.instructions:
            receipt_path = CONFIG._ensure_safe_project_path(config_root, ".plex/applied.json")
            receipt = CONFIG._validate_receipt_structure(json.loads(receipt_path.read_text()), args.scope) if receipt_path.is_file() else {"hosts": {}}
            record = receipt["hosts"].get(args.host, {}).get("instructions")
            instruction_plan = CONFIG.plan_instructions(config_root, args.host, args.scope, record, dev=dev_enabled)

        heading("Plan")
        if setup_mode == "refresh":
            print("  Update existing installation; saved settings retained unless explicitly overridden.")
        print(f"  Client        {args.host}\n  Team scope    {args.scope}\n  Settings      {config_root / '.plex'}")
        if args.scope == "project":
            print(f"  Project       {project}")
        print(f"  Agent files   {config_root / CONFIG.host_agents_relpath(args.host, args.scope)}")
        if shortcut:
            print(f"  Command       {shortcut}")
        if state.get("resolved"):
            for other in CONFIG.HOSTS:
                other_state = state["hosts"][other]
                if other not in refresh_clients and (other_state.get("installed_roles") or other_state.get("outdated_roles")):
                    if (state["resolved"]["hosts"][other] != resolved["hosts"][other]
                            or state["resolved"]["roles"] != resolved["roles"]):
                        print(f"  Warning: shared team/profile changes also affect {other}; its files are not refreshed by this run.")
        if args.scope == "user":
            local = CONFIG.check_project(project, args.host)
            if local.get("preset_exists") or local.get("hosts", {}).get(args.host, {}).get("installed_roles") or local.get("conflicts"):
                print("  Existing project configuration/roles may override user defaults; they will be preserved.")
        if instruction_plan:
            print(f"  Instructions {instruction_plan['path']} (Plex block only)")
            print(CONFIG.instruction_block(dev=dev_enabled).decode())
        print(f"  Mode     {resolved['team'] or 'custom'}\n  Profile  {resolved['model_profile']}")
        if len(refresh_clients) > 1:
            print(f"  Shared team/profile: refresh configured clients {', '.join(refresh_clients)}")
        print(f"  Interaction {resolved['interaction']}")
        print(f"  Limit    {resolved['max_agents']} concurrent assignments")
        for role, settings in resolved["hosts"][args.host].items():
            print(f"  plex-{role:<12} {settings.get('model', 'inherit'):<18} "
                  f"{settings.get('reasoning', '')}")
        if resolved["inactive_overrides"][args.host]:
            print("  Inactive overrides: " + ", ".join(resolved["inactive_overrides"][args.host]))
        for role in state["hosts"][args.host].get("installed_roles", []):
            if role not in rendered:
                print(f"  Archive  plex-{role}")
        commands = [] if args.roles_only or dev_enabled else plugin_commands(args.host, args.scope)
        if dev_enabled:
            print(f"  Development source: {ROOT}")
            print("  Project skills: .agents/skills/plex, .agents/skills/plex-setup (live symlinks)")
            print("  Shared Plex plugin: disabled only in this trusted project; other projects unchanged.")
        elif dev_plan:
            print("  Leave development mode: remove owned links and restore project plugin discovery.")
        if commands:
            print("\n  Shared plugin: installed for this user/client profile; skills are not copied into the project.")
            print(f"  Shared source: {ROOT} (keep this directory after installation)")
            print("  Native plugin installation:")
            for command in commands:
                print("    " + shlex.join(command))

        print("  Roles, instructions, snapshot and receipt use the existing backup/rollback mechanism.")
        if resolved["process"] == "bmad":
            print("  BMad: verify runtime and active skills in each working project before use.")
        if selection is not None:
            selection.update(setup_mode=setup_mode, instructions=args.instructions, team=resolved["team"], max_agents=resolved["max_agents"], model_profile=resolved["model_profile"], interaction=resolved["interaction"])
        if bmad_init:
            print(f"  BMad init {bmad_init['skill']} -> {project / '_bmad'} (official setup)")
        if args.dry_run:
            if resolved["process"] == "bmad" and args.install_bmad:
                print("  BMad selected user-skill installation plan (existing selected skill files may be replaced):")
                for command in bmad_install_commands(args.host):
                    print("    " + shlex.join(command))
            if resolved["process"] == "bmad" and args.scope == "project" and not bmad_runtime_ready(project):
                print("  BMad runtime is missing: normal setup will offer official initialization.")
            print("\nPreview only. No files or plugins changed.")
            return 0

        if interactive and choose("Apply this plan?", {"no": "Cancel without changes", "yes": "Apply"}, "no") != "yes":
            if selection is not None:
                selection["cancelled"] = True
            print("Cancelled. No changes.")
            return 0

        if bmad_init:
            initialize_bmad(project, bmad_init)
        if resolved["process"] == "bmad" and args.scope == "project":
            run([sys.executable, str(project / "_bmad/scripts/resolve_config.py"),
                 "--project-root", str(project)], project)
        if commands:
            heading("1 / 2  Install native plugin")
            build_plugin(args.host)
            plugin_started = True
            for command in commands:
                run(command, project)
            if not dev_plan:
                verify_plugin(args.host, project)
            print("  OK: shared plugin installed.")
        heading(f"2 / 2  Apply {args.scope} roles" if commands else f"Apply {args.scope} roles")
        if (preset.read_bytes() if preset.is_file() else None) != source_bytes:
            raise ValueError("Project settings changed after preview; review the new settings and retry.")
        if instruction_plan:
            current = instruction_plan["path"].read_bytes() if instruction_plan["path"].is_file() else None
            if current != instruction_plan["before"]:
                raise ValueError("Instruction file changed after preview; review and retry.")
        with apply_dev(dev_plan) if dev_plan else nullcontext():
            result = CONFIG.apply_project(project, args.host, args.team, args.model_profile,
                                          max_agents=args.max_agents, host_overrides=host_overrides, interaction=args.interaction,
                                          scope=args.scope, instructions=args.instructions)
        for client in refresh_clients:
            if client != args.host:
                other_instructions = bool(receipt["hosts"][client].get("instructions")) if setup_mode == "refresh" else args.instructions
                CONFIG.apply_project(project, client, scope=args.scope, instructions=other_instructions)
        for client in refresh_clients:
            if CONFIG.check_project(project, client, args.scope)["status"] != "in_sync":
                raise ValueError(f"Post-install check failed for client {client}")
        if commands and dev_plan:
            verify_plugin(args.host, project)
        print(f"  OK: {len(result['installed_roles'])} roles; configuration in sync.")
        if result["backup_dir"]:
            print(f"  Backups: {config_root / result['backup_dir']}")
        others = [client for client in result.get("other_hosts_needing_refresh", []) if client not in refresh_clients]
        if others:
            print(f"  Refresh the other clients: {', '.join(others)}")
        if resolved["process"] == "bmad":
            print("  BMad roles registered; run plex-setup in the host to verify active skill bindings.")
        if shortcut:
            install_command()
        print("\nSetup complete. No separate plex-setup step is needed for this team configuration.")
        print("Reload the host's plugins/agents. Invoke the plex skill when you want coordinated work.")
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"\nSetup stopped: {error}", file=sys.stderr)
        if plugin_started:
            print("Shared dependencies or native plugin state may have changed; inspect before retrying.", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nSetup interrupted. Check project state if application had started.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
