"""
Retrieve IDs of GitLab items using the GitLab API.
"""

import logging
import re

import requests


def get_group_id(group_path: str, token: str) -> int | None:
    """
    Get the ID of a GitLab group.

    :param group_path: Group path name in the GitLab URL.
    :param token: Token for the GitLab API.
    """
    gitlab_headers = {
        "PRIVATE-TOKEN": token,
    }

    # Get group ID
    gitlab_response = requests.get(
        "https://gitlab.com/api/v4/groups",
        timeout=10,
        params={"search": group_path},
        headers=gitlab_headers,
    )

    if not gitlab_response.ok:
        logging.error("Failed to fetch group %s", group_path)
        return None

    payload = gitlab_response.json()
    for group in payload:
        if group["path"] == group_path:
            group_id = group["id"]
            logging.debug("Group %s has ID %s", group_path, group_id)
            return group_id

    logging.error("Failed to find ID of group %s", group_path)
    return None


def get_project_id(issue_link: str, token: str, regex) -> int | None:
    """
    Get the ID of a GitLab project from a GitLab issue.

    :param issue_link: Link to the GitLab issue.
    :param token: Token for the GitLab API.
    """
    gitlab_headers = {
        "PRIVATE-TOKEN": token,
    }

    match = re.match(regex, issue_link)
    if not match:
        logging.error(
            "Invalid URL '%s' does not match GitLab URL pattern '%s'",
            issue_link,
            regex.pattern,
        )
        return None

    group_name = match.group("orga")
    group_id = get_group_id(group_name, token)

    project_path = match.group("project")

    # Get project ID
    gitlab_response = requests.get(
        f"https://gitlab.com/api/v4/groups/{group_id}/search",
        timeout=10,
        params={"scope": "projects", "search": project_path},
        headers=gitlab_headers,
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
