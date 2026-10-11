# Changelog

## 1.1.0

- Bundle engine 1.1.0 at parity with SpinDoctor 3.1.2 update `3.1.2-298-20261010`:
  298 logical qubits, 59 per entangled factor, `mcx7`, and prepared-factor Born-Z sampling above 29 qubits.
- Expose all six tools through Hermes' native `register(ctx)` API, adding the function table and theory testing
  from files, pasted text and a confirmed chat summary.
- Register a native skill with explicit description, function-table guidance, confirmed chat-theory workflow,
  absolute attachment paths, CLI fallback and current simulator limits.
- Keep all imports within the plugin package; derive schemas from the bundled engine; return JSON errors for
  invalid calls and serialize native calls within the process to protect persistent state.
- Put `plugin.yaml` and `__init__.py` at repository root, document explicit Hermes enablement and distinguish
  the native Python plugin from the separate portable Hermes integration.
- Use GPL-3.0-or-later with RUSSELL PHILIP SMITHSON credited as author.
