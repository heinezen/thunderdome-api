"""
Main entrypoint for storyboard interaction.
"""

import argparse
import logging


def init_subparser(subparser: argparse.ArgumentParser) -> None:
    """
    Initializes the parser for storyboard-specific args.
    """

    cli = subparser.add_subparsers(dest='subcommand', required=True)

    fetch_parser = cli.add_parser(
        'fetch', help='Fetch sprint planning storyboard from the Thunderdome API')
    fetch_parser.add_argument('boardid', type=str, help='Storyboard ID to fetch')
    fetch_parser.add_argument('iteration', type=str, help='Link to the GitLab iteration')
    fetch_parser.add_argument('api_key', type=str, help='API key for the Thunderdome API')
    fetch_parser.add_argument('token', type=str, help='Token for the GitLab API')

    fetch_parser.add_argument('--filter-goals', nargs='+', type=str,
                              help='Only fetch from goals with the specified names')
    fetch_parser.add_argument('--filter-columns', nargs='+', type=str,
                              help='Only fetch from column with the specified names')


def main(args) -> None:
    """
    Main entrypoint for storyboard command.
    """
    logging.basicConfig(level=logging.INFO)

    if args.subcommand == "fetch":
        # TODO
        pass
