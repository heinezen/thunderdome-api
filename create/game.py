"""
Create a Thunderdome game from GitLab issues.
"""
from __future__ import annotations

import logging
import typing

import requests

if typing.TYPE_CHECKING:
    import argparse


def create_game(plans: list[dict], args: argparse.Namespace) -> None:
    """
    Create a Thunderdome game.

    :plans: Plans for the battle.
    :args: Command line arguments.
    """
    thunderdome_headers = {
        "accept": "application/json",
        "X-API-Key": args.api_key,
    }

    thunderdome_response = requests.get(
        "https://thunderdome.dev/api/auth/user", timeout=10, headers=thunderdome_headers
    )
    payload = thunderdome_response.json()
    user_id = payload["data"]["id"]

    # Create battle

    # query parameters
    battle_settings_query = {
        "userId": user_id,
    }

    request_url = f"https://thunderdome.dev/api/users/{user_id}/battles"
    if args.teamid is not None:
        battle_settings_query["teamId"] = args.teamid
        request_url = (
            f"https://thunderdome.dev/api/teams/{args.teamid}/users/{user_id}/battles"
        )

    # mandatory body parameters
    battle_settings_body = {
        "name": args.name,
        "plans": plans,
        "pointAverageRounding": args.round_type,
        "pointValuesAllowed": args.allowed_values,
    }

    # optional body parameters
    if args.auto_finish is not None:
        battle_settings_body["autoFinishVoting"] = args.auto_finish

    if args.leaders is not None:
        battle_settings_body["leaders"] = args.leaders

    if args.scale_id is not None:
        battle_settings_body["estimationScaleId"] = args.scale_id

    if args.hide_identity is not None:
        battle_settings_body["hideVoterIdentity"] = args.hide_identity

    if args.join_password is not None:
        battle_settings_body["joinCode"] = args.join_password

    if args.leader_password is not None:
        battle_settings_body["leaderCode"] = args.leader_password

    thunderdome_response = requests.post(
        request_url,
        timeout=10,
        headers=thunderdome_headers,
        params=battle_settings_query,
        json=battle_settings_body,
    )

    if not thunderdome_response.ok:
        logging.error("Failed to create battle")
        logging.error(thunderdome_response.json())
