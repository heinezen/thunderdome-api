"""
Retrieve storyboard stories from the Thunderdome API.
"""

import logging
import requests


def get_stories(
    board_id: str,
    api_key: str,
    filter_goals: list[str] = None,
    filter_columns: list[str] = None,
) -> list[dict]:
    """
    Get stories from the Thunderdome API.

    :param board_id: Storyboard ID to fetch.
    :param api_key: API key for the Thunderdome API.
    :param filter_goals: Names of the storyboard goals that are considered. Stories
                         from other goals are ignored.
    :param filter_columns: Names of the storyboard columns that are considered. Stories
                           from other columns are ignored.
    :return: Stories from the storyboard.
    """
    logging.info("Fetching plans for storyboard %s...", board_id)

    thunderdome_headers = {
        "accept": "application/json",
        "X-API-Key": api_key,
    }

    # Thunderdome request
    thunderdome_response = requests.get(
        f"https://thunderdome.dev/api/storyboards/{board_id}",
        timeout=10,
        headers=thunderdome_headers,
    )

    if not thunderdome_response.ok:
        logging.error("Failed to fetch storyboard %s", board_id)
        return []

    payload = thunderdome_response.json()

    stories = []
    for goal in payload["data"]["goals"]:
        if filter_goals is not None and \
                goal["name"] not in filter_goals:
            continue

        for column in goal["columns"]:
            if filter_columns is not None and \
                    column["name"] not in filter_columns:
                continue

            stories.extend(column["stories"])

    logging.debug("Fetched %d stories", len(stories))

    return stories
