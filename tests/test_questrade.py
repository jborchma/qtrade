"""Questrade test module
"""
from unittest import mock
from requests import Session
import pytest
from qtrade import Questrade

TOKEN_URL = (
    "https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token="
)

VALID_ACCESS_TOKEN = {
    "access_token": "hunter2",
    "api_server": "https://questrade.api",
    "expires_in": 1234,
    "refresh_token": "hunter2",
    "token_type": "Bearer",
}

INVALID_ACCESS_TOKEN = {
    "access_token": "hunter3",
    "api_server": "https://questrade.api",
    "expires_in": 1234,
    "refresh_token": "hunter3",
}
ACCOUNT_RESPONSE = {"accounts": [{"number": 123}, {"number": 456}]}
POSITION_RESPONSE = {
    "positions": [
        {
            "averageEntryPrice": 1000,
            "closedPnl": 0,
            "closedQuantity": 0,
            "currentMarketValue": 3120,
            "currentPrice": 1040,
            "isRealTime": False,
            "isUnderReorg": False,
            "openPnl": 120,
            "openQuantity": 3,
            "symbol": "XYZ",
            "symbolId": 1234567,
            "totalCost": 3000,
        },
        {
            "averageEntryPrice": 500,
            "closedPnl": 0,
            "closedQuantity": 0,
            "currentMarketValue": 4000,
            "currentPrice": 1000,
            "isRealTime": False,
            "isUnderReorg": False,
            "openPnl": 2000,
            "openQuantity": 4,
            "symbol": "ABC",
            "symbolId": 7654321,
            "totalCost": 2000,
        },
    ]
}
ACTIVITY_RESPONSE = {
    "activities": [
        {
            "action": "Buy",
            "commission": -5.01,
            "currency": "CAD",
            "description": "description text",
            "grossAmount": -1000,
            "netAmount": -1005.01,
            "price": 10,
            "quantity": 100,
            "settlementDate": "2018-08-09T00:00:00.000000-04:00",
            "symbol": "XYZ.TO",
            "symbolId": 1234567,
            "tradeDate": "2018-08-07T00:00:00.000000-04:00",
            "transactionDate": "2018-08-09T00:00:00.000000-04:00",
            "type": "Trades",
        }
    ]
}
TICKER_INFO = {
    "averageVol20Days": 2,
    "averageVol3Months": 4,
    "currency": "CAD",
    "description": "XYZ Company Inc.",
    "dividend": 0,
    "dividendDate": None,
    "eps": 2,
    "exDate": None,
    "hasOptions": True,
    "highPrice52": 25.00,
    "industryGroup": "XYZ Industry",
    "industrySector": "XYZ",
    "industrySubgroup": "XYZ Special",
    "isQuotable": True,
    "isTradable": True,
    "listingExchange": "TSX",
    "lowPrice52": 9.83,
    "marketCap": 275784564,
    "minTicks": [{"minTick": 0.005, "pivot": 0}, {"minTick": 0.01, "pivot": 0.5}],
    "optionContractDeliverables": {"cashInLieu": 0, "underlyings": []},
    "optionDurationType": None,
    "optionExerciseType": None,
    "optionExpiryDate": None,
    "optionRoot": "",
    "optionStrikePrice": None,
    "optionType": None,
    "outstandingShares": 1234664,
    "pe": None,
    "prevDayClosePrice": 20.01,
    "securityType": "Stock",
    "symbol": "XYZ",
    "symbolId": 1234567,
    "tradeUnit": 1,
    "yield": 0,
}
TICKER_RESPONSE_SINGLE = {"symbols": [TICKER_INFO]}
TICKER_RESPONSE_MULTIPLE = {"symbols": [TICKER_INFO, TICKER_INFO]}
QUOTE = {
    "VWAP": 0,
    "askPrice": None,
    "askSize": 0,
    "bidPrice": None,
    "bidSize": 0,
    "delay": 0,
    "high52w": 25.00,
    "highPrice": 0,
    "isHalted": False,
    "lastTradePrice": 20.01,
    "lastTradePriceTrHrs": None,
    "lastTradeSize": 0,
    "lastTradeTick": "Equal",
    "lastTradeTime": "2018-09-14T00:00:00.000000-04:00",
    "low52w": 9.83,
    "lowPrice": 0,
    "openPrice": 0,
    "symbol": "XYZ",
    "symbolId": 1234567,
    "tier": "",
    "volume": 0,
}
QUOTE_RESPONSE_SINGLE = {"quotes": [QUOTE]}
QUOTE_RESPONSE_MULTIPLE = {"quotes": [QUOTE, QUOTE]}
HIST_RESPONSE = {
    "candles": [
        {
            "VWAP": 34.246962,
            "close": 33.56,
            "end": "2018-08-02T00:00:00.000000-04:00",
            "high": 34.97,
            "low": 33.51,
            "open": 34.7,
            "start": "2018-08-01T01:00:00.000000-04:00",
            "volume": 3251329,
        },
        {
            "VWAP": 33.724063,
            "close": 34.4,
            "end": "2018-08-03T00:00:00.000000-04:00",
            "high": 34.57,
            "low": 32.85,
            "open": 33.59,
            "start": "2018-08-02T00:00:00.000000-04:00",
            "volume": 3642444,
        },
    ]
}

ACCESS_TOKEN_YAML = """access_token: hunter2
api_server: http://www.api_url.com
expires_in: 1234
refresh_token: hunter2
token_type: Bearer
"""

INCOMPLETE_ACCESS_TOKEN_YAML = """access_token: hunter2
api_server: http://www.api_url.com
expires_in: 1234
"""

# taken from https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
# Since a lot of the methods in the Questrade class use `requests.get` and get the json data,
# it makes sense to wrap this in a class
class MockResponse:
    """Class that includes json data and status code for request get results
    """

    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        """Method to return mocked json data
        """
        return self.json_data

    def raise_for_status(self):
        """Method to raise Exceptions for certain returned statuses
        """
        http_error_msg = ""
        if 400 <= self.status_code < 500:
            http_error_msg = "%s Client Error" % (self.status_code)

        elif 500 <= self.status_code < 600:
            http_error_msg = "%s Server Error" % (self.status_code)

        if http_error_msg:
            raise Exception(http_error_msg)


### Specific request responses ###


def mocked_access_token_requests_get(*args, **kwargs):
    """mocking access token requests get method
    """
    if args[0] == TOKEN_URL + "hunter2":
        return MockResponse(VALID_ACCESS_TOKEN, 200)
    elif args[0] == TOKEN_URL + "hunter3":
        return MockResponse(INVALID_ACCESS_TOKEN, 200)
    else:
        return MockResponse(None, 404)


def mocked_acct_id_get(*args, **kwargs):
    """mocking acct_id requests get
    """
    if args[1] == "http://www.api_url.com/v1/accounts":
        return MockResponse(ACCOUNT_RESPONSE, 200)
    else:
        return MockResponse(None, 404)


def mocked_positions_get(*args, **kwargs):
    """mocking acct_id requests get
    """
    if args[1] == "http://www.api_url.com/v1/accounts/123/positions":
        return MockResponse(POSITION_RESPONSE, 200)
    else:
        return MockResponse(None, 404)


def mocked_activities_get(*args, **kwargs):
    """mocking activities requests get
    """
    if args[1] == "http://www.api_url.com/v1/accounts/123/activities" and kwargs[
        "params"
    ] == {
        "endTime": "2018-08-10T00:00:00-05:00",
        "startTime": "2018-08-07T00:00:00-05:00",
    }:
        return MockResponse(ACTIVITY_RESPONSE, 200)
    else:
        return MockResponse(None, 404)


def mocked_ticker_get(*args, **kwargs):
    """mocking ticker info requests get
    """
    if args[1] == "http://www.api_url.com/v1/symbols" and kwargs["params"] == {
        "names": "XYZ"
    }:
        return MockResponse(TICKER_RESPONSE_SINGLE, 200)
    elif args[1] == "http://www.api_url.com/v1/symbols" and kwargs["params"] == {
        "names": "XYZ,ABC"
    }:
        return MockResponse(TICKER_RESPONSE_MULTIPLE, 200)
    else:
        return MockResponse(None, 404)


def mocked_quote_get(*args, **kwargs):
    """mocking quote requests get
    """
    if args[1] == "http://www.api_url.com/v1/symbols" and kwargs["params"] == {
        "names": "XYZ"
    }:
        return MockResponse(TICKER_RESPONSE_SINGLE, 200)
    elif args[1] == "http://www.api_url.com/v1/symbols" and kwargs["params"] == {
        "names": "XYZ,ABC"
    }:
        return MockResponse(TICKER_RESPONSE_MULTIPLE, 200)
    if args[1] == "http://www.api_url.com/v1/markets/quotes" and kwargs["params"] == {
        "ids": "1234567"
    }:
        return MockResponse(QUOTE_RESPONSE_SINGLE, 200)
    elif args[1] == "http://www.api_url.com/v1/markets/quotes" and kwargs["params"] == {
        "ids": "1234567,1234567"
    }:
        return MockResponse(QUOTE_RESPONSE_MULTIPLE, 200)
    else:
        return MockResponse(None, 404)


def mocked_historical_get(*args, **kwargs):
    """mocking historical data requests get
    """
    if args[1] == "http://www.api_url.com/v1/symbols" and kwargs["params"] == {
        "names": "XYZ"
    }:
        return MockResponse(TICKER_RESPONSE_SINGLE, 200)
    if args[1] == "http://www.api_url.com/v1/markets/candles/1234567" and kwargs[
        "params"
    ] == {
        "startTime": "2018-08-01T00:00:00-05:00",
        "interval": "OneDay",
        "endTime": "2018-08-02T00:00:00-05:00",
    }:
        return MockResponse(HIST_RESPONSE, 200)
    else:
        return MockResponse(None, 404)


### TEST FUNCTIONS ###


@mock.patch(
    "qtrade.questrade.requests.get", side_effect=mocked_access_token_requests_get
)
def test_get_access_token(mock_get):
    """This function tests the get access token method.
    """
    qtrade = Questrade(access_code="hunter2")
    assert set(qtrade.access_token.keys()) == set(
        ["access_token", "api_server", "expires_in", "refresh_token", "token_type"]
    )
    with pytest.raises(Exception) as e_info:
        _ = Questrade(access_code="hunter3")
        assert str(e_info.value) == "Token type was not provided."


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
def test_init_via_yaml():
    """This function tests when the class is initiated via yaml file.
    """
    qtrade = Questrade(token_yaml="access_token.yml")
    assert set(qtrade.access_token.keys()) == set(
        ["access_token", "api_server", "expires_in", "refresh_token", "token_type"]
    )
    assert qtrade.access_token["access_token"] == "hunter2"
    assert qtrade.access_token["api_server"] == "http://www.api_url.com"
    assert qtrade.access_token["expires_in"] == 1234
    assert qtrade.access_token["refresh_token"] == "hunter2"
    assert qtrade.access_token["token_type"] == "Bearer"


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
def test_init_via_incomplete_yaml():
    """This function tests when the class is initiated via incomplete yaml file.
    """
    with pytest.raises(Exception) as e_info:
        _ = Questrade(token_yaml="access_token.yml")
        assert str(e_info.value) == "Refresh token was not provided."


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch(
    "qtrade.questrade.requests.get", side_effect=mocked_access_token_requests_get
)
def test_refresh_token_yaml(mock_get):
    """This function tests the refresh token method by using the yaml.
    """
    qtrade = Questrade(token_yaml="access_token.yml")
    qtrade.refresh_access_token(from_yaml=True)
    assert set(qtrade.access_token.keys()) == set(
        ["access_token", "api_server", "expires_in", "refresh_token", "token_type"]
    )
    assert qtrade.access_token["api_server"] == "https://questrade.api"


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch(
    "qtrade.questrade.requests.get", side_effect=mocked_access_token_requests_get
)
def test_refresh_token_non_yaml(mock_get):
    """This function tests the refresh token method without yaml use.
    """
    qtrade = Questrade(token_yaml="access_token.yml")
    qtrade.refresh_access_token()
    assert set(qtrade.access_token.keys()) == set(
        ["access_token", "api_server", "expires_in", "refresh_token", "token_type"]
    )
    assert qtrade.access_token["api_server"] == "https://questrade.api"


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch.object(Session, "request", side_effect=mocked_acct_id_get)
def test_get_account_id(mock_get):
    """This function tests the account ID function.
    """
    qtrade = Questrade(token_yaml="access_token.yml")
    acct_id = qtrade.get_account_id()
    assert acct_id == [123, 456]


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch.object(Session, "request", side_effect=mocked_positions_get)
def test_get_positions(mock_get):
    """This function tests the get account positions method.
    """
    qtrade = Questrade(token_yaml="access_token.yml")
    positions = qtrade.get_account_positions(123)
    assert positions[0]["symbol"] == "XYZ"
    assert positions[1]["symbol"] == "ABC"
    assert positions[0]["currentMarketValue"] == 3120
    assert positions[1]["currentMarketValue"] == 4000
    assert len(positions) == 2
    assert len(positions[0]) == 12
    assert len(positions[1]) == 12

    with pytest.raises(Exception):
        _ = qtrade.get_account_positions(987)


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch.object(Session, "request", side_effect=mocked_activities_get)
def test_get_activity(mock_get):
    """This function tests the get account activities method.
    """
    qtrade = Questrade(token_yaml="access_token.yml")
    activities = qtrade.get_account_activities(123, "2018-08-07", "2018-08-10")
    assert activities[0]["action"] == "Buy"
    assert activities[0]["tradeDate"] == "2018-08-07T00:00:00.000000-04:00"
    assert len(activities) == 1
    assert len(activities[0]) == 14

    with pytest.raises(Exception):
        _ = qtrade.get_account_activities(987, "2018-08-07", "2018-08-10")


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch.object(Session, "request", side_effect=mocked_ticker_get)
def test_get_ticker_information(mock_get):
    """This function tests the get ticker information method.
    """
    qtrade = Questrade(token_yaml="access_token.yml")
    ticker_info_single = qtrade.ticker_information("XYZ")
    assert len(ticker_info_single) == 34
    assert ticker_info_single["symbol"] == "XYZ"
    assert ticker_info_single["marketCap"] == 275784564

    ticker_info_multiple = qtrade.ticker_information(["XYZ", "ABC"])
    assert len(ticker_info_multiple) == 2
    assert len(ticker_info_multiple[0]) == 34
    assert len(ticker_info_multiple[1]) == 34
    assert ticker_info_multiple[0]["symbol"] == "XYZ"


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch.object(Session, "request", side_effect=mocked_quote_get)
def test_get_quote(mock_get):
    """This function tests the get quote method.
    """
    qtrade = Questrade(token_yaml="access_token.yml")
    quote_single = qtrade.get_quote("XYZ")
    assert len(quote_single) == 21
    assert quote_single["high52w"] == 25.00
    assert quote_single["symbolId"] == 1234567

    quote_multiple = qtrade.get_quote(["XYZ", "ABC"])
    assert len(quote_multiple) == 2
    assert len(quote_multiple[0]) == 21
    assert len(quote_multiple[1]) == 21
    assert quote_multiple[0]["high52w"] == 25.00
    assert quote_multiple[1]["high52w"] == 25.00


@mock.patch("builtins.open", mock.mock_open(read_data=ACCESS_TOKEN_YAML))
@mock.patch.object(Session, "request", side_effect=mocked_historical_get)
def test_get_historical_data(mock_get):
    """This function tests the get historical data method.
    """
    qtrade = Questrade(token_yaml="access_token.yml")
    historical_data = qtrade.get_historical_data(
        "XYZ", "2018-08-01", "2018-08-02", "OneDay"
    )
    assert len(historical_data) == 2
    assert len(historical_data[0]) == 8
    assert len(historical_data[1]) == 8
    assert historical_data[0]["start"] == "2018-08-01T01:00:00.000000-04:00"
    assert historical_data[1]["start"] == "2018-08-02T00:00:00.000000-04:00"
