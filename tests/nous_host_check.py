#!/usr/bin/env python3
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Repeatable native Hermes component checks, without installing Hermes.

Supply the official pinned source via --hermes-source or HERMES_SOURCE.
This tests real package loading, registrars, registry dispatch and ownership
handles. Full CLI/config/manifest startup and real model calls are excluded.
Usage: python -B tests/nous_host_check.py --hermes-source PATH --out native.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from native_components import EXPECTED_SOURCE_PIN, load_host

EXPECTED = {"spindoctor_run_script", "spindoctor_run_preset", "spindoctor_list_presets",
            "spindoctor_report", "spindoctor_functions", "spindoctor_test_theory"}
SKILL = "spindoctor-qwerty:spindoctor-qwerty"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-source")
    parser.add_argument("--plugin", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--out", default="nous-native-results.json")
    args = parser.parse_args()
    package = Path(args.plugin).resolve()
    checks = []
    started = time.monotonic()

    def check(name, passed, detail=""):
        checks.append({"check": name, "pass": bool(passed), "detail": str(detail)[:500]})
        print(("PASS " if passed else "FAIL ") + name + ("" if passed else " -- " + str(detail)[:300]), flush=True)

    NativeComponents, registry, revision = load_host(args.hermes_source)
    with tempfile.TemporaryDirectory(prefix="nous-native-") as temporary:
        root = Path(temporary).resolve()
        os.environ["SPINDOCTOR_WORKSPACE"] = str(root / "default-ws")
        os.environ.pop("SPINDOCTOR_MEASUREMENT_SEED", None)
        os.environ.pop("SPINDOCTOR_FIELD_SEED", None)
        host = NativeComponents(root / "home-a")
        prior_spindoctor = sys.modules.get("spindoctor")
        sentinel = types.ModuleType("spindoctor")
        sentinel.native_test_sentinel = True
        sys.modules["spindoctor"] = sentinel
        try:
            module, ctx = host.load_package(package)

            def tool(name, arguments, **kwargs):
                raw = registry.dispatch(name, arguments, scope=host.scope_key, **kwargs)
                if not isinstance(raw, str):
                    raise TypeError("Native handler returned non-string output")
                decoded = json.loads(raw)
                if not isinstance(decoded, dict):
                    raise TypeError("Native handler returned non-object JSON")
                return decoded

            def script(text, workspace=None):
                arguments = {"script": text}
                if workspace:
                    arguments["workspace"] = str(workspace)
                return tool("spindoctor_run_script", arguments)

            metadata = json.loads((package / "plugin.yaml").read_text(encoding="utf-8"))
            check("official host source pin", revision == EXPECTED_SOURCE_PIN, revision)
            check("plugin manifest declares six tools", set(metadata["provides_tools"]) == EXPECTED, metadata["provides_tools"])
            check("plugin and engine versions", metadata["version"] == "1.1.0"
                  and module.tools.api.CARTRIDGE_VERSION == "1.1.0"
                  and module.tools.api.ENGINE_VERSION == "3.1.2")
            check("GPL-3.0-or-later and author metadata", metadata["license"] == "GPL-3.0-or-later"
                  and "RUSSELL PHILIP SMITHSON" in metadata["author"]
                  and "Version 3, 29 June 2007" in (package / "LICENSE").read_text(encoding="utf-8"))
            check("native registry has all six handlers", host._plugin_tool_names == EXPECTED, sorted(host._plugin_tool_names))
            entries = [registry.get_entry(name, scope=host.scope_key) for name in EXPECTED]
            check("native registry receives model descriptions and object schemas", all(
                entry and entry.toolset == "spindoctor_qwerty"
                and entry.schema.get("name") == entry.name
                and entry.schema.get("description")
                and entry.schema.get("parameters", {}).get("type") == "object"
                for entry in entries))
            check("native schemas match engine tool contracts", all(
                module.schemas.SCHEMAS[item["name"]] == item for item in module.tools.api.TOOLS))
            check("relative imports do not overwrite an existing spindoctor module", sys.modules.get("spindoctor") is sentinel
                  and module.tools.api.__name__.startswith(module.__name__ + ".engine.spindoctor."))
            skill_path = host.find_plugin_skill(SKILL)
            check("namespaced native skill resolves to package SKILL.md", skill_path == package / "skills" / "spindoctor-qwerty" / "SKILL.md"
                  and skill_path.is_file(), skill_path)
            skill_metadata = host.list_plugin_skill_metadata()
            check("native skill metadata is available for progressive disclosure", host.list_plugin_skills("spindoctor-qwerty") == ["spindoctor-qwerty"]
                  and len(skill_metadata) == 1 and skill_metadata[0]["name"] == SKILL
                  and bool(skill_metadata[0]["description"]), skill_metadata)
            check("registration writes no simulator workspace", not (root / "default-ws").exists())
            listing = tool("spindoctor_list_presets", {}, task_id="native-task", session_id="native-session", parent_agent=object())
            check("native dispatch accepts Hermes context kwargs and lists 241 presets", listing.get("ok") and listing.get("count") == 241)
            functions = tool("spindoctor_functions", {})
            check("native dispatch returns Markdown function table", functions.get("ok") and "| Function |" in functions.get("markdown", "")
                  and "298" in functions.get("markdown", ""))
            invalid = tool("spindoctor_run_script", [])
            check("non-object tool arguments return a useful JSON error", not invalid.get("ok") and "object" in invalid.get("error", ""), invalid)
            unknown = tool("spindoctor_no_such_tool", {})
            check("native registry rejects unknown tool names", "Unknown tool" in unknown.get("error", ""), unknown)
            empty = tool("spindoctor_run_script", {})
            malformed = tool("spindoctor_run_script", {"script": 9})
            check("missing and malformed scripts stay in JSON error channel", not empty.get("ok") and empty.get("error")
                  and not malformed.get("ok") and malformed.get("error"))
            unknown_command = script("q.nonexistent operation")
            check("unsupported commands are reported as failures", not unknown_command.get("ok")
                  and bool(unknown_command.get("results", [{}])[0].get("error")), unknown_command)
            too_wide = script("q.circuit new above_limit 299")
            too_many_shots = script("q.circuit new shot_limit 1\nq.circuit run shots 100001 basis z")
            check("logical qubit and shot limits are enforced through native dispatch", not too_wide.get("ok") and not too_many_shots.get("ok"))
            too_long = script("q." + "x" * 5000)
            check("command length limit is enforced through native dispatch", not too_long.get("ok")
                  and "4096" in str(too_long), too_long)
            traversal = tool("spindoctor_report", {"name": "../outside.txt"})
            check("report traversal is refused", not traversal.get("ok") and "inside" in traversal.get("error", ""), traversal)

            bell = script("q.circuit new native_bell 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 128 basis z")
            check("native script executes a Bell circuit", bell.get("ok") and len(bell.get("results", [])) == 4, bell.get("error"))
            report_groups = [row.get("reports", []) for row in bell.get("results", [])]
            all_reports = [path for group in report_groups for path in group]
            check("every successful script command has distinct TXT/JSON/PDF reports", len(report_groups) == 4
                  and all({Path(path).suffix.lower() for path in group} >= {".txt", ".json", ".pdf"} for group in report_groups)
                  and len(all_reports) == len(set(all_reports))
                  and all(Path(path).is_absolute() and Path(path).is_file() for path in all_reports), report_groups)
            report_files = [path for path in all_reports if path.endswith(".txt")]
            read = tool("spindoctor_report", {"name": Path(report_files[-1]).name}) if report_files else {}
            check("native report tool reads a generated report", read.get("ok") and bool(read.get("text")), read.get("error"))
            persisted = script("q.circuit show")
            check("native calls preserve workspace circuit state", persisted.get("ok") and "native_bell" in json.dumps(persisted), persisted.get("error"))
            explicit = script("q.circuit new explicit_workspace 1", root / "explicit-ws")
            check("explicit workspace argument takes precedence", explicit.get("ok")
                  and Path(explicit.get("workspace", "")).resolve() == root / "explicit-ws"
                  and (root / "explicit-ws" / "spindoctor-cartridge-session.json").is_file())
            preset = tool("spindoctor_run_preset", {"preset_id": "qc-061", "workspace": str(root / "preset-ws")})
            check("native preset handler executes and writes reports", preset.get("ok") and bool(preset.get("reports")), preset.get("error"))
            theory = tool("spindoctor_test_theory", {"action": "extract", "source": "text", "text": "A Hadamard gate gives a balanced measurement."})
            check("native theory handler extracts text", theory.get("ok") and "Hadamard" in json.dumps(theory), theory.get("error"))
            concurrent_workspace = root / "concurrent-ws"

            def concurrent_call(index):
                return script("q.circuit new native_concurrent_%d 1" % index, concurrent_workspace)

            with ThreadPoolExecutor(max_workers=4) as pool:
                concurrent = list(pool.map(concurrent_call, range(8)))
            saved = json.loads((concurrent_workspace / "spindoctor-cartridge-session.json").read_text(encoding="utf-8"))
            check("native wrapper serializes concurrent shared-workspace writes", all(row.get("ok") for row in concurrent)
                  and all("native_concurrent_%d" % index in json.dumps(saved) for index in range(8)))

            host_b = NativeComponents(root / "home-b")
            module_b, ctx_b = host_b.load_package(package)
            check("different Hermes homes have isolated package modules and registries", module_b.__name__ != module.__name__
                  and module_b.tools.api is not module.tools.api
                  and registry.get_entry("spindoctor_functions", scope=host_b.scope_key).handler is module_b.tools.spindoctor_functions
                  and registry.get_entry("spindoctor_functions", scope=host.scope_key).handler is module.tools.spindoctor_functions)
            host_b.dispose_registered_handles()
            check("disposing a different home's handles preserves this home's tools", registry.get_entry("spindoctor_functions", scope=host_b.scope_key) is None
                  and registry.get_entry("spindoctor_functions", scope=host.scope_key) is not None)

            old_handles = list(host._registration_order)
            old_tools = module.tools
            old_tools.native_reload_sentinel = True
            reloaded, reload_ctx = host.load_package(package)
            check("real directory reload evicts stale relative submodules", reloaded is not module
                  and reloaded.tools is not old_tools and not hasattr(reloaded.tools, "native_reload_sentinel"))
            for handle in reversed(old_handles):
                handle.dispose()
            check("disposing stale handles preserves newer registrations", all(
                registry.get_entry(name, scope=host.scope_key).handler is reloaded.tools.HANDLERS[name] for name in EXPECTED)
                  and host.find_plugin_skill(SKILL) is not None)
            host.dispose_registered_handles()
            check("native ownership disposal removes all tools and skill", not host._registration_order
                  and not host._plugin_tool_names and host.find_plugin_skill(SKILL) is None
                  and all(registry.get_entry(name, scope=host.scope_key) is None for name in EXPECTED))
            final_module, final_ctx = host.load_package(package)
            check("fresh registration after disposal starts cleanly", host._plugin_tool_names == EXPECTED
                  and len(host._registration_order) == 7 and host.find_plugin_skill(SKILL) is not None)
        finally:
            host.dispose_registered_handles()
            if prior_spindoctor is None:
                sys.modules.pop("spindoctor", None)
            else:
                sys.modules["spindoctor"] = prior_spindoctor

    summary = {"passed": sum(item["pass"] for item in checks), "total": len(checks),
               "seconds": round(time.monotonic() - started, 2), "python": sys.version.split()[0],
               "host_source_pin": revision, "coverage": "partial real Hermes source components",
               "excluded": ["YAML/config/manifest parsing", "plugin enablement and catalog gates",
                            "full PluginManager startup", "CLI/model calls", "load deadline guards"],
               "checks": checks}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("SUMMARY %d/%d passed in %.2fs" % (summary["passed"], summary["total"], summary["seconds"]))
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

