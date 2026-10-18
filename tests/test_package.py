"""Package contracts and an isolated native install; no model calls."""

import json
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plex_package_installer", ROOT / "setup.py")
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)
ALL_ROLES = (
    "analyst", "pm", "po", "ux", "architect", "dev", "qa", "reviewer", "explorer", "researcher",
)


def read_json(path):
    return json.loads(path.read_text())


def read_role(path, host):
    text = path.read_text()
    if host == "codex":
        return tomllib.loads(text)
    return yaml.safe_load(text.split("---", 2)[1])


def selected_assets(team_path, preset, host):
    extension = "toml" if host == "codex" else "md"
    for role in preset["roles"]:
        yield role, team_path.parent / "agents" / host / f"{role}.{extension}"


class PackageTests(unittest.TestCase):
    def test_build_exports_only_reviewed_files_and_refreshes_without_stale_files(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp).resolve() / "checkout"
            checkout.mkdir()
            shutil.copy2(ROOT / ".gitignore", checkout / ".gitignore")
            for line in (ROOT / ".gitignore").read_text().splitlines():
                if line.startswith("!/") and not line.endswith("/"):
                    for source in ROOT.glob(line[2:]):
                        target = checkout / source.relative_to(ROOT)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, target)
            private = checkout / "skills/plex/private.txt"
            private.write_text("must not ship")
            public = checkout / "skills/plex/references/new-guide.md"
            public.write_text("New reusable guide")
            cache = checkout / "skills/plex/__pycache__/skill.pyc"
            cache.parent.mkdir()
            cache.write_bytes(b"not source")
            with patch.object(INSTALLER, "ROOT", checkout):
                package = INSTALLER.build_plugin("claude")
                self.assertFalse((package / private.relative_to(checkout)).exists())
                self.assertFalse((package / cache.relative_to(checkout)).exists())
                self.assertEqual((package / public.relative_to(checkout)).read_bytes(), public.read_bytes())
                self.assertFalse((package / ".gitignore").exists())
                self.assertFalse((package / ".codex-plugin").exists())
                self.assertEqual((package / "THIRD_PARTY_NOTICES.md").read_bytes(),
                                 (checkout / "THIRD_PARTY_NOTICES.md").read_bytes())
                before = {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()}
                self.assertEqual(INSTALLER.build_plugin("claude"), package)
                self.assertEqual(before, {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()})
                (package / "stale.txt").write_text("old export")
                skill = checkout / "skills/plex/SKILL.md"
                skill.write_text(skill.read_text() + "\nUpdated source.\n")
                INSTALLER.build_plugin("claude")
                self.assertFalse((package / "stale.txt").exists())
                self.assertEqual((package / "skills/plex/SKILL.md").read_bytes(), skill.read_bytes())
                skill.unlink()
                with self.assertRaisesRegex(ValueError, "Missing or unsafe"):
                    INSTALLER.build_plugin("claude")
                self.assertTrue((package / "skills/plex/SKILL.md").is_file())

    def test_hosts_expose_the_same_plugin_and_skills(self):
        hosts = ("codex", "claude", "antigravity")
        packages = [INSTALLER.build_plugin(host) for host in hosts]
        manifests = [read_json(ROOT / "plugins" / host / f".{host}-plugin/plugin.json")
                     for host in ("codex", "claude", "antigravity")]
        for manifest in manifests[1:]:
            self.assertEqual(manifest["name"], manifests[0]["name"])
            self.assertEqual(manifest["version"], manifests[0]["version"])
        skill_sets = []
        for package, manifest in zip(packages, manifests):
            for team in ("pnet", "bmad"):
                coordinator = Path("teams") / team / "coordinator.md"
                self.assertEqual((package / coordinator).read_bytes(), (ROOT / coordinator).read_bytes())
            skill_root = (package / manifest.get("skills", "./skills")).resolve()
            self.assertTrue(skill_root.is_relative_to(package))
            names = set()
            for path in skill_root.glob("*/SKILL.md"):
                header = yaml.safe_load(path.read_text().split("---", 2)[1])
                self.assertEqual(header["name"], path.parent.name)
                self.assertNotIn(header["name"], names)
                names.add(header["name"])
            self.assertTrue(names)
            skill_sets.append(names)
        self.assertEqual(skill_sets[0], skill_sets[1])
        self.assertEqual(skill_sets[0], skill_sets[2])
        native = read_json(ROOT / ".agents/plugins/marketplace.json")
        claude = read_json(ROOT / ".claude-plugin/marketplace.json")
        for market in (native, claude):
            self.assertEqual(len(market["plugins"]), 1)
            self.assertEqual(market["plugins"][0]["name"], manifests[0]["name"])
        native_source = native["plugins"][0]["source"]["path"]
        claude_source = claude["plugins"][0]["source"]
        self.assertEqual((ROOT / native_source).resolve(), packages[0])
        self.assertEqual((ROOT / claude_source).resolve(), packages[1])

    def test_team_role_catalog_matches_definition_for_all_hosts(self):
        all_roles = set()
        for team in (ROOT / "teams").glob("*/team.toml"):
            roles = set(tomllib.loads(team.read_text())["roles"])
            all_roles.update(roles)
            for host in ("codex", "claude", "antigravity"):
                extension = "toml" if host == "codex" else "md"
                assets = team.parent / "agents" / host
                self.assertEqual({p.stem for p in assets.glob(f"*.{extension}")}, roles)
        self.assertEqual(all_roles, set(ALL_ROLES))

    def test_role_instructions_match_across_hosts(self):
        for team in (ROOT / "teams").glob("*/team.toml"):
            base = team.parent / "agents"
            for role in tomllib.loads(team.read_text())["roles"]:
                with self.subTest(team=team.parent.name, role=role):
                    codex = read_role(base / "codex" / f"{role}.toml", "codex")
                    claude = (base / "claude" / f"{role}.md").read_text().split("---", 2)[2].strip()
                    antigravity = (base / "antigravity" / f"{role}.md").read_text().split("---", 2)[2].strip()
                    self.assertEqual(claude, codex["developer_instructions"].strip())
                    self.assertEqual(antigravity, codex["developer_instructions"].strip())

    def test_each_preset_has_native_roles_for_both_hosts(self):
        for path in (ROOT / "teams").glob("*/team.toml"):
            preset = tomllib.loads(path.read_text())
            with self.subTest(preset=path.name):
                self.assertIn(preset.get("process", "plain"), ("plain", "bmad"))
                self.assertIs(type(preset["max_agents"]), int)
                self.assertGreater(preset["max_agents"], 0)
                self.assertTrue(preset["roles"])
                self.assertEqual(len(preset["roles"]), len(set(preset["roles"])))
                for host in ("codex", "claude", "antigravity"):
                    for role, asset in selected_assets(path, preset, host):
                        with self.subTest(host=host, role=role):
                            self.assertTrue(asset.is_file(), asset)
                            data = read_role(asset, host)
                            self.assertEqual(data["name"], f"plex-{role}")
                            self.assertTrue(data["description"])
                            if host == "codex":
                                self.assertTrue(data["developer_instructions"])
                                self.assertNotIn("model", data)
                                self.assertNotIn("model_reasoning_effort", data)
                            else:
                                self.assertEqual(data["model"], "inherit")
                                if host == "antigravity":
                                    self.assertIsInstance(data["tools"], list)
                if preset["process"] == "bmad":
                    self.assertEqual(set(preset["skills"]), set(preset["roles"]))
                    for role, bindings in preset["skills"].items():
                        self.assertTrue(bindings)
                        self.assertEqual(len(bindings), len(set(bindings)))
                        codex_asset = path.parent / f"agents/codex/{role}.toml"
                        codex_data = read_role(codex_asset, "codex")
                        for skill_name in bindings:
                            self.assertIn(skill_name, codex_data["developer_instructions"])
                        for md_host in ("claude", "antigravity"):
                            md_asset = path.parent / f"agents/{md_host}/{role}.md"
                            md_body = md_asset.read_text().split("---", 2)[2].strip()
                            self.assertEqual(md_body, codex_data["developer_instructions"].strip())

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is not installed")
    def test_native_codex_install_contains_presets_skills_and_assets(self):
        with tempfile.TemporaryDirectory(prefix="plex-package-test-") as temp:
            env = {**os.environ, "CODEX_HOME": temp}

            def run(*args, cwd=temp):
                result = subprocess.run(
                    ["codex", *args], env=env, cwd=cwd, text=True,
                    capture_output=True, timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            export = INSTALLER.build_plugin("codex")
            marketplace = read_json(ROOT / ".agents/plugins/marketplace.json")
            manifest = read_json(export / ".codex-plugin/plugin.json")
            run("plugin", "marketplace", "add", str(ROOT), "--json")
            run("plugin", "add", f'{manifest["name"]}@{marketplace["name"]}', "--json")
            inventory = run("plugin", "list", "--marketplace", marketplace["name"], "--json")
            self.assertEqual(len(inventory["installed"]), 1)
            installed = inventory["installed"][0]
            self.assertEqual(installed["version"], manifest["version"])
            self.assertTrue(installed["enabled"] and installed["installed"])
            roots = list((Path(temp).resolve() / "plugins/cache").rglob(".codex-plugin/plugin.json"))
            self.assertEqual(len(roots), 1)
            package = roots[0].parents[1]
            for directory in ("skills", "teams"):
                for source in (ROOT / directory).rglob("*"):
                    if source.is_file() and "__pycache__" not in source.parts:
                        copied = package / source.relative_to(ROOT)
                        self.assertTrue(copied.is_file(), copied)
                        self.assertTrue(copied.resolve().is_relative_to(package))
                        self.assertEqual(copied.read_bytes(), source.read_bytes())

            project_dir = Path(temp).resolve() / "sample-project"
            project_dir.mkdir()
            script_path = package / "skills/plex-setup/scripts/resolve_config.py"
            apply_res = subprocess.run(
                [
                    sys.executable, str(script_path),
                    "apply", str(project_dir),
                    "--host", "codex",
                    "--team", "bmad",
                    "--model-profile", "openai-plus",
                ],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(apply_res.returncode, 0, apply_res.stderr)
            applied_payload = json.loads(apply_res.stdout)
            self.assertEqual(
                applied_payload["effective_roles"]["architect"],
                {"model": "gpt-6.1-sol", "reasoning": "medium"},
            )
            self.assertEqual(
                applied_payload["effective_roles"]["pm"],
                tomllib.loads((ROOT / "teams/bmad/profiles/openai.toml").read_text())["profiles"]["plus"]["pm"],
            )

            codex_config = Path(temp).resolve() / "config.toml"
            existing_cfg = codex_config.read_text() if codex_config.exists() else ""
            codex_config.write_text(
                existing_cfg + f'\n[projects."{project_dir.resolve()}"]\ntrust_level = "trusted"\n'
            )
            doctor_res = subprocess.run(
                ["codex", "doctor", "--json"],
                env=env, cwd=str(project_dir), text=True,
                capture_output=True, timeout=60,
            )
            doctor = json.loads(doctor_res.stdout)
            self.assertEqual(doctor["checks"]["config.load"]["status"], "ok", doctor["checks"]["config.load"])

    @unittest.skipUnless(shutil.which("agy"), "Antigravity CLI is not installed")
    def test_native_antigravity_validate_and_install(self):
        with tempfile.TemporaryDirectory(prefix="plex-agy-test-") as temp:
            env = {**os.environ, "HOME": temp}
            export = INSTALLER.build_plugin("antigravity")
            val_res = subprocess.run(
                ["agy", "plugin", "validate", str(export), "--strict", "--json"],
                env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(val_res.returncode, 0, val_res.stderr or val_res.stdout)
            val_data = json.loads(val_res.stdout)
            self.assertEqual(val_data["findings"], [])
            self.assertEqual(val_data["components"]["skills"], 2)

            inst_res = subprocess.run(
                ["agy", "plugin", "install", str(export)],
                env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(inst_res.returncode, 0, inst_res.stderr)

            list_res = subprocess.run(
                ["agy", "plugin", "list", "--json"],
                env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(list_res.returncode, 0, list_res.stderr)
            installed = json.loads(list_res.stdout)
            self.assertEqual(len(installed), 1)
            self.assertEqual(installed[0]["name"], "pnet-plex")
            self.assertTrue(installed[0]["enabled"])

            project_dir = Path(temp).resolve() / "sample-project"
            project_dir.mkdir()
            script_path = Path(installed[0]["path"]) / "skills/plex-setup/scripts/resolve_config.py"
            apply_res = subprocess.run(
                [
                    sys.executable, str(script_path),
                    "apply", str(project_dir),
                    "--host", "antigravity",
                    "--team", "bmad",
                    "--model-profile", "google-plus",
                ],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(apply_res.returncode, 0, apply_res.stderr)
            applied_payload = json.loads(apply_res.stdout)
            self.assertEqual(
                applied_payload["effective_roles"]["architect"],
                {"model": "inherit", "reasoning": "medium"},
            )
            self.assertEqual(
                applied_payload["effective_roles"]["dev"],
                {"model": "flash", "reasoning": "max"},
            )

            (project_dir / ".agents/plugin.json").write_text('{"name": "project-agents"}\n')
            agents_val = subprocess.run(
                ["agy", "plugin", "validate", str(project_dir / ".agents"), "--strict", "--json"],
                env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(agents_val.returncode, 0, agents_val.stderr or agents_val.stdout)
            agents_data = json.loads(agents_val.stdout)
            self.assertEqual(agents_data["findings"], [])
            self.assertEqual(agents_data["components"]["agents"], 7)


if __name__ == "__main__":
    unittest.main()
