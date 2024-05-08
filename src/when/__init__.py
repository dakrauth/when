"""
Calculate and convert times across time zones and cities of significant population.
"""

__version__ = "3.2.0"
VERSION = tuple(int(i) for i in __version__.split("."))


def __getattr__(name):
    if name == "when":
        from .core import When

        return When()

    raise AttributeError(f"What is {name}?")
