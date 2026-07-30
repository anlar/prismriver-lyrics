## Testing

After each change, run `make test`. Don't invoke `pytest`, `ruff`, or `uv run`
test commands directly — `make test` runs the full suite (pytest across the
workspace) plus `ruff check` in the right order.
