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
import tomllib


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "plex_config", ROOT / "skills/plex-setup/scripts/resolve_config.py"
)
CONFIG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIG)


def heading(text):
    color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    print(f"\n\033[1;36m{text}\033[0m" if color else f"\n{text}", flush=True)


def choose(label, choices, default):
    ui = terminal_ui()
    if ui:
        labels = {"__default__": "Default", "__manual__": "Other model…", "__done__": "Done",
                  "inherit": "Inherit session settings", "custom": "Custom"}
        if label == "Model profile":
            for name in choices:
                vendor, _, tier = name.partition("-")
                if tier in CONFIG.PROFILE_TIERS:
                    title = {"openai": "OpenAI", "anthropic": "Anthropic", "google": "Google"}.get(vendor, vendor.title())
                    labels[name] = f"{title} · " + ("Pro+" if tier == "pro-plus" else tier.title())
        return ui.select(label, choices=[ui.Choice(
            labels.get(name, name) if label == "Model profile" else f"{labels.get(name, name)}  {detail}",
            value=name, description=detail if label == "Model profile" else None)
                                        for name, detail in choices.items()], default=default).unsafe_ask()
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
        return {name: {} for name in CONFIG.ANTIGRAVITY_MODELS}
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
        for name in CONFIG.list_catalog()["model_profiles"]:
            profile = CONFIG.named_file("model-profiles", name).get(host, {})
            for value in (profile, *(v for v in profile.values() if isinstance(v, dict))):
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


def plugin_commands(host):
    if host == "codex":
        return [
            ["codex", "plugin", "marketplace", "add", str(ROOT), "--json"],
            ["codex", "plugin", "add", "pnet-plex@pnet-plex", "--json"],
        ]
    if host == "antigravity":
        return [
            ["agy", "plugin", "install", str(ROOT)],
        ]
    return [
        ["claude", "plugin", "marketplace", "add", str(ROOT)],
        ["claude", "plugin", "install", "pnet-plex@pnet-plex", "--scope", "project"],
    ]


def run(command, project):
    result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=120)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise ValueError(f"{shlex.join(command)}\n{detail}")
    return result.stdout


def install_command():
    if not shutil.which("uv"):
        raise ValueError("Install uv before installing the plex command (https://docs.astral.sh/uv/).")
    destination = Path.home() / ".local/bin/plex"
    source = ROOT / "setup.py"
    if destination.is_symlink() and destination.resolve() == source:
        pass
    elif destination.exists() or destination.is_symlink():
        raise ValueError(f"Command already exists; left unchanged: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(source)
    print(f"Command ready: {destination}\nRun plex from any project directory.")
    if str(destination.parent) not in os.environ.get("PATH", "").split(os.pathsep):
        print('Add this to your shell configuration: export PATH="$HOME/.local/bin:$PATH"')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, help="Existing target project directory")
    parser.add_argument("--host", choices=CONFIG.HOSTS)
    parser.add_argument("--team", help="Work mode (role set); preserve current selection if omitted")
    parser.add_argument("--model-profile", help="Model profile; preserve current selection if omitted")
    parser.add_argument("--max-agents", type=int, help="Shared limit of concurrent Plex assignments (positive integer)")
    parser.add_argument("--roles-only", action="store_true", help="Configure roles without installing the plugin")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show planned commands and roles without writes")
    mode.add_argument("--install-command", action="store_true", help="Link this checkout as ~/.local/bin/plex")
    parser.add_argument("--yes", action="store_true", help="Apply without prompts; requires --project and --host")
    args = parser.parse_args(argv)
    interactive = sys.stdin.isatty() and not args.yes
    if not args.install_command and not interactive and (args.project is None or args.host is None):
        parser.error("Unattended runs require --project and --host")
    if not args.install_command and not interactive and not (args.yes or args.dry_run):
        parser.error("Use --yes to apply, or --dry-run to preview without prompts")

    plugin_started = False
    host_overrides = None
    try:
        if args.install_command:
            install_command()
            return 0
        heading("pNet Plex  /  Setup")
        print("Work mode + model profile → native project agents. No LLM calls.")
        if args.project is None:
            args.project = Path(ask_text("Project directory", str(Path.cwd())))
        project = args.project.expanduser().absolute()
        if not project.is_dir():
            raise ValueError(f"Project directory does not exist: {project}")
        if args.host is None:
            args.host = choose(
                "Host",
                {"codex": "Codex", "claude": "Claude Code", "antigravity": "Antigravity (agy)"},
                "codex",
            )

        # Reuse the core path checks before reading or planning any project file.
        preset = CONFIG._ensure_safe_project_path(project, ".plex/preset.toml")
        source_bytes = preset.read_bytes() if preset.is_file() else None
        existing = tomllib.loads(source_bytes.decode("utf-8")) if source_bytes is not None else None
        if existing is not None:
            CONFIG.resolve(existing)
        catalog = CONFIG.list_catalog()
        if interactive:
            if args.team is None:
                choices = {
                    name: ("Standalone" if name == "default" else "Requires BMad skills + project runtime")
                    + ": " + ", ".join(catalog["teams"][name]["roles"])
                    for name in sorted(catalog["teams"], key=lambda name: (name != "default", name))
                }
                current = existing.get("team") if existing else "default"
                if current is None:
                    choices["keep-custom"] = "Keep the current custom team"
                    current = "keep-custom"
                selected = choose("Work mode", choices, current)
                args.team = None if selected in {"keep-custom", current} and existing else selected
        candidate = CONFIG.build_preset_toml(existing, args.team, args.model_profile, max_agents=args.max_agents)
        team_config = tomllib.loads(candidate)
        if CONFIG.resolve(team_config)["process"] == "bmad" and not args.dry_run:
            for name in ("resolve_config.py", "resolve_customization.py", "render_skill.py"):
                if not (project / "_bmad/scripts" / name).is_file():
                    raise ValueError(
                        "BMad runtime is missing or incomplete. No changes made.\n"
                        f"Open {args.host} in {project} and ask the official bmad-toolbox bmad skill "
                        "to run 'bmad setup', then rerun plex.\n"
                        "Or choose work mode 'default' to use Plex without BMad."
                    )
        if interactive:
            if args.model_profile is None:
                choices = {}
                for name in sorted(catalog["model_profiles"], key=CONFIG.profile_sort_key):
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
                print("\nProfile defaults for this mode and host; existing project overrides still apply.")
                choices["custom"] = "Choose model and reasoning for each agent"
                saved_profile = existing.get("model_profile", "inherit") if existing else "inherit"
                current = saved_profile
                if current not in choices:
                    current = "custom"
                if any(isinstance(v, dict) and v for v in team_config.get(args.host, {}).values()):
                    current = "custom"
                selected = choose(
                    "Model profile", choices, current,
                )
                if selected == "custom":
                    host_overrides = customize_roles(team_config, args.host, project)
                else:
                    args.model_profile = None if existing and selected == saved_profile else selected
        candidate = CONFIG.build_preset_toml(existing, args.team, args.model_profile,
                                             max_agents=args.max_agents, host_overrides=host_overrides)
        resolved = CONFIG.resolve(tomllib.loads(candidate))
        if interactive and args.max_agents is None:
            print("\nOne shared limit for concurrent Plex assignments across all roles. Host limits still apply.")
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
            candidate = CONFIG.build_preset_toml(existing, args.team, args.model_profile,
                                                 max_agents=limit, host_overrides=host_overrides)
            resolved = CONFIG.resolve(tomllib.loads(candidate))
        rendered = CONFIG.render_host_roles(resolved, args.host)
        # CLI availability is needed only for native plugin installation.
        cli = host_cli(args.host)
        if not args.roles_only and not args.dry_run and not shutil.which(cli):
            raise ValueError(f"{cli} CLI not found. Install it or use --roles-only.")
        if not args.roles_only and not args.dry_run and args.host == "codex" and os.environ.get("CODEX_HOME"):
            profile = Path(os.environ["CODEX_HOME"]).expanduser()
            if not profile.is_dir():
                raise ValueError(f"CODEX_HOME directory does not exist: {profile}. Create the test profile directory first.")
        state = CONFIG.check_project(project, args.host)
        if state["conflicts"]:
            raise ValueError("\n".join(state["conflicts"]))

        heading("Plan")
        print(f"  Project  {project}\n  Host     {args.host}")
        print(f"  Mode     {resolved['team'] or 'custom'}\n  Profile  {resolved['model_profile']}")
        print(f"  Limit    {resolved['max_agents']} concurrent assignments")
        for role, settings in resolved["hosts"][args.host].items():
            print(f"  plex-{role:<12} {settings.get('model', 'inherit'):<18} "
                  f"{settings.get('reasoning', '')}")
        if resolved["inactive_overrides"][args.host]:
            print("  Inactive overrides: " + ", ".join(resolved["inactive_overrides"][args.host]))
        for role in state["hosts"][args.host].get("installed_roles", []):
            if role not in rendered:
                print(f"  Archive  plex-{role}")
        commands = [] if args.roles_only else plugin_commands(args.host)
        if commands:
            print("\n  Native plugin installation:")
            for command in commands:
                print("    " + shlex.join(command))
            print("  Codex: active CODEX_HOME/profile. Claude: project scope; marketplace is user-level. Antigravity: ~/.gemini/config/plugins.")
        print("  Project roles, snapshot and receipt use the existing backup/rollback mechanism.")
        if resolved["process"] == "bmad":
            print("  BMad: existing runtime required; active skills must be verified via plex-setup.")
        if args.dry_run:
            print("\nPreview only. No files or plugins changed.")
            return 0

        if interactive and choose("Apply this plan?", {"no": "Cancel without changes", "yes": "Apply"}, "no") != "yes":
            print("Cancelled. No changes.")
            return 0

        if resolved["process"] == "bmad":
            run([sys.executable, str(project / "_bmad/scripts/resolve_config.py"),
                 "--project-root", str(project)], project)
        if commands:
            heading("1 / 2  Install native plugin")
            plugin_started = True
            for command in commands:
                run(command, project)
            print("  Native plugin manager completed.")
        heading("2 / 2  Apply project roles" if commands else "Apply project roles")
        if (preset.read_bytes() if preset.is_file() else None) != source_bytes:
            raise ValueError("Project settings changed after preview; review the new settings and retry.")
        result = CONFIG.apply_project(project, args.host, args.team, args.model_profile,
                                      max_agents=args.max_agents, host_overrides=host_overrides)
        verified = CONFIG.check_project(project, args.host)
        if verified["status"] != "in_sync":
            raise ValueError(f"Post-install check: {verified['status']}")
        print(f"  OK: {len(result['installed_roles'])} roles; configuration in sync.")
        if result["backup_dir"]:
            print(f"  Backups: {project / result['backup_dir']}")
        if result["other_host"]["needs_refresh"]:
            others = result.get("other_hosts_needing_refresh") or [result["other_host"]["host"]]
            print(f"  Refresh the other host: {', '.join(others)}")
        if resolved["process"] == "bmad":
            print("  BMad roles registered; run plex-setup in the host to verify active skill bindings.")
        print("\nReload the host's plugins/agents before testing Plex.")
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
