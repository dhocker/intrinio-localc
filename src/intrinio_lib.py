#
# intrinio_lib - Reusable classes and functions for accessing Intrinio
# Copyright (C) 2017  Dave Hocker (email: AtHomeX10@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the LICENSE.md file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program (the LICENSE.md file).  If not, see <http://www.gnu.org/licenses/>.
#

import urllib.request
import urllib.parse
import urllib.error
import json
import os
import os.path
import ssl
import math
from intrinio_app_logger import AppLogger
from extn_helper import float_to_date_str, normalize_date


# Logger init
the_app_logger = AppLogger("intrinio-extension")
logger = the_app_logger.getAppLogger()


class QConfiguration:
    """
    Encapsulates Intrinio credentials
    """
    auth_user = ""
    auth_passwd = ""
    # Base URL for Intrinio services
    base_url = "https://api.intrinio.com"
    macOS = False
    file_path = ""
    full_file_path = ""
    cacerts = ""
    loglevel = ""

    @classmethod
    def load(cls):
        """
        Load credentials from configuration file. The location of the intrinio.conf
        file is OS dependent. The permissions of the intrinio.conf file should allow
        access ONLY by the user.
        :return: None
        """
        file_name = "intrinio.conf"
        if os.name == "posix":
            # Linux or OS X
            cls.file_path = "{0}/libreoffice/intrinio/".format(os.environ["HOME"])
            cls.macOS = (os.uname()[0] == "Darwin")
        elif os.name == "nt":
            # Windows
            cls.file_path = "{0}\\libreoffice\\intrinio\\".format(os.environ["APPDATALOCAL"])
        cls.full_file_path = cls.file_path + file_name

        # Read intrinio.conf file
        try:
            cf = open(cls.full_file_path, "r")
            cfj = json.loads(cf.read())
            cls.auth_user = cfj["user"]
            cls.auth_passwd = cfj["password"]
            if "certifi" in cfj:
                cls.cacerts = cfj["certifi"]
            if "loglevel" in cfj:
                cls.loglevel = cfj["loglevel"]
                the_app_logger.set_log_level(cls.loglevel)
            cf.close()
        except FileNotFoundError as ex:
            logger.error("%s was not found", cls.full_file_path)
        except Exception as ex:
            logger.error("An exception occurred while attempting to load intrinio.conf")
            logger.error(str(ex))

    @classmethod
    def save(cls, username, password):
        """
        Save configuraton back to intrinio.conf
        :return:
        """
        cls.auth_user = username
        cls.auth_passwd = password

        # Make sure folders exist
        if not os.path.exists(cls.file_path):
            os.makedirs(cls.file_path)

        conf = {}
        conf["user"] = cls.auth_user
        conf["password"] = cls.auth_passwd
        conf["certifi"] = cls.cacerts

        logger.debug("Saving configuration to %s", cls.full_file_path)
        cf = open(cls.full_file_path, "w")
        json.dump(conf, cf, indent=4)
        cf.close()

        if os.name == "posix":
            import stat
            # The user gets R/W permissions
            os.chmod(cls.full_file_path, stat.S_IRUSR | stat.S_IWUSR)
        else:
            pass

    @classmethod
    def get_masked_user(cls):
        return cls.auth_user[:int(len(cls.auth_user) / 2)] + ("*" * int(len(cls.auth_user) / 2))

    @classmethod
    def is_configured(cls):
        """
        Intrinio is configured if there is a user and password in the intrinio.conf file.
        :return:
        """
        if cls.macOS:
            return QConfiguration.auth_user and QConfiguration.auth_passwd and QConfiguration.cacerts
        return QConfiguration.auth_user and QConfiguration.auth_passwd

# Set up configuration with user credentials
QConfiguration.load()


class IntrinioBase:
    page_size = 100

    @staticmethod
    def setup_authorization(url_string):
        """
        Set up basic authorization for the given URL.
        :param url_string:
        :return: None
        """
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url_string, QConfiguration.auth_user, QConfiguration.auth_passwd)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        ssl_ctx = ssl.create_default_context(cafile=QConfiguration.cacerts)
        httpshandler = urllib.request.HTTPSHandler(context=ssl_ctx)
        opener = urllib.request.build_opener(httpshandler, authhandler)
        urllib.request.install_opener(opener)

    @staticmethod
    def get_usage(access_code):
        """
        Get Intrinio usage stats for the given access_code
        :param access_code:
        :return: Usage stats in a dict
        """
        template_url = "{0}/usage/current?access_code={1}"
        url_string = template_url.format(QConfiguration.base_url, access_code)
        res = IntrinioBase.exec_request(url_string)
        return res

    @staticmethod
    def get_excel_version():
        """
        Get Excel version info. Really not useful for LOCalc, but included as an exercise.
        :return: Version info in a dict
        """
        template_url = "{0}/excel"
        url_string = template_url.format(QConfiguration.base_url)
        res = IntrinioBase.exec_request(url_string)
        return res

    @staticmethod
    def exec_request(url_string):
        """
         Submit https request to Intrinio
        :param url_string:
        :return: JSON decoded dict containing results of https GET.
        The status_code key is added to return the HTTPS status code.
        """
        # print(url_string)
        IntrinioBase.setup_authorization(url_string)
        try:
            logger.debug("Calling Intrinio: %s", url_string)
            response = urllib.request.urlopen(url_string)
            status_code = response.getcode()
            logger.debug("Status code: %d", status_code)
            res = response.read()
            res = str(res, "utf-8")
        except urllib.error.HTTPError as ex:
            logger.error(ex.msg)
            logger.error(str(ex))
            return {"status_code":ex.code}

        j = json.loads(res)
        j["status_code"] = status_code
        return j

    @staticmethod
    def status_code_message(status_code):
        """
        Return an appropriate message for a non-200 status code
        :param status_code:
        :return:
        """
        if status_code == 429:
            return "Plan limit reached"
        elif status_code == 401:
            return "Your username and password keys are incorrect"
        elif status_code == 403:
            return "Visit Intrinio.com to subscribe"
        elif status_code == 503:
            return "You have reached your throttle limit regarding requests/second"
        return "Unexpected status code " + str(status_code)

    @staticmethod
    def get_page_number(sequence):
        """
        Compute the page_number that contains a given sequence number
        using the fixed page size.
        :param sequence:
        :return:
        """
        return math.ceil((sequence + 1) / IntrinioBase.page_size)

    @staticmethod
    def get_page_index(sequence):
        """
        Compute the page index of a given sequence number. The page index
        is the offset of the sequence number item within a page.
        :param sequence:
        :return:
        """
        page_number = IntrinioBase.get_page_number(sequence)
        return sequence - ((page_number - 1) * IntrinioBase.page_size)


class IntrinioCompanies(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def verify_company(ticker):
        """
        Call Intrinio API to verify a given company ticker symbol
        :param ticker:
        :return:
        """

        template_url = "{0}/companies/verify?ticker={1}"
        url_string = template_url.format(QConfiguration.base_url, ticker.upper())
        res = IntrinioCompanies.exec_request(url_string)
        if "ticker" in res:
            return res["ticker"] == ticker
        return False


class IntrinioSecurities(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def verify_security(ticker):
        """
        Call Intrinio API to verify a given security ticker symbol
        :param ticker:
        :return:
        """

        template_url = "{0}/securities/verify?ticker={1}"
        url_string = template_url.format(QConfiguration.base_url, ticker.upper())
        res = IntrinioSecurities.exec_request(url_string)
        if "ticker" in res:
            return res["ticker"] == ticker
        return False


class IntrinioBanks(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def verify_bank(identifier):
        """
        Call Intrinio API to verify a given bank identifier
        :param identifier:
        :return:
        """

        template_url = "{0}/banks/verify?identifier={1}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper())
        res = IntrinioBanks.exec_request(url_string)
        if "identifier" in res:
            return res["identifier"] == identifier
        return False


class IntrinioDataPoint(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_data_point(identifier, item):
        """

        :param identifier:
        :param item:
        :return:
        """

        template_url = "{0}/data_point?identifier={1}&item={2}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(), item)
        res = IntrinioDataPoint.exec_request(url_string)
        logger.debug("%s %s %s", res["identifier"], res["item"], res["value"])
        return res


class IntrinioHistoricalPrices(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_price_page(identifier, sequence, start_date, end_date, frequency):
        """
        Retrieve the page of price data that contains the given sequence number
        :param identifier:
        :param sequence:
        :param start_date:
        :param end_date:
        :param frequency:
        :return:
        """
        page_number = IntrinioHistoricalPrices.get_page_number(sequence)

        template_url = "{0}/prices?identifier={1}&page_size={2}&page_number={3}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(),
                                         IntrinioHistoricalPrices.page_size, page_number)

        # Add additional query parameters
        if start_date:
            url_string += "&start_date=" + start_date
        if end_date:
            url_string += "&end_date=" + end_date
        if frequency:
            url_string += "&frequency=" + frequency

        print (url_string)
        # Note for future reference. It looks like this URL is designed for
        # you to run the query for the first page. It returns the number of total_pages available
        # as one of the JSON values. You could use that value to know how many pages are
        # left to be retrieved.
        # Also, it should be noted that the dates go backwards. Sequence 0 will always
        # be the newest date, while sequence numbers 1 to n will go backwards in time.
        res = IntrinioHistoricalPrices.exec_request(url_string)
        logger.debug("Result count: %s", res["result_count"])
        return res


class IntrinioHistoricalData(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_historical_data_page(identifier, item, sequence, start_date, end_date, frequency, period_type):
        """
        Retrieve the page of price data that contains the given sequence number
        :param identifier:
        :param sequence:
        :param start_date:
        :param end_date:
        :param frequency:
        :param period_type:
        :return:
        """
        page_number = IntrinioHistoricalData.get_page_number(sequence)

        template_url = "{0}/historical_data?identifier={1}&item={2}&page_size={3}&page_number={4}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(), item,
                                         IntrinioHistoricalData.page_size, page_number)

        # Add additional query parameters
        if start_date:
            url_string += "&start_date=" + start_date
        if end_date:
            url_string += "&end_date=" + end_date
        if frequency:
            url_string += "&frequency=" + frequency
        if period_type:
            url_string += "&type=" + period_type

        # print (url_string)
        # Note for future reference. It looks like this URL is designed for
        # you to run the query for the first page. It returns the number of total_pages available
        # as one of the JSON values. You could use that value to know how many pages are
        # left to be retrieved.
        # Also, it should be noted that the dates go backwards. Sequence 0 will always
        # be the newest date, while sequence numbers 1 to n will go backwards in time.
        res = IntrinioHistoricalData.exec_request(url_string)
        logger.debug("Result count: %s", res["result_count"])
        return res


class IntrinioNews(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_news_page(identifier, sequence):
        """
        Retrieve the page of price data that contains the given sequence number
        :param identifier:
        :param sequence:
        :param start_date:
        :param end_date:
        :param frequency:
        :param period_type:
        :return:
        """
        page_number = IntrinioNews.get_page_number(sequence)

        template_url = "{0}/news?identifier={1}&page_size={2}&page_number={3}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(),
                                         IntrinioNews.page_size, page_number)

        print (url_string)
        # Note for future reference. It looks like this URL is designed for
        # you to run the query for the first page. It returns the number of total_pages available
        # as one of the JSON values. You could use that value to know how many pages are
        # left to be retrieved.
        # Also, it should be noted that the dates go backwards. Sequence 0 will always
        # be the newest date, while sequence numbers 1 to n will go backwards in time.
        res = IntrinioNews.exec_request(url_string)
        logger.debug("Result count: %s", res["result_count"])
        return res


class IntrinioFundamentals(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_fundamentals_page(identifier, statement, period_type, sequence):
        """

        :param identifier: Ticker symbol
        :param statement: income_statement | balance_sheet | cash_flow_statement | calculations
        :param period_type: FY | QTR | TTM | YTD
        :param sequence: most recent first: 0..last available
        :return:
        """
        page_number = IntrinioFundamentals.get_page_number(sequence)

        template_url = "{0}/fundamentals/standardized?identifier={1}&statement={2}&page_size={3}&page_number={4}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(), statement,
                                         IntrinioFundamentals.page_size, page_number)

        # Add additional query parameters
        if period_type:
            url_string += "&type=" + period_type

        # print (url_string)
        # Note for future reference. It looks like this URL is designed for
        # you to run the query for the first page. It returns the number of total_pages available
        # as one of the JSON values. You could use that value to know how many pages are
        # left to be retrieved.
        # Also, it should be noted that the dates go backwards. Sequence 0 will always
        # be the newest date, while sequence numbers 1 to n will go backwards in time.
        res = IntrinioFundamentals.exec_request(url_string)
        logger.debug("Result count: %s", res["result_count"])
        return res


class IntrinioTags(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_tags_page(identifier, statement, sequence):
        """
        Retrieve the page of price data that contains the given sequence number
        :param identifier:
        :param sequence:
        :param start_date:
        :param end_date:
        :param frequency:
        :param period_type:
        :return:
        """
        page_number = IntrinioTags.get_page_number(sequence)

        template_url = "{0}/tags/standardized?identifier={1}&statement={2}&page_size={3}&page_number={4}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(), statement,
                                         IntrinioTags.page_size, page_number)

        print (url_string)
        # Note for future reference. It looks like this URL is designed for
        # you to run the query for the first page. It returns the number of total_pages available
        # as one of the JSON values. You could use that value to know how many pages are
        # left to be retrieved.
        # Also, it should be noted that the dates go backwards. Sequence 0 will always
        # be the newest date, while sequence numbers 1 to n will go backwards in time.
        res = IntrinioTags.exec_request(url_string)
        # print (res)
        return res


class IntrinioFinancials(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_financials_page(identifier, statement, fiscal_year, fiscal_period, page_number):
        """

        :param identifier:
        :param statement:
        :param fiscal_year:
        :param fiscal_period:
        :param page_number: 1-total_pages
        :return:
        """
        template_url = "{0}/financials/standardized?ticker={1}&statement={2}&fiscal_year={3}&fiscal_period={4}&page_size={5}&page_number={6}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(), statement,
                                         fiscal_year, fiscal_period,
                                         IntrinioFinancials.page_size, page_number)

        # print (url_string)
        # Note for future reference. It looks like this URL is designed for
        # you to run the query for the first page. It returns the number of total_pages available
        # as one of the JSON values. You could use that value to know how many pages are
        # left to be retrieved.
        # Also, it should be noted that the dates go backwards. Sequence 0 will always
        # be the newest date, while sequence numbers 1 to n will go backwards in time.
        res = IntrinioFinancials.exec_request(url_string)
        # print (res)
        return res


from intrinio_cache import IdentifierCache, DataPointCache, UsageDataCache, HistoricalPricesCache, \
    HistoricalDataCache, IntrinioNewsCache, FundamentalsCache, IntrinioTagsCache, FinancialsDataCache, \
    FinancialsQueryCache

def is_valid_identifier(identifier):
    """
    Answer the question: Is this identifier believed to be valid?
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :return: Returns True if the identifier is believed to be valid.
    """
    id = identifier.upper()

    if not IdentifierCache.is_known_identifier(id):
        # This set of tests was adapted from the Excel addin
        if id.startswith("FRED.") or id == "DMD.ERP" or ":" in id or id.startswith("$"):
            IdentifierCache.add_identifier(id, True)
        else:
            if IntrinioCompanies.verify_company(id):
                IdentifierCache.add_identifier(id, True)
            elif IntrinioSecurities.verify_security(id):
                IdentifierCache.add_identifier(id, True)
            elif IntrinioBanks.verify_bank(id):
                IdentifierCache.add_identifier(id, True)
            else:
                # This identifier failed all of the tests
                IdentifierCache.add_identifier(id, False)

    return IdentifierCache.is_valid_identifier(id)


def get_data_point(identifier, item):
    """
    Return a data point value for a given identifer and item/tag.
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :param item: tag or series ID (e.g. close_price)
    :return: The data point value or a message
    """
    if DataPointCache.is_value_cached(identifier, item):
        logger.debug("Cache hit for data point %s %s", identifier, item)
        return DataPointCache.get_value(identifier, item)
    res = IntrinioDataPoint.get_data_point(identifier, item)
    if "value" in res:
        v = res["value"]
        DataPointCache.add_value(identifier, item, v)
        # After a successful API call, the usage stats are stale
        UsageDataCache.clear()
        if str(v).isnumeric():
            return float(v)
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_historical_prices(identifier, item, sequence, start_date=None, end_date=None, frequency=None):
    """
    Returns professional-grade historical stock prices for a security or stock market index.
    Reference: http://docs.intrinio.com/?javascript--api#prices
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :param item: date | open | high | low | close | volume | ex_dividend | split_ratio | adj_open | adj_high | adj_low | adj_close | adj_volume
    :param sequence: index of desired price within the entire set of data returned (0 to last available).
    :param start_date: First date for historical data.
    :param end_date: Last date for historical data.
    :param frequency: daily | weekly | monthly | quarterly | yearly
    :return: The data point value or a message
    """
    # TODO Consider validating the item

    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    # If dates are present, convert to ISO format
    try:
        n_start_date = normalize_date(start_date)
        n_end_date = normalize_date(end_date)
    except Exception as ex:
        logger.warning(str(ex))
        return str(ex)

    if HistoricalPricesCache.is_query_value_cached(identifier, n_start_date, n_end_date, frequency, page_number):
        logger.debug("Cache hit for historical price %s %s", identifier, item)
        query_value = HistoricalPricesCache.get_query_value(identifier, n_start_date, n_end_date, frequency, page_number)
        # Verify that item exists
        if len(query_value["data"]) > page_index:
            if item in query_value["data"][page_index]:
                v =  query_value["data"][page_index][item]
                if str(v).isnumeric():
                    return float(v)
            else:
                v = "Invalid item"
        else:
            v = "Sequence out of range"
        return v

    res = IntrinioHistoricalPrices.get_price_page(identifier, sequence, n_start_date, n_end_date, frequency)

    if "data" in res:
        HistoricalPricesCache.add_query_value(res, identifier, n_start_date, n_end_date, frequency, page_number)
        # Verify that item exists
        if len(res["data"]) > page_index:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
                if str(v).isnumeric():
                    v = float(v)
            else:
                v = "Invalid item"
        else:
            v = "Sequence out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_historical_data(identifier, item, sequence, start_date=None, end_date=None, frequency=None,
                        period_type=None, show_date=False):
    """
    Returns the historical data for for a selected identifier (ticker symbol or index symbol) for a selected tag.
    Reference: http://docs.intrinio.com/?javascript--api#historical-data
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :param item: date | open | high | low | close | volume | ex_dividend | split_ratio | adj_open | adj_high | adj_low | adj_close | adj_volume
    :param sequence: index of desired price within the entire set of data returned (0 to last available).
    :param start_date: First date for historical data.
    :param end_date: Last date for historical data.
    :param frequency: daily | weekly | monthly | quarterly | yearly
    :param period_type:
    :param show_date:
    :return: The data point value or a message
    """
    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    # If dates are present, convert to ISO format
    try:
        n_start_date = normalize_date(start_date)
        n_end_date = normalize_date(end_date)
    except Exception as ex:
        logger.warning(str(ex))
        return str(ex)

    if HistoricalDataCache.is_query_value_cached(identifier, item, n_start_date, n_end_date, frequency, period_type, page_number):
        logger.debug("Cache hit for historical price %s %s", identifier, item)
        query_value = HistoricalDataCache.get_query_value(identifier, item, n_start_date, n_end_date, frequency, period_type, page_number)
        if len(query_value["data"]) > page_index:
            if show_date:
                v = query_value["data"][page_index]["date"]
            else:
                v =  query_value["data"][page_index]["value"]
                if str(v).isnumeric():
                    v = float(v)
        else:
            v = "Sequence out of range"
        return v

    res = IntrinioHistoricalData.get_historical_data_page(identifier, item, sequence, n_start_date, n_end_date,
                                                          frequency, period_type)

    if "data" in res:
        HistoricalDataCache.add_query_value(res, identifier, item, n_start_date, n_end_date, frequency, period_type, page_number)
        if len(res["data"]) > page_index:
            if show_date:
                v = res["data"][page_index]["date"]
            else:
                v = res["data"][page_index]["value"]
                if str(v).isnumeric():
                    v = float(v)
        else:
            v = "Sequence is out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_news(identifier, item, sequence):
    """
    Returns company news for a selected identifier (ticker symbol or index symbol).
    Each sequence number represents a news article. The item is the desired news entry attribute.
    Reference: http://docs.intrinio.com/?javascript--api#company-news
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :param item: title | publication_date | summary | url
    :param sequence: index of desired news entry within the entire set of data returned (0 to last available).
    :return: The data point value or a message
    """
    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    if IntrinioNewsCache.is_query_value_cached(identifier, page_number):
        logger.debug("Cache hit for company news %s %s %d", identifier, item, sequence)
        query_value = IntrinioNewsCache.get_query_value(identifier, page_number)
        if len(query_value["data"]) > page_index:
            if item in query_value["data"][page_index]:
                v =  query_value["data"][page_index][item]
            else:
                v = "Invalid item"
        else:
            v = "Sequence out of range"

        return v

    res = IntrinioNews.get_news_page(identifier, sequence)

    if "data" in res:
        IntrinioNewsCache.add_query_value(res, identifier, page_number)
        if len(res["data"]) > page_index:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
            else:
                v = "Invalid item"
        else:
            v = "Sequence is out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_fundamentals_data(identifier, statement, period_type, sequence, item):
    """
    Returns a list of available standardized fundamentals (fiscal year and fiscal period)
    for a given ticker and statement.
    :param identifier:
    :param statement:
    :param period_type:
    :param sequence:
    :param item:
    :return:
    """
    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    if FundamentalsCache.is_query_value_cached(identifier, statement, period_type, page_number):
        logger.debug("Cache hit for fundamentals data %s %s %s %d", identifier, statement, period_type, sequence)
        query_value = FundamentalsCache.get_query_value(identifier, statement, period_type, page_number)
        if len(query_value["data"]) > page_index:
            if item in query_value["data"][page_index]:
                v =  query_value["data"][page_index][item]
            else:
                v = "Invalid item: " + item
        else:
            v = "Sequence out of range"
        return v

    res = IntrinioFundamentals.get_fundamentals_page(identifier, statement, period_type, sequence)

    if "data" in res:
        FundamentalsCache.add_query_value(res, identifier, statement, period_type, page_number)
        if len(res["data"]) > page_index:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
            else:
                v = "Invalid item: " + item
        else:
            v = "Sequence is out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_tags(identifier, statement, sequence, item):
    """
    Returns the standardized tags and labels for a given ticker, statement, and date or fiscal year/fiscal quarter.
    :param identifier: Stock ticker symbol.
    :param statement: income_statement | balance_sheet | cash_flow_statement | calculations | current
    :param sequence: an integer whose value is 0-max available number of results.
    :param item: name | tag | parent | factor | balance | type | units
    :return:
    """
    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    if IntrinioTagsCache.is_query_value_cached(identifier, statement, page_number):
        logger.debug("Cache hit for standardized tags %s %s %s %d", identifier, statement, item, sequence)
        query_value = IntrinioTagsCache.get_query_value(identifier, statement, page_number)
        if len(query_value["data"]) > page_index:
            if item in query_value["data"][page_index]:
                v =  query_value["data"][page_index][item]
            else:
                v = "Invalid item: " + item
        else:
            v = "Sequence out of range"
        return v

    res = IntrinioTags.get_tags_page(identifier, statement, sequence)

    if "data" in res:
        IntrinioTagsCache.add_query_value(res, identifier, statement, page_number)
        if len(res["data"]) > sequence:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
            else:
                v = "Invalid item: " + item
        else:
            v = "Sequence is out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_financials_data(identifier, statement, fiscal_year, fiscal_period, tag):
    """
    Returns professional-grade historical financial data for a specific data tag.
    :param identifier: Stock ticker symbol.
    :param statement:
    :param fiscal_year:
    :param fiscal_period:
    :param tag:
    :return:
    """
    logger.debug("get_financials_data: %s %s %d %s %s", identifier, statement, fiscal_year, fiscal_period, tag)
    # Translate fiscal year and period if required
    if int(fiscal_year) < 1900:
        # fiscal year is a sequence number and fiscal period is a type
        lookup_fp = fiscal_period
        lookup_fy = int(fiscal_year)
        fiscal_year = get_fundamentals_data(identifier, statement, lookup_fp, lookup_fy, "fiscal_year")
        fiscal_period = get_fundamentals_data(identifier, statement, lookup_fp, lookup_fy, "fiscal_period")
        logger.debug("Translated fy/fp from %d/%s to %d/%s", lookup_fy, lookup_fp, fiscal_year, fiscal_period)

    # Check cache for the specific tag
    if FinancialsDataCache.is_query_value_cached(identifier, statement, fiscal_year, fiscal_period, tag):
        logger.debug("Cache hit for financials data: %s %s %d %s %s",
                     identifier, statement, fiscal_year, fiscal_period, tag)
        v = FinancialsDataCache.get_query_value(identifier, statement, fiscal_year, fiscal_period, tag)
        return v

    # Before calling Intrinio API, check to see if we have already fetched the data for this query
    # If we have run the query, then the requested tag is not defined.
    if FinancialsQueryCache.is_query_value_cached(identifier, statement, fiscal_year, fiscal_period):
        logger.debug("Tag not defined for financials data %s %s %d %s %s",
                     identifier, statement, fiscal_year, fiscal_period, tag)
        v = "na"
        return v


    # We have to read ALL of the pages for the given parameters to get all of the tags available.
    # Essentially, we are building a big cache of all available data.
    total_pages = 1
    current_page = 1
    tag_found = False
    while current_page <= total_pages:
        res = IntrinioFinancials.get_financials_page(identifier, statement, fiscal_year, fiscal_period, current_page)
        # print (res)
        if "total_pages" in res:
            total_pages = int(res["total_pages"])
            logger.debug("Total financials pages: %d", total_pages)
        else:
            # This is an error
            return IntrinioBase.status_code_message(res["status_code"])
        # Cache each tag/value pair in this page
        if "data" not in res:
            logger.debug("Financials page contains no data")
        for tv in res["data"]:
            logger.debug("Adding to financials data cache: %s %s %s %d %s %s", tv["value"],
                   identifier, statement, fiscal_year, fiscal_period, tv["tag"])
            # Note that this overwrites an existing cache entry
            FinancialsDataCache.add_query_value(tv["value"], identifier, statement, fiscal_year, fiscal_period, tv["tag"])
            # Note when we find the desired tag and its value
            if tv["tag"] == tag:
                tag_found = True
                v = tv["value"]
                logger.debug("Financial tag found: %s=%s", tv["tag"], tv["value"])

        # Mark this query as cached
        FinancialsQueryCache.add_query_value(True, identifier, statement, fiscal_year, fiscal_period)
        logger.debug("Added financials query to cache: %d %s %s %d %s", True, identifier, statement, fiscal_year, fiscal_period)

        # On to the next page
        current_page += 1

    if tag_found:
        return v

    # Prevent another API call for this tag
    FinancialsDataCache.add_query_value("na", identifier, statement, fiscal_year, fiscal_period, tag)
    logger.debug("Adding financials data cache: %s %s %d %s %s %s", "na", identifier, statement, fiscal_year, fiscal_period, tag)
    return "na"


#
# Intrinio login dialog
# Adapted from https://forum.openoffice.org/en/forum/viewtopic.php?f=45&t=56397#p248794
#


try:
    import uno
    logger.debug("Attempt to import uno succeeded")
    # logger.debug("sys.path = %s", sys.path)
except Exception as ex:
    logger.error("Attempt to import uno failed %s", str(ex))
try:
    # https://www.openoffice.org/api/docs/common/ref/com/sun/star/awt/PosSize.html
    from com.sun.star.awt.PosSize import POSSIZE # flags the x- and y-coordinate, width and height
    logger.debug("Attempt to import com.sun.star.awt.PosSize succeeded")
except Exception as ex:
    logger.error("Attempt to import com.sun.star.awt.PosSize failed %s", str(ex))


def _add_awt_model(dlg_model, srv, ctl_name, prop_list):
    """
    Helper function for building dialog
    Insert UnoControl<srv>Model into given DialogControlModel
    :param dlg_model: dialog model where control is to be added
    :param srv: control model type to be added
    :param ctl_name: name to be assigned to the control model
    :param prop_list: properties to be assigned to new control model
    :return: None
    """
    ctl_model = dlg_model.createInstance("com.sun.star.awt.UnoControl" + srv + "Model")
    while prop_list:
        prp = prop_list.popitem()
        uno.invoke(ctl_model,"setPropertyValue",(prp[0],prp[1]))
        #works with awt.UnoControlDialogElement only:
        ctl_model.Name = ctl_name
    dlg_model.insertByName(ctl_name, ctl_model)


def intrinio_login():
    """
    Ask user for Intrinio login credentials
    :return: If successful, returns username and password as a tuple (something truthy)
    If canceled, returns False.
    """
    # Reference: https://www.openoffice.org/api/docs/common/ref/com/sun/star/awt/module-ix.html
    global logger

    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager
    dlg_model = smgr.createInstance("com.sun.star.awt.UnoControlDialogModel")
    dlg_model.Title = 'Intrinio Access Keys'
    _add_awt_model(dlg_model, 'FixedText', 'lblName', {
        'Label': 'User Name',
    }
                   )
    _add_awt_model(dlg_model, 'Edit', 'txtName', {})
    _add_awt_model(dlg_model, 'FixedText', 'lblPWD', {
        'Label': 'Password',
    }
                   )
    _add_awt_model(dlg_model, 'Edit', 'txtPWD', {
        'EchoChar': 42,
    }
                   )
    _add_awt_model(dlg_model, 'Button', 'btnOK', {
        'Label': 'Save',
        'DefaultButton': True,
        'PushButtonType': 1,
    }
                   )
    _add_awt_model(dlg_model, 'Button', 'btnCancel', {
        'Label': 'Cancel',
        'PushButtonType': 2,
    }
                   )

    lmargin = 10  # left margin
    rmargin = 10  # right margin
    tmargin = 10  # top margin
    bmargin = 10  # bottom margin
    cheight = 25  # control height
    pad = 5  # top/bottom padding where needed
    theight = cheight + pad  # total height of a control

    # Poor man's grid
    # layout "control-name", [x, y, w, h]
    layout = {
        "lblName": [lmargin, tmargin, 100, cheight],
        "txtName": [lmargin + 100, tmargin, 250, cheight],
        "lblPWD": [lmargin, tmargin + (theight * 1), 100, cheight],
        "txtPWD": [lmargin + 100, tmargin + (theight * 1), 250, cheight],
        "btnOK": [lmargin + 100, tmargin + (theight * 2), 100, cheight],
        "btnCancel": [lmargin + 200, tmargin + (theight * 2), 100, cheight]
    }

    dialog = smgr.createInstance("com.sun.star.awt.UnoControlDialog")
    dialog.setModel(dlg_model)
    name_ctl = dialog.getControl('txtName')
    pass_ctl = dialog.getControl('txtPWD')

    # Apply layout to controls. Must be done within the dialog.
    for name, d in layout.items():
        ctl = dialog.getControl(name)
        ctl.setPosSize(d[0], d[1], d[2], d[3], POSSIZE)

    dialog.setPosSize(300, 300, lmargin + rmargin + 100 + 250, tmargin + bmargin + (theight * 3), POSSIZE)
    dialog.setVisible(True)

    # Run the dialog. Returns the value of the PushButtonType.
    # 1 = save
    # 2 = cancel
    button_id = dialog.execute()
    logger.debug("intrinio login dialog returned: %s", button_id)
    if button_id == 1:
        return (name_ctl.getText(), pass_ctl.getText())
    else:
        return False
