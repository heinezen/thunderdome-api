#!/usr/bin/env python3

"""
Main entrypoint for the application.
"""

import argparse
import logging
import re
import requests

GITLAB_URL_REGEX = re.compile(
    r"https:\/\/gitlab\.com\/(?P<orga>[a-zA-Z0-9\-\_]+)\/"
    r"(?P<project>[a-zA-Z0-9\-\_]+)\/-\/issues\/(?P<issue>[0-9]+)")


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
    battle_settings.add_argument('--hide-identities', action='store_true',
                                 help='Hide identities of participants')
    battle_settings.add_argument('--join-password', type=str,
                                 help='Password for joining the battle')
    battle_settings.add_argument('--leader-password', type=str,
                                 help='Password for leading the battle')
    battle_settings.add_argument('--name', type=str, help='Name of the battle in Thunderdome')
    battle_settings.add_argument('--teamid', type=str, help='Team ID to create battle for')
    battle_settings.add_argument('--round-type', type=str, choices=('ceil', 'round', 'floor'),
                                 help='Rounding method for points')
    battle_settings.add_argument('--allowed_values', nargs='+', type=str,
                                 help='Allowed values for points')

    # GitLab items
    gitlab_items = create_parser.add_argument_group('GitLab items to include in the battle')
    gitlab_items.add_argument("--milestones", nargs="+",
                              help="Links to milestones to include in the battle")
    gitlab_items.add_argument("--iteration", nargs="+",
                              help="Links to iterations to include in the battle")
    gitlab_items.add_argument("--projects", nargs="+",
                              help="Links to projects to include in the battle")
    gitlab_items.add_argument("--epics", nargs="+",
                              help="Links to epics to include in the battle")
    gitlab_items.add_argument("--issues", nargs="+",
                              help="Links to issues to include in the battle")

    create_parser.add_argument("--with-weighted", action="store_true",
                               help=("Include GitLab items in the battle "
                                     "that already have a weight set"))

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
        pass


def get_plans(battle_id: str, api_key: str) -> list[dict]:
    """
    Get plans from the Thunderdome API.

    :param battle_id: Battle ID to fetch.
    :param api_key: API key for the Thunderdome API.
    :return: Plans for the battle.
    """
    logging.info("Fetching plans for battle %s...", battle_id)

    thunderdome_headers = {
        'accept': "application/json",
        "X-API-Key": api_key,
    }

    # Thunderdome request
    thunderdome_response = requests.get(f"https://thunderdome.dev/api/battles/{battle_id}",
                                        timeout=10,
                                        headers=thunderdome_headers)

    if not thunderdome_response.ok:
        logging.error("Failed to fetch battle %s", battle_id)
        return []

    payload = thunderdome_response.json()

    logging.debug("Fetched %d plans", len(payload["data"]["plans"]))

    return payload["data"]["plans"]


def transfer_points(plans: list[dict], gitlab_token: str, overwrite: bool = False) -> None:
    """
    Transfer points to GitLab issues.

    :param plans: Plans from the Thunderdome game.
    :param gitlab_token: Token for the GitLab API.
    :param overwrite: True to overwrite existing weights, False to preserve existing weights.
    """
    logging.info("Transferring points to GitLab...")

    gitlab_headers = {
        "PRIVATE-TOKEN": gitlab_token,
    }

    for plan in plans:
        points = plan["points"]
        if not points:
            logging.warning("Skipping plan %s: No points set for plan", plan["id"])
            continue

        try:
            _ = int(points)

        except ValueError:
            logging.error("Skipping plan %s: Points is not an integer, found '%s' instead",
                          plan["id"], points)
            continue

        link = plan["link"]
        if not link:
            logging.warning("Skipping plan %s: No link set for plan", plan["id"])
            continue

        match = re.match(GITLAB_URL_REGEX, plan["link"])
        if not match:
            logging.error(("Skipping plan %s: Invalid URL '%s' does "
                           "not match GitLab URL pattern '%s'"),
                          plan["id"], plan["link"], GITLAB_URL_REGEX.pattern)
            continue

        project_path = match.group("project")
        issue_iid = match.group("issue")

        # Get project ID
        gitlab_response = requests.get(
            f"https://gitlab.com/api/v4/projects?search={project_path}",
            timeout=10,
            headers=gitlab_headers)
        payload = gitlab_response.json()

        # Find project ID
        for project in payload:
            if project["path"] == project_path:
                project_id = project["id"]
                logging.debug("Project %s has ID %s", project_path, project_id)
                break

        else:
            logging.error("Failed to find ID of project %s", project_path)
            continue

        # Get issue information
        gitlab_response = requests.get(
            f"https://gitlab.com/api/v4/projects/{project_id}/issues/{issue_iid}",
            timeout=10,
            headers=gitlab_headers)
        payload = gitlab_response.json()

        if not gitlab_response.ok:
            logging.error("Failed to fetch issue %s#%s", project_path, issue_iid)
            continue

        if not "weight" in payload:
            logging.error("No 'weight' for issue in API response. Are you authenticated?")
            continue

        previous_weight = payload["weight"]

        if previous_weight is not None and overwrite is False:
            logging.info("Skipping %s#%s: Issue already has a weight set",
                         project_path, issue_iid)
            continue

        # Set weight
        gitlab_response = requests.put(
            f"https://gitlab.com/api/v4/projects/{project_id}/issues/{issue_iid}",
            timeout=10,
            headers=gitlab_headers,
            json={"weight": points})

        if not gitlab_response.ok:
            logging.error("Failed to set weight for %s#%s", project_path, issue_iid)

        else:
            if previous_weight is not None:
                logging.info("Changed weight to %s for %s#%s (was %s)",
                             points, project_path, issue_iid, previous_weight)
            else:
                logging.info("Set weight to %s for %s#%s",
                             points, project_path, issue_iid)


if __name__ == '__main__':
    main()
