'''
Calculate and convert times across time zones.
'''

__version__ = (1, 0, 0)
VERSION = '.'.join(str(i) for i in __version__)


def __getattr__(name):
    if name == 'when':
        from .core import When
        return When()

    raise AttributeError(f'What is {name}?')
