"""
Calculate and convert times across time zones and cities of significant population.
"""

__version__ = (3, 2, 0)
VERSION = ".".join(str(i) for i in __version__)


def __getattr__(name):
    if name == "when":
        from .core import When

        return When()

    raise AttributeError(f"What is {name}?")
