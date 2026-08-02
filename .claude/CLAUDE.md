## Testing

Don't invoke `pytest`, `ruff`, or `uv run` test commands directly — always go
through the `make` targets below.

After each change, run `make test-local`. It runs the full suite except the
live plugin tests in `packages/core/tests/test_plugins.py` (which hit real
lyrics sites over the network), plus `ruff check`.

If the change touched a plugin (anything under
`packages/core/src/prismriver_lyrics/plugins/`), also run
`make test-plugin PARAMETER=<plugin_name>` for that plugin, e.g.
`make test-plugin PARAMETER=musixmatch`.
