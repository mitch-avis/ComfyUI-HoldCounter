"""ComfyUI entry point.

Re-exports the node mappings from the implementation package and points ComfyUI at the bundled
``web/`` extension directory. The actual code lives under :mod:`_impl`.
"""

from ._impl import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
