# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Partial integration with real, pinned Hermes source; no dependency installation.

This imports the complete official registry, constants, ownership coordinator and
skill utilities. It compiles unchanged AST nodes for the real directory package
loader, manifest dataclass, context registrars, ledger and skill queries. There is
no fake context or fake registry. YAML/config parsing, enablement/catalog gates,
PluginManager startup, CLI/model behavior and deadline guards are not exercised.
No upstream host source is distributed inside this plugin.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import logging
import os
import subprocess
import sys
import threading
import types
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, Tuple, Union

EXPECTED_SOURCE_PIN = "7bc05085f09ee9bfa9cecaaa3cf44758bdff96a6"
SOURCE_ROOT = None
logger = logging.getLogger("hermes_cli.plugins")
_NS_PARENT = "hermes_plugins"
_MODULE_NAMESPACE_LOCK = threading.RLock()
_BARE_MODULE_SCOPE: dict[str, str] = {}
_UNSET = object()


def _compile_nodes(relative: str, names: set[str], methods: dict[str, set[str]] | None = None):
    """Select unchanged official AST nodes; original filenames/lines survive."""
    path = SOURCE_ROOT / relative
    original = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    selected = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    for node in original.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in names:
            if isinstance(node, ast.ClassDef) and methods and node.name in methods:
                node.body = [child for child in node.body
                             if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                             and child.name in methods[node.name]]
            selected.append(node)
    found = {node.name for node in selected if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    if found != names:
        raise RuntimeError(f"Official source nodes missing from {relative}: {names - found}")
    compiled = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(compiled)
    exec(compile(compiled, str(path), "exec"), globals())


def _source_revision(root: Path):
    marker = root / "SOURCE_PIN.txt"
    if marker.is_file():
        for line in marker.read_text(encoding="utf-8").splitlines():
            if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
                return line
    if (root / ".git").exists():
        try:
            result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                                    capture_output=True, text=True, timeout=10, check=True)
            return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return None


def load_host(source_root=None):
    """Return real host components from --hermes-source or HERMES_SOURCE."""
    global SOURCE_ROOT, registry, replacement_coordinator, hermes_home_key
    value = source_root or os.environ.get("HERMES_SOURCE")
    if not value:
        raise ValueError("Supply --hermes-source PATH or HERMES_SOURCE for an official Hermes checkout/snapshot.")
    root = Path(value).resolve()
    if SOURCE_ROOT is not None:
        if root != SOURCE_ROOT:
            raise ValueError("Only one Hermes source tree can be used per process.")
        return NativeComponents, registry, _source_revision(root)
    required = ("hermes_constants.py", "registration_lifecycle.py", "tools/registry.py",
                "hermes_cli/plugins_manifest.py", "hermes_cli/plugins_loader.py",
                "hermes_cli/plugins_ledger.py", "hermes_cli/plugins.py",
                "hermes_cli/plugins_content.py", "agent/skill_utils.py")
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError("Hermes source files missing: " + ", ".join(missing))
    revision = _source_revision(root)
    if revision is not None and revision != EXPECTED_SOURCE_PIN:
        raise ValueError(f"Host source revision {revision} differs from tested pin {EXPECTED_SOURCE_PIN}.")
    SOURCE_ROOT = root
    sys.path.insert(0, str(root))
    registry = importlib.import_module("tools.registry").registry
    replacement_coordinator = importlib.import_module("registration_lifecycle").replacement_coordinator
    hermes_home_key = importlib.import_module("hermes_constants").hermes_home_key
    _compile_nodes("hermes_cli/plugins_manifest.py", {"PluginManifest", "manifest_key"})
    _compile_nodes("hermes_cli/plugins_loader.py", {"_evict_modules", "_serialized_replacement", "PluginLoaderMixin"},
                   {"PluginLoaderMixin": {"_directory_module_name", "_load_directory_module"}})
    _compile_nodes("hermes_cli/plugins_ledger.py", {"PluginRegistration", "PluginLedgerMixin"})
    _compile_nodes("hermes_cli/plugins.py", {"PluginContext"},
                   {"PluginContext": {"__init__", "plugin_id", "_track", "_track_replacement",
                                      "_track_mapping_entry", "_register_entry", "register_tool",
                                      "_tool_override_allowed"}})
    _compile_nodes("hermes_cli/plugins_content.py", {"register_skill"})
    PluginContext.register_skill = register_skill

    class Components(PluginLoaderMixin, PluginLedgerMixin):
        """Harness initialization; loading/registration/dispatch use official code."""

        def __init__(self, home: Path):
            self.home_path = Path(home).resolve()
            self.scope_key = hermes_home_key(self.home_path)
            self._plugin_tool_names = set()
            self._plugin_skills = {}
            self._registration_order = []
            self._ownership_ledger = {}
            self._memory_hook_registrations = {}

        def load_package(self, path: Path, name: str = "spindoctor-qwerty"):
            # Manifest metadata is constructed from the real dataclass, not YAML.
            manifest = PluginManifest(name=name, key=name, path=str(Path(path).resolve()), source="user")
            module = self._load_directory_module(manifest)
            ctx = PluginContext(manifest, self)
            module.register(ctx)
            return module, ctx

        def dispose_registered_handles(self):
            for handle in list(reversed(self._registration_order)):
                handle.dispose()

    # Preserve the exact real PluginManager skill query methods too.
    query_path = SOURCE_ROOT / "hermes_cli/plugins.py"
    query_tree = ast.parse(query_path.read_text(encoding="utf-8"), filename=str(query_path))
    query_class = next(node for node in query_tree.body
                       if isinstance(node, ast.ClassDef) and node.name == "PluginManager")
    query_names = {"find_plugin_skill", "list_plugin_skills", "list_plugin_skill_metadata"}
    query_nodes = [node for node in query_class.body
                   if isinstance(node, ast.FunctionDef) and node.name in query_names]
    query_module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
                              + query_nodes, type_ignores=[])
    ast.fix_missing_locations(query_module)
    exec(compile(query_module, str(query_path), "exec"), globals())
    for name in query_names:
        setattr(Components, name, globals()[name])
    globals()["NativeComponents"] = Components
    return Components, registry, revision

