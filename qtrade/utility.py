"""Collection of utility functions
"""

import yaml

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
            token_yaml = yaml.load(yaml_file)
    except Exception:
        raise Exception

    # should add validation of yaml contents in the future
    return token_yaml
