"""Core module for Questrade API wrapper."""

import logging
from typing import Any, Dict, List, Optional, Union

import requests
import yaml

from .utility import TokenDict, get_access_token_yaml, validate_access_token

log = logging.getLogger(__name__)  # pylint: disable=C0103

TOKEN_URL = "https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token="


class Questrade:
    """Questrade baseclass.

    This class holds the methods to get access tokens, refresh access tokens as well as get
    stock quotes and portfolio overview. An instance of the class needs to be either initialized
    with an access_code or the path of a access token yaml file.

    Parameters
    ----------
    access_code: str, optional
        Access code from Questrade
    token_yaml: str, optional
        Path of the yaml-file holding the token payload
    save_yaml: bool, optional
        Boolean to indicate if the token payload will be saved in a yaml-file. Default True.
    """

    def __init__(
        self,
        access_code: Optional[str] = None,
        token_yaml: Optional[str] = None,
        save_yaml: bool = True,
    ):

        self.access_token: TokenDict
        self.headers = None
        self.session = requests.Session()

        self.access_code = access_code
        self.token_yaml = token_yaml

        if access_code is None and self.token_yaml is not None:
            self.access_token = get_access_token_yaml(self.token_yaml)
            self.headers = {
                "Authorization": self.access_token["token_type"]
                + " "
                + self.access_token["access_token"]
            }
            # add headers to session
            self.session.headers.update(self.headers)
        else:
            self._get_access_token(save_yaml=save_yaml)

        self.account_id = None
        self.positions = None

    def _send_message(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict[str, Any]:  # pylint: disable=R0913
        """Send an API request.

        Parameters
        ----------
        method: str
            HTTP method (get, post, delete, etc.)
        endpoint: str
            Endpoint (to be added to base URL)
        params: dict, optional
            HTTP request parameters
        data: dict, optional
            JSON-encoded string payload for POST
        json: dict, optional
            Dictionary payload for POST

        Returns
        -------
        dict/list:
            JSON response
        """
        if self.access_token is not None:
            url = self.access_token["api_server"] + "/v1/" + endpoint
        else:
            log.error("Access token not set...")
            raise Exception("Access token not set...")
        resp = self.session.request(method, url, params=params, data=data, json=json, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def save_token_to_yaml(self, yaml_path: str = "access_token.yml"):
        """Save the token payload as a yaml-file.

        Parameters
        ----------
        yaml_path: str, optional
            Path of the yaml-file. If the file already exists, it will be overwritten. Defaults to
            access_token.yml
        """
        with open(yaml_path, "w") as yaml_file:
            log.debug("Saving access token to yaml file...")
            yaml.dump(self.access_token, yaml_file)

    def _get_access_token(
        self, save_yaml: bool = False, yaml_path: str = "access_token.yml"
    ) -> TokenDict:
        """Get access token.

        This internal method gets the access token from the access code and optionally saves it in
        access_token.yaml.

        Parameters
        ----------
        save_yaml: bool, optional
            Boolean to indicate if the token payload will be saved in a yaml-file. Default False.
        yaml_path: str, optional
            Path of the yaml-file that will be saved. If the file already exists, it will be
            overwritten. Defaults to access_token.yml

        Returns
        -------
        dict
            Dict with the access token data.
        """
        url = TOKEN_URL + str(self.access_code)
        log.info("Getting access token...")
        data = requests.get(url)
        data.raise_for_status()
        response = data.json()

        # validate response
        validate_access_token(**response)

        self.access_token = response

        # clean the api_server entry of the escape characters
        self.access_token["api_server"] = self.access_token["api_server"].replace("\\", "")
        if self.access_token["api_server"][-1] == "/":
            self.access_token["api_server"] = self.access_token["api_server"][:-1]

        # set headers
        self.headers = {
            "Authorization": self.access_token["token_type"]
            + " "
            + self.access_token["access_token"]
        }

        self.session.headers.update(self.headers)

        # save access token
        if save_yaml:
            log.info("Saving yaml file to {}...".format(yaml_path))  # pylint: disable=W1202
            self.save_token_to_yaml(yaml_path=yaml_path)

        return self.access_token

    def refresh_access_token(
        self, from_yaml: bool = False, yaml_path: str = "access_token.yml"
    ) -> TokenDict:
        """Refresh access token.

        This method refreshes the access token. This only works if the overall access has not yet
        expired. By default it will look for the yaml-file, but it could also look for the internal
        state

        Parameters
        ----------
        from_yaml: bool, optional [False]
            This parameter controls if the refresh token is sourced from a yaml file
            or if the attribute `access_token` is used (default). If True, the yaml-file will be
            updated.
        yaml_path: str, optional
            Path of the yaml-file that will be updated. Defaults to access_token.yml

        Returns
        -------
        dict
            Dict with the access token data.
        """
        if from_yaml:
            old_access_token = get_access_token_yaml("access_token.yml")
        else:
            old_access_token = self.access_token

        url = TOKEN_URL + str(old_access_token["refresh_token"])
        log.info("Refreshing access token...")
        data = requests.get(url)
        data.raise_for_status()
        response = data.json()

        # validate response
        validate_access_token(**response)
        # set access token
        self.access_token = response

        # clean the api_server entry of the escape characters
        self.access_token["api_server"] = self.access_token["api_server"].replace("\\", "")
        if self.access_token["api_server"][-1] == "/":
            self.access_token["api_server"] = self.access_token["api_server"][:-1]

        # set headers
        self.headers = {
            "Authorization": self.access_token["token_type"]
            + " "
            + self.access_token["access_token"]
        }

        # update headers
        self.session.headers.update(self.headers)

        # save access token
        if from_yaml:
            self.save_token_to_yaml(yaml_path=yaml_path)

        return self.access_token

    def get_account_id(self) -> List[int]:
        """Get account ID.

        This method gets the accounts ID connected to the token.

        Returns
        -------
        list:
            List of account IDs.
        """
        log.info("Getting account ID...")
        response: Dict[str, List[Dict[str, int]]] = self._send_message("get", "accounts")

        account_id = []
        try:
            for account in response["accounts"]:
                account_id.append(account["number"])
        except Exception:
            log.error(response)
            raise Exception

        self.account_id = account_id  # type: ignore

        return account_id

    def get_account_positions(self, account_id: int) -> List[Dict]:
        """Get account positions.

        This method will get the positions for the account ID connected to the token.

        The returned data is a list where for each position, a dictionary with the following
        data will be returned:

        ``{'averageEntryPrice': 1000,
        'closedPnl': 0,
        'closedQuantity': 0,
        'currentMarketValue': 3120,
        'currentPrice': 1040,
        'isRealTime': False,
        'isUnderReorg': False,
        'openPnl': 120,
        'openQuantity': 3,
        'symbol': 'XYZ',
        'symbolId': 1234567,
        'totalCost': 3000}``


        Parameters
        ----------
        account_id: int
            Account ID for which the positions will be returned.

        Returns
        -------
        list:
            List of dictionaries, where each list entry is a dictionary with basic position
            information.

        """
        log.info("Getting account positions...")
        response = self._send_message("get", "accounts/" + str(account_id) + "/positions")
        try:
            positions = response["positions"]
        except Exception:
            print(response)
            raise Exception

        self.positions = positions

        return positions

    def get_account_activities(self, account_id: int, start_date: str, end_date: str) -> List[Dict]:
        """Get account activities.

        This method will get the account activities for a given account ID in a given time
        interval.

        This method will in general return a list of dictionaries, where each dictionary represents
        one trade/account activity. Each dictionary is of the form

        ``{'action': 'Buy',
        'commission': -5.01,
        'currency': 'CAD',
        'description': 'description text',
        'grossAmount': -1000,
        'netAmount': -1005.01,
        'price': 10,
        'quantity': 100,
        'settlementDate': '2018-08-09T00:00:00.000000-04:00',
        'symbol': 'XYZ.TO',
        'symbolId': 1234567,
        'tradeDate': '2018-08-07T00:00:00.000000-04:00',
        'transactionDate': '2018-08-09T00:00:00.000000-04:00',
        'type': 'Trades'}``

        Parameters
        ----------
        account_id: int
            Accound ID for which the activities will be returned.
        startDate: str
            Start date of time period, format YYYY-MM-DD
        endDate: str
            End date of time period, format YYYY-MM-DD

        Returns
        -------
        list:
            List of dictionaries, where each list entry is a dictionary with basic order & dividend
            information.

        """
        payload = {
            "startTime": str(start_date) + "T00:00:00-05:00",
            "endTime": str(end_date) + "T00:00:00-05:00",
        }

        log.info("Getting account activities...")
        response = self._send_message(
            "get", "accounts/" + str(account_id) + "/activities", params=payload
        )

        try:
            activities = response["activities"]
        except Exception:
            print(response)
            raise Exception

        return activities

    def ticker_information(self, tickers: Union[str, List[str]]) -> Union[Dict, List[Dict]]:
        """Get ticker information.

        This function gets information such as a quote for a single ticker or a list of tickers.

        Parameters
        ----------
        tickers: str or [str]
            List of tickers or a single ticker

        Returns
        -------
        dict or [dict]
            Dictionary with ticker information or list of dictionaries with ticker information
        """
        if isinstance(tickers, str):
            tickers = [tickers]

        payload = {"names": ",".join(tickers)}

        log.info("Getting ticker data...")
        response = self._send_message("get", "symbols", params=payload)
        try:
            symbols = response["symbols"]
        except Exception:
            print(response)
            raise Exception

        if len(tickers) == 1:
            symbols = symbols[0]

        return symbols

    def get_quote(self, tickers: List[str]) -> Union[Dict, List[Dict]]:
        """Get quote.

        This function gets information such as a quote for a single ticker or a list of tickers.

        Parameters
        ----------
        tickers: [str]
            List of tickers

        Returns
        -------
        dict or [dict]
            Dictionary with quotes or list of dictionaries with quotes
        """
        if isinstance(tickers, str):
            tickers = [tickers]

        # translate tickers to IDs
        info = self.ticker_information(tickers)
        if len(tickers) == 1 and isinstance(info, dict):
            ids = [info["symbolId"]]
        else:
            ids = [stock["symbolId"] for stock in info]

        payload = {"ids": ",".join(map(str, ids))}

        log.info("Getting quote...")
        response = self._send_message("get", "markets/quotes", params=payload)
        try:
            quotes = response["quotes"]
        except Exception:
            print(response)
            raise Exception

        if len(ids) == 1:
            quotes = quotes[0]

        return quotes

    def get_historical_data(
        self, ticker: str, start_date: str, end_date: str, interval: str
    ) -> List:
        """Get historical ticker data.

        This method get gets historical data for a time interval and a defined time frequency.

        Parameters
        ----------
        ticker: str
            Ticker Symbol
        start_date: str
            Date in the format YYYY-MM-DD
        end_date: str
            Date in the format YYYY-MM-DD
        interval: str
            Time frequency, i.e. OneDay.

        Returns
        -------
        list:
            list of historical data for each interval. The list is ordered by date.
        """
        # translate tickers to IDs
        info = self.ticker_information(ticker)
        if isinstance(info, dict):
            ids = info["symbolId"]
        else:
            log.error(f"Something went wrong retrieving the symbol ID for ticker {ticker}...")
            raise Exception(f"Something went wrong retrieving the symbol ID for ticker {ticker}...")
        payload = {
            "startTime": str(start_date) + "T00:00:00-05:00",
            "endTime": str(end_date) + "T00:00:00-05:00",
            "interval": str(interval),
        }

        log.info(
            "Getting historical data for {0} from {1} to {2}".format(ticker, start_date, end_date)
        )

        response = self._send_message("get", "markets/candles/" + str(ids), params=payload)
        try:
            quotes = response["candles"]
        except Exception:
            print(response)
            raise Exception

        return quotes

    def submit_order(self, acct_id: int, order_dict: Dict[str, Union[int, bool, str]]) -> Dict:
        """Submit order.

        This method submits an order to Questrade. Note that currently only partner apps can submit
        orders to the Questrade API. The order information is provided in a dictionary of the form

        ``{'accountNumber': 1234567,
        'symbolId': 3925293,
        'quantity': 1,
        'icebergQuantity': 1,
        'limitPrice': 57.58,
        'isAllOrNone': True,
        'isAnonymous': False,
        'orderType': 'Limit',
        'timeInForce': 'GoodTillCanceled',
        'action': 'Buy',
        'primaryRoute': 'AUTO',
        'secondaryRoute': 'AUTO'}``

        Parameters
        ----------
        acct_id: int
            Account ID for the account to which the order is to be submitted.
        order_dict: dict
            Dictionary with the necessary order entries.

        Returns
        -------
        dict
            Dictionary with the API response to the order submission.
        """
        uri = self.access_token["api_server"] + "/v1/accounts/" + str(acct_id) + "/orders"
        log.info("Posting order...")
        data = self.session.post(uri, json=order_dict)
        data.raise_for_status()
        response = self._send_message(
            "post", "accounts/" + str(acct_id) + "/orders", json=order_dict
        )

        return response
