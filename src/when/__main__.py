#!/usr/bin/env python


def main():
    import sys

    from . import cli

    return sys.exit(cli.main(sys.argv[1:]))


if __name__ == "__main__":
    main()
