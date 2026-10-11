# Nous native plugin 1.1.0 validation

Date: 2026-10-11. Base: SpinDoctor 3.1.2 update `3.1.2-298-20261010`; bundled engine 1.1.0.
Host source pin: Nous Research Hermes Agent `7bc05085f09ee9bfa9cecaaa3cf44758bdff96a6`.
Windows component checks use Python 3.12.14.

## Current results

- Native source component checks: **34/34 passed**. Actual Hermes package namespace/relative imports,
  six schemas and handlers, native skill registration/resolution, invalid arguments and command limits,
  persistent state, serialization within one plugin instance, independent host homes, reload module eviction,
  stale registration ownership and disposal, then clean re-registration.
- Generic end-to-end suite through the **native registry bridge**: **12/12 passed**. All 16 command families,
  298-qubit `mcx7`, mixed-folder ingestion, a preset, theory from a file/chat summary/chat transcript,
  and all recorded preset references `qc-001` through `qc-025`: 20 identical and 5 documented differences.
  The report check validates 255 PDF files and their 255 TXT twins structurally.
- Bundled engine: all **35 files byte-identical** to the published upgrade kit at
  `89a8205a4eba18bb039b7101779b18718c8cf93e`. No simulator results changed.
- `plugin.yaml` is JSON syntax, a YAML subset, and parses as an object. Names, version, author, license,
  declared tools and skill structure are checked offline.
- Strict publication scan: clean. No binaries or archives are required for the native plugin.
- Hermes' own `plugin-guard-v11` at the pinned source: **CAUTION**, no critical/dangerous findings.
  One high finding is the engine's own-process `/proc/self/status` memory read. Nine medium findings
  concern PDF/report encodings, skill-relative paths and test subprocesses. The actual default installation
  policy asks for confirmation; `--force` explicitly accepts that caution. This is documented in README.

## Coverage boundary

This is partial integration with real source components, not a full installed Hermes session. Complete
official registry/constants/ownership/skill utility modules are imported. Selected unchanged AST nodes
from the pinned loader, context, registration ledger and skill APIs are compiled for component tests.
The harness supplies initialization state; it does not replace the registry or native handler dispatch.
Upstream host source is supplied externally and is not bundled in this repository.

Not exercised: YAML/config/manifest parsing in Hermes, plugin enablement/catalog gates, full PluginManager
or CLI startup, load deadline guards, a real model, interactive UI, Linux or macOS native loading. Report
checks cover PDF structure; these reports were not visually inspected.

## Inherited engine evidence

A fresh Windows run of the kit passed **10/10 offline checks**, including 168 function-table examples,
43/43 theory checks with and without the optional PDF library, 32/32 engine checks with NumPy,
wide-register reference replay and the 11-file 298-qubit example. Two scratch test-harness adaptations
were required: use `pypdf` to extract PDF text because `pdftotext` is absent, and exclude the already
documented internal `actualAmplitudeWrites`/`actualTensorProducts` accounting differences from the wide
example comparison. The engine was not modified. This is not a claim that the unadapted kit passed:
its initial Windows run was 8/10 for those two reasons. Network link checks were skipped.

The upgrade kit records SpinDoctor 3.1.2's own suite passing **18/18 with three checks adapted** from the old
29-qubit bound to 298. That historical C# run and its publishing approval were not repeated here.
The kit also records 241-preset parity and accepted CPU/GPU, work-accounting, checkpoint and state-file
differences. The new host suite verifies the recorded first 25 preset references through native dispatch.

The previous Mistral Vibe integration was verified separately from its GitHub snapshot
`8983e40af40b20ebbd79a1572b4a501046c2eb19`: fresh Windows MCP tests **12/12**, all 54 source files unchanged
after testing. Its historical real-Vibe 29/29 was not rerun.
