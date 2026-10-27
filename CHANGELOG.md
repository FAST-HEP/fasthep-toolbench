# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project uses
calendar versioning (`YYYY.MM.N`) rather than semantic versioning.

Add new entries under `## [Unreleased]`, in the category they belong to. At release time, rename
`## [Unreleased]` to `## [<version>] - <YYYY-MM-DD>` and start a fresh `## [Unreleased]` above it.

## [Unreleased]

### Added

- `fasthep_toolbench.package.environment`: pure, import-safe helpers for inspecting the running
  Python environment and package provenance — `python_info`, `installed_distributions`,
  `distribution_info` (parses `direct_url.json`, including VCS revision and editable source path),
  `git_state` (repository root, revision, dirty flag), and `find_lockfile`.
- `fasthep_toolbench.misc.file_sha256` and `file_fingerprint` for hashing files; the existing
  `get_file_hash` is now built on top of them.

### Changed

- **Breaking:** `rich`, `httpx`, and `tabulate` are no longer hard dependencies. They are now
  optional extras (`display`, `http`, or both via `all`); a plain `import fasthep_toolbench` no
  longer pulls them in. Code that uses `fasthep_toolbench.display` or `fasthep_toolbench.http` must
  now depend on `fasthep-toolbench[display,http]` explicitly.

### Fixed

- `run_command` no longer fails when called from a process that already has other threads
  running (for example `fasthep-render`'s D2 graph compile hook during a real workflow compile).
  `sh` forks to exec the external command, and CPython warns whenever `fork()` runs in a
  multi-threaded process; that specific, known-safe warning is now suppressed instead of
  propagating as an exception under strict `filterwarnings = ["error"]` test suites.
- `git_state` and `distribution_info` are now robust against adverse environments: an inherited
  `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` no longer redirects git calls to the wrong repository,
  git calls no longer run repository-configured hooks or write a shared/read-only index, diagnostic
  text no longer depends on locale, an unreadable `direct_url.json` is recorded as a note instead of
  raising, and credentials embedded in a `direct_url.json` URL are redacted before being recorded.

## [2026.08.2] - 2026-08-19

### Fixed

- `misc.formatted_today` used naive local time; it now takes an explicit `timezone` parameter
  (defaulting to UTC) and uses timezone-aware `datetime.now()`.
