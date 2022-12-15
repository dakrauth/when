#!/usr/bin/env python

def main():
    import sys
    from .main import main as _main
    return _main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
