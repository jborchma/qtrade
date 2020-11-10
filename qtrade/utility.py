"""Collection of utility functions."""
import logging
import sys
from typing import Optional

import yaml

if sys.version_info < (3, 8, 0):
    from typing_extensions import TypedDict
else:
    from typing import (  # type: ignore  ## needed to do this for mypy error in python < 3.8
        TypedDict,
    )


log = logging.getLogger(__name__)  # pylint: disable=C0103

TokenDict = TypedDict(
    "TokenDict",
    {
        "access_token": str,
        "api_server": str,
        "expires_in": int,
        "refresh_token": str,
        "token_type": str,
    },
)


def get_access_token_yaml(token_yaml: str) -> TokenDict:
    """Read in access token yaml.

    Parameters
    ----------
    token_yaml: str
        Path of the token yaml file

    Returns
    -------
    dict
        Dicitonary with the access token parameters
    """
    try:
        with open(token_yaml) as yaml_file:
            log.debug("Loading access token from yaml...")
            token_yaml_payload: TokenDict = yaml.load(yaml_file, Loader=yaml.FullLoader)
    except Exception:
        log.error("Error loading access token from yaml...")
        raise

    validate_access_token(**token_yaml_payload)
    return token_yaml_payload


def validate_access_token(
    access_token: Optional[str] = None,
    api_server: Optional[str] = None,
    expires_in: Optional[int] = None,
    refresh_token: Optional[str] = None,
    token_type: Optional[str] = None,
):
    """Validate access token.

    This function validates the access token and ensures that all requiered
    attributes are provided.

    Parameters
    ----------
    access_token: str, optional
        Access token
    api_server: str, optional
        Api server URL
    expires_in: int, optional
        Time until token expires
    refresh_token: str, optional
        Refresh token
    token_type: str, optional
        Token type

    Raises
    ------
    Exception
        If any of the inputs is None.
    """
    log.debug("Validating access token...")
    if access_token is None:
        raise Exception("Access token was not provided.")
    if api_server is None:
        raise Exception("API server URL was not provided.")
    if expires_in is None:
        raise Exception("Expiry time was not provided.")
    if refresh_token is None:
        raise Exception("Refresh token was not provided.")
    if token_type is None:
        raise Exception("Token type was not provided.")
