"""Test harness.

The plugin lives in ``plugin/`` (``__init__.py`` + relative imports). We load it the way Hermes's
validator does: as a package from its path, under the name ``phone_senses``.
The phone helper is a standalone script, loaded from its file.
"""
from __future__ import annotations

import importlib.util
import secrets
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HELPER_DIR = ROOT / "phone_helper"
PLUGIN_DIR = ROOT / "plugin"


def _load(name: str, path: Path, package_dir: Path | None = None):
    if name in sys.modules:
        return sys.modules[name]
    kwargs = {"submodule_search_locations": [str(package_dir)]} if package_dir else {}
    spec = importlib.util.spec_from_file_location(name, path, **kwargs)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_helper():
    return _load("ps_helper", HELPER_DIR / "helper.py")


def load_plugin():
    return _load("phone_senses", PLUGIN_DIR / "__init__.py", PLUGIN_DIR)


# Make ``import phone_senses`` work in every test module.
load_plugin()


@pytest.fixture(scope="session")
def helper():
    return load_helper()


@pytest.fixture()
def mock_server(helper):
    """A real HTTP helper in mock mode on a random local port: (base_url, secret, app)."""
    secret = secrets.token_hex(32)
    runner = helper.MockRunner()
    app = helper.App(secret, runner, mock=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), helper.make_handler(app))
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", secret, app
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture()
def plugin(mock_server, tmp_path):
    """The plugin wired to a mock helper and a temp database: (package, helper_app)."""
    import sqlite3

    ps = load_plugin()
    url, secret, app = mock_server
    ps.client.set_client(ps.client.PhoneClient(url, secret, timeout=5))
    db = tmp_path / "data.db"
    ps.storage.set_connector(lambda: sqlite3.connect(db))
    settings: dict = {}

    class Ctx:
        def get_config(self, key, default=None):
            return settings.get(key, default)

    ps.client.configure(Ctx())
    ps.settings = settings
    try:
        yield ps, app
    finally:
        ps.client.set_client(None)
        ps.storage.set_connector(None)
        ps.client.configure(None)
