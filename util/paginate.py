
"""
Make paginated requests.
"""

import logging
import typing

import requests


def paginate_request(
    url: str, params: dict, headers: dict
) -> typing.Generator[requests.Response, None, None]:
    """
    Paginate through a GitLab API request.

    :param url: URL to the GitLab API.
    :param params: Parameters for the request.
    :param headers: Headers for the request.
    :return: Response from the request.
    """
    response = requests.get(url, timeout=10, params=params, headers=headers)
    if not response.ok:
        logging.error("Failed to fetch %s", url)
        return None

    yield response

    while "next" in response.links:
        response = requests.get(
            response.links["next"]["url"], timeout=10, headers=headers
        )
        if not response.ok:
            logging.error("Failed to fetch %s", url)
            return None

        yield response
