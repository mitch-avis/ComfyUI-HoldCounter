from .hold_counter_node import HoldCounter

NODE_CLASS_MAPPINGS = {
    "HoldCounter": HoldCounter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HoldCounter": "Hold Counter",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
