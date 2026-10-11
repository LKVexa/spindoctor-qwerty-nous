---
name: spindoctor-qwerty
description: Run SpinDoctor circuits and presets, show the function table, ingest command folders, and test theories from files, pasted text or a confirmed chat summary. Use for Bell/GHZ/QFT circuits, qubits, gates, measurements or SpinDoctor.
license: GPL-3.0-or-later
compatibility: Nous Research Hermes Agent with native Python plugins; Python 3.8+ for the bundled engine. Classical FP64 simulation only.
metadata:
  author: RUSSELL PHILIP SMITHSON
  version: "1.1.0"
---

Use the native tools in the `spindoctor_qwerty` toolset. The registered skill name is
`spindoctor-qwerty:spindoctor-qwerty`. On first use or when asked for help, capabilities or functions,
call `spindoctor_functions` and show its Markdown table verbatim. `section="presets"` lists all 241 presets.

The six tools are `spindoctor_functions`, `spindoctor_run_script`, `spindoctor_run_preset`,
`spindoctor_list_presets`, `spindoctor_report` and `spindoctor_test_theory`. If the host exposes tools through
search, search for these exact names before calling them.

Provide absolute local paths for attachment files, transcripts and folders. Ask the host to make uploaded
attachments available as local files, or pass their text. The plugin does not read the conversation or fetch
attachments by itself. Reports/state default to `~/spindoctor-workspace`; `SPINDOCTOR_WORKSPACE` or a call's
`workspace` parameter can select another folder. Keep reports outside the plugin installation.

For a chat-derived theory, summarize the claims, assumptions, variables and measurable prediction, then
obtain the user's confirmation or correction before calling `spindoctor_test_theory` with `source="chat"`.
Pass the confirmed summary and optional verbatim excerpts or an exported transcript. `action="extract"`
reads the source; `action="run"` tests it and writes TXT, JSON and PDF reports. Verdicts are supported,
not supported or inconclusive within the stated simulator limits.

Example script: `q.circuit new bell 2`, `q.circuit add h 0`, `q.circuit add cx 0 1`,
`q.circuit run shots 1000 basis z` (one command per line). Use `spindoctor_run_preset` with `preset_id="qc-001"`
for the first preset. Folder ingestion uses `q.folder run path="<absolute-folder>"`.

The bundled CLI is at `../../engine/scripts/spindoctor_cli.py` relative to this SKILL.md. Resolve that path
against the skill file's actual directory before using a shell fallback. Run `python3 <absolute-cli> functions`
or `python3 <absolute-cli> run "q.help"`; on Windows choose `py -3` or `python` if `python3` is unavailable.
Examples are under `../../engine/examples/theory/`.

SpinDoctor is a classical FP64 simulator running on an ordinary computer. It is not a quantum computer and
claims no quantum advantage. It supports 298 logical qubits with at most 59 in one entangled factor, further
limited by memory (2^n x 16 bytes for a dense n-qubit factor). Above 29 qubits, measurements use prepared-factor
Born-Z sampling in basis z only. Full joint query analysis is limited to 16 qubits. Auxiliary compile/noise/error
correction tools retain their own limits. `mcx7` has seven controls and one target.
