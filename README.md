# SpinDoctor Qwerty for Nous Research Hermes Agent

Native Python tools for [Hermes Agent](https://github.com/NousResearch/hermes-agent), running the SpinDoctor 3.1.2
classical FP64 simulator. Version 1.1.0 bundles engine 1.1.0 and exposes six tools, 241 presets, command folders,
the function table and theory tests with TXT, JSON, PDF and CSV reports. This uses Hermes' `plugin.yaml` and
`register(ctx)` API. The separate `spindoctor-qwerty-hermes` repository uses the portable Agent Plugins format.

SpinDoctor is a classical simulator on an ordinary computer. It is not a quantum computer and claims no
quantum speed-up or advantage. It supports up to 298 logical qubits, at most 59 per entangled factor, with dense
factors limited by memory (2^n x 16 bytes). Above 29 qubits, measurements use basis z and prepared-factor Born-Z
sampling. Full joint query analysis is limited to 16 qubits; other command families have their own limits.

## Install

Use an existing Hermes installation. The audited Hermes source requires Python 3.11 through 3.14; the bundled
engine itself supports Python 3.8+. No Python packages are required by this plugin, and it makes no network calls.
Hermes has its own installation requirements.

```text
hermes plugins install LKVexa/spindoctor-qwerty-nous --enable
hermes plugins list
```

Hermes' plugin guard reports **CAUTION** for this package and asks whether to install anyway. In the audited
source, its one high-severity finding is the engine's read of its own `/proc/self/status` to estimate memory
use; there are no critical/dangerous findings. Other findings concern report encodings, skill-relative paths
and test subprocesses. Review the findings before accepting that prompt. A non-interactive install refuses
CAUTION unless you explicitly accept it with `--force`:

```text
hermes plugins install LKVexa/spindoctor-qwerty-nous --force --enable
```

For a local folder installation, copy the contents of this repository into
`~/.hermes/plugins/spindoctor-qwerty/`, keeping `plugin.yaml` and `__init__.py` at that folder's root. On Windows
that is `%USERPROFILE%\.hermes\plugins\spindoctor-qwerty\`. If you use a custom Hermes home, use its `plugins`
folder instead. Then enable it and start a new Hermes session:

```text
hermes plugins enable spindoctor-qwerty
```

The native toolset is `spindoctor_qwerty`. If your Hermes profile saves an explicit selection of toolsets,
confirm this toolset is selected. The registered skill is `spindoctor-qwerty:spindoctor-qwerty`.
Disabling the plugin uses `hermes plugins disable spindoctor-qwerty`.

Unlike an MCP subprocess integration, the native tools use Hermes' Python interpreter. There is no `python3`
launcher setting to edit on Windows. For the optional standalone CLI below, choose `python3` on Linux/macOS
or `py -3`/`python` on Windows.

## Use

Ask Hermes to show the SpinDoctor functions, run a Bell or GHZ circuit, run a preset, process a folder, or test a
theory. The function-table tool returns the table in [FUNCTIONS.md](FUNCTIONS.md), with a runnable command for
every family. `section="presets"` lists the 241 presets.

| Tool | Purpose |
|---|---|
| `spindoctor_functions` | Show the command/function table or all presets |
| `spindoctor_run_script` | Run `q.*` commands, one per line |
| `spindoctor_run_preset` | Run `qc-001` through `qc-241` with optional overrides |
| `spindoctor_list_presets` | List or search presets |
| `spindoctor_report` | List reports or read a TXT report |
| `spindoctor_test_theory` | Extract or test a theory from a local file, text or a confirmed chat summary |

Tools return JSON strings in Hermes' native handler format. Errors are returned in the result. There are no
hooks and registration performs no simulator work. Calls within one loaded plugin instance are serialized.

Reports and persistent state default to `~/spindoctor-workspace`. Set `SPINDOCTOR_WORKSPACE` before starting
Hermes or pass an absolute `workspace` in a tool call to choose another folder. Use absolute file and folder
paths: Hermes does not promise a session working directory for native handlers. Keep reports outside the
plugin installation.

Standalone CLI example from the repository root:

```text
python3 engine/scripts/spindoctor_cli.py functions
python3 engine/scripts/spindoctor_cli.py run "q.circuit new bell 2" "q.circuit add h 0" "q.circuit add cx 0 1" "q.circuit run shots 1000 basis z"
```

## Theory testing and folders

For a file, supply its absolute local path (`.txt`, `.md`, `.pdf`, `.py`, `.json`, `.csv`, `.q`). For pasted text,
use `source="text"`. For chat history, Hermes summarizes the claims, assumptions, variables and measurable
prediction, asks you to confirm or correct that summary, then passes it with `source="chat"` and optional
quoted excerpts or an exported transcript (`.txt`, `.md`, `.json`, `.html`). The plugin cannot read the
conversation or retrieve attachments itself. The host must provide the content or a local path.

`action="extract"` reads the source. `action="run"` runs a `q.*` experiment, compares measurable checks and
writes TXT, JSON and PDF reports with a supported, not supported or inconclusive verdict and the test limits.
Examples live in `engine/examples/theory/`. Sample PDFs can be regenerated with
`python3 engine/examples/theory/make_sample_pdfs.py`.

`q.folder run path="<absolute-folder>"` processes supported top-level files in ordinal order (`.txt`, `.csv`,
`.json`, `.qasm`, `.qasm2`, `.circuit`, `.pdf`). Limits are 128 supported files, 4 MiB per file, 128 commands
per file and 4096 characters per command. Unsupported files are listed as skipped. The first failing file
stops the job. Folder execution is synchronous.

## Validation

The host API was audited against official Hermes source commit
`7bc05085f09ee9bfa9cecaaa3cf44758bdff96a6`. See [E2E_RESULTS.md](E2E_RESULTS.md) for exact coverage and results.
This is **partial integration with official Hermes source components**: the tests import the complete
registry and compile selected unchanged source nodes for package loading, native registration, skills and
handle disposal. They require a matching Hermes source checkout via `HERMES_SOURCE`. Manifest/config parsing,
enablement/catalog gates, full PluginManager/CLI startup, load deadline guards, a real model, interactive UI
and macOS are outside that component test.

With a source checkout at the pinned revision, run these from this repository's root. On Windows use
`python` or `py -3` instead of `python3`, and set `HERMES_SOURCE` to the checkout's absolute path.

```text
python3 tests/nous_host_check.py --hermes-source <hermes-source> --out <results-json>
python3 tests/e2e_mcp.py --server python3 tests/native_bridge.py --hermes-source <hermes-source> --examples engine/examples/theory --out <results-json>
```

Official references:

- [Hermes plugin management](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins)
- [Native plugin authoring](https://hermes-agent.nousresearch.com/docs/guides/build-a-hermes-plugin)
- [Pinned plugin API source](https://github.com/NousResearch/hermes-agent/blob/7bc05085f09ee9bfa9cecaaa3cf44758bdff96a6/hermes_cli/plugins.py)

## Author and license

Author: **RUSSELL PHILIP SMITHSON** <russellsmithson77@outlook.com>.

Copyright (C) 2026 RUSSELL PHILIP SMITHSON. Licensed under GPL v3 or later (`GPL-3.0-or-later`);
see [LICENSE](LICENSE), [NOTICE](NOTICE) and [COPYRIGHT](COPYRIGHT). Hermes is third-party software by
Nous Research. Host source is used externally for tests and is not bundled with this plugin.
