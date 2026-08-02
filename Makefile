.PHONY: test test-local test-plugin run run-tui install-pipx

test:
	uv run --all-packages pytest
	uv run ruff check packages

test-local:
	uv run --all-packages pytest --ignore=packages/core/tests/test_plugins.py
	uv run ruff check packages

test-plugin:
	uv run --all-packages pytest packages/core/tests/test_plugins.py -k "$(PARAMETER)"

run:
	uv run prismriver-lyrics $(ARGS)

run-tui:
	uv run prismriver-lyrics-tui

install-pipx:
	rm -rf dist
	uv build --all-packages -o dist
	pipx install --force dist/prismriver_lyrics-*-py3-none-any.whl --pip-args "--find-links dist"
	pipx install --force dist/prismriver_lyrics_tui-*-py3-none-any.whl --pip-args "--find-links dist"
