# Capability preflight checklist

- `tokn license features` reports the active tier and enabled feature families.
- `tokn skillpack status` and `list` describe the local cache; they do not
  install a pack.
- `tokn introspect --section modes` exposes mode metadata.
- `tokn doctor prompts` audits prompt sources and overrides.
- `tokn wiki status` is variant-dependent; a public build is not proof of an
  embedded offline wiki.

The local pack inventory and license tier are intentionally not captured.
