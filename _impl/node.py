"""HoldCounter ComfyUI node.

Outputs an integer index that increments only after every N consecutive queue runs (``hold``
behaviour) and walks an inclusive ``[min_index, max_index]`` range using one of several modes:

- ``loop``     — wrap from max back to min (default).
- ``clamp``    — stop at max, then keep emitting max forever.
- ``pingpong`` — bounce: 0,1,2,3,4,3,2,1,0,1,…
- ``random``   — uniformly random in range each tick (held for ``runs_per_index`` runs).
- ``shuffle`` — walk a random permutation of the range; reshuffle after a full pass.

State is per-node (keyed by ``unique_id``) so multiple HoldCounter nodes in the same workflow
advance independently. State is in-memory; restarting ComfyUI resets every counter.

The pure index math lives in :func:`_compute_index` so it can be unit-tested without importing
ComfyUI; ``NodeState`` owns shuffle permutations and reset bookkeeping.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# Public constants -------------------------------------------------------------------------------

MODES: tuple[str, ...] = ("loop", "clamp", "pingpong", "random", "shuffle")
DEFAULT_MODE: str = "loop"


# Pure helpers -----------------------------------------------------------------------------------


def _compute_index(
    tick: int,
    lo: int,
    hi: int,
    mode: str,
    *,
    seed: int = 0,
) -> int:
    """Return the index for a given tick under the deterministic modes.

    The ``shuffle`` mode is *not* handled here because it requires per-node state; use
    :meth:`NodeState.shuffle_index` for that. Calling this function with ``mode="shuffle"`` falls
    back to ``loop`` semantics.

    Args:
        tick: Monotonic counter (``run_count // runs_per_index``). lo: Inclusive lower bound. May be
        greater than ``hi``; we swap. hi: Inclusive upper bound. mode: One of :data:`MODES`. seed:
        Per-tick seed used for ``random`` mode. Ignored otherwise.

    Returns:
        An integer in ``[min(lo, hi), max(lo, hi)]``.
    """
    if lo > hi:
        lo, hi = hi, lo
    range_size = hi - lo + 1

    if mode == "clamp":
        return min(lo + tick, hi)
    if mode == "pingpong":
        period = max(1, 2 * range_size - 2)
        pos = tick % period
        return lo + pos if pos < range_size else lo + (period - pos)
    if mode == "random":
        return random.Random(seed).randint(lo, hi)
    # "loop" (and any unknown mode → safest fallback)
    return lo + (tick % range_size)


@dataclass
class NodeState:
    """Per-node mutable state. One instance per ``unique_id``."""

    count: int = 0
    last_reset_token: int = 0
    cached_tick: int | None = None
    cached_index: int | None = None
    perm: list[int] = field(default_factory=list[int])
    perm_seed: int = 0
    perm_pass: int = 0

    def reset(self) -> None:
        self.count = 0
        self.cached_tick = None
        self.cached_index = None
        self.perm = []
        self.perm_pass = 0

    def shuffle_index(self, tick: int, lo: int, hi: int, seed: int) -> int:
        """Return ``perm[tick % len(perm)]``, reshuffling between passes."""
        if lo > hi:
            lo, hi = hi, lo
        size = hi - lo + 1
        if size <= 0:
            return lo
        current_pass = tick // size
        if not self.perm or len(self.perm) != size or current_pass != self.perm_pass:
            rng = random.Random(seed + current_pass)
            self.perm = list(range(lo, hi + 1))
            rng.shuffle(self.perm)
            self.perm_pass = current_pass
            self.perm_seed = seed
        return self.perm[tick % size]


# Process-global state. Keyed by stringified ComfyUI node ``unique_id``.
_STATES: dict[str, NodeState] = {}


def _get_state(unique_id: str) -> NodeState:
    state = _STATES.get(unique_id)
    if state is None:
        state = NodeState()
        _STATES[unique_id] = state
    return state


# ComfyUI node -----------------------------------------------------------------------------------


class HoldCounter:
    """A held, range-bound, multi-mode integer counter for ComfyUI."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, object]]:
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
                "mode": (list(MODES), {"default": DEFAULT_MODE}),
            },
            "optional": {
                "format": ("STRING", {"default": "{}", "multiline": False}),
                # Hidden trigger widget — incremented by the JS reset button.
                "reset_trigger": (
                    "INT",
                    {"default": 0, "min": 0, "max": 2_147_483_647, "step": 1},
                ),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("INT", "STRING")
    RETURN_NAMES = ("index", "index_str")
    FUNCTION = "execute"
    CATEGORY = "utils"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs: object) -> float:
        """Force re-execution every run so the held counter actually advances."""
        return float("nan")

    def execute(
        self,
        runs_per_index: int,
        min_index: int,
        max_index: int,
        mode: str = DEFAULT_MODE,
        format: str = "{}",
        reset_trigger: int = 0,
        unique_id: object = "default",
        **_legacy: object,
    ) -> dict[str, object]:
        """Return the current index and advance the per-node counter.

        Returns a dict with ``ui`` (so the value displays in the node body) and ``result`` (the
        ``(int, str)`` tuple passed downstream). Unknown legacy kwargs (e.g. the v1 ``loop`` and
        ``reset`` inputs from saved workflows) are accepted and ignored.
        """
        node_key = str(unique_id)
        state = _get_state(node_key)

        # Defensive: the UI minimum is 1 but a bad caller could pass 0/negative.
        if runs_per_index < 1:
            runs_per_index = 1

        # Reset button: token monotonically increases with each click.
        if reset_trigger != state.last_reset_token:
            state.reset()
            state.last_reset_token = reset_trigger

        if min_index <= max_index:
            lo, hi = min_index, max_index
        else:
            lo, hi = max_index, min_index

        if mode not in MODES:
            mode = DEFAULT_MODE

        tick = state.count // runs_per_index

        # Hold: only recompute when the tick actually advanced (cheap, but also makes ``random``
        # mode hold a single value across the run window instead of re-rolling).
        if state.cached_tick == tick and state.cached_index is not None:
            index = state.cached_index
        else:
            if mode == "shuffle":
                # Mix node id into the seed so independent counters shuffle differently.
                seed = (hash(node_key) ^ tick) & 0x7FFFFFFF
                index = state.shuffle_index(tick, lo, hi, seed)
            else:
                # For ``random``, mix node id + tick so each tick of each node looks independent.
                seed = (hash(node_key) ^ (tick * 2654435761)) & 0x7FFFFFFF
                index = _compute_index(tick, lo, hi, mode, seed=seed)
            state.cached_tick = tick
            state.cached_index = index

        state.count += 1

        formatted = _safe_format(format, index)
        return {
            "ui": {"text": [formatted]},
            "result": (index, formatted),
        }


def _safe_format(fmt: str, value: int) -> str:
    """Apply ``fmt.format(value)`` but never raise on bad user input."""
    if not fmt:
        return str(value)
    try:
        return fmt.format(value)
    except (IndexError, KeyError, ValueError):
        return str(value)
