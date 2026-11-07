"""Test harness.

The repo root *is* the plugin package (``__init__.py`` + relative imports), but the folder name
is not importable, so we load it the way Hermes's validator does: as a package from its path.
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
    return _load("phone_senses", ROOT / "__init__.py", ROOT)


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
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", secret, app
    finally:
        server.shutdown()
        server.server_close()
