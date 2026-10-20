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
                  "basic": "Basic", "plus": "Plus", "pro": "Pro", "pro-plus": "Pro+"}
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


def command_destination():
    destination = Path.home() / ".local/bin/plex"
    if destination.is_symlink() and destination.resolve() in {ROOT / "setup.py", ROOT / "setup.sh"}:
        return destination
    if destination.exists() or destination.is_symlink():
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
        if args.instructions is not None:
            options.append("--instructions" if args.instructions else "--no-instructions")
        selection = {}
        status = main(options, shared_profile=True, selection=selection)
        if status or selection.get("cancelled"):
            print(f"Stopped at {client}. Completed clients: {', '.join(completed) or 'none'}. Rerun to continue.")
            return status
        completed.append(client)
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
            CONFIG.apply_project(project, client, scope=args.scope, instructions=args.instructions is not False)
        for client in clients:
            if CONFIG.check_project(project, client, args.scope)["status"] != "in_sync":
                raise ValueError(f"Final check failed for client {client}; rerun setup")
        print(f"All selected clients are in sync: {', '.join(completed)}.")
    return 0


def plex_status(project, clients, scope=None):
    version = json.loads((ROOT / "plugins/codex/.codex-plugin/plugin.json").read_text())["version"]
    reports = []
    for client in clients:
        report = CONFIG.check_project(project, client, scope or "auto")
        state = report.get("hosts", {}).get(client, {})
        configured = state.get("configured", False)
        plugin = "not_checked"
        if configured:
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
                        "roles": state.get("installed_roles", []), "plugin": plugin,
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
                for conflict in item["conflicts"]:
                    print(f"  Conflict: {conflict}")
            print("\nConfiguration/plugin checks only; runtime model routing is not verified.")
        return int(any(item["conflicts"] or item["configured"] and
                       (item["status"] != "in_sync" or item["plugin"] != "enabled")
                       for item in result["clients"]))
    scope = args.scope or "project"
    plans = [CONFIG.uninstall_project(project, client, scope, dry_run=True) for client in clients]
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
    results = [CONFIG.uninstall_project(project, client, scope) for client in clients]
    print(json.dumps(results, indent=2))
    if not args.json:
        print("Shared plugins, source checkout, preset preferences and backups were retained.")
    return 0


def main(argv=None, *, shared_profile=False, selection=None):
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
    parser.add_argument("--roles-only", action="store_true", help="Configure roles without installing the plugin")
    parser.add_argument("--command", action=argparse.BooleanOptionalAction, default=True,
                        help="Create ~/.local/bin/plex during full installation (default: enabled)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show planned commands and roles without writes")
    mode.add_argument("--install-command", action="store_true", help="Link this checkout as ~/.local/bin/plex")
    parser.add_argument("--yes", action="store_true", help="Apply without prompts; requires --client and --project for project scope")
    args = parser.parse_args(argv)
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
        print("One setup: shared Plex plugin + your selected team. No model calls.")
        print("The plugin supplies shared skills; team scope controls where roles and instructions are written.")
        clients = list(dict.fromkeys(([args.host] if args.host else []) + (args.clients or [])))
        if args.clients or not args.host or args.model_profile in CONFIG.PROFILE_TIERS:
            shared_profile = True
        if not clients:
            clients = choose_clients()
        if len(clients) > 1:
            return setup_clients(args, clients, interactive)
        args.host = clients[0]

        # Fail before configuration menus when the required host is unavailable.
        if not args.roles_only and not args.dry_run and not shutil.which(host_cli(args.host)):
            raise ValueError(f"{host_cli(args.host)} CLI not found. Install it or use --roles-only.")
        shortcut = command_destination() if not args.roles_only and args.command else None
        project = select_target(args, interactive)
        config_root = CONFIG.installation_root(project, args.host, args.scope)

        # Reuse the core path checks before reading or planning any managed file.
        preset = CONFIG._ensure_safe_project_path(config_root, ".plex/preset.toml")
        source_bytes = preset.read_bytes() if preset.is_file() else None
        existing = tomllib.loads(source_bytes.decode("utf-8")) if source_bytes is not None else None
        if existing is not None:
            CONFIG.resolve(existing)
        def saved_profile(config):
            return config.get("model_profile", "inherit")

        def build_candidate(profile, **overrides):
            return CONFIG.build_preset_toml(
                existing, args.team, profile, interaction=args.interaction,
                **overrides,
            )

        catalog = CONFIG.list_catalog()
        if interactive:
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
        if interactive and preview_profile is None and existing:
            selected_team = args.team or CONFIG.resolve(existing)["team"] or (
                "bmad" if existing.get("process") == "bmad" else "pnet")
            if saved_profile(existing) not in catalog["model_profiles"][selected_team]:
                print("The saved model profile is unavailable in the selected team. Choose a profile below.")
                preview_profile = "inherit"
        candidate = build_candidate(preview_profile, max_agents=args.max_agents)
        team_config = tomllib.loads(candidate)
        if CONFIG.resolve(team_config)["process"] == "bmad" and args.scope == "project" and not args.dry_run:
            for name in ("resolve_config.py", "resolve_customization.py", "render_skill.py"):
                if not (project / "_bmad/scripts" / name).is_file():
                    raise ValueError(
                        "BMad runtime is missing or incomplete. No changes made.\n"
                        f"Open {args.host} in {project} and ask the official bmad-toolbox bmad skill "
                        "to run 'bmad setup', then rerun plex.\n"
                        "Or choose work mode 'pnet' to use Plex without BMad."
                    )
        if interactive:
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
        if shared_profile and resolved["model_profile"] not in ("inherit", *CONFIG.PROFILE_TIERS):
            raise ValueError("Choose one shared profile: inherit, basic, plus, pro or pro-plus; client-specific profiles remain available through legacy --host setup")
        if interactive and args.max_agents is None:
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
            instruction_plan = CONFIG.plan_instructions(config_root, args.host, args.scope, record)

        heading("Plan")
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
            print(CONFIG.instruction_block().decode())
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
        commands = [] if args.roles_only else plugin_commands(args.host, args.scope)
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
            selection.update(team=resolved["team"], max_agents=resolved["max_agents"], model_profile=resolved["model_profile"], interaction=resolved["interaction"])
        if args.dry_run:
            print("\nPreview only. No files or plugins changed.")
            return 0

        if interactive and choose("Apply this plan?", {"no": "Cancel without changes", "yes": "Apply"}, "no") != "yes":
            if selection is not None:
                selection["cancelled"] = True
            print("Cancelled. No changes.")
            return 0

        if resolved["process"] == "bmad" and args.scope == "project":
            run([sys.executable, str(project / "_bmad/scripts/resolve_config.py"),
                 "--project-root", str(project)], project)
        if commands:
            heading("1 / 2  Install native plugin")
            build_plugin(args.host)
            plugin_started = True
            for command in commands:
                run(command, project)
            verify_plugin(args.host, project)
            print("  OK: shared plugin installed and enabled.")
        heading(f"2 / 2  Apply {args.scope} roles" if commands else f"Apply {args.scope} roles")
        if (preset.read_bytes() if preset.is_file() else None) != source_bytes:
            raise ValueError("Project settings changed after preview; review the new settings and retry.")
        if instruction_plan:
            current = instruction_plan["path"].read_bytes() if instruction_plan["path"].is_file() else None
            if current != instruction_plan["before"]:
                raise ValueError("Instruction file changed after preview; review and retry.")
        result = CONFIG.apply_project(project, args.host, args.team, args.model_profile,
                                      max_agents=args.max_agents, host_overrides=host_overrides, interaction=args.interaction,
                                      scope=args.scope, instructions=args.instructions)
        for client in refresh_clients:
            if client != args.host:
                CONFIG.apply_project(project, client, scope=args.scope, instructions=args.instructions)
        for client in refresh_clients:
            if CONFIG.check_project(project, client, args.scope)["status"] != "in_sync":
                raise ValueError(f"Post-install check failed for client {client}")
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
            print("Native manager may have changed marketplace/plugin state; inspect it before retrying.", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nSetup interrupted. Check project state if application had started.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
