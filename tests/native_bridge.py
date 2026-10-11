#!/usr/bin/env python3
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test-only stdio bridge through real Hermes native registration and dispatch.

Used by e2e_mcp.py to reuse black-box engine checks against the Hermes wrapper.
It is not the production plugin transport or the full Hermes CLI.
Usage: python native_bridge.py --hermes-source OFFICIAL_SOURCE
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
from pathlib import Path

from native_components import load_host

PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-source")
    parser.add_argument("--plugin", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    # Reserve stdout for protocol frames before loading third-party host/plugin code.
    output = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
    input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    sys.stdout = sys.stderr
    NativeComponents, registry, revision = load_host(args.hermes_source)
    home = Path(os.environ.get("SPINDOCTOR_WORKSPACE") or tempfile.gettempdir()) / ".hermes-native-test"
    host = NativeComponents(home)
    module, ctx = host.load_package(Path(args.plugin))
    package_version = json.loads((Path(args.plugin) / "plugin.yaml").read_text(encoding="utf-8"))["version"]

    def respond(message):
        if not isinstance(message, dict):
            return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}
        identifier = message.get("id")
        if identifier is None:
            return None
        method = message.get("method")
        params = message.get("params") or {}
        try:
            if method == "initialize":
                requested = params.get("protocolVersion")
                result = {"protocolVersion": requested if requested in PROTOCOLS else PROTOCOLS[0],
                          "capabilities": {"tools": {"listChanged": False}},
                          "serverInfo": {"name": "spindoctor-qwerty-nous-native-test", "version": package_version}}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": [{"name": entry.name, "description": entry.schema.get("description", ""),
                                     "inputSchema": entry.schema["parameters"]}
                                    for name in sorted(host._plugin_tool_names)
                                    for entry in [registry.get_entry(name, scope=host.scope_key)]]}
            elif method == "tools/call":
                # This is the actual Hermes registry; never call engine.api here.
                raw = registry.dispatch(params.get("name"), params.get("arguments", {}), scope=host.scope_key)
                decoded = json.loads(raw) if isinstance(raw, str) else raw
                if not isinstance(decoded, dict):
                    decoded = {"ok": False, "error": "Native handler did not return a JSON object."}
                text = decoded["markdown"] if decoded.get("ok") and isinstance(decoded.get("markdown"), str) else raw
                result = {"content": [{"type": "text", "text": text}], "structuredContent": decoded,
                          "isError": not decoded.get("ok", False)}
            else:
                return {"jsonrpc": "2.0", "id": identifier,
                        "error": {"code": -32601, "message": "Method not found: " + str(method)}}
            return {"jsonrpc": "2.0", "id": identifier, "result": result}
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32603, "message": str(exc)}}

    try:
        for line in input_stream:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except ValueError:
                output.write(json.dumps({"jsonrpc": "2.0", "id": None,
                                         "error": {"code": -32700, "message": "Parse error"}}) + "\n")
                output.flush()
                continue
            for item in message if isinstance(message, list) else [message]:
                response = respond(item)
                if response is not None:
                    output.write(json.dumps(response, ensure_ascii=False, default=str) + "\n")
                    output.flush()
    finally:
        host.dispose_registered_handles()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

