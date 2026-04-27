"""ComfyUI entry point.

Re-exports the node mappings from the implementation package and points ComfyUI at the bundled
``web/`` extension directory. The actual code lives under :mod:`_impl`.

The ``try / except ImportError`` covers two import contexts:

* **ComfyUI** loads this file via :func:`importlib.util.spec_from_file_location` with the
  surrounding directory as a package, so the relative ``from ._impl …`` form succeeds.
* **pytest** synthesises a ``Package`` collector for the rootdir and imports ``__init__.py`` with no
  parent package. The relative form raises and the absolute fallback (which works because
  ``pythonpath = ["."]`` is set in ``pyproject.toml``) takes over.
"""

try:
    from ._impl import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
except ImportError:
    from _impl import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
