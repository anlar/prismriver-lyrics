.PHONY: test test-local test-plugin test-strict run run-tui install-pipx release-pypi-main release-pypi-test

test:
	uv run --all-packages pytest --verbose
	uv run ruff check packages

test-local:
	uv run --all-packages pytest --ignore=packages/core/tests/test_plugins.py --verbose
	uv run ruff check packages

test-plugin:
	uv run --all-packages pytest packages/core/tests/test_plugins.py -k "$(PARAMETER)" --verbose

test-strict:
	uv run --all-packages pytest --runxfail --verbose
	uv run ruff check packages

run:
	uv run prismriver-lyrics $(ARGS)

run-tui:
	uv run prismriver-lyrics-tui

install-pipx:
	rm -rf dist
	uv build --all-packages -o dist
	pipx install --force dist/prismriver_lyrics-*-py3-none-any.whl --pip-args "--find-links dist"
	pipx install --force dist/prismriver_lyrics_tui-*-py3-none-any.whl --pip-args "--find-links dist"

release-pypi-main:
	rm -rf dist
	uv build --all-packages -o dist
	uv publish dist/*

release-pypi-test:
	rm -rf dist
	uv build --all-packages -o dist
	uv publish --publish-url https://test.pypi.org/legacy/ dist/*
