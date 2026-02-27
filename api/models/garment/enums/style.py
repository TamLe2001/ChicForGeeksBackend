"""Style enum for garments."""

from enum import Enum


class Style(str, Enum):
    """Style/genre options for garments."""
    STREETWEAR = "streetwear"
    FORMAL = "formal"
    CASUAL = "casual"
    SPORTY = "sporty"
    PREPPY = "preppy"
    Y2K = "y2k"
