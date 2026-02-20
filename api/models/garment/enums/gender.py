"""Gender enum for garments."""

from enum import Enum


class Gender(str, Enum):
    """Gender options for garments."""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"
