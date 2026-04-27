"""Implementation package for the HoldCounter ComfyUI custom node."""

from .node import (
    DEFAULT_MODE,
    MODES,
    HoldCounter,
    NodeState,
)

NODE_CLASS_MAPPINGS = {
    "HoldCounter": HoldCounter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HoldCounter": "Hold Counter",
}

__all__ = [
    "DEFAULT_MODE",
    "MODES",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "HoldCounter",
    "NodeState",
]
