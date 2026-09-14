# fasthep-toolbench Agent Instructions

`fasthep-toolbench` provides reusable integration utilities and external-tool
adapters shared across FAST-HEP packages. These instructions are
repository-local and should remain valid when this repository is cloned
independently.

## Ownership

This repository owns:

- reusable integration utilities with clear cross-package use;
- convenience layers around libraries such as `importlib`, `importlib.metadata`,
  `httpx`, Rich, and external command execution;
- Python interfaces to external tools such as `dasgoclient` and D2;
- tool specifications and implementations exposed through the Toolbench tool
  registry;
- capability discovery, availability checks, installation helpers, and
  structured external-tool execution results.

This repository does not own:

- Flow's generic registry/profile loading, compiler, runtime, or workflow
  execution;
- CLI's user-facing `fasthep` commands, argument UX, diagnostics, or exit
  policy;
- Render's decision about when graph rendering is needed; Toolbench only
  provides the D2 adapter and command execution boundary;
- Curator's dataset inspection and metadata semantics;
- Carpenter's analysis operations, event processing, and data products.

Do not use Toolbench as a dumping ground for package-local helpers. Shared
utilities should have a coherent integration purpose or demonstrated
cross-package use.

## Important Locations

- `src/fasthep_toolbench/__init__.py` and `src/fasthep_toolbench/tools.py` -
  public convenience exports.
- `src/fasthep_toolbench/api.py` - public tool listing, execution, and
  information APIs.
- `src/fasthep_toolbench/model.py` - `ToolSpec`, `ToolParam`,
  `ToolAvailability`, `ToolBinding`, and structured result models.
- `src/fasthep_toolbench/profiles/registry.yaml` - bundled tool registry.
- `src/fasthep_toolbench/registry.py` - registry loading, entry-point discovery,
  and registry merging.
- `src/fasthep_toolbench/loader.py` - `module:object` loading and tool binding
  resolution.
- `src/fasthep_toolbench/args.py` - command-style argument parsing into tool
  parameters.
- `src/fasthep_toolbench/command.py` - subprocess-like external command
  execution and `CommandResult`.
- `src/fasthep_toolbench/availability.py` and
  `src/fasthep_toolbench/install.py` - executable discovery and installation
  helpers.
- `src/fasthep_toolbench/cms/das.py` - `cms.dasgoclient` adapter and CMS DAS
  dataset-list discovery helpers.
- `src/fasthep_toolbench/graph/d2.py` - D2 external-tool adapter.
- `src/fasthep_toolbench/http/download.py` - HTTP download helpers.
- `src/fasthep_toolbench/package/` - package import and version discovery
  helpers.
- `src/fasthep_toolbench/display/` and `src/fasthep_toolbench/format.py` -
  reusable display and structured text formatting helpers.
- `tests/test_tools.py` - registry, command, DAS, D2, install, and formatting
  tests.
- `tests/test_download.py` - HTTP download tests.
- `tests/test_package.py` - import/version smoke test.
- `docs/` - Sphinx documentation source.

## Commands

Install and run tasks from the repository root:

```bash
pixi install
pixi run format
pixi run lint
pixi run lint-fix
pixi run typecheck
pixi run test
pixi run build
pixi run check
pixi run ci
pixi run check-dist
pixi run --environment docs docs
pixi run --environment docs docs-clean
```

`check` runs `lint`, `typecheck`, and `test`. `ci` runs `check` and `build`.
Build before `check-dist` so `dist/*` exists. Documentation tasks need the
`docs` environment because Sphinx is declared there. The Pixi environments
include `py311`, `py313`, `py314`, and `docs`; use the default environment
unless a compatibility or documentation check needs a specific environment.

## Tool Registry

Built-in registered tool names are:

- `cms.dasgoclient` - spec `fasthep_toolbench.cms.das:DASGOCLIENT_SPEC`, impl
  `fasthep_toolbench.cms.das:run_dasgoclient`.
- `d2` - spec `fasthep_toolbench.graph.d2:D2_SPEC`, impl
  `fasthep_toolbench.graph.d2:run_d2`.

Register workflow-visible tools through `src/fasthep_toolbench/profiles/registry.yaml`
or through entry points in the `fasthep_toolbench.registries` group. Keep tool
specs, implementation signatures, registry entries, argument parsing, and tests
aligned. Return structured results such as `CommandResult` or JSON-compatible
mappings whenever workflow consumers need machine-readable output.

Use public Flow extension contracts when Toolbench data is consumed by Flow
profiles or workflows. Do not import Flow compiler internals from Toolbench.

## External Boundaries

- Avoid imports, network access, executable discovery, installation, or
  subprocess execution during module import.
- Invoke external commands as argument lists; do not introduce shell parsing or
  `shell=True` behaviour.
- Report command failures clearly with executable, exit code, stdout/stderr, and
  timeout state where appropriate.
- Apply explicit network timeouts and structured error handling for `httpx`
  calls.
- Never expose credentials, tokens, X.509 proxy contents, or sensitive
  environment values in logs, exceptions, or structured results. Paths may be
  useful evidence; secret contents are not.
- Keep live-service and executable integration tests explicit and optional.
  Routine unit tests should mock network, `httpx`, installer, and command
  boundaries.

Optional external dependencies include:

- `dasgoclient` plus network/CMS DAS access and, for protected data, valid
  credentials or an X.509 proxy;
- `d2` for graph rendering;
- GitHub release/network access for automatic D2 installation helpers.

## Testing Expectations

- Tool registry, specs, loading, argument parsing, command execution, D2, DAS,
  install helpers, and text formatting:
  `pixi run pytest tests/test_tools.py`.
- HTTP download helpers:
  `pixi run pytest tests/test_download.py`.
- Package import/version smoke:
  `pixi run pytest tests/test_package.py`.

Keep routine tests deterministic and local. Mock `httpx`, `run_command`,
`run_dasgoclient`, installer downloaders, and executable availability rather
than requiring network services or installed external tools. Add live-service
tests only with explicit markers or opt-in instructions.

## Generated Files and Care Areas

- `src/fasthep_toolbench/_version.py` is generated by Hatch/Hatch-VCS. Do not
  edit it by hand; keep `src/fasthep_toolbench/_version.pyi` aligned with
  imports.
- Distribution artifacts, Sphinx builds, downloaded archives, installed tool
  binaries, discovery JSON, and generated command outputs are generated
  products. Do not check them in unless they are deliberate fixtures.
- Preserve the public API surface in `fasthep_toolbench.__init__` and
  `fasthep_toolbench.tools`; downstream packages may import these helpers
  directly.
