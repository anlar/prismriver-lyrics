.PHONY: test run run-tui install-pipx

test:
	uv run --all-packages pytest
	uv run ruff check packages

run:
	uv run prismriver-lyrics $(ARGS)

run-tui:
	uv run prismriver-lyrics-tui

install-pipx:
	rm -rf dist
	uv build --all-packages -o dist
	pipx install --force dist/prismriver_lyrics_tui-*-py3-none-any.whl --pip-args "--find-links dist"
