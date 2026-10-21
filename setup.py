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
import textwrap
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
    ("choice-title", "bold"),
    ("description", "fg:#808080"),
    ("answer", "fg:#06b6d4 bold"),
    ("question", "bold"),
    ("instruction", "fg:#808080"),
]


def style(text, tone="bold", *, file=None):
    stream = sys.stdout if file is None else file
    colors = {"title": "1;36", "bold": "1", "muted": "2", "ok": "1;32",
              "warn": "1;33", "error": "1;31", "command": "36"}
    if stream.isatty() and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb":
        return f"\033[{colors[tone]}m{text}\033[0m"
    return str(text)


def heading(text):
    width = min(64, max(20, shutil.get_terminal_size().columns - 2))
    print("\n" + style(text, "title") + "\n" + style("─" * width, "muted"), flush=True)


def field(label, value, tone="bold"):
    prefix = f"  {label:<14}  "
    value = str(value).replace("\n", "\n" + " " * len(prefix))
    print(style(prefix, "muted") + style(value, tone))


def notice(text, tone="muted", *, file=None):
    stream = sys.stdout if file is None else file
    labels = {"ok": "OK", "warn": "WARN", "error": "ERROR", "muted": "INFO"}
    prefix = f"[{labels[tone]}] "
    width = max(16, shutil.get_terminal_size().columns - len(prefix) - 2)
    lines = "\n".join(textwrap.fill(line, width=width, break_long_words=False,
                                  break_on_hyphens=False) for line in str(text).splitlines())
    print("  " + style(prefix, tone, file=stream) + lines.replace("\n", "\n  " + " " * len(prefix)), file=stream)


def show_command(command):
    text = shlex.join(command) if isinstance(command, (list, tuple)) else command
    print("    " + style("$ ", "muted") + style(text, "command"))


def role_table(roles):
    rows = [(f"plex-{role}", values.get("model", "inherit"), values.get("reasoning", "session default"))
            for role, values in roles.items()]
    headers = ("SUBAGENT", "MODEL", "REASONING")
    widths = [max(len(row[i]) for row in [headers, *rows]) for i in range(3)]
    print()
    if sum(widths) + 8 > shutil.get_terminal_size().columns:
        for name, model, reasoning in rows:
            print("  " + style(name) + "\n    " + style(f"{model} / {reasoning}", "command"))
    else:
        print("  " + style("  ".join(value.ljust(width) for value, width in zip(headers, widths)), "muted"))
        for name, model, reasoning in rows:
            print("  " + style(name.ljust(widths[0])) + "  " + style(model.ljust(widths[1]), "command")
                  + "  " + style(reasoning, "muted"))


def coordinator_summary(resolved, host):
    recommendation = resolved["coordinator"].get(host, {})
    print("\n  " + style("Root coordinator · your main chat"))
    if recommendation:
        field("Suggested", " / ".join(recommendation[key] for key in ("model", "reasoning") if key in recommendation), "command")
        field("For profile", resolved["model_profile"], "muted")
    else:
        field("Model", "Your session choice; no profile recommendation", "muted")
    notice("Choose the main-chat model in your client. Plex keeps your session model.")


class HelpFormatter(argparse.RawDescriptionHelpFormatter):
    def start_section(self, heading):
        super().start_section(style(heading, "title"))


def choose(label, choices, default):
    ui = terminal_ui()
    if ui:
        labels = {"__default__": "Default", "__manual__": "Other model…", "__done__": "Done",
                  "inherit": "Inherit session settings", "custom": "Custom",
                  "basic": "Basic", "plus": "Plus", "pro": "Pro", "pro-plus": "Pro+",
                  "refresh": "Update only", "configure": "Reconfigure",
                  "project": "Project (recommended)", "user": "User-wide",
                  "pnet": "pnet · Standalone", "bmad": "bmad · BMad workflows",
                  "interactive": "Interactive", "balanced": "Balanced (recommended)", "auto": "Auto"}
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
            [("class:choice-title", labels.get(name, name))],
            value=name, description=detail.replace("; ", "\n"))
                                        for name, detail in choices.items()], default=default,
                         pointer="›", style=ui.Style(MENU_STYLE),
                         instruction="↑/↓ move · Enter confirm").unsafe_ask()
    heading(label)
    names = list(choices)
    for index, name in enumerate(names, 1):
        print(f"  {index}. {name:<16} {choices[name]}")
    while True:
        answer = input(style(f"Choice [{default}]: ", "command")).strip() or default
        if answer.isdigit() and 1 <= int(answer) <= len(names):
            answer = names[int(answer) - 1]
        if answer in choices:
            return answer
        notice("Choose a listed name or number.", "warn")


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
        notice("Select at least one listed client, for example 1,2.", "warn")


def terminal_ui():
    if (sys.stdin.isatty() and sys.stdout.isatty()
            and "NO_COLOR" not in os.environ and os.environ.get("TERM") != "dumb"):
        try:
            import questionary
            return questionary
        except ImportError:
            pass
    return None


def ask_text(label, default=""):
    ui = terminal_ui()
    if ui:
        return ui.text(label, default=default, style=ui.Style(MENU_STYLE)).unsafe_ask()
    return input(style(f"{label} [{default}]: ", "command")).strip() or default


def model_catalog(host, project):
    if host == "claude":
        return {name: {} for name in ("sonnet", "opus", "haiku", "fable", "inherit")}
    if host == "antigravity":
        return {name: {} for name in CONFIG.ANTIGRAVITY_NATIVE_MODELS}
    notice("Reading the active Codex model catalog…")
    try:
        result = subprocess.run(["codex", "debug", "models"], cwd=project,
                                capture_output=True, text=True, timeout=15)
        if result.returncode:
            raise ValueError("catalog unavailable")
        return {item["slug"]: item for item in json.loads(result.stdout)["models"]
                if item.get("visibility", "list") == "list"}
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        notice("Codex catalog unavailable. Using packaged suggestions; availability is unverified.", "warn")
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
    heading("Custom model overrides")
    field("Base profile", resolved["model_profile"])
    notice("Default uses profile/project settings.")
    notice("Model availability depends on your provider and account.")
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
            notice(f"Previous reasoning {current!r} is not listed for this model; choose a supported level.", "warn")
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
            notice(f"Keeping existing command: {destination}. Setup continues without replacing it.", "warn")
            show_command([str(ROOT / "setup.sh")])
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
    heading("Plex command")
    notice(f"Command ready: {destination}", "ok")
    show_command("plex")
    if str(destination.parent) not in os.environ.get("PATH", "").split(os.pathsep):
        notice("Add this to your shell configuration:", "warn")
        show_command('export PATH="$HOME/.local/bin:$PATH"')


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
    heading("Install BMad dependencies")
    notice("Installing the selected official BMad skills for this user. Existing selected "
           "user skill files may be replaced; other projects share them. Installed plugins "
           "are not changed. These changes remain after cancellation or later failure.", "warn")
    for command in bmad_install_commands(host):
        show_command(command)
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
            field("BMad default", f"{question['prompt']} = {answer}")
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
    notice("BMad runtime initialized by its official setup. It remains if a later Plex step fails.", "ok")


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
    notice("One profile is shared by all clients. Each installation has a plan to confirm; stopping preserves completed clients.")
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
        if args.archive_other_agents and client == "codex":
            options.append("--archive-other-agents")
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
            notice(f"Stopped at {client}. Completed clients: {', '.join(completed) or 'none'}. Rerun to continue.", "warn")
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
        notice(f"All selected clients are in sync: {', '.join(completed)}.", "ok")
    return 0


DEV_PLUGIN = "pnet-plex@pnet-plex"
DEV_BLOCK = ('# plex-dev:start\n[plugins."pnet-plex@pnet-plex"]\nenabled = false\n# plex-dev:end\n')
DEV_SKILLS = ("plex", "plex-setup")


def plan_skills(project, development=False, *, aliases=False, scope="project"):
    """Plan owned skill links; only dev mode manages a project plugin override."""
    project = CONFIG.installation_root(project, "codex", scope).resolve()
    receipt = CONFIG._ensure_safe_project_path(project, ".plex/dev.json")
    alias_receipt = CONFIG._ensure_safe_project_path(project, ".plex/skill-aliases.json")
    before = receipt.read_bytes() if receipt.exists() else None
    alias_before = alias_receipt.read_bytes() if alias_receipt.exists() else None
    if before is not None and alias_before is not None:
        raise ValueError("Conflicting Plex skill receipts; inspect before changing links")
    saved = before if before is not None else alias_before
    record = json.loads(saved) if saved is not None else None
    if saved is not None and (not isinstance(record, dict) or set(record) != {"source", "config_block"}
                               or not isinstance(record["source"], str) or not Path(record["source"]).is_absolute()
                               or type(record["config_block"]) is not bool):
        raise ValueError("Invalid Plex skill receipt; inspect before changing links")
    if (scope != "project" and (development or before is not None)) or (alias_before is not None and record["config_block"]):
        raise ValueError("Only project development mode may own a plugin override")
    directory = ".agents/skills" if scope == "project" else "skills"
    CONFIG._ensure_safe_project_path(project, directory)
    links = []
    source = ROOT
    enabled = development or aliases
    for name in DEV_SKILLS:
        path = project / directory / name
        old = str(Path(record["source"]) / "skills" / name) if record else None
        actual = os.readlink(path) if path.is_symlink() else None
        if (old is not None and actual != old) or (old is None and (path.exists() or path.is_symlink())):
            raise ValueError(f"Foreign or modified Plex skill preserved: {path}")
        target = str(source / "skills" / name) if enabled else None
        if enabled and not (ROOT / "skills" / name / "SKILL.md").is_file():
            raise ValueError(f"Plex skill source is incomplete: {name}")
        links.append((path, actual, target))
    files = {}
    owned_block = False
    if development or before is not None:
        config = CONFIG._ensure_safe_project_path(project, ".codex/config.toml")
        config_before = config.read_bytes() if config.exists() else None
        text = (config_before or b"").decode("utf-8")
        plugins = tomllib.loads(text).get("plugins", {})
        if not isinstance(plugins, dict) or (DEV_PLUGIN in plugins and not isinstance(plugins[DEV_PLUGIN], dict)):
            raise ValueError("Invalid project plugin settings; preserved")
        if before is not None and record["config_block"] and text.count(DEV_BLOCK) != 1:
            raise ValueError("Managed Plex dev plugin override changed; preserved")
        if development:
            owned_block = record["config_block"] if before is not None else False
            if before is None and plugins.get(DEV_PLUGIN) is None:
                text += ("" if not text or text.endswith("\n\n") else "\n" if text.endswith("\n") else "\n\n") + DEV_BLOCK
                owned_block = True
            if tomllib.loads(text).get("plugins", {}).get(DEV_PLUGIN, {}).get("enabled") is not False:
                raise ValueError('Set [plugins."pnet-plex@pnet-plex"] enabled = false in project .codex/config.toml before --dev; existing override preserved')
        elif record["config_block"]:
            text = text.replace(DEV_BLOCK, "", 1)
        files[config] = (config_before, text.encode() if text else None)
    after = (json.dumps({"source": str(source), "config_block": owned_block}, indent=2) + "\n").encode() if enabled else None
    files[receipt] = (before, after if development else None)
    files[alias_receipt] = (alias_before, after if aliases and not development else None)
    return {"project": project, "enabled": enabled, "was_development": before is not None,
            "links": links, "files": files}


@contextmanager
def apply_skills(plan):
    """Roll back owned skill changes on failure, preserving concurrent edits."""
    changed = []
    def link_value(path):
        CONFIG._ensure_safe_project_path(plan["project"], str(path.parent.relative_to(plan["project"])))
        if path.is_symlink():
            return os.readlink(path)
        if path.exists():
            raise ValueError(f"Foreign Plex skill preserved: {path}")
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
                raise ValueError(f"Plex skill settings changed after preview: {path}")
        for path, before, after in plan["links"]:
            if link_value(path) != before:
                raise ValueError(f"Plex skill changed after preview: {path}")
            if after is not None and not (Path(after) / "SKILL.md").is_file():
                raise ValueError(f"Plex skill target is missing: {after}")
        for path, before, after in plan["links"]:
            if before != after:
                if link_value(path) != before:
                    raise ValueError(f"Plex skill changed during apply: {path}")
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
            raise ValueError("Plex skill rollback needs recovery: " + "; ".join(failures))
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
                plan_skills(project, True)
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
        skill_aliases = None
        if configured and client == "codex" and plugin != "development":
            alias_receipt = CONFIG._ensure_safe_project_path(Path(report["root"]), ".plex/skill-aliases.json")
            skill_aliases = "not_installed"
            if alias_receipt.is_file():
                try:
                    alias_plan = plan_skills(project, aliases=True, scope=report["scope"])
                    for path, before, after in alias_plan["links"]:
                        if before is None or not (Path(before) / "SKILL.md").is_file():
                            raise ValueError(f"Plex skill target is missing: {path}")
                    skill_aliases = "enabled" if all(before == after for _, before, after in alias_plan["links"]) else "needs_refresh"
                except (OSError, ValueError) as error:
                    skill_aliases = str(error)
                if skill_aliases != "enabled":
                    report["conflicts"].append(f"Short skill links: {skill_aliases}")
        resolved = report.get("resolved") or {}
        reports.append({"client": client, "scope": report.get("scope", scope or "auto"),
                        "root": report.get("root"), "configured": configured,
                        "status": report["status"] if configured or report.get("conflicts") else "unconfigured",
                        "team": resolved.get("team"), "profile": resolved.get("model_profile"),
                        "roles": state.get("installed_roles", []), "plugin": plugin, "dev_source": dev_source, "skill_aliases": skill_aliases,
                        "conflicts": report.get("conflicts", [])})
    return {"version": version, "source": str(ROOT), "clients": reports}


def removal_report(results, preview=False):
    heading("Plex · Removal preview" if preview else "Plex · Uninstall complete")
    for item in results:
        print("\n  " + style(f"{item['host']} · {item['scope']}"))
        field("Status", item["status"], "muted" if preview else "ok")
        if item.get("root"):
            field("Root", item["root"], "muted")
        roles = item["removed_roles"]
        field("Remove roles" if preview else "Removed roles", len(roles))
        if roles:
            notice(", ".join(f"plex-{role}" for role in roles))
        if item.get("instruction_block_removed"):
            field("Instructions", "Remove managed block only" if preview else "Managed block removed")
        if item.get("remove_dev_links_and_override"):
            field("Dev mode", "Remove owned links and plugin override")
        if item.get("remove_skill_aliases"):
            field("Chat skills", "Remove owned $plex and $plex-setup links")
        if item.get("backup_dir"):
            field("Backups", Path(item["root"]) / item["backup_dir"], "muted")
    if preview:
        print()
        notice("Preview only. No files or plugins changed.", "ok")


def maintenance(args):
    project = (args.project or Path.cwd()).expanduser().absolute()
    clients = list(dict.fromkeys(([args.host] if args.host else []) + (args.clients or []))) or list(CONFIG.HOSTS)
    if args.action == "status":
        result = plex_status(project, clients, args.scope)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            heading(f"Plex {result['version']} · Status")
            field("Source", result["source"], "muted")
            for item in result["clients"]:
                heading(f"{item['client']} · {item['scope']}")
                healthy = item["status"] == "in_sync" and item["plugin"] in {"enabled", "development"}
                tone = "ok" if healthy else "muted" if item["status"] == "unconfigured" else "warn"
                field("Status", item["status"], tone)
                field("Team / profile", f"{item['team'] or '—'} / {item['profile'] or '—'}")
                field("Plugin", item["plugin"], tone)
                if item["skill_aliases"] is not None:
                    field("Short skills", item["skill_aliases"], "ok" if item["skill_aliases"] == "enabled" else "warn")
                field("Root", item["root"], "muted")
                field("Native roles", len(item["roles"]))
                if item["dev_source"]:
                    field("Dev source", item["dev_source"], "command")
                for conflict in item["conflicts"]:
                    notice(f"Conflict: {conflict}", "error")
            print()
            notice("Configuration/plugin checks only; runtime model routing is not verified.")
        return int(any(item["conflicts"] or item["configured"] and
                       (item["status"] != "in_sync" or item["plugin"] not in {"enabled", "development"})
                       for item in result["clients"]))
    scope = args.scope or "project"
    skill_root = CONFIG.installation_root(project, "codex", scope) if "codex" in clients else None
    dev_plan = (plan_skills(project, scope=scope) if "codex" in clients and any(
        CONFIG._ensure_safe_project_path(skill_root, name).is_file()
        for name in (".plex/dev.json", ".plex/skill-aliases.json")) else None)
    plans = [CONFIG.uninstall_project(project, client, scope, dry_run=True) for client in clients]
    if dev_plan:
        for plan in plans:
            if plan["host"] == "codex":
                plan["remove_dev_links_and_override"] = dev_plan["was_development"]
                plan["remove_skill_aliases"] = not dev_plan["was_development"]
    if args.dry_run:
        if args.json:
            print(json.dumps(plans, indent=2))
        else:
            removal_report(plans, preview=True)
        return 0
    if not args.yes:
        if not sys.stdin.isatty():
            raise ValueError("Use uninstall --dry-run to preview or uninstall --yes to confirm")
        if not args.json:
            removal_report(plans, preview=True)
        question = "Remove these Plex roles and owned instruction blocks? [y/N] "
        if args.json:
            print(question, end="", file=sys.stderr, flush=True)
            answer = input()
        else:
            answer = input(question)
        if answer.strip().lower() not in {"y", "yes"}:
            if args.json:
                print("[]")
            else:
                notice("Uninstall cancelled.")
            return 0
    results = []
    for client in clients:
        with apply_skills(dev_plan) if dev_plan and client == "codex" else nullcontext():
            result = CONFIG.uninstall_project(project, client, scope)
            if dev_plan and client == "codex":
                result["remove_dev_links_and_override"] = dev_plan["was_development"]
                result["remove_skill_aliases"] = not dev_plan["was_development"]
            results.append(result)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        removal_report(results)
        notice("Shared plugins, source checkout, preset preferences and backups were retained.")
    return 0


def main(argv=None, *, shared_profile=False, selection=None, setup_mode=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="plex", usage="%(prog)s [command] [options]",
        description="Plex · Configure and inspect your agent team.", formatter_class=HelpFormatter,
        epilog="Examples:\n  plex                             Open setup\n  plex status --client codex        Check this project\n  plex update                       Download and refresh\n  plex uninstall --dry-run          Preview removal\n  plex --dev --client codex         Use this checkout's skills")
    target_options = parser.add_argument_group("Clients and scope")
    team_options = parser.add_argument_group("Team and models")
    bmad_options = parser.add_argument_group("BMad dependencies")
    output_options = parser.add_argument_group("Execution and output")
    update_options = parser.add_argument_group("Source updates")
    parser.add_argument("action", nargs="?", choices=("setup", "status", "update", "uninstall"), default="setup")
    output_options.add_argument("--json", action="store_true", help="Machine-readable status or uninstall output (no styling)")
    update_options.add_argument("--release", help="Published tag for update; defaults to newest published release")
    update_options.add_argument("--development", action="store_true", help="Explicitly update to main")
    target_options.add_argument("--project", type=Path, help="Existing target project directory")
    target_options.add_argument("--client", dest="clients", action="append", choices=CONFIG.HOSTS,
                        help="Client to configure; repeat to select several")
    target_options.add_argument("--host", choices=CONFIG.HOSTS, help="Compatibility alias for one --client")
    target_options.add_argument("--scope", choices=("project", "user"), help="Role installation scope; default: project (recommended)")
    target_options.add_argument("--instructions", action=argparse.BooleanOptionalAction, default=None,
                        help="Add/update the managed Plex block in the native instruction file (default: enabled)")
    team_options.add_argument("--team", help="Work mode (role set); preserve current selection if omitted")
    team_options.add_argument("--model-profile", help="Model profile; preserve current selection if omitted")
    team_options.add_argument("--interaction", choices=CONFIG.INTERACTIONS,
                        help="Interaction mode: interactive, balanced (default), auto; preserve saved selection")
    team_options.add_argument("--max-agents", type=int, help="Shared limit of concurrent Plex assignments (positive integer)")
    bmad_options.add_argument("--install-bmad", action="store_true", help="Install the selected official BMad user skills; may replace selected skill files; project scope also initializes runtime")
    bmad_options.add_argument("--init-bmad", action="store_true", help="Initialize missing project runtime using installed official BMad setup; --yes accepts module defaults")
    bmad_options.add_argument("--bmad-skill", type=Path, help="Installed bmad setup skill directory; otherwise discover supported installed sources")
    target_options.add_argument("--dev", action=argparse.BooleanOptionalAction, default=None,
                        help="Codex project: link this checkout as local Plex skills; --no-dev restores shared plugin discovery")
    output_options.add_argument("--archive-other-agents", action="store_true",
                        help="Codex only: back up and remove other unmanaged agent files in the selected scope")
    output_options.add_argument("--roles-only", action="store_true", help="Configure roles without installing the plugin")
    output_options.add_argument("--command", action=argparse.BooleanOptionalAction, default=True,
                        help="Create ~/.local/bin/plex during full installation (default: enabled)")
    mode = output_options.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show planned commands and roles without writes")
    mode.add_argument("--install-command", action="store_true", help="Link this checkout as ~/.local/bin/plex")
    output_options.add_argument("--yes", action="store_true", help="Apply without prompts; requires --client and --project for project scope")
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
            notice(f"Plex {args.action} stopped: {error}", "error", file=sys.stderr)
            return 1
        except (EOFError, KeyboardInterrupt):
            notice("Plex maintenance interrupted; inspect the last reported state.", "warn", file=sys.stderr)
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
            notice("Development setup: this checkout supplies project-local Plex skills. No model calls.")
        else:
            notice("Shared Plex skills + your selected team. No model calls.")
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
        alias_receipt = CONFIG._ensure_safe_project_path(
            CONFIG.installation_root(project, "codex", args.scope), ".plex/skill-aliases.json") if args.host == "codex" else None
        alias_enabled = args.host == "codex" and not dev_enabled and (not args.roles_only or alias_receipt.exists())
        dev_plan = plan_skills(project, dev_enabled, aliases=alias_enabled, scope=args.scope) if args.host == "codex" and (
            dev_enabled or alias_enabled or bool(dev_receipt and dev_receipt.exists())) else None
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
                notice("The saved model profile is unavailable in the selected team. Choose a profile below.", "warn")
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
                notice("Cancelled. No changes.")
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
                    notice("Official BMad setup is missing. Install the selected user skills; this may replace selected skill files and affects other projects. Existing plugins remain unchanged.", "warn")
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
                    tier = next((tier for tier in sorted(CONFIG.PROFILE_TIERS, key=len, reverse=True)
                                 if name == tier or name.endswith(f"-{tier}")), "inherit")
                    choices[name] = {
                        "inherit": "Use client defaults for subagent models and reasoning",
                        "basic": "Lightweight defaults with team-specific overrides",
                        "plus": "Mixed models for execution, planning and review",
                        "pro": "More capable settings for demanding assignments",
                        "pro-plus": "Strongest configured role settings",
                    }[tier]
                notice("Profiles configure subagents. The final plan shows effective models, including project overrides.")
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
            notice("One shared limit for concurrent Plex assignments across all roles. Client limits still apply.")
            while True:
                answer = ask_text("Parallel agents", str(resolved["max_agents"])).strip()
                try:
                    limit = int(answer)
                    if limit > 0:
                        break
                except ValueError:
                    pass
                notice("Enter a positive whole number.", "warn")
            args.max_agents = limit
            candidate = build_candidate(args.model_profile,
                                                 max_agents=limit, host_overrides=host_overrides)
            resolved = CONFIG.resolve(tomllib.loads(candidate))
        rendered = CONFIG.render_host_roles(resolved, args.host, args.scope)
        if not args.roles_only and not args.dry_run and args.host == "codex" and os.environ.get("CODEX_HOME"):
            profile = Path(os.environ["CODEX_HOME"]).expanduser()
            if not profile.is_dir():
                raise ValueError(f"CODEX_HOME directory does not exist: {profile}. Create the test profile directory first.")
        archive_agents = {}
        if args.archive_other_agents and args.host != "codex":
            raise ValueError("--archive-other-agents requires Codex")
        if args.host == "codex":
            others = CONFIG.other_codex_agents(config_root, resolved["roles"], args.scope)
            if others:
                heading("Other Codex agents")
                for name, digest in others.items():
                    field("Preserved" if digest is None else "Existing", name, "muted")
                notice("These agents are also available to the coordinator and may affect role selection.", "warn")
                notice("Only listed files are eligible; explicit config.toml registrations and symlinks are preserved.")
                eligible = {name: digest for name, digest in others.items() if digest is not None}
                archive = args.archive_other_agents and bool(eligible)
                if eligible and interactive and not args.dry_run and not archive:
                    archive = choose("Other Codex agents", {
                        "keep": "Keep existing agents (recommended)",
                        "archive": "Move eligible files to a Plex backup",
                    }, "keep") == "archive"
                archive_agents = eligible if archive else {}
                notice("Move listed agents to backup when applying." if archive else "Keep existing agents; Plex must use only its active team.")
        state = CONFIG.check_project(project, args.host, args.scope)
        if archive_agents:
            ignored = {f"Unmanaged file collision: {path} is not owned by .plex/applied.json" for path in archive_agents}
            state["conflicts"] = [item for item in state["conflicts"] if item not in ignored]
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

        heading("Installation plan")
        if setup_mode == "refresh":
            notice("Update existing installation; saved settings retained unless explicitly overridden.")
        field("Client", args.host)
        field("Team scope", args.scope)
        field("Settings", config_root / ".plex", "muted")
        if args.scope == "project":
            field("Project", project, "command")
        field("Agent files", config_root / CONFIG.host_agents_relpath(args.host, args.scope), "muted")
        if shortcut:
            field("Command", shortcut, "command")
        if state.get("resolved"):
            for other in CONFIG.HOSTS:
                other_state = state["hosts"][other]
                if other not in refresh_clients and (other_state.get("installed_roles") or other_state.get("outdated_roles")):
                    if (state["resolved"]["hosts"][other] != resolved["hosts"][other]
                            or state["resolved"]["roles"] != resolved["roles"]):
                        notice(f"Shared team/profile changes also affect {other}; its files are not refreshed by this run.", "warn")
        if args.scope == "user":
            local = CONFIG.check_project(project, args.host)
            if local.get("preset_exists") or local.get("hosts", {}).get(args.host, {}).get("installed_roles") or local.get("conflicts"):
                notice("Existing project configuration/roles may override user defaults; they will be preserved.", "warn")
        if instruction_plan:
            field("Instructions", instruction_plan["path"], "muted")
            notice("Only the managed Plex block is updated; surrounding instructions are preserved.")
        field("Team", resolved["team"] or "custom")
        field("Profile", resolved["model_profile"], "command")
        if len(refresh_clients) > 1:
            field("Refresh", ", ".join(refresh_clients))
        field("Interaction", resolved["interaction"], "command")
        field("Concurrency", f"{resolved['max_agents']} assignments")
        coordinator_summary(resolved, args.host)
        print("\n  " + style(f"Subagents · {len(resolved['roles'])} roles"))
        role_table(resolved["hosts"][args.host])
        if resolved["inactive_overrides"][args.host]:
            notice("Inactive overrides: " + ", ".join(resolved["inactive_overrides"][args.host]))
        for role in state["hosts"][args.host].get("installed_roles", []):
            if role not in rendered:
                field("Archive", f"plex-{role}", "warn")
        commands = [] if args.roles_only or dev_enabled else plugin_commands(args.host, args.scope)
        heading("Skills and dependencies")
        if dev_enabled:
            field("Dev source", ROOT, "command")
            field("Project skills", ".agents/skills/plex, .agents/skills/plex-setup", "muted")
            notice("Live symlinks follow this working checkout.")
            notice("Shared Plex plugin: disabled only in this trusted project; other projects unchanged.")
        elif alias_enabled:
            field("Chat skills", "$plex, $plex-setup", "command")
            field("Skill links", ".agents/skills" if args.scope == "project" else config_root / "skills", "muted")
            notice("Links use the shared Plex checkout; skill contents are not copied.")
        elif dev_plan:
            notice("Leave development mode: remove owned links and restore project plugin discovery.")
        if args.roles_only and not dev_enabled:
            notice("Roles only: shared plugin installation is skipped.")
        if commands:
            notice("Shared plugin: installed for this user/client profile; skills are not copied into the project.")
            field("Plugin source", ROOT, "muted")
            print("\n  " + style("Native plugin commands", "bold"))
            for command in commands:
                show_command(command)

        notice("Managed changes use backups and rollback.")
        if resolved["process"] == "bmad":
            notice("BMad: verify runtime and active skills in each working project before use.")
        if selection is not None:
            selection.update(setup_mode=setup_mode, instructions=args.instructions, team=resolved["team"], max_agents=resolved["max_agents"], model_profile=resolved["model_profile"], interaction=resolved["interaction"])
        if bmad_init:
            field("BMad setup", bmad_init["skill"], "muted")
            field("BMad runtime", project / "_bmad", "command")
        if args.dry_run:
            if resolved["process"] == "bmad" and args.install_bmad:
                notice("BMad selected user-skill installation plan (existing selected skill files may be replaced):", "warn")
                for command in bmad_install_commands(args.host):
                    show_command(command)
            if resolved["process"] == "bmad" and args.scope == "project" and not bmad_runtime_ready(project):
                notice("BMad runtime is missing: normal setup will offer official initialization.", "warn")
            notice("Preview only. No files or plugins changed.", "ok")
            return 0

        if interactive and choose("Apply this plan?", {"no": "Cancel without changes", "yes": "Apply"}, "no") != "yes":
            if selection is not None:
                selection["cancelled"] = True
            notice("Cancelled. No changes.")
            return 0

        if bmad_init:
            heading("Initialize BMad project")
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
            if not (dev_plan and dev_plan["was_development"]):
                verify_plugin(args.host, project)
            notice("Shared plugin installed.", "ok")
        heading(f"2 / 2  Apply {args.scope} roles" if commands else f"Apply {args.scope} roles")
        if (preset.read_bytes() if preset.is_file() else None) != source_bytes:
            raise ValueError("Project settings changed after preview; review the new settings and retry.")
        if instruction_plan:
            current = instruction_plan["path"].read_bytes() if instruction_plan["path"].is_file() else None
            if current != instruction_plan["before"]:
                raise ValueError("Instruction file changed after preview; review and retry.")
        with apply_skills(dev_plan) if dev_plan else nullcontext():
            result = CONFIG.apply_project(project, args.host, args.team, args.model_profile,
                                          max_agents=args.max_agents, host_overrides=host_overrides, interaction=args.interaction,
                                          scope=args.scope, instructions=args.instructions, archive_agents=archive_agents)
        for client in refresh_clients:
            if client != args.host:
                other_instructions = bool(receipt["hosts"][client].get("instructions")) if setup_mode == "refresh" else args.instructions
                CONFIG.apply_project(project, client, scope=args.scope, instructions=other_instructions)
        for client in refresh_clients:
            if CONFIG.check_project(project, client, args.scope)["status"] != "in_sync":
                raise ValueError(f"Post-install check failed for client {client}")
        if commands and dev_plan and dev_plan["was_development"]:
            verify_plugin(args.host, project)
        notice(f"{len(result['installed_roles'])} roles; configuration in sync.", "ok")
        if result.get("archived_other_agents"):
            notice(f"{len(result['archived_other_agents'])} other agents moved to backup.", "ok")
        if result["backup_dir"]:
            field("Backups", config_root / result["backup_dir"], "muted")
        others = [client for client in result.get("other_hosts_needing_refresh", []) if client not in refresh_clients]
        if others:
            notice(f"Refresh the other clients: {', '.join(others)}", "warn")
        if resolved["process"] == "bmad":
            notice("BMad roles registered; run plex-setup in the host to verify active skill bindings.")
        if shortcut:
            install_command()
        heading("Setup complete")
        notice("No separate plex-setup step is needed for this team configuration.", "ok")
        notice("Open a new client session, then invoke the plex skill for coordinated work.")
        print("\n  " + style("Next commands", "bold"))
        launcher = ["plex"] if shortcut and str(shortcut.parent) in os.environ.get("PATH", "").split(os.pathsep) else [str(ROOT / "setup.sh")]
        show_command([*launcher, "status", "--client", args.host])
        show_command(launcher)
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        notice(f"Setup stopped: {error}", "error", file=sys.stderr)
        if plugin_started:
            notice("Shared dependencies or native plugin state may have changed; inspect before retrying.", "warn", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        notice("Setup interrupted. Check project state if application had started.", "warn", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
