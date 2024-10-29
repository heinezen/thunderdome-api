#!/usr/bin/env python3

"""
Main entrypoint for the application.
"""

import argparse
import logging
import re

import requests

from fetch.point_transfer import transfer_points
from util.definitions import GITLAB_ISSUE_URL_REGEX
from util.gitlab_issue import get_issues_from_epics, get_issues_from_iterations, \
      get_issues_from_milestones, get_issues_from_projects, get_issue_info
from util.thunderdome_plan import get_plans


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

    create_parser.add_argument("--with-weighted",action="store_true",
                               help=("Include GitLab items in the battle "
                               "that already have a weight set"))
    create_parser.add_argument("--with-closed", action="store_true",
                               help=("Include GitLab items in the battle "
                               "that are closed"))

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



def create_game(plans: list[dict], args: argparse.Namespace) -> None:
    """
    Create a Thunderdome game.

    :plans: Plans for the battle.
    :args: Command line arguments.
    """
    thunderdome_headers = {
        "accept": "application/json",
        "X-API-Key": args.api_key,
    }

    thunderdome_response = requests.get(
        "https://thunderdome.dev/api/auth/user", timeout=10, headers=thunderdome_headers
    )
    payload = thunderdome_response.json()
    user_id = payload["data"]["id"]

    # Create battle

    # query parameters
    battle_settings_query = {
        "userId": user_id,
    }

    request_url = f"https://thunderdome.dev/api/users/{user_id}/battles"
    if args.teamid is not None:
        battle_settings_query["teamId"] = args.teamid
        request_url = (
            f"https://thunderdome.dev/api/teams/{args.teamid}/users/{user_id}/battles"
        )

    # mandatory body parameters
    battle_settings_body = {
        "name": args.name,
        "plans": plans,
        "pointAverageRounding": args.round_type,
        "pointValuesAllowed": args.allowed_values,
    }

    # optional body parameters
    if args.auto_finish is not None:
        battle_settings_body["autoFinishVoting"] = args.auto_finish

    if args.leaders is not None:
        battle_settings_body["leaders"] = args.leaders

    if args.scale_id is not None:
        battle_settings_body["estimationScaleId"] = args.scale_id

    if args.hide_identity is not None:
        battle_settings_body["hideVoterIdentity"] = args.hide_identity

    if args.join_password is not None:
        battle_settings_body["joinCode"] = args.join_password

    if args.leader_password is not None:
        battle_settings_body["leaderCode"] = args.leader_password

    thunderdome_response = requests.post(
        request_url,
        timeout=10,
        headers=thunderdome_headers,
        params=battle_settings_query,
        json=battle_settings_body,
    )

    if not thunderdome_response.ok:
        logging.error("Failed to create battle")
        logging.error(thunderdome_response.json())


def create_plans(args: argparse.Namespace) -> list[dict]:
    """
    Create plans for a battle in the Thunderdome API.

    :param args: Command line arguments.
    """
    issues: dict[int, str] = {}

    if args.milestones:
        issues.update(get_issues_from_milestones(args.milestones, args.token))

    if args.iterations:
        issues.update(get_issues_from_iterations(args.iterations, args.token))

    if args.projects:
        issues.update(get_issues_from_projects(args.projects, args.token))

    if args.epics:
        issues.update(get_issues_from_epics(args.epics, args.token))

    if args.issues:
        for issue in args.issues:
            info = get_issue_info(issue, args.token)
            issues.update({info["id"]: info["web_url"]})

    logging.info("Found %d unique issues", len(issues))

    plans = create_plans_from_issues(
        issues, args.token, args.with_weighted, args.with_closed
    )

    return plans


def create_plans_from_issues(
    links: dict[int, str],
    token: str,
    with_weighted: bool = False,
    with_closed: bool = False
) -> list[dict]:
    """
    Create Thunderdome plans from GitLab issues.

    :param links: GitLab issues to create plans from.
    :param token: Token for the GitLab API.
    :return: Plans for the battle.
    """
    logging.info("Fetching issues from GitLab...")

    plans: list[dict] = []
    for issue_link in links.values():
        issue = get_issue_info(issue_link, token)

        match = re.match(GITLAB_ISSUE_URL_REGEX, issue_link)

        if not with_weighted:
            if issue["weight"] is not None:
                logging.info(
                    "Skipping %s#%s: Issue already has a weight set",
                    match.group("project"),
                    match.group("issue")
                )
                continue

        if not with_closed:
            if not issue["state"] == "opened":
                # Skip closed issues
                logging.info(
                    "Skipping %s#%s: Issue is closed",
                    match.group("project"),
                    match.group("issue")
                )
                continue

        if issue:
            plan = {
                "description": issue["description"],
                "id": str(issue["id"]),
                "link": issue["web_url"],
                "name": issue["title"],
                # "priority": issue["priority"], # TODO: Get priority from labels
                "referenceId": f"{match.group('project')}#{issue['iid']}",
                "type": "Task",
            }
            plans.append(plan)

    return plans


if __name__ == "__main__":
    main()
