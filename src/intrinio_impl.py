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
# See the LICENSE file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program (the LICENSE file).  If not, see <http://www.gnu.org/licenses/>.
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
from intrinio_lib import IntrinioBase, QConfiguration, intrinio_login

# Logger init
app_logger = AppLogger("intrinio-extension")
logger = app_logger.getAppLogger()
logger.debug("Logger running...")


class IntrinioImpl(unohelper.Base, XIntrinio ):
    """Define the main class for the Intrinio LO Calc extension """
    def __init__( self, ctx ):
        self.ctx = ctx
        # Reset usage data when it is known to be stale
        self.usage_data = None
        logger.debug("IntrinioImpl initialized")
        logger.debug("self: %s", str(self))
        logger.debug("ctx: %s", str(ctx))

    def getIntrinioUsage(self, access_code, key):
        """

        :param access_code: e.g. com_fin_data. See Intrinio site for list
        :param key: Name of usage stat to return
        :return:
        """
        logger.debug("getIntrinioUsage called: %s %s", access_code, key)
        if _check_configuration():
            if not self.usage_data:
                self.usage_data = IntrinioBase.get_usage(access_code)
            return self.usage_data[key]
        else:
            self.usage_data = None
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
                if res:
                    # The return value is a tuple (username, password)
                    QConfiguration.save(res[0], res[1])
                else:
                    logger.error("intrinio_login() returned false")
                dialog_lock.release()
                configured = QConfiguration.is_configured()
            else:
                logger.warn("Intrinio configuration dialog is already active")
        except Exception as ex:
            logger.error("intrinio_login() failed %s", str(ex))
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
