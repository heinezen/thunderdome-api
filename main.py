#!/usr/bin/env python3

"""
Main entrypoint for the application.
"""

import argparse
import logging
import re
import requests

GITLAB_ORGA_MILESTONE_REGEX = re.compile(
    r"https:\/\/gitlab\.com\/groups/(?P<orga>[a-zA-Z0-9\-\_]+)\/-\/"
    r"milestones\/(?P<milestone>[0-9]+)"
)
GITLAB_PROJECT_MILESTONE_REGEX = re.compile(
    r"https:\/\/gitlab\.com\/(?P<orga>[a-zA-Z0-9\-\_]+)\/(?:(?P<subgroup>[a-zA-Z0-9\-\_]+)\/)*"
    r"(?P<project>[a-zA-Z0-9\-\_]+)\/-\/milestones\/(?P<milestone>[0-9]+)"
)
GITLAB_ITERATION_REGEX = re.compile(
    r"https:\/\/gitlab\.com\/groups/(?P<orga>[a-zA-Z0-9\-\_]+)\/-\/"
    r"cadences\/(?P<cadence>[0-9]+)\/iterations\/(?P<iteration>[0-9]+)"
)
GITLAB_EPIC_URL_REGEX = re.compile(
    r"https:\/\/gitlab\.com\/groups\/(?P<orga>[a-zA-Z0-9\-\_]+)\/-\/"
    r"epics\/(?P<epic>[0-9]+)"
)
GITLAB_PROJECT_URL_REGEX = re.compile(
    r"https:\/\/gitlab\.com\/(?P<orga>[a-zA-Z0-9\-\_]+)\/(?:(?P<subgroup>[a-zA-Z0-9\-\_]+)\/)*"
    r"(?P<project>[a-zA-Z0-9\-\_]+)"
)
GITLAB_ISSUE_URL_REGEX = re.compile(
    r"https:\/\/gitlab\.com\/(?P<orga>[a-zA-Z0-9\-\_]+)\/(?:(?P<subgroup>[a-zA-Z0-9\-\_]+)\/)*"
    r"(?P<project>[a-zA-Z0-9\-\_]+)\/-\/issues\/(?P<issue>[0-9]+)"
)


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
        plans = fetch_plans(args.battleid, args.api_key)
        transfer_points(plans, args.token, args.overwrite)

    elif args.command == "create":
        plans = create_plans(args)
        create_game(plans, args)


def fetch_plans(battle_id: str, api_key: str) -> list[dict]:
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

        match = re.match(GITLAB_ISSUE_URL_REGEX, plan["link"])
        if not match:
            logging.error(("Skipping plan %s: Invalid URL '%s' does "
                           "not match GitLab URL pattern '%s'"),
                          plan["id"], plan["link"], GITLAB_ISSUE_URL_REGEX.pattern)
            continue

        project_path = match.group("project")
        issue_iid = match.group("issue")

        # Get project ID
        project_id = get_project_id(link, gitlab_token)

        # Get issue information
        gitlab_response = requests.get(
            f"https://gitlab.com/api/v4/projects/{project_id}/issues/{issue_iid}",
            timeout=10,
            headers=gitlab_headers
        )
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
            json={"weight": points}
        )

        if not gitlab_response.ok:
            logging.error("Failed to set weight for %s#%s", project_path, issue_iid)

        else:
            if previous_weight is not None:
                logging.info("Changed weight to %s for %s#%s (was %s)",
                             points, project_path, issue_iid, previous_weight)
            else:
                logging.info("Set weight to %s for %s#%s",
                             points, project_path, issue_iid)


def create_game(plans: list[dict], args: argparse.Namespace) -> None:
    """
    Create a Thunderdome game.

    :plans: Plans for the battle.
    :args: Command line arguments.
    """
    thunderdome_headers = {
        'accept': "application/json",
        "X-API-Key": args.api_key,
    }

    thunderdome_response = requests.get(
        "https://thunderdome.dev/api/auth/user",
        timeout=10,
        headers=thunderdome_headers)
    payload = thunderdome_response.json()
    user_id = payload["data"]["id"]

    # Create battle

    # query parameters
    battle_settings_query = {
        "userId": user_id,
        "teamId": args.teamid,
    }

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
        f"https://thunderdome.dev/api/teams/{args.teamid}/users/{user_id}/battles",
        timeout=10,
        headers=thunderdome_headers,
        params=battle_settings_query,
        json=battle_settings_body)

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

    plans = create_plans_from_issues(issues, args.token)

    return plans


def create_plans_from_issues(links: dict[int, str], token: str) -> list[dict]:
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

        if issue:
            plan = {
                "description": issue["description"],
                "id": str(issue["id"]),
                "link": issue["web_url"],
                "name": issue["title"],
                # "priority": issue["priority"], # TODO: Get priority from labels
                "referenceId": str(issue["iid"]),
                "type": "Task",
            }
            plans.append(plan)

    return plans


def get_issues_from_milestones(links: list[str], token: str) -> dict[int, str]:
    """
    Get issues from GitLab milestones.

    :param links: GitLab milestones to create plans from.
    :param token: Token for the GitLab API.
    """
    logging.info("Fetching milestones from GitLab...")

    gitlab_headers = {
        "PRIVATE-TOKEN": token,
    }

    issues: dict[int, str] = {}
    for link in links:
        # check if the link is a group milestone
        match = re.match(GITLAB_ORGA_MILESTONE_REGEX, link)
        if not match:
            logging.error(
                "Invalid URL '%s' does not match GitLab URL pattern '%s'",
                link, GITLAB_ORGA_MILESTONE_REGEX.pattern)
            continue

        group_name = match.group("orga")

        # get group ID
        group_id = get_group_id(group_name, token)

        # get milestone ID
        milestone_iid = match.group("milestone")
        gitlab_response = requests.get(
            f"https://gitlab.com/api/v4/groups/{group_id}/milestones",
            timeout=10,
            params={"iids": [milestone_iid]},
            headers=gitlab_headers
        )

        if not gitlab_response.ok:
            logging.error("Failed to fetch milestone %s", milestone_iid)
            continue

        payload = gitlab_response.json()
        milestone_name = payload[0]["title"]

        def paginate_issues(next_url = None) -> requests.Response:
            """
            Get issues in a GitLab milestone.

            :param next_url: URL to paginate through issues.
                             If None, the initial request is created instead.
            :return: Issues in the milestone.
            """
            if next_url:
                gitlab_response = requests.get(
                    next_url,
                    timeout=10,
                    headers=gitlab_headers
                )

            else:
                gitlab_response = requests.get(
                    "https://gitlab.com/api/v4/issues",
                    timeout=10,
                    params={"milestone": milestone_name, "per_page": 100},
                    headers=gitlab_headers
                )

            if not gitlab_response.ok:
                logging.error("Failed to fetch issues in milestone %s", milestone_name)
                continue

            return gitlab_response

        gitlab_response = paginate_issues()

        payload = gitlab_response.json()
        for issue in payload:
            issues.update({issue["id"]: issue["web_url"]})

        # Paginate through issues
        while "next" in gitlab_response.links:
            gitlab_response = paginate_issues(gitlab_response.links["next"]["url"])
            payload = gitlab_response.json()
            for issue in payload:
                issues.update({issue["id"]: issue["web_url"]})

    return issues


def get_issues_from_iterations(links: list[str], token: str) -> dict[int, str]:
    """
    Create Thunderdome plans from GitLab iterations.

    :param links: GitLab iterations to create plans from.
    :param token: Token for the GitLab API.
    """
    logging.info("Fetching iterations from GitLab...")

    gitlab_headers = {
        "PRIVATE-TOKEN": token,
    }

    issues: dict[int, str] = {}
    for link in links:
        match = re.match(GITLAB_ITERATION_REGEX, link)
        if not match:
            logging.error("Invalid URL '%s' does not match GitLab URL pattern '%s'",
                          link, GITLAB_ITERATION_REGEX.pattern)
            continue

        iteration_id = match.group("iteration")

        def paginate_issues(next_url = None) -> requests.Response:
            """
            Get issues in a GitLab iteration.

            :param next_url: URL to paginate through issues.
                             If None, the initial request is created instead.
            :return: Issues in the iteration.
            """
            if next_url:
                gitlab_response = requests.get(
                    next_url,
                    timeout=10,
                    headers=gitlab_headers
                )

            else:
                gitlab_response = requests.get(
                    "https://gitlab.com/api/v4/issues",
                    timeout=10,
                    params={"iteration_id": iteration_id, "per_page": 100},
                    headers=gitlab_headers
                )

            if not gitlab_response.ok:
                logging.error("Failed to fetch issues in iteration %s", iteration_id)
                continue

            return gitlab_response

        # get issues in iteration
        gitlab_response = paginate_issues()
        payload = gitlab_response.json()
        for issue in payload:
            issues.update({issue["id"]: issue["web_url"]})

        # Paginate through issues
        while "next" in gitlab_response.links:
            gitlab_response = paginate_issues(gitlab_response.links["next"]["url"])
            payload = gitlab_response.json()
            for issue in payload:
                issues.update({issue["id"]: issue["web_url"]})

    return issues


def get_issues_from_projects(links: list[str], token: str) -> dict[int, str]:
    """
    Create Thunderdome plans from GitLab projects.

    :param links: GitLab projects to create plans from.
    :param token: Token for the GitLab API.
    """
    logging.info("Fetching projects from GitLab...")

    gitlab_headers = {
        "PRIVATE-TOKEN": token,
    }

    issues: dict[int, str] = {}
    for link in links:
        match = re.match(GITLAB_PROJECT_URL_REGEX, link)
        if not match:
            logging.error("Invalid URL '%s' does not match GitLab URL pattern '%s'",
                          link, GITLAB_PROJECT_URL_REGEX.pattern)
            continue

        project_path = match.group("project")

        # get project ID
        project_id = get_project_id(link, token)

        def paginate_issues(next_url = None) -> requests.Response:
            """
            Get issues in a GitLab project.

            :param next_url: URL to paginate through issues.
                             If None, the initial request is created instead.
            :return: Issues in the project.
            """
            if next_url:
                gitlab_response = requests.get(
                    next_url,
                    timeout=10,
                    headers=gitlab_headers
                )

            else:
                gitlab_response = requests.get(
                    f"https://gitlab.com/api/v4/projects/{project_id}/issues",
                    timeout=10,
                    params={"per_page": 100},
                    headers=gitlab_headers
                )

            if not gitlab_response.ok:
                logging.error("Failed to fetch issues in project %s", project_path)
                continue

            return gitlab_response

        # get issues in project
        gitlab_response = paginate_issues()
        payload = gitlab_response.json()
        for issue in payload:
            issues.update({issue["id"]: issue["web_url"]})

        # Paginate through issues
        while "next" in gitlab_response.links:
            gitlab_response = paginate_issues(gitlab_response.links["next"]["url"])
            payload = gitlab_response.json()
            for issue in payload:
                issues.update({issue["id"]: issue["web_url"]})

    return issues


def get_issues_from_epics(links: list[str], token: str) -> dict[int, str]:
    """
    Create Thunderdome plans from GitLab epics.

    :param links: GitLab epics to create plans from.
    :param token: Token for the GitLab API.
    """
    logging.info("Fetching epics from GitLab...")

    gitlab_headers = {
        "PRIVATE-TOKEN": token,
    }

    issues: dict[int, str] = {}
    for link in links:
        match = re.match(GITLAB_EPIC_URL_REGEX, link)
        if not match:
            logging.error("Invalid URL '%s' does not match GitLab URL pattern '%s'",
                          link, GITLAB_EPIC_URL_REGEX.pattern)
            continue

        group_name = match.group("orga")
        epic_iid = match.group("epic")

        # get group ID
        gitlab_response = requests.get(
            "https://gitlab.com/api/v4/groups",
            timeout=10,
            params={"search": group_name},
            headers=gitlab_headers
        )

        if not gitlab_response.ok:
            logging.error("Failed to fetch group %s", group_name)
            continue

        payload = gitlab_response.json()
        for group in payload:
            if group["name"] == group_name:
                group_id = group["id"]
                logging.debug("Group %s has ID %s", group_name, group_id)
                break

        else:
            logging.error("Failed to find ID of group %s", group_name)
            continue

        def paginate_issues(next_url = None) -> requests.Response:
            """
            Get issues in a GitLab epic.

            :param next_url: URL to paginate through issues.
                             If None, the initial request is created instead.
            :return: Issues in the epic.
            """
            if next_url:
                gitlab_response = requests.get(
                    next_url,
                    timeout=10,
                    headers=gitlab_headers
                )

            else:
                gitlab_response = requests.get(
                    f"https://gitlab.com/api/v4/groups/{group_id}/epics/{epic_iid}/issues",
                    timeout=10,
                    params={"per_page": 100},
                    headers=gitlab_headers
                )

            if not gitlab_response.ok:
                logging.error("Failed to fetch issues in epic %s", epic_iid)
                continue

            return gitlab_response

        # get issues in epic
        gitlab_response = paginate_issues()
        payload = gitlab_response.json()
        for issue in payload:
            issues.update({issue["id"]: issue["web_url"]})

        # Paginate through issues
        while "next" in gitlab_response.links:
            gitlab_response = paginate_issues(gitlab_response.links["next"]["url"])
            payload = gitlab_response.json()
            for issue in payload:
                issues.update({issue["id"]: issue["web_url"]})

    return issues


def get_issue_info(issue_link: str, token: str) -> dict | None:
    """
    Get information about a GitLab issue from the GitLab API.

    :param link: Link to the GitLab issue.
    :param token: Token for the GitLab API.
    """
    gitlab_headers = {
        "PRIVATE-TOKEN": token,
    }

    match = re.match(GITLAB_ISSUE_URL_REGEX, issue_link)
    if not match:
        logging.error("Invalid URL '%s' does not match GitLab URL pattern '%s'",
                      issue_link, GITLAB_ISSUE_URL_REGEX.pattern)
        return None

    project_path = match.group("project")
    issue_iid = match.group("issue")

    # Get project ID
    gitlab_response = requests.get(
        "https://gitlab.com/api/v4/projects",
        timeout=10,
        params={"search": project_path},
        headers=gitlab_headers
    )
    payload = gitlab_response.json()

    # Find project ID
    for project in payload:
        if project["path"] == project_path:
            project_id = project["id"]
            logging.debug("Project %s has ID %s", project_path, project_id)
            break

    else:
        logging.error("Failed to find ID of project %s", project_path)
        return None

    # Get issue information
    gitlab_response = requests.get(
        f"https://gitlab.com/api/v4/projects/{project_id}/issues/{issue_iid}",
        timeout=10,
        headers=gitlab_headers
    )

    if not gitlab_response.ok:
        logging.error("Failed to fetch issue %s#%s", project_path, issue_iid)
        return None

    return gitlab_response.json()


def get_group_id(group_name: str, token: str) -> int | None:
    """
    Get the ID of a GitLab group.

    :param group_name: Name of the GitLab group.
    :param token: Token for the GitLab API.
    """
    gitlab_headers = {
        "PRIVATE-TOKEN": token,
    }

    # Get group ID
    gitlab_response = requests.get(
        "https://gitlab.com/api/v4/groups",
        timeout=10,
        params={"search": group_name},
        headers=gitlab_headers
    )

    if not gitlab_response.ok:
        logging.error("Failed to fetch group %s", group_name)
        return None

    payload = gitlab_response.json()
    for group in payload:
        if group["name"] == group_name:
            group_id = group["id"]
            logging.debug("Group %s has ID %s", group_name, group_id)
            return group_id

    logging.error("Failed to find ID of group %s", group_name)
    return None


def get_project_id(issue_link: str, token: str) -> int | None:
    """
    Get the ID of a GitLab project from a GitLab issue.

    :param issue_link: Link to the GitLab issue.
    :param token: Token for the GitLab API.
    """
    gitlab_headers = {
        "PRIVATE-TOKEN": token,
    }

    match = re.match(GITLAB_ISSUE_URL_REGEX, issue_link)
    if not match:
        logging.error("Invalid URL '%s' does not match GitLab URL pattern '%s'",
                      issue_link, GITLAB_ISSUE_URL_REGEX.pattern)
        return None

    group_name = match.group("orga")
    group_id = get_group_id(group_name, token)

    project_path = match.group("project")

    # Get project ID
    gitlab_response = requests.get(
        f"https://gitlab.com/api/v4/groups/{group_id}/projects",
        timeout=10,
        params={"scope": "projects", "search": project_path},
        headers=gitlab_headers
    )
    payload = gitlab_response.json()

    # Find project ID
    for project in payload:
        if project["path"] == project_path:
            project_id = project["id"]
            logging.debug("Project %s has ID %s", project_path, project_id)
            return project_id

    logging.error("Failed to find ID of project %s", project_path)
    return None


if __name__ == '__main__':
    main()
