"""Offline copy of `hermes plugins validate`'s capability probe and manifest checks."""
from __future__ import annotations

from pathlib import Path

import pytest

import phone_senses

yaml = pytest.importorskip("yaml")
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = yaml.safe_load((ROOT / "plugin" / "plugin.yaml").read_text(encoding="utf-8"))
CONFIG_TYPES = {"str", "string", "int", "integer", "float", "number", "bool", "boolean", "list", "array",
                "dict", "object", "secret"}


class RecordingContext:
    """Mirrors hermes_cli/plugin_validate.py: records registrations, get_config returns the default."""

    def __init__(self):
        self.tools, self.hooks, self.commands, self.skills = [], [], [], []

    def register_tool(self, name, *args, **kwargs):
        self.tools.append(name)

    def register_hook(self, hook_name, callback, *, hold_stream=False):
        self.hooks.append(hook_name)

    def register_command(self, name, *args, **kwargs):
        self.commands.append(name)

    def register_skill(self, name, path, *args, **kwargs):
        assert Path(path).is_file()
        self.skills.append(name)

    def get_config(self, key, default=None):
        return default


def test_register_matches_declared_capabilities():
    ctx = RecordingContext()
    phone_senses.register(ctx)
    assert sorted(ctx.tools) == sorted(MANIFEST["provides_tools"])
    assert len(ctx.tools) == len(set(ctx.tools))
    assert ctx.hooks == MANIFEST["provides_hooks"] == ["pre_tool_call"]
    assert ctx.commands == ["phone"] and ctx.skills == ["phone-senses"]


def test_manifest_fields():
    for field in ("name", "version", "description", "requires_hermes", "license"):
        assert MANIFEST.get(field)
    assert MANIFEST["name"] == "phone-senses" and MANIFEST["requires_hermes"].startswith(">=")
    for key, spec in MANIFEST["config_schema"].items():
        assert str(spec.get("type")).lower() in CONFIG_TYPES, key
    assert MANIFEST["config_schema"]["helper_token"] == {**MANIFEST["config_schema"]["helper_token"],
                                                         "type": "secret", "env": "PHONE_SENSES_TOKEN"}


def test_schemas_well_formed():
    for name, schema in phone_senses.TOOL_SCHEMAS.items():
        assert schema["name"] == name and name.startswith("phone_")
        assert schema["parameters"]["type"] == "object" and len(schema["description"]) > 15
        for req in schema["parameters"]["required"]:
            assert req in schema["parameters"]["properties"]


def test_no_compiled_or_secret_files_tracked():
    import subprocess
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    assert not [f for f in files if f.endswith((".pyc", ".db", ".so", ".exe", ".env")) or f == ".env"]
