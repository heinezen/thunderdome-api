#!/usr/bin/env python3

"""
Main entrypoint for the application.
"""

import argparse

def init_subparsers(cli: argparse._SubParsersAction) -> None:
    """
    Initialize all subparsers.
    """
    from game.main import init_subparser
    subparser = cli.add_parser('game', help='Interact with the Thunderdome poker game API')
    init_subparser(subparser)


def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser(
        description='Thunderdome API automation script')
    cli = parser.add_subparsers(dest='command', required=True)

    init_subparsers(cli)

    return parser.parse_args()


def main() -> None:
    """
    Main entrypoint.
    """
    args = parse_args()

    if args.command == 'game':
        from game.main import main as run
        run(args)


if __name__ == "__main__":
    main()
