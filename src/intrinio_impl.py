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
#Try/except is for LibreOffice Python3.x vs. OpenOffice Python2.x.
try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
except ImportError:
    from urllib2 import Request, urlopen, URLError
import threading
from codecs import iterdecode
import unohelper
from com.intrinio.fintech.localc import XIntrinio

# Add current directory to path to import local modules
cmd_folder = os.path.realpath(os.path.abspath
                              (os.path.split(inspect.getfile
                                             ( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

# Local imports go here
from app_logger import AppLogger
from intrinio_lib import IntrinioBase, QConfiguration, intrinio_login, is_valid_identifier, get_data_point, \
    get_historical_prices
from intrinio_cache import UsageDataCache
import xml.etree.ElementTree as etree

# Logger init
app_logger = AppLogger("intrinio-extension")
logger = app_logger.getAppLogger()
# Extract version from description.xml
tree = etree.parse(cmd_folder + "/description.xml")
root = tree.getroot()
nodes = root.findall('{http://openoffice.org/extensions/description/2006}version')
logger.debug("Intrinio-LOCalc Version: %s", nodes[0].attrib["value"])


class IntrinioImpl(unohelper.Base, XIntrinio ):
    """Define the main class for the Intrinio LO Calc extension """
    def __init__( self, ctx ):
        self.ctx = ctx
        logger.debug("IntrinioImpl initialized")
        logger.debug("self: %s", str(self))
        logger.debug("ctx: %s", str(ctx))

    def IntrinioUsage(self, access_code, key):
        """
        Return usage data for Intrinio API
        :param access_code: e.g. com_fin_data. See Intrinio site for list
        :param key: Name of usage stat to return
        :return:
        """
        logger.debug("IntrinioUsage called: %s %s", access_code, key)
        if _check_configuration():
            if not UsageDataCache.is_usage_data():
                usage_data = IntrinioBase.get_usage(access_code)
                UsageDataCache.add_usage_data(usage_data)
            else:
                logger.debug("Cache hit for usage data %s %s", access_code, key)
            return UsageDataCache.get_usage_data()[key]
        else:
            UsageDataCache.clear()
            return "No configuration"

    def IntrinioDataPoint(self, identifier, item):
        """
        Retrieve a single data point for an identifier/item combination.
        Basically the same as the Excel IntrinioDataPoint function
        :param identifier: ticker symbol
        :param item: tag or series id
        :return:
        """
        logger.debug("IntrinioDataPoint called: %s %s", identifier, item)
        if _check_configuration():
            if is_valid_identifier(identifier):
                return get_data_point(identifier, item)
            else:
                logger.debug("Invalid identifier %s", identifier)
                return "Invalid identifier"
        else:
            return "No configuration"

    def IntrinioHistoricalPrices(self, ticker, item, sequence_number, start_date, end_date, frequency):
        """
        Return a single price of type 'item' for ticker symbol 'ticker'.
        Reference http://docs.intrinio.com/excel-addin#intriniohistoricalprices
        :param ticker:
        :param item:
        :param sequence_number:
        :param start_date:
        :param end_date:
        :param frequency:
        :return:
        """
        logger.debug("IntrinioHistoricalPrices called: %s %s %d %s %s %s", ticker, item, sequence_number, start_date, end_date, frequency)
        if _check_configuration():
            if is_valid_identifier(ticker):
                return get_historical_prices(ticker, item, sequence_number, start_date, end_date, frequency)
            else:
                logger.debug("Invalid ticker symbol %s", ticker)
                return "Invalid ticker symbol"
        else:
            return "No configuration"

    def IntrinioHistoricalData(self, identifier, item, sequence_number, start_date, end_date, frequency, period_type, show_date):
        """
        Returns the historical data for for a selected identifier (ticker symbol or index symbol) for a selected tag.
        :param identifier:
        :param item:
        :param sequence_number:
        :param start_date:
        :param end_date:
        :param frequency:
        :param period_type:
        :param show_date:
        :return:
        """
        logger.debug("IntrinioHistoricalData called: %s %s %d %s %s %s %s %s", identifier, item, sequence_number,
                     start_date, end_date, frequency, period_type, show_date)
        if _check_configuration():
            if is_valid_identifier(identifier):
                # return get_historical_data(identifier, item, sequence_number, start_date, end_date, frequency, period_type, show_date)
                return "Not implemented"
            else:
                logger.debug("Invalid identifier %s", identifier)
                return "Invalid identifier"
        else:
            return "No configuration"


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
        try:
            if dialog_lock.acquire(blocking=False):
                logger.debug("Calling intrinio_login()")
                res = intrinio_login()
                logger.debug("Returned from intrinio_login()")
                if res:
                    # The return value is a tuple (username, password)
                    QConfiguration.save(res[0], res[1])
                else:
                    logger.error("intrinio_login() returned false")
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
