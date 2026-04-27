<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to **ComfyUI-HoldCounter** are documented here. The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] — 2026-04-26

### Changed

- Restructured Python sources into a proper `hold_counter/` subpackage. The top-level `__init__.py`
  is now a thin ComfyUI entry point; implementation lives in `hold_counter/node.py`. No public
  behaviour change.

### Fixed

- Pyright `reportUnknownVariableType` on `NodeState.perm` (typed the dataclass `default_factory`
  explicitly).
- CHANGELOG markdownlint MD024 (duplicate headings) — disabled per-file via comment.

## [2.0.0] — 2026-04-26

### Added

- **`mode` enum** combining the old `loop` toggle with new advancement strategies: `loop`, `clamp`,
  `pingpong`, `random`, `shuffle`. Default is `loop` (preserves prior behaviour).
- **`format` input** + **`index_str` second output** for emitting padded/templated strings such as
  `"0007"` (`{:04d}`) — handy for filename prefixes. Bad format strings fall back to `str(index)`
  rather than raising.
- **Per-node state** keyed by ComfyUI's `unique_id`. Multiple HoldCounter nodes in the same workflow
  now advance independently instead of sharing a single global counter.
- **Reset button** in the node body (replaces the sticky `reset` BOOLEAN). Clicking it rewinds *that
  node's* counter only.
- **Pure `_compute_index()` helper** + a 23-case pytest suite covering loop / clamp / pingpong /
  random / shuffle / range-inversion / zero-guard semantics.
- **Defensive guard** for `runs_per_index < 1` (clamped to 1 to prevent `ZeroDivisionError`).
- **CI workflow** running `ruff format --check`, `ruff check`, `pyright`, and `pytest` on Python
  3.10 / 3.11 / 3.12 for every push and PR.
- **Dependabot** weekly updates for GitHub Actions versions.
- **Comfy Registry tags** (`utils`, `batch`, `automation`, `counter`) for Manager filter discovery.
- Example workflow under `workflows/`.
- This `CHANGELOG.md`.

### Changed

- **BREAKING:** the `loop` BOOLEAN input was removed in favour of `mode = "loop" | "clamp" | …`.
  Saved v1 workflows will load (the legacy widget value is silently ignored) but you should pick a
  `mode` value to be explicit.
- **BREAKING:** the `reset` BOOLEAN input was removed and replaced by the JS reset button. Saved v1
  workflows continue to load.
- Counter state is now per-node, not module-global. Workflows that intentionally relied on a single
  shared counter across multiple HoldCounter nodes will need to be updated (this was almost
  certainly accidental for everyone).

### Notes

The node is `OUTPUT_NODE = True` so it executes every queue submission even if its outputs are not
wired to anything downstream.

## [1.1.1] — 2026-04-26

### Fixed

- Display widget no longer renders blank on the very first run after a node is created.
- `onExecuted` no longer calls `setSize`/`computeSize`, which was snapping the node back to its
  default size on every run and discarding the user's manual resize.
- Workflow load no longer crashes with `Cannot set properties of undefined (setting 'readOnly')`
  when the new ComfyUI frontend creates the STRING widget asynchronously.

## [1.1.0] — 2026-04-26

### Added

- Live `current_index` display widget rendered inside the node body each run.
- `min_index` / `max_index` inputs (defaults `0` / `1`).
- `loop` toggle to wrap from `max_index` back to `min_index` (default on); when off, clamps at the
  max.
- `WEB_DIRECTORY` export so the bundled JS extension is served by ComfyUI.
- Packaging: `pyproject.toml` (PEP 621 + `[tool.comfy]`), `LICENSE` (MIT), `README.md`,
  `requirements.txt`, `.gitignore`, GitHub Actions publish workflow for the Comfy Registry.

## [1.0.0] — 2026-04-26

### Added

- Initial release: integer counter that holds each value for `runs_per_index` consecutive queue
  runs.

[2.0.1]: https://github.com/mitch-avis/ComfyUI-HoldCounter/releases/tag/v2.0.1
[2.0.0]: https://github.com/mitch-avis/ComfyUI-HoldCounter/releases/tag/v2.0.0
[1.1.1]: https://github.com/mitch-avis/ComfyUI-HoldCounter/releases/tag/v1.1.1
[1.1.0]: https://github.com/mitch-avis/ComfyUI-HoldCounter/releases/tag/v1.1.0
[1.0.0]: https://github.com/mitch-avis/ComfyUI-HoldCounter/releases/tag/v1.0.0
