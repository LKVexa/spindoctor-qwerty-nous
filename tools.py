# SpinDoctor Qwerty 1.1.0 - Nous native tool handlers
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Hermes handlers take an argument dictionary and return a JSON string."""
import json
import threading

from .engine.spindoctor import api

# Shared state is persistent. Serialize calls to avoid concurrent session writes.
_LOCK = threading.RLock()


def _run(name, args):
    try:
        if args is not None and not isinstance(args, dict):
            raise ValueError("Tool arguments must be an object.")
        with _LOCK:
            result = api.call(name, dict(args or {}))
        if not result.get("ok"):
            result.setdefault("error", "SpinDoctor call failed")
        return api.as_json(result)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)


def spindoctor_run_script(args, **kwargs):
    return _run("spindoctor_run_script", args)


def spindoctor_run_preset(args, **kwargs):
    return _run("spindoctor_run_preset", args)


def spindoctor_list_presets(args, **kwargs):
    return _run("spindoctor_list_presets", args)


def spindoctor_report(args, **kwargs):
    return _run("spindoctor_report", args)


def spindoctor_functions(args, **kwargs):
    return _run("spindoctor_functions", args)


def spindoctor_test_theory(args, **kwargs):
    return _run("spindoctor_test_theory", args)


HANDLERS = {
    "spindoctor_run_script": spindoctor_run_script,
    "spindoctor_run_preset": spindoctor_run_preset,
    "spindoctor_list_presets": spindoctor_list_presets,
    "spindoctor_report": spindoctor_report,
    "spindoctor_functions": spindoctor_functions,
    "spindoctor_test_theory": spindoctor_test_theory,
}
