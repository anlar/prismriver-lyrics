# prismriver-lyrics

A `uv` workspace (`packages/core`, `packages/tui`) built and tested with `uv`.

## Validation

A task is not done until all of these pass:

```sh
make test-local
```

and, for each plugin touched by the change (matching its `test_<plugin>_NN`
tests in `packages/core/tests/test_plugins.py`):

```sh
make test-plugin PARAMETER=<plugin>
```

`test-local` runs the full suite plus `ruff check` but skips `test_plugins.py`,
since that file hits real lyrics sites over the network. Always run
`test-plugin` for affected plugins on top of it — network access being
unavailable is not a reason to skip verifying a plugin change actually works
against the real site.
