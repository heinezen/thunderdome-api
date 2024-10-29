"""
Update an existing Thunderdome game.
"""
from __future__ import annotations

import logging
import typing

import requests

if typing.TYPE_CHECKING:
    import argparse


def update_game(battle_id: str, plans: list[dict], args: argparse.Namespace) -> None:
    """
    Update a Thunderdome game.

    :param battle_id: ID of the battle that is updated.
    :param plans: Plans for the battle.
    :param args: Command line arguments.
    """
    thunderdome_headers = {
        "accept": "application/json",
        "X-API-Key": args.api_key,
    }

    # Update battle

    request_url = f"https://thunderdome.dev/api/battles/{battle_id}/plans"

    for plan in plans:
        # TODO: Dirty fix because the name key for creating a plan in a new game
        #       is different from the name key for updating a game
        plan["planName"] = plan["name"]
        thunderdome_response = requests.post(
            request_url,
            timeout=10,
            headers=thunderdome_headers,
            json=plan,
        )

        if not thunderdome_response.ok:
            logging.error("Failed to update battle")
            logging.error(thunderdome_response.json())
