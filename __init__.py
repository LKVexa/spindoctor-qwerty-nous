# SpinDoctor Qwerty 1.1.0 - Nous Research Hermes native plugin
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Six native tools and a skill; no hooks or commands run on registration."""
from pathlib import Path

from . import schemas, tools

TOOLSET = "spindoctor_qwerty"


def register(ctx):
    for name, handler in tools.HANDLERS.items():
        ctx.register_tool(
            name=name, toolset=TOOLSET,
            schema=schemas.SCHEMAS[name], handler=handler,
        )
    ctx.register_skill(
        name="spindoctor-qwerty",
        path=Path(__file__).resolve().parent / "skills" / "spindoctor-qwerty" / "SKILL.md",
        description=("Run SpinDoctor circuit scripts and presets, show its function table, "
                     "and test theories from files, text or a confirmed chat summary."),
    )
