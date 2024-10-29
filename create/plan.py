"""
Create Thunderdome game plans.
"""
from __future__ import annotations

import logging
import re
import typing

from util.definitions import GITLAB_ISSUE_URL_REGEX
from util.gitlab_issue import get_issues_from_epics, get_issues_from_iterations, \
      get_issues_from_milestones, get_issues_from_projects, get_issue_info


if typing.TYPE_CHECKING:
    import argparse


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