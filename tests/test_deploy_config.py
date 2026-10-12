"""The Vercel entrypoint in pyproject.toml must point at the real FastAPI app."""
import importlib
import json
import tomllib
from pathlib import Path

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parent.parent


def test_vercel_entrypoint_resolves_to_the_app():
    entry = tomllib.loads((ROOT / 'pyproject.toml').read_text())['tool']['vercel']['entrypoint']
    module, attr = entry.split(':')
    assert isinstance(getattr(importlib.import_module(module), attr), FastAPI)


def test_vercel_function_path_exists():
    functions = json.loads((ROOT / 'vercel.json').read_text())['functions']
    for path in functions:
        assert (ROOT / path).is_file(), path
