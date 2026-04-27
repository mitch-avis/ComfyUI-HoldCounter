"""Pytest suite for the pure compute helpers in ``hold_counter_node``.

The math is intentionally factored into pure functions so it can be exercised without importing
ComfyUI. The class itself is covered indirectly through these tests.
"""

import importlib
import sys
from pathlib import Path

import pytest

# Make the repo root importable when running pytest from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

mod = importlib.import_module("hold_counter_node")
compute_index = mod._compute_index  # type: ignore[attr-defined]
NodeState = mod.NodeState


# ---------------------------------------------------------------------------
# loop mode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tick", "expected"),
    [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 0), (6, 1), (10, 0)],
)
def test_loop_wraps_at_max(tick: int, expected: int) -> None:
    assert compute_index(tick, lo=0, hi=4, mode="loop") == expected


def test_loop_with_offset_range() -> None:
    assert [compute_index(t, lo=10, hi=12, mode="loop") for t in range(7)] == [
        10,
        11,
        12,
        10,
        11,
        12,
        10,
    ]


# ---------------------------------------------------------------------------
# clamp mode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tick", "expected"),
    [(0, 0), (1, 1), (4, 4), (5, 4), (100, 4)],
)
def test_clamp_holds_at_max(tick: int, expected: int) -> None:
    assert compute_index(tick, lo=0, hi=4, mode="clamp") == expected


# ---------------------------------------------------------------------------
# pingpong mode
# ---------------------------------------------------------------------------


def test_pingpong_bounces() -> None:
    seq = [compute_index(t, lo=0, hi=4, mode="pingpong") for t in range(12)]
    # 0,1,2,3,4,3,2,1, then repeats
    assert seq == [0, 1, 2, 3, 4, 3, 2, 1, 0, 1, 2, 3]


def test_pingpong_single_value_range() -> None:
    # When lo == hi the only valid index is lo, regardless of tick.
    assert all(compute_index(t, lo=7, hi=7, mode="pingpong") == 7 for t in range(20))


# ---------------------------------------------------------------------------
# range inversion + zero guard
# ---------------------------------------------------------------------------


def test_lo_greater_than_hi_is_swapped() -> None:
    # Caller supplies lo > hi; helper handles it gracefully.
    assert compute_index(2, lo=5, hi=2, mode="loop") == 4


def test_runs_per_index_does_not_apply_inside_compute() -> None:
    # _compute_index works in *ticks*, not *runs*. The runs->tick conversion is the caller's job; we
    # just make sure tick=0 always produces lo across modes.
    for mode in ("loop", "clamp", "pingpong"):
        assert compute_index(0, lo=3, hi=8, mode=mode) == 3


# ---------------------------------------------------------------------------
# random mode (seeded for determinism)
# ---------------------------------------------------------------------------


def test_random_mode_stays_in_range() -> None:
    seen = {compute_index(t, lo=0, hi=9, mode="random", seed=t) for t in range(200)}
    assert seen.issubset(set(range(10)))
    # With 200 draws over a size-10 range we're overwhelmingly likely to hit every value.
    assert len(seen) == 10


def test_random_mode_is_deterministic_for_a_given_seed() -> None:
    a = compute_index(42, lo=0, hi=99, mode="random", seed=12345)
    b = compute_index(42, lo=0, hi=99, mode="random", seed=12345)
    assert a == b


# ---------------------------------------------------------------------------
# shuffle mode (NodeState owns the permutation)
# ---------------------------------------------------------------------------


def test_shuffle_visits_every_value_before_repeating() -> None:
    state = NodeState()
    seen: list[int] = []
    for tick in range(5):
        seen.append(state.shuffle_index(tick, lo=0, hi=4, seed=99))
    assert sorted(seen) == [0, 1, 2, 3, 4]


def test_shuffle_reshuffles_after_a_full_pass() -> None:
    state = NodeState()
    first_pass = [state.shuffle_index(t, lo=0, hi=4, seed=1) for t in range(5)]
    second_pass = [state.shuffle_index(t, lo=0, hi=4, seed=1) for t in range(5, 10)]
    assert sorted(first_pass) == [0, 1, 2, 3, 4]
    assert sorted(second_pass) == [0, 1, 2, 3, 4]
    # Re-seeding deterministically means the two passes are *probably* not identical, but with a
    # 5-element permutation a collision happens roughly 1/120 of the time. Use seed=1 where the two
    # passes are known to differ.
    assert first_pass != second_pass


# ---------------------------------------------------------------------------
# zero / negative runs_per_index guard inside the class wrapper
# ---------------------------------------------------------------------------


def test_zero_runs_per_index_does_not_raise() -> None:
    """The class normalizes runs_per_index >= 1 even if a caller passes 0 directly."""
    HoldCounter = mod.HoldCounter
    counter = HoldCounter()
    out = counter.execute(
        runs_per_index=0,
        min_index=0,
        max_index=4,
        mode="loop",
        format="{}",
        unique_id="test-node-zero",
    )
    assert out["result"][0] == 0
