[![Build Status](https://travis-ci.com/jborchma/qtrade.svg?branch=master)](https://travis-ci.com/jborchma/qtrade)

# Qtrade

This is a very basic Python 3 wrapper for the [Questrade API](https://www.questrade.com/api/documentation/getting-started), a Canadian low cost broker.

## Usage


### Token management

The central class can be initialized via

```python
from qtrade import Questrade

qtrade = Questrade(access_code='<access_code>')
qtrade.get_access_token()
```
where `<access_code>` is the token that one gets from the Questrade API portal. It is called
`access_code` since this initial token is used to get the full token data that will include
```python
{'access_token': <access_token>,
 'api_server': '<api_url>',
 'expires_in': 1234,
 'refresh_token': <refresh_token>,
 'token_type': 'Bearer'}
 ```

The first call initializes the class and the second call gets the full token.

Another way to initialize the class is to use a token yaml-file via:
```python
qtrade = Questrade(token_yaml='<yaml_path>')
```
where the yaml-file would have the general form
```yaml
access_token: <access_token>
api_server: <api_url>
expires_in: 1234
refresh_token: <refresh_token>
token_type: Bearer
```

If the token is expired, one can use
```python
qtrade.refresh_token()
```
to refresh the access token using the saved refresh token.

Once the tokens are set correctly, I have currently added methods to get ticker quotes, the
current status of all positions in any Questrade account that is associated with the tokens,
any account activities such as trades and dividend payments as well as historical data for
tickers that are supported by Questrade.

### Basic functionality

There currently exists some basic functionality to get stock information via

```python
aapl, amzn = qtrade.ticker_information(['AAPL', 'AMZN'])
```

and current stock quotes can be obtained via

```python
aapl, amzn = qtrade.get_quote(['AAPL', 'AMZN'])
```

In addition, one can get historical stock quotes via

```python
aapl_history = = qtrade.get_historical_data('AAPL', '2018-08-01', '2018-08-21','OneHour')
```

Here, the last input parameter is the interval between quotes. Another option could be `'OneDay'`. For more options, see the [Questrade API description](http://www.questrade.com/api/documentation/rest-operations/enumerations/enumerations#historical-data-granularity).

### Account information

In addition, the Questrade API gives access to account information about the accounts connected to
the token. The accounts IDs can be accessed via

```python
account_ids = qtrade.get_account_id()
```

By using the correct account ID, one can get the positions of the accounts via

```python
positions = qtrade.get_account_positions(account_id=123456)
```

Finally, there exists a method to get all account activities (trades, dividends recieved, etc.) of
an account in a certain time frame via

```python
activities = qtrade.get_account_activities(123456, '2018-08-01', '2018-08-16')
```


## Contributors

There is a test suite that can be run via `python -m pytest`.
