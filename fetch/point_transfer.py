"""
Transfer points from Thunderdome games o GitLab issues.
"""

import logging
import re

import requests

from util.definitions import GITLAB_ISSUE_URL_REGEX
from util.gitlab_id import get_project_id


def transfer_points(
    plans: list[dict],
    gitlab_token: str,
    overwrite: bool = False
) -> None:
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
            logging.error(
                "Skipping plan %s: Points is not an integer, found '%s' instead",
                plan["id"],
                points,
            )
            continue

        link = plan["link"]
        if not link:
            logging.warning("Skipping plan %s: No link set for plan", plan["id"])
            continue

        match = re.match(GITLAB_ISSUE_URL_REGEX, plan["link"])
        if not match:
            logging.error(
                (
                    "Skipping plan %s: Invalid URL '%s' does "
                    "not match GitLab URL pattern '%s'"
                ),
                plan["id"],
                plan["link"],
                GITLAB_ISSUE_URL_REGEX.pattern,
            )
            continue

        project_path = match.group("project")
        issue_iid = match.group("issue")

        # Get project ID
        project_id = get_project_id(link, gitlab_token, GITLAB_ISSUE_URL_REGEX)

        # Get issue information
        gitlab_response = requests.get(
            f"https://gitlab.com/api/v4/projects/{project_id}/issues/{issue_iid}",
            timeout=10,
            headers=gitlab_headers,
        )
        payload = gitlab_response.json()

        if not gitlab_response.ok:
            logging.error("Failed to fetch issue %s#%s", project_path, issue_iid)
            continue

        if not "weight" in payload:
            logging.error(
                "No 'weight' for issue in API response. Are you authenticated?"
            )
            continue

        previous_weight = payload["weight"]

        if previous_weight is not None and overwrite is False:
            logging.info(
                "Skipping %s#%s: Issue already has a weight set",
                project_path,
                issue_iid,
            )
            continue

        # Set weight
        gitlab_response = requests.put(
            f"https://gitlab.com/api/v4/projects/{project_id}/issues/{issue_iid}",
            timeout=10,
            headers=gitlab_headers,
            json={"weight": points},
        )

        if not gitlab_response.ok:
            logging.error("Failed to set weight for %s#%s", project_path, issue_iid)

        else:
            if previous_weight is not None:
                logging.info(
                    "Changed weight to %s for %s#%s (was %s)",
                    points,
                    project_path,
                    issue_iid,
                    previous_weight,
                )
            else:
                logging.info(
                    "Set weight to %s for %s#%s", points, project_path, issue_iid
                )
