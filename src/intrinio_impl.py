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
import app_logger

# Logger init
app_logger.EnableLogging()
logger = app_logger.getAppLogger()
logger.debug("Logger running...")


class IntrinioImpl(unohelper.Base, XIntrinio ):
    """Define the main class for the Intrinio LO Calc extension """
    def __init__( self, ctx ):
        self.ctx = ctx
        logger.debug("IntrinioImpl initialized")

    def getIntrinioUsage(self, access_code, key):
        """

        :param access_code: e.g. com_fin_data. See Intrinio site for list
        :param key: Name of usage stat to return
        :return:
        """
        logger.debug("getIntrinioUsage called: %s %s", access_code, key)
        return "{0} {1} is not implemented".format(access_code, key)

#
# Boiler plate code for adding an instance of the extension
#

def createInstance( ctx ):
    return IntrinioImpl( ctx )

g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation( \
    createInstance,"com.intrinio.fintech.localc.python.IntrinioImpl",
        ("com.sun.star.sheet.AddIn",),)
