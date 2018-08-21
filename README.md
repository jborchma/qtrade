# Qtrade

This is a very basic wrapper for the Questrade API, a Canadian low cost broker.

## Installation

This package can easily be installed via

```
pip git+https://github.com/jborchma/qtrade.git
```

## Usage

The central class can be initialized via

```
from qtrade import Questrade

qtrade = Questrade(access_code='<access_code>')
qtrade.get_access_token()
```
where `<access_code>` is the token that one gets from the Questrade API portal. It is called
`access_code` since this initial token is used to get the full token data that will include
```
{'access_token': <access_token>,
 'api_server': '<api_url>',
 'expires_in': 1234,
 'refresh_token': <refresh_token>,
 'token_type': 'Bearer'}
 ```

The first call initializes the class and the second call gets the full token.

Another way to initialize the class is to use a token yaml-file via:
```
qtrade = Questrade(token_yaml='<yaml_path>')
```
where the yaml-file would have the general form
```
access_token: <access_token>
api_server: <api_url>
expires_in: 1234
refresh_token: <refresh_token>
token_type: Bearer
```

If the token is expired, one can use
```
qtrade.refresh_token()
```
to refresh the access token using the saved refresh token.

Once the tokens are set correctly, I have currently added methods to get ticker quotes, the
current status of all positions in any Questrade account that is associated with the tokens,
any account activities such as trades and dividend payments as well as historical data for
tickers that are supported by Questrade.
