"""Image enum for garments."""

from enum import Enum


class Image(str, Enum):
    """Image options for garments."""
    PROFILE = "profile"
    CUSTOM = "custom"
