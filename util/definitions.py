"""
Definitions of shared constants.
"""

import re


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

# Maximum number of issues to fetch per request
GITLAB_PAGINATION_LIMIT = 100
