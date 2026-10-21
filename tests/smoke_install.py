"""Bare-Python installer lifecycle; run in a clean container without uv or client CLIs."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    assert shutil.which("uv") is None, "This check must exercise the Python fallback"
    assert importlib.util.find_spec("questionary") is None, "Use an image without setup dependencies"
    assert all(shutil.which(client) is None for client in ("codex", "claude", "agy"))
    with tempfile.TemporaryDirectory(prefix="plex smoke ") as temp:
        base = Path(temp)
        home, project = base / "home", base / "project with spaces"
        home.mkdir()
        project.mkdir()
        env = {**os.environ, "HOME": str(home), "CODEX_HOME": str(home / "codex"),
               "CLAUDE_CONFIG_DIR": str(home / "claude"), "NO_COLOR": "1", "TERM": "dumb"}
        roots = {"codex": Path(env["CODEX_HOME"]), "claude": Path(env["CLAUDE_CONFIG_DIR"]),
                 "antigravity": home / ".gemini"}
        def run(*command):
            result = subprocess.run(command, cwd=project, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            if result.returncode:
                raise AssertionError(f"Command failed ({result.returncode}): {command}\n{result.stdout}")
            return result.stdout
        for scope in ("project", "user"):
            for client, filename in (("codex", "AGENTS.md"), ("claude", "CLAUDE.md"), ("antigravity", "GEMINI.md")):
                root = project if scope == "project" else roots[client]
                root.mkdir(parents=True, exist_ok=True)
                instructions = root / filename
                original = "# Personal instructions\nPreserve these instructions.\n"
                instructions.write_text(original)
                agents = root / (f".{client}/agents" if scope == "project" and client != "antigravity"
                                 else ".agents/agents" if scope == "project"
                                 else "config/agents" if client == "antigravity" else "agents")
                foreign = agents / "legacy.toml" if client == "codex" else None
                if foreign:
                    agents.mkdir(parents=True, exist_ok=True)
                    foreign.write_text('name = "legacy"\ndescription = "Keep this agent"\n')
                setup = (str(ROOT / "setup.sh"), "--project", str(project), "--client", client,
                         "--scope", scope, "--team", "pnet", "--model-profile", "inherit",
                         "--roles-only", "--no-command", "--yes")
                run(*setup, "--dry-run")
                assert instructions.read_text() == original
                run(*setup)
                installed = instructions.read_bytes()
                assert installed.startswith(original.encode()) and b"plex:managed:start" in installed
                run(*setup)
                assert instructions.read_bytes() == installed, "Refresh must preserve instruction bytes"
                state = json.loads(run("python3", str(ROOT / "skills/plex-setup/scripts/resolve_config.py"),
                                       "check", str(project), "--host", client, "--scope", scope))
                assert state["status"] == "in_sync", state
                assert len(list(agents.glob("plex-*"))) == 6
                remove = (str(ROOT / "setup.sh"), "uninstall", "--project", str(project),
                          "--client", client, "--scope", scope, "--json")
                json.loads(run(*remove, "--dry-run"))
                assert instructions.read_bytes() == installed
                json.loads(run(*remove, "--yes"))
                assert instructions.read_text().startswith(original)
                assert "plex:managed:start" not in instructions.read_text()
                assert not list(agents.glob("plex-*"))
                if foreign:
                    assert foreign.read_text() == 'name = "legacy"\ndescription = "Keep this agent"\n'
                print(f"OK: {client}, {scope}: preview / install / refresh / check / uninstall")


if __name__ == "__main__":
    main()
