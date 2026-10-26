"""TOML metadata, automatic legacy migration and preserved recovery evidence."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("metadata_setup", ROOT / "setup.py")
I = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(I)
C = I.CONFIG


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        env = {"HOME": str(self.root / "home"), "CODEX_HOME": str(self.root / "home/.codex"),
               "CLAUDE_CONFIG_DIR": str(self.root / "home/.claude")}
        context = patch.dict(os.environ, env)
        context.start()
        self.addCleanup(context.stop)

    def legacy_install(self, project, host="codex", scope="project"):
        C.apply_project(project, host, team="bmad", model_profile="pro-plus",
                        max_agents=4, interaction="auto", scope=scope,
                        host_overrides={host: {"dev": {"reasoning": "high"}}})
        root = C.installation_root(project, host, scope)
        alias = root / ".plex/skill-aliases.toml"
        alias.write_text(C.metadata_toml({"source": str(ROOT), "config_block": False}))
        saved = {}
        for name in ("applied", "resolved", "skill-aliases"):
            target = root / ".plex" / (name + ".toml")
            value = C.read_metadata(target)
            saved[name] = value
            target.with_suffix(".json").write_text(json.dumps(value, ensure_ascii=False, indent=2))
            target.unlink()
        return root, saved

    def test_metadata_toml_roundtrips_profiles_workflows_and_quoted_values(self):
        for team in ("pnet", "bmad"):
            for profile in ("inherit", "plus", "pro-plus", "ultra-plus"):
                value = C.resolve({"team": team, "model_profile": profile})
                text = C.metadata_toml(value)
                self.assertEqual(tomllib.loads(text), value)
                self.assertIn("[hosts.codex", text)
        value = {"source": '/workspace/"quoted"\\path\n界', "enabled": False,
                 "empty": {}, "list": [], "dotted.key": {"hyphen-key": "value"}}
        self.assertEqual(tomllib.loads(C.metadata_toml(value)), value)
        with self.assertRaises(ValueError):
            C.metadata_toml({"unsupported": None})

    def test_apply_migrates_all_metadata_in_every_scope_and_client(self):
        for scope in ("project", "user"):
            for host in C.HOSTS:
                with self.subTest(scope=scope, host=host):
                    project = self.root / (scope + "-" + host)
                    project.mkdir()
                    root, saved = self.legacy_install(project, host, scope)
                    before = {p: p.read_bytes() for p in (root / ".plex").glob("*.json")}
                    status = C.check_project(project, host, scope)
                    self.assertEqual(status["status"], "in_sync")
                    self.assertEqual(status["metadata"]["format"], "json")
                    self.assertEqual({p: p.read_bytes() for p in before}, before)
                    result = C.apply_project(project, host, scope=scope)
                    self.assertEqual(len(result["migrated_metadata"]), 3)
                    for name, value in saved.items():
                        target = root / ".plex" / (name + ".toml")
                        self.assertFalse(target.with_suffix(".json").exists())
                        self.assertEqual(C.read_metadata(target), value)
                        backup = root / result["backup_dir"] / "metadata" / (name + ".json")
                        self.assertEqual(backup.read_bytes(), before[target.with_suffix(".json")])
                    self.assertEqual(C.check_project(project, host, scope)["metadata"]["format"], "toml")
                    again = C.apply_project(project, host, scope=scope)
                    self.assertEqual(again["written_roles"], [])
                    self.assertEqual(again["migrated_metadata"], [])
                    self.assertIsNone(again["backup_dir"])

    def test_migration_conflict_symlink_and_failure_preserve_sources(self):
        for case in ("conflict", "symlink", "failure", "concurrent"):
            with self.subTest(case=case):
                project = self.root / case
                project.mkdir()
                root, saved = self.legacy_install(project)
                original = {p.name: p.read_bytes() for p in (root / ".plex").glob("*.json")}
                target = root / ".plex/resolved.toml"
                if case == "conflict":
                    target.write_text(C.metadata_toml({**saved["resolved"], "max_agents": 99}))
                    with self.assertRaisesRegex(ValueError, "Conflicting"):
                        C.apply_project(project, "codex")
                elif case == "symlink":
                    external = self.root / "external.json"
                    external.write_text("private external data")
                    (root / ".plex/resolved.json").unlink()
                    (root / ".plex/resolved.json").symlink_to(external)
                    with self.assertRaisesRegex(ValueError, "symlink"):
                        C.apply_project(project, "codex")
                    self.assertEqual(external.read_text(), "private external data")
                    continue
                else:
                    archive = C._ApplyTransaction.archive
                    def fail(transaction, path, backup):
                        archive(transaction, path, backup)
                        if path.name == "applied.json":
                            raise OSError("migration failure")
                    write = C._atomic_write_bytes
                    legacy = root / ".plex/resolved.json"
                    def race(path, data):
                        digest = write(path, data)
                        if path == target:
                            legacy.write_text(json.dumps({**saved["resolved"], "max_agents": 9}))
                        return digest
                    with patch.object(C._ApplyTransaction, "archive", fail) if case == "failure" else patch.object(C, "_atomic_write_bytes", race):
                        with self.assertRaises((OSError, ValueError)):
                            C.apply_project(project, "codex")
                    self.assertFalse(target.exists())
                    self.assertFalse((root / ".plex/applied.toml").exists())
                    if case == "concurrent":
                        self.assertEqual(json.loads(legacy.read_text())["max_agents"], 9)
                        del original[legacy.name]
                for name, data in original.items():
                    self.assertEqual((root / ".plex" / name).read_bytes(), data)

    def test_legacy_skill_links_migrate_with_backups_and_rollback(self):
        project = self.root / "aliases"
        project.mkdir()
        with I.apply_skills(I.plan_skills(project, aliases=True)):
            pass
        target = project / ".plex/skill-aliases.toml"
        value = C.read_metadata(target)
        legacy = target.with_suffix(".json")
        raw = json.dumps(value).encode()
        legacy.write_bytes(raw)
        target.unlink()
        plan = I.plan_skills(project, aliases=True)
        self.assertFalse(target.exists())
        with self.assertRaises(OSError):
            with I.apply_skills(plan):
                raise OSError("later apply failure")
        self.assertEqual(legacy.read_bytes(), raw)
        self.assertFalse(target.exists())
        with I.apply_skills(I.plan_skills(project, aliases=True)):
            pass
        self.assertFalse(legacy.exists())
        self.assertEqual(C.read_metadata(target), value)
        self.assertTrue(any(p.read_bytes() == raw for p in project.glob('.plex/backups/*/codex/metadata/skill-aliases.json')))

    def test_legacy_uninstall_removes_owned_files(self):
        project = self.root / "uninstall"
        project.mkdir()
        root, _ = self.legacy_install(project)
        result = C.uninstall_project(project, "codex")
        self.assertEqual(result["status"], "uninstalled")
        self.assertFalse((root / ".plex/applied.json").exists())
        self.assertFalse((root / ".plex/resolved.json").exists())

    def test_legacy_changes_after_planning_are_not_overwritten(self):
        project = self.root / "planning-race"
        project.mkdir()
        root, saved = self.legacy_install(project)
        read = C.read_metadata
        legacy = root / ".plex/applied.json"
        changed = json.loads(json.dumps(saved["applied"]))
        changed["hosts"]["codex"]["max_agents"] = 9
        def race(path):
            value = read(path)
            if path.name == "applied.toml":
                legacy.write_text(json.dumps(changed))
            return value
        with patch.object(C, "read_metadata", race):
            with self.assertRaisesRegex(ValueError, "metadata changed"):
                C.apply_project(project, "codex")
        self.assertEqual(json.loads(legacy.read_text()), changed)
        self.assertFalse((root / ".plex/applied.toml").exists())

    def test_matching_duplicates_migrate_but_ambiguous_json_is_preserved(self):
        project = self.root / "matching"
        project.mkdir()
        root, saved = self.legacy_install(project)
        (root / ".plex/resolved.toml").write_text(C.metadata_toml(saved["resolved"]))
        C.apply_project(project, "codex")
        self.assertFalse((root / ".plex/resolved.json").exists())
        legacy = root / ".plex/applied.json"
        raw = '{"hosts":{},"hosts":{}}'
        legacy.write_text(raw)
        with self.assertRaisesRegex(ValueError, "Duplicate metadata key"):
            C.apply_project(project, "codex")
        self.assertEqual(legacy.read_text(), raw)
