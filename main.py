#!/usr/bin/env python3

"""
Main entrypoint for the application.
"""

import argparse
import logging

from itertools import batched

from create.game import create_game
from create.plan import create_plans
from fetch.point_transfer import transfer_points
from update.game import update_game
from update.plan import get_updated_plans
from util.thunderdome_plan import get_plans


class MapPriorityAction(argparse.Action):
    """
    Action for parsing GitLab labels to Thunderdome priorities.
    """
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if not len(values) % 2 == 0:
            raise argparse.ArgumentTypeError("Priority assignment items list "
                                             "must have even length")

        result = {}
        for key, val in batched(values, n=2):
            label = str(key)
            priority = int(val)
            if priority not in (1,2,3,4,5,6,99):
                raise argparse.ArgumentTypeError("Thunderdome priority must be one of "
                                                 "1,2,3,4,5,6,99")
            result[label] = priority

        result = dict(sorted(result.items(), key=lambda item: item[1]))

        setattr(namespace, self.dest, result)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    """

    parser = argparse.ArgumentParser(
        description='Thunderdome API automation script')
    subparsers = parser.add_subparsers(dest='command', required=True)

    fetch_parser = subparsers.add_parser(
        'fetch', help='Fetch battles from the Thunderdome API')
    fetch_parser.add_argument('battleid', help='Battle ID to fetch')
    fetch_parser.add_argument('api_key', help='API key for the Thunderdome API')
    # fetch_parser.add_argument('gitlab_group_id', help='GitLab group')
    fetch_parser.add_argument('token', help='Token for the GitLab API')

    fetch_parser.add_argument("--overwrite", action="store_true",
                              help="Overwrite existing weights")

    create_parser = subparsers.add_parser(
        'create', help='Create Thunderdome battles from GitLab items')
    create_parser.add_argument('api_key', help='API key for the Thunderdome API')
    create_parser.add_argument('token', help='Token for the GitLab API')

    update_parser = subparsers.add_parser(
        'update', help='Update Thunderdome battles from GitLab items')
    update_parser.add_argument('battleid', help='Battle ID to fetch')
    update_parser.add_argument('api_key', help='API key for the Thunderdome API')
    update_parser.add_argument('token', help='Token for the GitLab API')

    # TODO: Use a shared parser for common arguments

    # Thunderdome battle creation arguments
    battle_settings = create_parser.add_argument_group('Battle creation arguments')
    battle_settings.add_argument('--auto-finish', action='store_true',
                                 help='Automatically finish the battle when everybody voted')
    battle_settings.add_argument('--leaders', nargs='+', type=str,
                                 help='User IDs of leaders')
    battle_settings.add_argument('--scale_id', type=str, help='Estimation scale ID')
    battle_settings.add_argument('--hide-identity', action='store_true',
                                 help='Hide identities of participants')
    battle_settings.add_argument('--join-password', type=str,
                                 help='Password for joining the battle')
    battle_settings.add_argument('--leader-password', type=str,
                                 help='Password for leading the battle')
    battle_settings.add_argument('--name', type=str, default="API Game",
                                 help='Name of the battle in Thunderdome')
    battle_settings.add_argument('--teamid', type=str, help='Team ID to create battle for')
    battle_settings.add_argument('--round-type', type=str, choices=('ceil', 'round', 'floor'),
                                 default='ceil',
                                 help='Rounding method for points')
    battle_settings.add_argument('--allowed-values', nargs='+', type=str, default=[],
                                 help='Allowed values for points')

    # GitLab items
    gitlab_items = create_parser.add_argument_group('GitLab items to include in the battle')
    gitlab_items.add_argument("--milestones", nargs="+", default=[],
                              help="Links to milestones to include in the battle")
    gitlab_items.add_argument("--iterations", nargs="+", default=[],
                              help="Links to iterations to include in the battle")
    gitlab_items.add_argument("--projects", nargs="+", default=[],
                              help="Links to projects to include in the battle")
    gitlab_items.add_argument("--epics", nargs="+", default=[],
                              help="Links to epics to include in the battle")
    gitlab_items.add_argument("--issues", nargs="+", default=[],
                              help="Links to issues to include in the battle")

    create_parser.add_argument("--with-weighted", action="store_true",
                               help=("Include GitLab items in the battle "
                               "that already have a weight set"))
    create_parser.add_argument("--with-closed", action="store_true",
                               help=("Include GitLab items in the battle "
                               "that are closed"))

    create_parser.add_argument("--label-priority", action=MapPriorityAction, nargs="*",
                               help="Map GitLab labels to Thunderdome priorities")

    # GitLab items
    gitlab_items = update_parser.add_argument_group('GitLab items to include in the battle')
    gitlab_items.add_argument("--milestones", nargs="+", default=[],
                              help="Links to milestones to include in the battle")
    gitlab_items.add_argument("--iterations", nargs="+", default=[],
                              help="Links to iterations to include in the battle")
    gitlab_items.add_argument("--projects", nargs="+", default=[],
                              help="Links to projects to include in the battle")
    gitlab_items.add_argument("--epics", nargs="+", default=[],
                              help="Links to epics to include in the battle")
    gitlab_items.add_argument("--issues", nargs="+", default=[],
                              help="Links to issues to include in the battle")

    update_parser.add_argument("--with-weighted",action="store_true",
                               help=("Include GitLab items in the battle "
                               "that already have a weight set"))
    update_parser.add_argument("--with-closed", action="store_true",
                               help=("Include GitLab items in the battle "
                               "that are closed"))

    update_parser.add_argument("--label-priority", action=MapPriorityAction, nargs="*",
                               help=("Map GitLab label names to Thunderdome priorities"
                                     "(Example: 'high 1 medium 2')"
                               ))

    return parser.parse_args()


def main() -> None:
    """
    Main entrypoint.
    """
    args = parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.command == "fetch":
        plans = get_plans(args.battleid, args.api_key)
        transfer_points(plans, args.token, args.overwrite)

    elif args.command == "create":
        plans = create_plans(args)

        if not plans:
            logging.info("Skipping battle creation: No plans generated")
            return

        create_game(plans, args)

    elif args.command == "update":
        plans = get_plans(args.battleid, args.api_key)

        logging.info("Found %d unique Thunderdome plans", len(plans))

        new_plans = get_updated_plans(plans, args)
        update_game(args.battleid, new_plans, args)


if __name__ == "__main__":
    main()
