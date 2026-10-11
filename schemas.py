# SpinDoctor Qwerty 1.1.0 - Nous native tool schemas
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Use the bundled engine schemas so the host and engine stay in agreement."""
from .engine.spindoctor.api import TOOLS

SCHEMAS = {
    tool["name"]: {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["parameters"],
    }
    for tool in TOOLS
}
