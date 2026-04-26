"""
Custom node: HoldCounter

Outputs an integer index that increments only after every N consecutive queue runs, where N is
configurable via the ``runs_per_index`` input. The output is constrained to the inclusive range
``[min_index, max_index]`` and can either loop back to ``min_index`` after reaching ``max_index`` or
clamp at ``max_index``.

Examples (with min_index=0, max_index=4, loop=True):

    runs_per_index=1: 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, ...

    runs_per_index=2: 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 0, 0, ...

    runs_per_index=3: 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 0, ...

State is module-level and survives across queue runs within a single ComfyUI session. Restarting
ComfyUI resets the counter to zero, as does the optional ``reset`` boolean input.
"""

_STATE: dict[str, int] = {"count": 0}


class HoldCounter:
    """Outputs a held, range-bound integer index suitable for use as a Load Image index or any
    other node expecting a sequential integer that should be held for multiple runs before
    advancing."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, tuple[str, dict[str, object]]]]:
        return {
            "required": {
                "runs_per_index": (
                    "INT",
                    {"default": 1, "min": 1, "max": 1000, "step": 1},
                ),
                "min_index": (
                    "INT",
                    {"default": 0, "min": 0, "max": 1_000_000, "step": 1},
                ),
                "max_index": (
                    "INT",
                    {"default": 1, "min": 0, "max": 1_000_000, "step": 1},
                ),
            },
            "optional": {
                "loop": ("BOOLEAN", {"default": True}),
                "reset": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("index",)
    FUNCTION = "execute"
    CATEGORY = "utils"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs: object) -> float:
        """Force re-execution every run, bypassing ComfyUI's cache."""
        return float("nan")

    def execute(
        self,
        runs_per_index: int,
        min_index: int,
        max_index: int,
        loop: bool = True,
        reset: bool = False,
    ) -> dict[str, object]:
        """Return the current index and advance the internal counter.

        Returns a dict with both ``ui`` (so the value displays in the node body) and ``result`` (the
        actual INT output passed downstream).
        """
        if reset:
            _STATE["count"] = 0

        # Normalize so lo <= hi even if the user inverts the range.
        lo, hi = (
            (min_index, max_index) if min_index <= max_index else (max_index, min_index)
        )
        range_size = hi - lo + 1

        raw = _STATE["count"] // runs_per_index
        if loop:
            index = lo + (raw % range_size)
        else:
            index = min(lo + raw, hi)

        _STATE["count"] += 1

        return {"ui": {"text": [str(index)]}, "result": (index,)}
