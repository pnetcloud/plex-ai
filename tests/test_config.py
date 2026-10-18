"""Configuration resolution, deterministic role rendering, check and apply lifecycle tests."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/plex-setup/scripts/resolve_config.py"
SPEC = importlib.util.spec_from_file_location("plex_config", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
resolve = MODULE.resolve
render_host_roles = MODULE.render_host_roles
check_project = MODULE.check_project
apply_project = MODULE.apply_project


class ConfigTests(unittest.TestCase):
    def test_shared_tiers_reuse_each_clients_vendor_settings(self):
        for team in ('pnet', 'bmad'):
            for tier in MODULE.PROFILE_TIERS:
                shared = resolve({'team':team, 'model_profile':tier})
                for host, vendor in [('codex','openai'), ('claude','anthropic'), ('antigravity','google')]:
                    standalone = resolve({'team':team, 'model_profile':f'{vendor}-{tier}'})
                    self.assertEqual(shared['hosts'][host], standalone['hosts'][host])

    def test_structured_skill_activation_keeps_role_context_and_merges_once(self):
        text = ('Role identity.\n\nSkill activation:\n'
                'Before substantive work, resolve and read these real installed skills '
                'using the host active skill inventory: bmad-agent-dev, bmad-build. '
                'Missing skills are blockers.\n\nWorking mode:\n1. Follow the installed workflow.\n')
        result = MODULE._inject_skill_bindings(text, ['bmad-agent-dev', 'bmad-build', 'custom-check'])
        self.assertTrue(result.startswith('Role identity.\n\nSkill activation:\n'))
        self.assertIn('bmad-agent-dev, bmad-build, custom-check.', result)
        self.assertEqual(result.count('Before substantive work'), 1)
        self.assertTrue(result.endswith('Working mode:\n1. Follow the installed workflow.\n'))
        self.assertEqual(MODULE._inject_skill_bindings(result, ['custom-check']), result)
        self.assertEqual(MODULE._inject_skill_bindings(text, []), text)

    def test_multiline_instructions_round_trip_without_text_changes(self):
        values = ('', 'One line', '\nLeading and trailing\n\n',
                  'First paragraph.\n\nSecond paragraph.',
                  'Quotes: """\nPath: C:\\new\\test\nLiteral: \\n\nРусский 中文 🧭',
                  'Controls: \t\r\b\f\x00\x1f\x7f')
        for value in values:
            with self.subTest(value=value):
                rendered = 'developer_instructions = ' + MODULE.toml_multiline(value)
                self.assertEqual(tomllib.loads(rendered)['developer_instructions'], value)
        for process in ('plain', 'bmad'):
            resolved = resolve({'team': 'pnet' if process == 'plain' else 'bmad'})
            for role, item in render_host_roles(resolved, 'codex').items():
                asset = tomllib.loads(MODULE.select_asset_path(process, 'codex', role).read_text())
                expected = MODULE._inject_skill_bindings(asset['developer_instructions'],
                                                         resolved['skills'].get(role, []))
                self.assertIn('developer_instructions = """\n', item['content'])
                self.assertEqual(tomllib.loads(item['content'])['developer_instructions'], expected)

    def test_antigravity_renders_only_explicit_native_tiers(self):
        for model in MODULE.ANTIGRAVITY_NATIVE_MODELS:
            with self.subTest(model=model):
                resolved = resolve({"team": "pnet", "antigravity": {"model": model}})
                for role in render_host_roles(resolved, "antigravity").values():
                    self.assertIn(f'model: {json.dumps(model)}\n', role["content"])
        for model in ("claude-opus-5-5-medium", "claude-sonnet-5-5-low",
                      "gemini-4-argon-medium", "gemini-3.8-flash-high"):
            with self.subTest(model=model):
                resolved = resolve({"team": "pnet", "antigravity": {"model": model}})
                with self.assertRaisesRegex(ValueError, "native model routing does not support"):
                    render_host_roles(resolved, "antigravity")

    def test_unsupported_antigravity_routing_is_a_read_only_conflict(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp).resolve()
            apply_project(project, "antigravity", team="pnet", model_profile="inherit")
            before = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
            with self.assertRaisesRegex(ValueError, "No model substitution"):
                apply_project(project, "antigravity", host_overrides={
                    "antigravity": {"pm": {"model": "claude-opus-5-5-medium"}}})
            self.assertEqual(before, {p: p.read_bytes() for p in project.rglob("*") if p.is_file()})
            (project / ".plex/preset.toml").write_text(
                'team = "pnet"\n[antigravity.pm]\nmodel = "claude-opus-5-5-medium"\n')
            state = check_project(project, "antigravity")
            self.assertEqual(state["status"], "conflict")
            self.assertEqual(state["hosts"]["antigravity"]["status"], "conflict")
            self.assertIn("native model routing does not support", " ".join(state["conflicts"]))
            self.assertNotEqual(check_project(project, "codex")["status"], "conflict")

    def test_removed_model_named_profiles_are_rejected(self):
        for name in ("sol-luna", "openai-sol-luna", "astra-luna", "openai-astra-luna",
                     "opus-sonnet", "anthropic-opus-sonnet"):
            with self.subTest(profile=name), self.assertRaises(ValueError):
                resolve({"team": "pnet", "model_profile": name})

    def test_failed_write_rolls_back_and_can_be_retried(self):
        for configured in (False, True):
            with self.subTest(configured=configured), tempfile.TemporaryDirectory() as temp:
                project = Path(temp).resolve()
                if configured:
                    apply_project(project, "codex", team="bmad", model_profile="inherit")
                paths = [*project.glob(".codex/agents/*"), *project.glob(".plex/*.json"),
                         *project.glob(".plex/*.toml")]
                before = {p: p.read_bytes() for p in paths}
                original = MODULE._atomic_write_bytes
                count = 0

                def fail_once(path, data):
                    nonlocal count
                    count += 1
                    if count == 2:
                        raise OSError("simulated write failure")
                    return original(path, data)

                with patch.object(MODULE, "_atomic_write_bytes", fail_once):
                    with self.assertRaises(OSError):
                        apply_project(project, "codex", team="pnet", model_profile="openai-plus")
                after_paths = [*project.glob(".codex/agents/*"), *project.glob(".plex/*.json"),
                               *project.glob(".plex/*.toml")]
                self.assertEqual({p: p.read_bytes() for p in after_paths}, before)
                self.assertFalse((project / ".plex/.apply.lock").exists())
                apply_project(project, "codex", team="pnet", model_profile="openai-plus")
                self.assertEqual(check_project(project, "codex")["status"], "in_sync")

    def test_concurrent_metadata_edits_are_preserved_and_roles_rolled_back(self):
        for relpath in (".plex/preset.toml", ".plex/resolved.json", ".plex/applied.json"):
            with self.subTest(path=relpath), tempfile.TemporaryDirectory() as temp:
                project = Path(temp).resolve()
                apply_project(project, "codex", team="pnet")
                before = {p: p.read_bytes() for p in project.glob(".codex/agents/*")}
                original = MODULE._atomic_write_bytes
                edited = False

                def edit_once(path, data):
                    nonlocal edited
                    if path.parent.name == "agents" and not edited:
                        edited = True
                        (project / relpath).write_bytes(b"concurrent user edit")
                    return original(path, data)

                with patch.object(MODULE, "_atomic_write_bytes", edit_once):
                    with self.assertRaisesRegex(ValueError, "Concurrent modification"):
                        apply_project(project, "codex", model_profile="openai-plus")
                self.assertTrue(edited)
                self.assertEqual((project / relpath).read_bytes(), b"concurrent user edit")
                self.assertEqual({p: p.read_bytes() for p in project.glob(".codex/agents/*")}, before)

    def test_rollback_preserves_concurrent_role_edit_and_reports_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp).resolve()
            apply_project(project, "codex", team="pnet")
            original = MODULE._atomic_write_bytes
            role_path = project / ".codex/agents/plex-dev.toml"
            def fail_after_edit(path, data):
                if path == project / ".codex/agents/plex-reviewer.toml":
                    role_path.write_bytes(b"concurrent role edit")
                    raise OSError("simulated failure")
                return original(path, data)

            with patch.object(MODULE, "_atomic_write_bytes", fail_after_edit):
                with self.assertRaisesRegex(ValueError, "rollback needs recovery"):
                    apply_project(project, "codex", model_profile="openai-plus")
            self.assertEqual(role_path.read_bytes(), b"concurrent role edit")

    def test_existing_apply_lock_prevents_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp).resolve()
            lock = project / ".plex/.apply.lock"
            lock.parent.mkdir()
            lock.write_text("another process")
            with self.assertRaisesRegex(ValueError, "Another apply"):
                apply_project(project, "codex", team="pnet")
            self.assertEqual(lock.read_text(), "another process")
            self.assertFalse((project / ".codex").exists())

    def test_all_shipped_team_profile_combinations(self):
        for team in (ROOT / "teams").glob("*/team.toml"):
            for profile in MODULE.list_catalog()["model_profiles"][team.parent.name]:
                with self.subTest(team=team.parent.name, profile=profile):
                    result = resolve({"team": team.parent.name, "model_profile": profile})
                    self.assertEqual(result["roles"], tomllib.loads(team.read_text())["roles"])
                    for host in ("codex", "claude", "antigravity"):
                        self.assertEqual(set(result["hosts"][host]), set(result["roles"]))
                    if profile.startswith("openai-") or profile in MODULE.PROFILE_TIERS:
                        for high_role in set(result["roles"]) & {"pm", "architect", "reviewer"}:
                            self.assertIn(result["hosts"]["codex"][high_role]["reasoning"], MODULE.EFFORTS)
                    else:
                        self.assertTrue(all(v == {} for v in result["hosts"]["codex"].values()))
                    if not profile.startswith("anthropic-") and profile not in MODULE.PROFILE_TIERS:
                        self.assertTrue(all(v == {"model": "inherit"}
                                            for v in result["hosts"]["claude"].values()))
                    if not profile.startswith("google-") and profile not in MODULE.PROFILE_TIERS:
                        self.assertTrue(all(v == {"model": "inherit"}
                                            for v in result["hosts"]["antigravity"].values()))

    def test_named_team_uses_its_own_templates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            shutil.copytree(ROOT / "teams", root / "teams")
            shutil.copytree(root / "teams/pnet", root / "teams/focused")
            asset = root / "teams/focused/agents/codex/dev.toml"
            asset.write_text(asset.read_text().replace("Working mode:", "Selected team marker\n\nWorking mode:"))
            with patch.object(MODULE, "ROOT", root):
                resolved = resolve({"team": "focused"})
                self.assertIn("Selected team marker", MODULE.render_role(resolved, "codex", "dev"))

    def test_missing_team_template_never_falls_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            shutil.copytree(ROOT / "teams", root / "teams")
            (root / "teams/bmad/agents/codex/reviewer.toml").unlink()
            with patch.object(MODULE, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "team bmad/reviewer"):
                    resolve({"team": "bmad"})
                self.assertEqual(resolve({"team": "pnet"})["roles"],
                                 ["pm", "explorer", "researcher", "dev", "reviewer", "qa"])

    def test_vendor_tiers(self):
        catalog = MODULE.list_catalog()["model_profiles"]["bmad"]
        self.assertEqual(set(catalog), {"inherit", *MODULE.PROFILE_TIERS} | {
            f"{vendor}-{tier}"
            for vendor in ("openai", "anthropic", "google", "google-anthropic")
            for tier in MODULE.PROFILE_TIERS
        })
        expected = {
            "openai-basic": ("gpt-6-luna", "gpt-6-luna"),
            "openai-plus": ("gpt-6.1-sol", "gpt-6-luna"),
            "openai-pro": ("gpt-6.1-sol", "gpt-6-luna"),
            "openai-pro-plus": ("gpt-6-astra", "gpt-6.1-sol"),
            "anthropic-basic": ("haiku", "haiku"),
            "anthropic-plus": ("sonnet", "haiku"),
            "anthropic-pro": ("sonnet", "haiku"),
            "anthropic-pro-plus": ("opus", "sonnet"),
            "google-basic": ("flash", "flash"),
            "google-plus": ("inherit", "flash"),
            "google-pro": ("inherit", "inherit"),
            "google-pro-plus": ("inherit", "inherit"),
            "google-anthropic-basic": ("claude-sonnet-5-5-low", "claude-sonnet-5-5-low"),
            "google-anthropic-plus": ("claude-sonnet-5-5-medium", "claude-sonnet-5-5-low"),
            "google-anthropic-pro": ("claude-opus-5-5-medium", "claude-sonnet-5-5-medium"),
            "google-anthropic-pro-plus": ("claude-opus-5-5-high", "claude-sonnet-5-5-medium"),
        }
        for profile, (strong, dev) in expected.items():
            host = (
                "codex" if profile.startswith("openai-")
                else "claude" if profile.startswith("anthropic-")
                else "antigravity"
            )
            resolved = resolve({"team": "bmad", "model_profile": profile})["hosts"][host]
            self.assertEqual(resolved["architect"]["model"], strong)
            review_model = {"openai-basic": "gpt-6.1-sol", "anthropic-basic": "sonnet",
                            "google-basic": "inherit", "google-anthropic-basic": "claude-sonnet-5-5-medium"}.get(profile, strong)
            self.assertEqual(resolved["reviewer"]["model"], review_model)
            pm = {"openai-pro-plus": "gpt-6.1-sol", "anthropic-pro-plus": "sonnet",
                  "google-anthropic-pro": "claude-sonnet-5-5-medium",
                  "google-anthropic-pro-plus": "claude-sonnet-5-5-medium"}.get(profile, strong)
            self.assertEqual(resolved["pm"]["model"], pm)
            self.assertEqual(resolved["dev"]["model"], dev)

    def test_openai_basic_is_shared_and_other_tiers_are_explicit(self):
        document = tomllib.loads((ROOT / "teams/bmad/profiles/openai.toml").read_text())
        roles = {"analyst", "pm", "po", "ux", "architect", "dev", "reviewer"}
        for tier, profile in document["profiles"].items():
            if tier == "basic":
                self.assertEqual(profile, {"model": "gpt-6-luna", "reasoning": "high",
                                           "reviewer": {"model": "gpt-6.1-sol", "reasoning": "medium"}})
            else:
                self.assertEqual(set(profile), roles)
            for role, values in (profile.items() if tier != "basic" else []):
                self.assertEqual(set(values), {"model", "reasoning"})
                if tier in ("plus", "pro"):
                    self.assertEqual(
                        values["reasoning"] == "max",
                        role == "dev"
                        or (tier == "plus" and role == "ux"),
                    )
            for team in ("pnet", "bmad"):
                resolved = resolve({"team": team, "model_profile": f"openai-{tier}"})
                for role, values in resolved["hosts"]["codex"].items():
                    team_profile = tomllib.loads((ROOT / f"teams/{team}/profiles/openai.toml").read_text())["profiles"][tier]
                    expected = ({k: v for k, v in team_profile.items() if k in {"model", "reasoning"}}
                                | team_profile.get(role, {})) if tier == "basic" else team_profile[role]
                    self.assertEqual(values, expected)

    def test_anthropic_matches_openai_role_balance(self):
        models = {"gpt-6-luna": "haiku", "gpt-6.1-sol": "sonnet", "gpt-6-astra": "opus"}
        for tier in MODULE.PROFILE_TIERS:
            for team in ("pnet", "bmad"):
                openai = resolve({"team": team, "model_profile": f"openai-{tier}"})["hosts"]["codex"]
                anthropic = resolve({"team": team, "model_profile": f"anthropic-{tier}"})["hosts"]["claude"]
                self.assertEqual(set(openai), set(anthropic))
                for role, values in openai.items():
                    self.assertEqual(anthropic[role], {
                        "model": models[values["model"]], "reasoning": values["reasoning"],
                    })

    def test_new_vendor_file_discovery_and_invalid_sections(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            directory = root / "teams/pnet/profiles"
            directory.mkdir(parents=True)
            (directory.parent / "team.toml").write_text('process = "plain"\nroles = ["pm", "dev", "reviewer"]\n')
            profile = directory / "example.toml"
            profile.write_text('host = "codex"\n[profiles.basic]\nmodel = "example-model"\n')
            with patch.object(MODULE, "ROOT", root):
                self.assertEqual(MODULE.load_model_profiles("pnet")["example-basic"]["codex"], {"model": "example-model"})
                self.assertNotIn("claude", MODULE.named_file("profiles", "example-basic", "pnet"))
                profile.write_text('host = "codex"\n[profiles]\nbasic = "not a table"\n')
                with self.assertRaisesRegex(ValueError, "expected a table"):
                    MODULE.load_model_profiles("pnet")

    def test_precedence_is_per_field(self):
        config = {"team": "bmad", "model_profile": "openai-plus",
                  "codex": {"reasoning": "low", "architect": {"model": "custom-model"},
                            "dev": {"reasoning": "max"}}}
        roles = resolve(config)["hosts"]["codex"]
        self.assertEqual(roles["architect"], {"model": "custom-model", "reasoning": "low"})
        self.assertEqual(roles["pm"], {"model": "gpt-6.1-sol", "reasoning": "low"})
        self.assertEqual(roles["reviewer"], {"model": "gpt-6.1-sol", "reasoning": "low"})
        self.assertEqual(roles["dev"], {"model": "gpt-6-luna", "reasoning": "max"})

    def test_switches_preserve_overrides_without_mutating_source(self):
        config = {"team": "bmad", "model_profile": "openai-plus",
                  "codex": {"dev": {"reasoning": "max"}}}
        original = json.dumps(config, sort_keys=True)
        first = resolve(config)
        self.assertEqual(json.dumps(config, sort_keys=True), original)
        self.assertEqual(first, resolve(config))
        config["team"] = "pnet"
        switched = resolve(config)
        self.assertEqual(switched["model_profile"], "openai-plus")
        self.assertEqual(switched["inactive_overrides"]["codex"], [])
        self.assertEqual(switched["hosts"]["codex"]["dev"]["reasoning"], "max")
        self.assertEqual(switched["hosts"]["codex"]["pm"],
                         MODULE.named_file("profiles", "openai-plus", "pnet")["codex"]["pm"])
        config["team"] = "bmad"
        config["model_profile"] = "openai-pro"
        roles = resolve(config)["hosts"]["codex"]
        self.assertEqual(roles["architect"]["model"], "gpt-6.1-sol")
        self.assertEqual(roles["dev"]["reasoning"], "max")
        config["model_profile"] = "inherit"
        self.assertEqual(resolve(config)["hosts"]["codex"]["dev"], {"reasoning": "max"})
        del config["codex"]
        self.assertEqual(resolve(config)["hosts"]["codex"]["dev"], {})

    def test_legacy_full_presets_remain_supported(self):
        for path in (ROOT / "teams").glob("*/team.toml"):
            config = tomllib.loads(path.read_text())
            config["codex"] = {"model": "custom-model"}
            self.assertEqual(resolve(config)["hosts"]["codex"]["reviewer"], {"model": "custom-model"})
        plain_team = resolve({"roles": ["pm", "dev", "reviewer"], "process": "plain"})
        self.assertEqual(plain_team["roles"], ["pm", "dev", "reviewer"])

    def test_default_team_migrates_to_pnet_on_refresh(self):
        self.assertEqual(resolve({"team": "default"})["team"], "pnet")
        source = MODULE.build_preset_toml({"team": "default", "model_profile": "openai-plus"})
        self.assertEqual(tomllib.loads(source)["team"], "pnet")

    def test_profiles_are_team_local_without_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            shutil.copytree(ROOT / "teams", root / "teams")
            profile = root / "teams/pnet/profiles/openai.toml"
            profile.write_text(profile.read_text().replace("gpt-6.1-sol", "team-specific-model"))
            with patch.object(MODULE, "ROOT", root):
                self.assertEqual(resolve({"team": "pnet", "model_profile": "openai-plus"})[
                    "hosts"]["codex"]["pm"]["model"], "team-specific-model")
                self.assertEqual(resolve({"team": "bmad", "model_profile": "openai-plus"})[
                    "hosts"]["codex"]["pm"]["model"], "gpt-6.1-sol")
                profile.unlink()
                existing = {"team": "bmad", "model_profile": "openai-plus"}
                with self.assertRaisesRegex(ValueError, "Unknown profiles"):
                    MODULE.build_preset_toml(existing, team="pnet")
                self.assertEqual(existing, {"team": "bmad", "model_profile": "openai-plus"})
                selected = MODULE.build_preset_toml(existing, team="pnet", model_profile="inherit")
                self.assertEqual(tomllib.loads(selected)["model_profile"], "inherit")

    def test_profile_roles_match_their_team(self):
        for name, team in MODULE.list_catalog()["teams"].items():
            for profile in MODULE.load_model_profiles(name).values():
                for settings in profile.values():
                    roles = set(settings) - {"model", "reasoning"}
                    if roles:
                        self.assertLessEqual(roles, set(team["roles"]))
                        if "model" not in settings:
                            self.assertEqual(roles, set(team["roles"]))

    def test_invalid_settings_are_rejected(self):
        cases = [
            {"team": "missing"}, {"team": "../bmad"},
            {"team": "pnet", "model_profile": "../inherit"},
            {"team": "pnet", "model_profile": "missing"},
            {"team": "pnet", "roles": ["worker"]},
            {"team": "pnet", "max_agents": True},
            {"team": "pnet", "max_agents": 0},
            {"team": "pnet", "codex": {"reviewr": {"model": "x"}}},
            {"team": "pnet", "codex": {"reasoning": "typo"}},
            {"team": "pnet", "codex": {"reasoning": []}},
            {"team": "pnet", "codex": {"model": ""}},
            {"team": "pnet", "codex": {"model": "inherit"}},
            {"team": "pnet", "claude": {"reasoning": "ultra"}},
            {"team": "pnet", "antigravity": {"model": "sonnet"}},
            {"team": "pnet", "antigravity": {"reasoning": "ultra"}},
            {"team": "pnet", "includes": ["other.toml"]},
            {"roles": ["dev", "dev"]},
            {"roles": ["../dev"]},
            *({"roles": [role], "process": "plain"}
              for role in ("unknown-role", "worker", "tester")),
            {"roles": ["dev"], "process": "bmad", "skills": {}},
            {"roles": ["dev"], "skills": {"dev": ["x", "x"]}},
        ]
        for config in cases:
            with self.subTest(config=config), self.assertRaises(ValueError):
                resolve(config)

    def test_cli_outputs_hashed_snapshot_and_never_writes(self):
        with tempfile.TemporaryDirectory(prefix="plex-config-test-") as temp:
            source = Path(temp).resolve() / "preset.toml"
            for content, success in [('team = "bmad"\nmodel_profile = "openai-plus"\n', True),
                                     ('team = "missing"\n', False), ('team = [', False)]:
                source.write_text(content)
                before = source.read_bytes()
                result = subprocess.run([sys.executable, str(SCRIPT), str(source)],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0 if success else 1, result.stderr)
                self.assertEqual(source.read_bytes(), before)
                self.assertEqual(list(Path(temp).resolve().iterdir()), [source])
                if success:
                    snapshot = json.loads(result.stdout)
                    self.assertEqual(snapshot["source_sha256"], hashlib.sha256(before).hexdigest())
                    self.assertEqual(snapshot["team"], "bmad")
                else:
                    self.assertEqual(result.stdout, "")
                    self.assertIn("Plex configuration error:", result.stderr)

    def test_render_host_roles_injects_models_and_extra_skills(self):
        inherit_resolved = resolve({"team": "pnet", "model_profile": "inherit"})
        codex_inherit = render_host_roles(inherit_resolved, "codex")
        parsed_worker = tomllib.loads(codex_inherit["dev"]["content"])
        self.assertNotIn("model", parsed_worker)
        self.assertNotIn("model_reasoning_effort", parsed_worker)

        custom_bmad = resolve({
            "process": "bmad",
            "roles": ["architect"],
            "skills": {"architect": ["bmad-agent-architect", "custom-arch-skill"]},
            "model_profile": "openai-plus",
        })
        codex_bmad = render_host_roles(custom_bmad, "codex")
        parsed_arch = tomllib.loads(codex_bmad["architect"]["content"])
        self.assertEqual(parsed_arch["model"], "gpt-6.1-sol")
        self.assertEqual(parsed_arch["model_reasoning_effort"], "medium")
        self.assertIn("bmad-agent-architect, custom-arch-skill.", parsed_arch["developer_instructions"])

        claude_opus = resolve({"team": "pnet", "model_profile": "anthropic-pro-plus"})
        claude_roles = render_host_roles(claude_opus, "claude")
        self.assertIn('\nmodel: "sonnet"\n', claude_roles["pm"]["content"])
        self.assertIn('\nmodel: "opus"\n', claude_roles["reviewer"]["content"])
        self.assertIn('\nmodel: "sonnet"\n', claude_roles["dev"]["content"])

        ag_plus = resolve({"team": "pnet", "model_profile": "google-plus"})
        ag_roles = render_host_roles(ag_plus, "antigravity")
        self.assertEqual(ag_roles["pm"]["relpath"], ".agents/agents/plex-pm.md")
        self.assertIn('\nmodel: "inherit"\n', ag_roles["pm"]["content"])
        self.assertIn('\neffort: low\n', ag_roles["pm"]["content"])
        self.assertIn('\nmodel: "flash"\n', ag_roles["dev"]["content"])
        self.assertIn('\neffort: max\n', ag_roles["dev"]["content"])

    def test_apply_check_and_switch_lifecycle_with_backups_and_dual_hosts(self):
        with tempfile.TemporaryDirectory(prefix="plex-lifecycle-test-") as temp:
            project = Path(temp).resolve()
            initial_check = check_project(project, host="codex")
            self.assertEqual(initial_check["status"], "needs_setup")

            applied_codex = apply_project(
                project, host="codex", team="bmad", model_profile="openai-plus"
            )
            self.assertEqual(applied_codex["status"], "applied")
            self.assertEqual(applied_codex["team"], "bmad")
            self.assertIsNone(applied_codex["backup_dir"])
            self.assertEqual(check_project(project, host="codex")["status"], "in_sync")

            applied_claude = apply_project(project, host="claude")
            self.assertEqual(applied_claude["status"], "applied")
            applied_ag = apply_project(project, host="antigravity")
            self.assertEqual(applied_ag["status"], "applied")
            self.assertTrue((project / ".agents/agents/plex-pm.md").is_file())
            self.assertEqual(check_project(project)["status"], "in_sync")

            switched_codex = apply_project(project, host="codex", team="pnet")
            self.assertEqual(switched_codex["team"], "pnet")
            self.assertEqual(switched_codex["archived_roles"], ["analyst", "architect", "po", "ux"])
            self.assertIsNotNone(switched_codex["backup_dir"])
            self.assertTrue(switched_codex["other_host"]["needs_refresh"])
            self.assertEqual(switched_codex["other_hosts_needing_refresh"], ["claude", "antigravity"])

            backup_path = project / switched_codex["backup_dir"]
            for retired in ("analyst", "architect", "po", "ux"):
                self.assertTrue((backup_path / f"plex-{retired}.toml").is_file())
                self.assertFalse((project / f".codex/agents/plex-{retired}.toml").exists())

            self.assertEqual(check_project(project, host="codex")["status"], "in_sync")
            self.assertEqual(check_project(project, host="claude")["status"], "needs_refresh")
            self.assertEqual(check_project(project, host="antigravity")["status"], "needs_refresh")

            refreshed_claude = apply_project(project, host="claude")
            self.assertEqual(refreshed_claude["archived_roles"], ["analyst", "architect", "po", "ux"])
            refreshed_ag = apply_project(project, host="antigravity")
            self.assertEqual(refreshed_ag["archived_roles"], ["analyst", "architect", "po", "ux"])
            self.assertEqual(check_project(project)["status"], "in_sync")

    def test_conflicts_abort_before_writes(self):
        with tempfile.TemporaryDirectory(prefix="plex-conflict-test-") as temp:
            project = Path(temp).resolve()
            unmanaged = project / ".codex/agents/plex-dev.toml"
            unmanaged.parent.mkdir(parents=True)
            unmanaged.write_text('name = "plex-dev"\n')
            with self.assertRaises(ValueError) as ctx:
                apply_project(project, host="codex", team="pnet")
            self.assertIn("Unmanaged file collision", str(ctx.exception))
            self.assertFalse((project / ".plex/preset.toml").exists())

        with tempfile.TemporaryDirectory(prefix="plex-edit-conflict-test-") as temp:
            project = Path(temp).resolve()
            apply_project(project, host="codex", team="pnet", model_profile="inherit")
            worker_path = project / ".codex/agents/plex-dev.toml"
            worker_path.write_text(worker_path.read_text() + "# local edit\n")
            check_state = check_project(project, host="codex")
            self.assertEqual(check_state["status"], "conflict")
            with self.assertRaises(ValueError) as ctx:
                apply_project(project, host="codex", model_profile="openai-plus")
            self.assertIn("modified outside Plex", str(ctx.exception))
            self.assertIn("# local edit", worker_path.read_text())


if __name__ == "__main__":
    unittest.main()
