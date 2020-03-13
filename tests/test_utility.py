"""Utility test module
"""
from unittest import mock
import pytest
from qtrade import utility

ACCESS_TOKEN_YAML = """access_token: hunter2
api_server: www.api_url.com
expires_in: 1234
refresh_token: hunter2
token_type: Bearer
"""

INCOMPLETE_ACCESS_TOKEN_YAML = """access_token: hunter2
api_server: www.api_url.com
expires_in: 1234
"""


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
def test_get_access_token_yaml():
    """This function tests the get access token yaml function
    """
    access_token = utility.get_access_token_yaml("filename.yml")
    assert set(access_token.keys()) == set(
        ["access_token", "api_server", "expires_in", "refresh_token", "token_type"]
    )
    assert access_token["access_token"] == "hunter2"
    assert access_token["api_server"] == "www.api_url.com"
    assert access_token["expires_in"] == 1234
    assert access_token["refresh_token"] == "hunter2"
    assert access_token["token_type"] == "Bearer"


def test_get_access_token_error():
    """This functions tests the error behaviour.
    """

    with pytest.raises(Exception) as e_info:
        access_token = utility.get_access_token_yaml("filename.yml")


@mock.patch("builtins.open", mock.mock_open(read_data=INCOMPLETE_ACCESS_TOKEN_YAML))
def test_get_access_token_yaml_error():
    """This function tests the get access token yaml function
    """
    with pytest.raises(Exception) as e_info:
        _ = utility.get_access_token_yaml("filename.yml")

        assert str(e_info.value) == "Refresh token was not provided."
