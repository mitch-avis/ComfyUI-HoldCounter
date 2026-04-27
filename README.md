# ComfyUI-HoldCounter

A tiny utility node for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that emits a sequential
integer index, holds it for a configurable number of consecutive queue runs, and optionally loops
over a min/max range. Useful as a Load Image batch index when you want each input image to be used
for several consecutive runs (e.g. multiple seeds per image) before advancing.

## Features

- **`runs_per_index`** — how many consecutive queue runs hold each index (default `1`).
- **`min_index` / `max_index`** — inclusive output range (defaults `0` / `1`).
- **`loop`** — wrap from `max_index` back to `min_index` (default on); when off, clamps at the max.
- **`reset`** — sticky toggle: while on, every queued run rewinds the counter to `min_index`. Tick
  on for one run, then untick.
- **Live display** — the current index is shown read-only inside the node body after each run.

## Examples

Sequence of outputs for `min_index=0`, `max_index=4`, `loop=true`:

| `runs_per_index` | Output sequence                                   |
| ---------------- | ------------------------------------------------- |
| 1                | 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, …                   |
| 2                | 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 0, …             |
| 3                | 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 0, … |

## Installation

### Via ComfyUI Manager (recommended once published)

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

The node appears under **utils → Hold Counter**. Connect the `index` output to e.g. the `index`
input of a *Load Image (Batch)* node.

The counter state is module-level and persists across queue runs within a single ComfyUI session.
Restarting ComfyUI resets it to zero.

## License

[MIT](LICENSE)
