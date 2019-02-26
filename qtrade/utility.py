"""Collection of utility functions
"""
import logging
import yaml

log = logging.getLogger(__name__) #pylint: disable=C0103


def get_access_token_yaml(token_yaml):
    """Utility function to read in access token yaml

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
            token_yaml = yaml.load(yaml_file)
    except Exception:
        log.error("Error loading access token from yaml...")
        raise

    validate_access_token(**token_yaml)
    return token_yaml

def validate_access_token(access_token=None, api_server=None, expires_in=None,
                          refresh_token=None, token_type=None):
    """Validate access token

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
        raise Exception('Access token was not provided.')
    if api_server is None:
        raise Exception('API server URL was not provided.')
    if expires_in is None:
        raise Exception('Expiry time was not provided.')
    if refresh_token is None:
        raise Exception('Refresh token was not provided.')
    if token_type is None:
        raise Exception('Token type was not provided.')
