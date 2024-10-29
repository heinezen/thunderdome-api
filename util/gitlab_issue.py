"""
Retrieve GitLab issue data using the GitLab API.
"""

import re
import logging

import requests

from .definitions import GITLAB_EPIC_URL_REGEX, GITLAB_ORGA_MILESTONE_REGEX, \
    GITLAB_PAGINATION_LIMIT, GITLAB_ITERATION_REGEX, GITLAB_PROJECT_URL_REGEX, \
    GITLAB_ISSUE_URL_REGEX
from .gitlab_id import get_group_id, get_project_id
from .paginate import paginate_request


def get_issues_from_milestones(links: list[str], token: str) -> dict[int, str]:
    """
    Get issues from GitLab milestones.

    :param links: GitLab milestone URLs to create plans from.
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
                link,
                GITLAB_ORGA_MILESTONE_REGEX.pattern,
            )
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
            headers=gitlab_headers,
        )

        if not gitlab_response.ok:
            logging.error("Failed to fetch milestone %s", milestone_iid)
            continue

        payload = gitlab_response.json()
        milestone_name = payload[0]["title"]

        for res in paginate_request(
            "https://gitlab.com/api/v4/issues",
            {
                "milestone": milestone_name, 
                "per_page": GITLAB_PAGINATION_LIMIT, 
                "scope": "all",
            },
            gitlab_headers,
        ):
            payload = res.json()
            for issue in payload:
                issues.update({issue["id"]: issue["web_url"]})

    return issues


def get_issues_from_iterations(links: list[str], token: str) -> dict[int, str]:
    """
    Create Thunderdome plans from GitLab iterations.

    :param links: GitLab iteration URLs to create plans from.
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
            logging.error(
                "Invalid URL '%s' does not match GitLab URL pattern '%s'",
                link,
                GITLAB_ITERATION_REGEX.pattern,
            )
            continue

        iteration_id = match.group("iteration")

        for res in paginate_request(
            "https://gitlab.com/api/v4/issues",
            {
                "iteration_id": iteration_id, 
                "per_page": GITLAB_PAGINATION_LIMIT,
                "scope": "all",
            },
            gitlab_headers,
        ):
            payload = res.json()
            for issue in payload:
                issues.update({issue["id"]: issue["web_url"]})

    return issues


def get_issues_from_projects(links: list[str], token: str) -> dict[int, str]:
    """
    Create Thunderdome plans from GitLab projects.

    :param links: GitLab project URLs to create plans from.
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
            logging.error(
                "Invalid URL '%s' does not match GitLab URL pattern '%s'",
                link,
                GITLAB_PROJECT_URL_REGEX.pattern,
            )
            continue

        # get project ID
        project_id = get_project_id(link, token, GITLAB_PROJECT_URL_REGEX)

        for res in paginate_request(
            f"https://gitlab.com/api/v4/projects/{project_id}/issues",
            {
                "per_page": GITLAB_PAGINATION_LIMIT, 
                "scope": "all",
            },
            gitlab_headers,
        ):
            payload = res.json()
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
            logging.error(
                "Invalid URL '%s' does not match GitLab URL pattern '%s'",
                link,
                GITLAB_EPIC_URL_REGEX.pattern,
            )
            continue

        group_name = match.group("orga")
        epic_iid = match.group("epic")

        # get group ID
        group_id = get_group_id(group_name, token)

        for res in paginate_request(
            f"https://gitlab.com/api/v4/groups/{group_id}/epics/{epic_iid}/issues",
            {
                "per_page": GITLAB_PAGINATION_LIMIT, 
                "scope": "all",
            },
            gitlab_headers,
        ):
            payload = res.json()
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
        logging.error(
            "Invalid URL '%s' does not match GitLab URL pattern '%s'",
            issue_link,
            GITLAB_ISSUE_URL_REGEX.pattern,
        )
        return None

    project_path = match.group("project")
    issue_iid = match.group("issue")

    # Get project ID
    project_id = get_project_id(issue_link, token, GITLAB_ISSUE_URL_REGEX)

    # Get issue information
    gitlab_response = requests.get(
        f"https://gitlab.com/api/v4/projects/{project_id}/issues/{issue_iid}",
        timeout=10,
        headers=gitlab_headers,
    )

    if not gitlab_response.ok:
        logging.error("Failed to fetch issue %s#%s", project_path, issue_iid)
        return None

    return gitlab_response.json()
