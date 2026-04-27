# ComfyUI-HoldCounter

A small but flexible utility node for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that
emits a sequential integer index, **holds** it for a configurable number of consecutive queue runs,
and walks an inclusive `[min_index, max_index]` range using the advancement mode of your choice.
Useful as a Load Image batch index when you want each input image to be used for several consecutive
runs (e.g. multiple seeds per image) before advancing — and for many other batch automation
patterns.

## Features

- **`runs_per_index`** — how many consecutive queue runs hold each index (default `1`).
- **`min_index` / `max_index`** — inclusive output range (defaults `0` / `1`). Order doesn't matter;
  if `min > max` they're swapped automatically.
- **`mode`** — how the index advances:
  - `loop` (default) — wrap from `max` back to `min`.
  - `clamp` — stop at `max`, then keep emitting `max` forever.
  - `pingpong` — bounce: `0,1,2,3,4,3,2,1,0,1,…`.
  - `random` — uniformly random in range each tick (still **held** for `runs_per_index` runs).
  - `shuffle` — walk a random permutation of the range; reshuffle after a full pass.
- **`format`** — Python-style format string applied to the emitted `index_str` output. Examples:
  `"{}"` → `"7"`, `"{:04d}"` → `"0007"`, `"frame_{:03d}"` → `"frame_007"`. Bad templates fall back
  to `str(index)` rather than raising.
- **Two outputs** — `index` (`INT`) and `index_str` (`STRING`). Wire either or both.
- **Reset button** in the node body — momentary; rewinds **only this node's** counter.
- **Per-node state** — multiple HoldCounter nodes in one workflow advance independently.
- **Live display** — the current `index_str` is shown read-only inside the node body after each run.

## Examples

Sequence of outputs for `min_index=0`, `max_index=4`:

| Mode       | Output sequence (`runs_per_index=1`)                 |
| ---------- | ---------------------------------------------------- |
| `loop`     | `0, 1, 2, 3, 4, 0, 1, 2, 3, 4, …`                    |
| `clamp`    | `0, 1, 2, 3, 4, 4, 4, 4, …`                          |
| `pingpong` | `0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3, 4, 3, …`        |
| `random`   | each value uniformly random in `[0, 4]`              |
| `shuffle`  | random permutation per pass, e.g. `2, 0, 4, 1, 3, …` |

Increasing `runs_per_index` simply repeats each emitted value that many times — for example,
`mode=loop`, `runs_per_index=2` produces `0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 0, …`.

## Installation

### Via ComfyUI Manager

1. Open **Manager → Install Custom Nodes**.
2. Search for `ComfyUI-HoldCounter` and click **Install**.
3. Restart ComfyUI.

### Manual install

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/mitch-avis/ComfyUI-HoldCounter.git
```

Then restart ComfyUI. There are no Python dependencies beyond ComfyUI itself.

## Usage

The node appears under **utils → Hold Counter**. Connect:

- `index` (`INT`) → e.g. the `index` input of a *Load Image (Batch)* node.
- `index_str` (`STRING`) → e.g. a filename prefix on a *Save Image* node.

A ready-to-import example lives in
[`workflows/hold_counter_basic.json`](workflows/hold_counter_basic.json).

### Notes

- Counter state is **per-node** (keyed by ComfyUI's internal `unique_id`) and persists across queue
  runs within a single ComfyUI session. Restarting ComfyUI resets every counter.
- The node is `OUTPUT_NODE = True`, so it executes every queue submission even when its outputs
  aren't connected to anything downstream.

## Development

```bash
cd ComfyUI/custom_nodes/hold_counter
uv venv && uv pip install -e ".[dev]"
uv tool run ruff format --check .
uv tool run ruff check .
uv run pyright .
uv run pytest --cov
```

CI runs the same checks across Python 3.10 / 3.11 / 3.12 on every push and PR.

## License

[MIT](LICENSE). See [CHANGELOG.md](CHANGELOG.md) for release notes.
