#
# Intrinio extension main interface to LO Calc
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
# References
# https://wiki.openoffice.org/wiki/Calc/Add-In/Python_How-To
# http://www.biochemfusion.com/doc/Calc_addin_howto.html
# https://github.com/madsailor/SMF-Extension
#

import os
import sys
import inspect
import threading
import unohelper
from com.intrinio.fintech.localc import XIntrinio

# Add current directory to path to import local modules
cmd_folder = os.path.realpath(os.path.abspath
                              (os.path.split(inspect.getfile
                                             ( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

# Local imports go here
from intrinio_app_logger import AppLogger
from intrinio_lib import IntrinioBase, QConfiguration
from intrinio_access import intrinio_login, is_valid_identifier, get_data_point, \
    get_historical_prices, get_historical_data, get_news, get_fundamentals_data, get_tags, \
    get_financials_data, get_reported_fundamentals_data, get_reported_tags, get_reported_financials_data, \
    get_usage
from intrinio_cache import UsageDataCache
from intrinio_indices import get_indices_by_query_count, get_indices_by_query, get_indices_by_query_tag_count, \
    get_indices_by_query_tag, get_index_by_identifier_tag_count, get_index_by_identifier_tag, \
    get_index_by_identifier
from extn_helper import date_str_to_float
import xml.etree.ElementTree as etree

# Logger init
the_app_logger = AppLogger("intrinio-extension")
logger = the_app_logger.getAppLogger()
# Extract version from description.xml
tree = etree.parse(cmd_folder + "/description.xml")
root = tree.getroot()
nodes = root.findall('{http://openoffice.org/extensions/description/2006}version')
logger.info("Intrinio-LOCalc Version: %s", nodes[0].attrib["value"])


class IntrinioImpl(unohelper.Base, XIntrinio ):
    """Define the main class for the Intrinio LO Calc extension """
    def __init__( self, ctx ):
        self.ctx = ctx
        logger.debug("IntrinioImpl initialized")
        logger.debug("self: %s", str(self))
        logger.debug("ctx: %s", str(ctx))

    def IntrinioUsage(self, accesscode, key):
        """
        Return usage data for Intrinio API
        :param accesscode: e.g. com_fin_data. See Intrinio site for list
        :param key: Name of usage stat to return
        :return:
        """
        logger.debug("IntrinioUsage called: %s %s", accesscode, key)
        if not _check_configuration():
            UsageDataCache.clear()
            return "No configuration"
        return get_usage(accesscode, key)

    def IntrinioDataPoint(self, identifier, item):
        """
        Retrieve a single data point for an identifier/item combination.
        Basically the same as the Excel IntrinioDataPoint function
        :param identifier: ticker symbol
        :param item: tag or series id
        :return:
        """
        logger.debug("IntrinioDataPoint called: %s %s", identifier, item)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(identifier):
            logger.debug("Invalid identifier %s", identifier)
            return "Invalid identifier"
        if not item:
            return "Invalid item"

        return get_data_point(identifier, item)

    def IntrinioHistoricalPrices(self, ticker, item, sequencenumber, startdate, enddate, frequency):
        """
        Return a single price of type 'item' for ticker symbol 'ticker'.
        Reference http://docs.intrinio.com/excel-addin#intriniohistoricalprices
        :param ticker:
        :param item:
        :param sequencenumber:
        :param startdate:
        :param enddate:
        :param frequency:
        :return:
        """
        logger.debug("IntrinioHistoricalPrices called: %s %s %d %s %s %s", ticker, item, sequencenumber, startdate, enddate, frequency)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(ticker):
            logger.debug("Invalid ticker symbol %s", ticker)
            return "Invalid ticker symbol"
        if not item:
            return "Invalid item"

        return get_historical_prices(ticker, item, sequencenumber, startdate, enddate, frequency)

    def IntrinioHistoricalData(self, identifier, item, sequence_number, startdate, enddate, frequency, periodtype, showdate):
        """
        Returns the historical data for for a selected identifier (ticker symbol or index symbol) for a selected tag.
        :param identifier:
        :param item:
        :param sequence_number:
        :param startdate:
        :param enddate:
        :param frequency:
        :param periodtype:
        :param showdate:
        :return:
        """
        logger.debug("IntrinioHistoricalData called: %s %s %d %s %s %s %s %s", identifier, item, sequence_number,
                     startdate, enddate, frequency, periodtype, showdate)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(identifier):
            logger.debug("Invalid identifier %s", identifier)
            return "Invalid identifier"
        if not item:
            return "Invalid item"

        return get_historical_data(identifier, item, sequence_number, startdate, enddate, frequency, periodtype,
                                   showdate)

    def IntrinioNews(self, identifier, item, sequence_number):
        """
        Returns the historical data for for a selected identifier (ticker symbol or index symbol) for a selected tag.
        :param identifier:
        :param item:
        :param sequence_number:
        :return:
        """
        logger.debug("IntrinioNews called: %s %s %d", identifier, item, sequence_number)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(identifier):
            logger.debug("Invalid identifier %s", identifier)
            return "Invalid identifier"
        if not item:
            return "Invalid item"

        v = get_news(identifier, item, sequence_number)
        # Convert ISO date to LO date-float
        if item == "publication_date":
            v = date_str_to_float(v)
        return v

    def IntrinioFundamentals(self, ticker, statement, period_type, sequence_number, item):
        """
        Returns a list of available standardized fundamentals.
        :param ticker:
        :param statement:
        :param period_type:
        :param sequence_number:
        :param item:
        :return:
        """
        logger.debug("IntrinioFundamentals called: %s %s %s %d %s", ticker, statement, period_type, sequence_number, item)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(ticker):
            logger.debug("Invalid ticker %s", ticker)
            return "Invalid ticker"
        if not statement:
            return "Invalid statement"
        if not item:
            return "Invalid item"

        v = get_fundamentals_data(ticker, statement, period_type, sequence_number, item)
        # Convert ISO date to LO date-float
        # if item == "publication_date":
        #     v = date_str_to_float(v)
        return v

    def IntrinioTags(self, identifier, statement, sequence_number, item):
        """
        Returns the standardized tags and labels for a given ticker, statement, and date or fiscal year/fiscal quarter.
        :param identifier:
        :param statement:
        :param sequence_number:
        :param item:
        :return:
        """
        logger.debug("IntrinioTags called: %s %s %d %s", identifier, statement, sequence_number, item)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(identifier):
            logger.debug("Invalid identifier %s", identifier)
            return "Invalid identifier"
        if not statement:
            return "Invalid statement"
        if not item:
            return "Invalid item"

        v = get_tags(identifier, statement, sequence_number, item)
        return v

    def IntrinioFinancials(self, ticker, statement, fiscalyear, fiscalperiod, tag, rounding):
        """
        Returns professional-grade historical financial data.
        :param ticker:
        :param statement:
        :param fiscalyear:
        :param fiscalperiod:
        :param tag:
        :param rounding:
        :return:
        """
        logger.debug("IntrinioFinancials called: %s %s %d %s %s %s", ticker, statement, fiscalyear, fiscalperiod, tag, rounding)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(ticker):
            logger.debug("Invalid ticker %s", ticker)
            return "Invalid ticker"
        if not statement:
            return "Invalid statement"
        if not tag:
            return "Invalid tag"

        v = get_financials_data(ticker, statement, fiscalyear, fiscalperiod, tag)

        # Apply rounding factor to numeric values
        try:
            v = float(v)
            if rounding:
                rounding = str(rounding).upper()
                logger.debug("Applying rounding %s", rounding)
                rf = 1.0
                if rounding == "K":
                    rf = 1000.0
                elif rounding == "M":
                    rf = 1000000.0
                elif rounding == "B":
                    rf = 1000000000.0
            v = v / rf
        except:
            pass
        return v

    def IntrinioReportedFundamentals(self, ticker, statement, period_type, sequence_number, item):
        """
        Returns a list of available as reported fundamentals.
        :param ticker:
        :param statement:
        :param period_type:
        :param sequence_number:
        :param item:
        :return:
        """
        logger.debug("IntrinioReportedFundamentals called: %s %s %s %d %s", ticker, statement, period_type, sequence_number, item)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(ticker):
            logger.debug("Invalid ticker %s", ticker)
            return "Invalid ticker"
        if not statement:
            return "Invalid statement"
        if not item:
            return "Invalid item"

        v = get_reported_fundamentals_data(ticker, statement, period_type, sequence_number, item)
        return v

    def IntrinioReportedTags(self, identifier, statement, fiscal_year, fiscal_period, sequence_number, item):
        """
        Returns the as reported XBRL tags and labels for a given ticker, statement, and date or fiscal year/fiscal quarter.
        :param identifier:
        :param statement:
        :param sequence_number:
        :param item:
        :return:
        """
        logger.debug("IntrinioReportedTags called: %s %s %d %s %d %s", identifier, statement, fiscal_year, fiscal_period, sequence_number, item)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(identifier):
            logger.debug("Invalid identifer %s", identifier)
            return "Invalid ticker"
        if not statement:
            return "Invalid statement"
        if not item:
            return "Invalid item"

        v = get_reported_tags(identifier, statement, fiscal_year, fiscal_period, sequence_number, item)
        return v

    def IntrinioReportedFinancials(self, ticker, statement, fiscalyear, fiscalperiod, xbrltag, xbrldomain):
        """
        Returns the As Reported Financials directly from the financial statements of the XBRL filings from the company.
        :param ticker:
        :param statement:
        :param fiscalyear:
        :param fiscalperiod:
        :param tag:
        :param rounding:
        :return:
        """
        logger.debug("IntrinioReportedFinancials called: %s %s %d %s %s %s", ticker, statement, fiscalyear, fiscalperiod, xbrltag, xbrldomain)
        if not _check_configuration():
            return "No configuration"
        if not is_valid_identifier(ticker):
            logger.debug("Invalid ticker %s", ticker)
            return ""
        if not statement:
            logger.debug("Invalid statement %s", statement)
            return ""
        if not xbrltag:
            logger.debug("Invalid xbrl_tag %s", xbrltag)
            return ""

        v = get_reported_financials_data(ticker, statement, fiscalyear, fiscalperiod, xbrltag, xbrldomain)
        return v

    def IntrinioBankFundamentals(self, ticker, statement, period_type, sequence_number, item):
        """
        Returns a list of available bank fundamentals.
        :param ticker:
        :param statement:
        :param period_type:
        :param sequence_number:
        :param item:
        :return:
        """
        logger.debug("IntrinioBankFundamentals called: %s %s %s %d %s", ticker, statement, period_type, sequence_number, item)
        # if _check_configuration():
        #     if is_valid_identifier(ticker):
        #         v = get_fundamentals_data(ticker, statement, period_type, sequence_number, item)
        #         # Convert ISO date to LO date-float
        #         # if item == "publication_date":
        #         #     v = date_str_to_float(v)
        #         return v
        #     else:
        #         logger.debug("Invalid ticker %s", ticker)
        #         return "Invalid ticker: " + ticker
        # else:
        #     return "No configuration"
        return "Not implemented"

    def IntrinioBankTags(self, identifier, statement, sequence_number, item):
        """
        Returns the as reported XBRL tags and labels for a given ticker, statement, and date or fiscal year/fiscal quarter.
        :param identifier:
        :param statement:
        :param sequence_number:
        :param item:
        :return:
        """
        logger.debug("IntrinioBankTags called: %s %s %d %s", identifier, statement, sequence_number, item)
        # if _check_configuration():
        #     if is_valid_identifier(identifier):
        #         v = get_tags(identifier, statement, sequence_number, item)
        #         return v
        #     else:
        #         logger.debug("Invalid identifier %s", identifier)
        #         return "Invalid identifier"
        # else:
        #     return "No configuration"
        return "Not implemented"

    def IntrinioBankFinancials(self, ticker, statement, fiscalyear, fiscalperiod, xbrltag, xbrldomain):
        """
        Returns the As Reported Financials directly from the financial statements of the XBRL filings from the company.
        :param ticker:
        :param statement:
        :param fiscalyear:
        :param fiscalperiod:
        :param tag:
        :param rounding:
        :return:
        """
        logger.debug("IntrinioBankFinancials called: %s %s %d %s %s %s", ticker, statement, fiscalyear, fiscalperiod, xbrltag, xbrldomain)
        # if _check_configuration():
        #     if is_valid_identifier(ticker):
        #         v = get_financials_data(ticker, statement, fiscalyear, fiscalperiod, tag)
        #     else:
        #         logger.debug("Invalid ticker %s", ticker)
        #         return "Invalid ticker"
        # else:
        #     return "No configuration"
        #
        # return v
        return "Not implemented"

    def IntrinioIndicesQuery(self, query, indextype, sequence, item):
        if _check_configuration():
            v = get_indices_by_query(query, indextype, sequence, item)
        else:
            v = "No configuration"

        return v

    def IntrinioIndicesQueryCount(self, query, indextype):
        if _check_configuration():
            v = get_indices_by_query_count(query, indextype)
        else:
            v = "No configuration"

        return v

    def IntrinioIndicesQueryTagCount(self, query, indextype):
        if _check_configuration():
            v = get_indices_by_query_tag_count(query, indextype)
        else:
            v = "No configuration"

        return v

    def IntrinioIndicesQueryTag(self, query, indextype, sequence):
        if _check_configuration():
            v = get_indices_by_query_tag(query, indextype, sequence)
        else:
            v = "No configuration"

        return v

    def IntrinioIndex(self, identifier, item):
        if _check_configuration():
            v = get_index_by_identifier(identifier, item)
        else:
            v = "No configuration"

        return v

    def IntrinioIndexTagCount(self, identifier):
        if _check_configuration():
            v = get_index_by_identifier_tag_count()
        else:
            v = "No configuration"

        return v

    def IntrinioIndexTag(self, identifier, sequencenumber):
        if _check_configuration():
            v = get_index_by_identifier_tag(sequencenumber)
        else:
            v = "No configuration"

        return v


# Configuration lock. Used to deal with the fact that sometimes
# LO Calc makes concurrent calls into the extension.
dialog_lock = threading.Lock()

def _check_configuration():
    """
    Force Intrinio configuration. Even if the configuration attempt
    fails, we'll continue on because the request might hit cache.
    Only if we need to call Intrinio will we fail the request.
    :return: Returns True if Intrinio is configured. Otherwise,
    returns False.
    """
    configured = QConfiguration.is_configured()

    if not configured:
        # Do not ask again is an automatic "not configured"
        if QConfiguration.do_not_ask_again:
            logger.debug("Configuration is not initialized and do not ask again is set")
            return False

        try:
            if dialog_lock.acquire(blocking=False):
                logger.debug("Calling intrinio_login()")
                res = intrinio_login()
                logger.debug("Returned from intrinio_login()")
                if res[0]:
                    # The return value is a tuple (True, username, password)
                    QConfiguration.save(res[1], res[2])
                else:
                    # The return value is a tuple (False, DoNotAskAgain)
                    logger.error("intrinio_login() returned false")
                    if res[1]:
                        QConfiguration.do_not_ask_again = True
                configured = QConfiguration.is_configured()
            else:
                logger.warn("Intrinio configuration dialog is already active")
        except Exception as ex:
            logger.error("Exception occurred trying to create configuraton: %s", str(ex))
        finally:
            dialog_lock.release()

    return configured

#
# Boiler plate code for adding an instance of the extension
#

def createInstance( ctx ):
    return IntrinioImpl( ctx )

g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation( \
    createInstance,"com.intrinio.fintech.localc.python.IntrinioImpl",
        ("com.sun.star.sheet.AddIn",),)
