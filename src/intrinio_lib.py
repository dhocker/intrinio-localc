#
# intrinio_lib - Reusable classes and functions for accessing Intrinio
# Copyright (C) 2017  Dave Hocker (email: qalydon17@gmail.com)
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
import inspect
from intrinio_app_logger import AppLogger


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
    loglevel = "info"
    cwd = ""
    do_not_ask_again = False

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
            cls.file_path = "{0}\\libreoffice\\intrinio\\".format(os.environ["LOCALAPPDATA"])
        cls.full_file_path = cls.file_path + file_name

        # Read intrinio.conf file
        try:
            cf = open(cls.full_file_path, "r")
            cfj = json.loads(cf.read())
            cls.auth_user = cfj["user"]
            cls.auth_passwd = cfj["password"]
            if "loglevel" in cfj:
                cls.loglevel = cfj["loglevel"]
            cf.close()
        except FileNotFoundError as ex:
            logger.error("%s was not found", cls.full_file_path)
        except Exception as ex:
            logger.error("An exception occurred while attempting to load intrinio.conf")
            logger.error(str(ex))

        # Either the default or the config override
        the_app_logger.set_log_level(cls.loglevel)

        # Set up path to certs
        cls.cwd = os.path.realpath(os.path.abspath
                                          (os.path.split(inspect.getfile
                                                         (inspect.currentframe()))[0]))
        # The embedded versio of Python found in some versions of LO Calc
        # does not handle certificates. Here we compensate by using the certificate
        # package from the certifi project: https://github.com/certifi/python-certifi
        if os.name == "posix":
            cls.cacerts = "{0}/cacert.pem".format(cls.cwd)
        elif os.name == "nt":
            # This may not be necessary in Windows
            cls.cacerts = "{0}\\cacert.pem".format(cls.cwd)
        logger.debug("Path to cacert.pem: %s", cls.cacerts)

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
        conf["loglevel"] = cls.loglevel

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
        status_code = 666
        try:
            logger.debug("HTTPS GET: %s", url_string)
            response = urllib.request.urlopen(url_string)
            status_code = response.getcode()
            logger.debug("Status code: %d", status_code)
            res = response.read()
            res = str(res, "utf-8")
        except urllib.error.HTTPError as ex:
            logger.error(ex.msg)
            logger.error(str(ex))
            return {"status_code":ex.code, "error_message":ex.msg}

        # Not every URL returns something
        if res:
            # Guard against invalid result returned by URL
            try:
                j = json.loads(res)
            except:
                logger.error("HTTPS GET: %s", url_string)
                logger.error("Status code: %d", status_code)
                logger.error("Returned invalid/unexpected JSON response: %s", res)
                j = {"bad_payload": res}
            j["status_code"] = status_code
        else:
            j = {"status_code" : status_code}
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


class IntrinioReportedFundamentals(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_fundamentals_page(identifier, statement, period_type, sequence):
        """

        :param identifier: Ticker symbol
        :param statement: income_statement | balance_sheet | cash_flow_statement
        :param period_type: FY | QTR
        :param sequence: most recent first: 0..last available
        It should be noted that the dates go backwards. Sequence 0 will always
        be the newest date, while sequence numbers 1 to n will go backwards in time.
        :return:
        """
        page_number = IntrinioReportedFundamentals.get_page_number(sequence)

        template_url = "{0}/fundamentals/reported?ticker={1}&statement={2}&page_size={3}&page_number={4}&type={5}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(), statement,
                                         IntrinioReportedFundamentals.page_size, page_number, period_type)

        # print (url_string)
        res = IntrinioReportedFundamentals.exec_request(url_string)
        # print (res)
        return res


class IntrinioReportedTags(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_tags_page(identifier, statement, fiscal_year, fiscal_period, sequence):
        """
        Returns the As Reported XBRL tags and labels
        :param identifier:
        :param sequence:
        :param start_date:
        :param end_date:
        :param frequency:
        :param period_type:
        :return:
        """
        page_number = IntrinioReportedTags.get_page_number(sequence)

        template_url = "{0}/tags/reported?identifier={1}&statement={2}&page_size={3}&page_number={4}&fiscal_year={5}&fiscal_period={6}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(), statement,
                                         IntrinioReportedTags.page_size, page_number, fiscal_year, fiscal_period)

        # print (url_string)
        res = IntrinioReportedTags.exec_request(url_string)
        # print (res)
        return res


class IntrinioReportedFinancials(IntrinioBase):
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
        template_url = "{0}/financials/reported?ticker={1}&statement={2}&fiscal_year={3}&fiscal_period={4}&page_size={5}&page_number={6}"
        url_string = template_url.format(QConfiguration.base_url, identifier.upper(), statement,
                                         fiscal_year, fiscal_period,
                                         IntrinioReportedFinancials.page_size, page_number)

        # print (url_string)
        # Note for future reference. It looks like this URL is designed for
        # you to run the query for the first page. It returns the number of total_pages available
        # as one of the JSON values. You could use that value to know how many pages are
        # left to be retrieved.
        # Also, it should be noted that the dates go backwards. Sequence 0 will always
        # be the newest date, while sequence numbers 1 to n will go backwards in time.
        res = IntrinioReportedFinancials.exec_request(url_string)
        # print (res)
        return res

