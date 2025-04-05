"""
Update game plans in the Thunderdome API.
"""
from __future__ import annotations

import logging
import typing

from game.create.plan import create_plans_from_issues
from util.gitlab_issue import get_issues_from_epics, get_issues_from_iterations, \
    get_issues_from_milestones, get_issues_from_projects, get_issue_info

if typing.TYPE_CHECKING:
    import argparse


def get_updated_plans(plans: list[dict], args: argparse.Namespace) -> list[dict]:
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

    logging.info("Found %d unique GitLab issues", len(issues))

    # Find GitLab URLs that are not in the Thunderdome game yet

    # swap key and value so we can search by web_url
    swapped_issues = dict((val, key) for key, val in issues.items())
    for plan in plans:
        if plan["link"] in swapped_issues:
            swapped_issues.pop(plan["link"])

    # Swap back to get issues by ID again
    issues = dict((val, key) for key, val in swapped_issues.items())

    new_plans = create_plans_from_issues(
        issues,
        args.token,
        args.label_priority,
        args.with_weighted,
        args.with_closed
    )

    logging.info("Found %d new plans", len(new_plans))

    if args.label_priority:
        # Sort plans by their priority
        new_plans.sort(key=lambda x: x["priority"])

    return new_plans
