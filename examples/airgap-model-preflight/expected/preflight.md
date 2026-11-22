# Expected static preflight

- `tokn doctor --provider ollama`, `gguf`, and `onnx` check static local
  provider configuration; they do not run inference.
- `tokn models status` reports whether a managed local model server is running.
- A correct file hash is necessary but does not establish model provenance,
  license suitability, or safe behavior.
- A complete air-gap inference additionally needs the staged model and its
  matching local runtime.

No endpoint address, model weight, or runtime transcript is included.
