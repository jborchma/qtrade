"""Core module for Questrade API wrapper
"""

import logging
import requests
import yaml

from .utility import get_access_token_yaml, validate_access_token

log = logging.getLogger(__name__) #pylint: disable=C0103

TOKEN_URL = 'https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token='

class Questrade():
    """Questrade baseclass

    This class holds the methods to get access tokens, refresh access tokens as well as get
    stock quotes and portfolio overview. An instance of the class needs to be either initialized
    with an access_code or the path of a access token yaml file.
    """

    def __init__(self, access_code=None, token_yaml=None):

        self.access_token = None
        self.headers = None

        self.access_code = access_code
        self.token_yaml = token_yaml

        if access_code is None:
            self.access_token = get_access_token_yaml(self.token_yaml)
            self.headers = {'Authorization': self.access_token['token_type'] \
                + ' ' + self.access_token['access_token']}
        else:
            self.get_access_token()

        self.account_id = None
        self.positions = None

    def get_access_token(self):
        """
        This method gets the access token from the access code and saves it in access_token.yaml.

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

        #clean the api_server entry of the escape characters
        self.access_token['api_server'] = self.access_token['api_server'].replace("\\", "")
        if self.access_token['api_server'][-1] == '/':
            self.access_token['api_server'] = self.access_token['api_server'][:-1]

        # set headers
        self.headers = {'Authorization': self.access_token['token_type'] \
            + ' ' + self.access_token['access_token']}

        # save access token
        with open('access_token.yml', 'w') as yaml_file:
            log.debug("Saving access token to yaml file...")
            yaml.dump(self.access_token, yaml_file)

        return self.access_token


    def refresh_access_token(self, from_yaml=True):
        """
        This method refreshes the access token saved in access_token.yml. This only works if the
        overall access has not yet expired.

        Parameters
        ----------
        from_yaml: bool, optional [True]
            This parameter controls if the refresh token is sourced from a yaml file (default)
            or if the attribute `access_token` is used.

        Returns
        -------
        dict
            Dict with the access token data.
        """
        if from_yaml:
            old_access_token = get_access_token_yaml('access_token.yml')
        else:
            old_access_token = self.access_token

        url = TOKEN_URL + str(old_access_token['refresh_token'])
        log.info("Refreshing access token...")
        data = requests.get(url)
        data.raise_for_status()
        response = data.json()

        # validate response
        validate_access_token(**response)
        # set access token
        self.access_token = response

        #clean the api_server entry of the escape characters
        self.access_token['api_server'] = self.access_token['api_server'].replace("\\", "")
        if self.access_token['api_server'][-1] == '/':
            self.access_token['api_server'] = self.access_token['api_server'][:-1]

        # set headers
        self.headers = {'Authorization': self.access_token['token_type'] \
            + ' ' + self.access_token['access_token']}

        # save access token
        with open('access_token.yml', 'w') as yaml_file:
            log.debug("Saving access token to yaml file...")
            yaml.dump(self.access_token, yaml_file)

        return self.access_token

    def get_account_id(self):
        """
        This method gets the accounts ID connected to the token.

        Returns
        -------
        list:
            List of account IDs.
        """
        uri = self.access_token['api_server'] + '/v1/' + 'accounts'

        log.info("Getting account ID...")
        data = requests.get(uri, headers=self.headers)
        data.raise_for_status()

        response = data.json()
        account_id = []
        try:
            for account in response['accounts']:
                account_id.append(account['number'])
        except Exception:
            print(response)
            raise Exception

        self.account_id = account_id

        return account_id

    def get_account_positions(self, account_id):
        """
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
        uri = self.access_token['api_server'] + '/v1/' + 'accounts/' + str(account_id) \
            + '/positions'
        log.info("Getting account positions...")
        data = requests.get(uri, headers=self.headers)
        data.raise_for_status()

        response = data.json()
        try:
            positions = response['positions']
        except Exception:
            print(response)
            raise Exception

        self.positions = positions

        return positions

    def get_account_activities(self, account_id, start_date, end_date):
        """
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
        uri = self.access_token['api_server'] + '/v1/' + 'accounts/' + str(account_id)\
            + '/activities'
        payload = {'startTime': str(start_date) + 'T00:00:00-05:00',
                   'endTime': str(end_date) + 'T00:00:00-05:00'}

        log.info("Getting account activities...")
        data = requests.get(uri, params=payload, headers=self.headers)
        data.raise_for_status()

        response = data.json()
        try:
            activities = response['activities']
        except Exception:
            print(response)
            raise Exception

        return activities

    def ticker_information(self, tickers):
        """
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

        uri = self.access_token['api_server'] + '/v1/symbols'
        payload = {'names': ",".join(tickers)}

        log.info("Getting ticker data...")
        data = requests.get(uri, params=payload, headers=self.headers)
        data.raise_for_status()

        response = data.json()
        try:
            symbols = response['symbols']
        except Exception:
            print(response)
            raise Exception

        if len(tickers) == 1:
            symbols = symbols[0]

        return symbols

    def get_quote(self, tickers):
        """
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
        if len(tickers) == 1:
            ids = [info['symbolId']]
        else:
            ids = [stock['symbolId'] for stock in info]

        uri = self.access_token['api_server'] + '/v1/markets/quotes'
        payload = {'ids': ",".join(map(str, ids))}

        log.info("Getting quote...")
        data = requests.get(uri, params=payload, headers=self.headers)
        data.raise_for_status()

        response = data.json()
        try:
            quotes = response['quotes']
        except Exception:
            print(response)
            raise Exception

        if len(ids) == 1:
            quotes = quotes[0]

        return quotes

    def get_historical_data(self, ticker, start_date, end_date, interval):
        """
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
        ids = info['symbolId']
        uri = self.access_token['api_server'] + '/v1/markets/candles/' + str(ids)
        payload = {'startTime': str(start_date) + 'T00:00:00-05:00',
                   'endTime': str(end_date)+ 'T00:00:00-05:00',
                   'interval': str(interval)}

        log.info("Getting historical data for {0} from {1} to {2}".format(
            ticker, start_date, end_date))
        data = requests.get(uri, params=payload, headers=self.headers)
        data.raise_for_status()

        response = data.json()
        try:
            quotes = response['candles']
        except Exception:
            print(response)
            raise Exception

        return quotes

    def submit_order(self, acct_id, order_dict):
        """
        This method submits an order to Questrade. The order information is provided in a
        dictionary of the form

        ``{"accountNumber" : 1234567,
           "symbolId": 3925293,
           "quantity": 1,
           "icebergQuantity": 1,
           "limitPrice": 57.58,
           "isAllOrNone": True,
           "isAnonymous": False,
           "orderType": "Limit",
           "timeInForce": "GoodTillCanceled",
           "action": "Buy",
           "primaryRoute": "AUTO",
           "secondaryRoute": "AUTO"
        }``

        Note that currently only partner apps can submit orders to the Questrade API.

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
        uri = self.access_token['api_server'] + '/v1/accounts/' + str(acct_id) + '/orders'
        log.info("Posting order...")
        data = requests.post(uri, json=order_dict, headers=self.headers)
        data.raise_for_status()
        response = data.json()

        return response
