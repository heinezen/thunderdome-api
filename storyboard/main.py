"""
Main entrypoint for storyboard interaction.
"""

import argparse
import logging
import re

from storyboard.fetch.iteration_assign import assign_iteration
from util.definitions import GITLAB_ITERATION_REGEX
from util.thunderdome_story import get_stories


def init_subparser(subparser: argparse.ArgumentParser) -> None:
    """
    Initializes the parser for storyboard-specific args.
    """

    cli = subparser.add_subparsers(dest="subcommand", required=True)

    fetch_parser = cli.add_parser(
        'fetch', help='Fetch sprint planning storyboard from the Thunderdome API')
    fetch_parser.add_argument('boardid', type=str, help='Storyboard ID to fetch')
    fetch_parser.add_argument('iteration', type=str, help='Link to the GitLab iteration')
    fetch_parser.add_argument('api_key', type=str, help='API key for the Thunderdome API')
    fetch_parser.add_argument('token', type=str, help='Token for the GitLab API')

    fetch_parser.add_argument("--filter-goals", nargs="+", type=str,
                              help="Only fetch from goals with the specified names")
    fetch_parser.add_argument("--filter-columns", nargs="+", type=str,
                              help="Only fetch from column with the specified names")
    fetch_parser.add_argument("--clear-iteration", action="store_true",
                              help=("Clear all issues from the iteration that were "
                                    "not fetched from the board"))


def main(args) -> None:
    """
    Main entrypoint for storyboard command.
    """
    logging.basicConfig(level=logging.INFO)

    if args.subcommand == "fetch":
        stories = get_stories(
            args.boardid,
            args.api_key,
            args.filter_goals,
            args.filter_columns
        )

        match = re.match(GITLAB_ITERATION_REGEX, args.iteration)
        if not match:
            logging.error(
                "Invalid URL '%s' does not match GitLab URL pattern '%s'",
                args.iteration,
                GITLAB_ITERATION_REGEX.pattern,
            )
            return

        iteration_id = match.group("iteration")

        assign_iteration(stories, iteration_id, args.token)
