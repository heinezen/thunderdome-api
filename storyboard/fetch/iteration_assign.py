"""
Assign a GitLab iteration (sprint) to GitLab issues for stories in a Thunderdome storyboard.
"""

import logging
import re

import requests

from util.definitions import GITLAB_ISSUE_URL_REGEX
from util.gitlab_id import get_project_id


def assign_iteration(
    stories: list[dict],
    iteration_id: str,
    gitlab_token: str
) -> None:
    """
    Assign iteration to GitLab issues linked in stories.

    :param stories: Stories from a Thunderdome storyboard.
    :param iteration_id: GitLab iteration ID.
    :param gitlab_token: Token for the GitLab API.
    """
    logging.info("Assigning iteration to GitLab issues...")

    gitlab_headers = {
        "PRIVATE-TOKEN": gitlab_token,
    }

    for story in stories:
        link = story["link"]
        if not link:
            logging.warning("Skipping story %s: No link set for story", story["id"])
            continue

        match = re.match(GITLAB_ISSUE_URL_REGEX, story["link"])
        if not match:
            logging.error(
                (
                    "Skipping story %s: Invalid URL '%s' does "
                    "not match GitLab URL pattern '%s'"
                ),
                story["id"],
                story["link"],
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

        if not gitlab_response.ok:
            logging.error("Failed to fetch issue %s#%s", project_path, issue_iid)
            continue

        # Set iteration by making a comment with a quick action
        # since GitLab does not allow setting the iteration for the issue
        # via the API
        # see also: https://gitlab.com/gitlab-org/gitlab/-/issues/395790
        quick_action_body = f"/iteration *iteration:{iteration_id}"
        gitlab_response = requests.post(
            f"https://gitlab.com/api/v4/projects/{project_id}/issues/{issue_iid}/notes",
            timeout=10,
            headers=gitlab_headers,
            params={'body': quick_action_body}
        )

        if not gitlab_response.ok:
            logging.error("Failed to set iteration %s for issue %s#%s",
                          iteration_id, project_path, issue_iid)
            continue

        logging.info("Set iteration to %s for %s#%s", iteration_id, project_path, issue_iid)
