# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Each change should be on one line, as GitHub markdown in the release section can't render a multi-line list item as a single line.

## [Unreleased]

### Added

- `metalarchives` plugin: fetches lyrics from metal-archives.com (Encyclopaedia Metallum).
- `songlyrics` plugin: fetches lyrics from songlyrics.com.

## [1.0.0] - 2026-08-04

### Added

- `prismriver-lyrics` CLI: search song lyrics across 30+ plugin sources by artist/title, with filtering by plugin id, language, translated/original, and synced/plain-text, plus a result cap.
- `prismriver-lyrics-tui`: a Textual terminal UI that follows the active MPRIS media player over D-Bus, searches on each track change, and renders results with the current line highlighted for time-synced (LRC) lyrics. Includes a manual search dialog, theme switching, and vim-style keybindings.
- On-disk SQLite cache of search results shared between the CLI and TUI, with a configurable TTL and a bypass flag.
