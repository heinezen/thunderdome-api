"""
Retrieve game plans from the Thunderdome API.
"""

import logging

import requests


def get_plans(battle_id: str, api_key: str) -> list[dict]:
    """
    Get plans from the Thunderdome API.

    :param battle_id: Battle ID to fetch.
    :param api_key: API key for the Thunderdome API.
    :return: Plans for the battle.
    """
    logging.info("Fetching plans for battle %s...", battle_id)

    thunderdome_headers = {
        "accept": "application/json",
        "X-API-Key": api_key,
    }

    # Thunderdome request
    thunderdome_response = requests.get(
        f"https://thunderdome.dev/api/battles/{battle_id}",
        timeout=10,
        headers=thunderdome_headers,
    )

    if not thunderdome_response.ok:
        logging.error("Failed to fetch battle %s", battle_id)
        return []

    payload = thunderdome_response.json()

    logging.debug("Fetched %d plans", len(payload["data"]["plans"]))

    return payload["data"]["plans"]
