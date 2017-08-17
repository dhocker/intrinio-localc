#
# url_helpers.py - Reusable functions for accessing URLs from either Python2 or Python3
# Copyright (C) 2017  Dave Hocker (email: galydon17@gmail.com)
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

import sys

if sys.version_info[0] == 2:
    import urllib2
else:
    import urllib.request
    import urllib.parse
    import urllib.error

import ssl
import json
from intrinio_app_logger import AppLogger

# Logger init
the_app_logger = AppLogger("intrinio-extension")
logger = the_app_logger.getAppLogger()


def setup_authorization3(url_string, user, password, cacerts):
    """
    Set up basic authorization for the given URL.
    :param url_string:
    :return: None
    """
    passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url_string, user, password)
    authhandler = urllib.request.HTTPBasicAuthHandler(passman)
    ssl_ctx = ssl.create_default_context(cafile=cacerts)
    httpshandler = urllib.request.HTTPSHandler(context=ssl_ctx)
    opener = urllib.request.build_opener(httpshandler, authhandler)
    urllib.request.install_opener(opener)


def setup_authorization2(url_string, user, password, cacerts):
    """
    Set up basic authorization for the given URL.
    :param url_string:
    :return: None
    """
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url_string, user, password)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    ssl_ctx = ssl.create_default_context(cafile=cacerts)
    httpshandler = urllib2.HTTPSHandler(context=ssl_ctx)
    opener = urllib2.build_opener(httpshandler, authhandler)
    urllib2.install_opener(opener)


def exec_request3(url_string, user, password, cacerts):
    """
     Submit https request to Intrinio
    :param url_string:
    :return: JSON decoded dict containing results of https GET.
    The status_code key is added to return the HTTPS status code.
    """
    # print(url_string)
    setup_authorization3(url_string, user, password, cacerts)
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
            # In Python3 JSON produces string output which is Unicode
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


def exec_request2(url_string, user, password, cacerts):
    """
     Submit https request to Intrinio
    :param url_string:
    :return: JSON decoded dict containing results of https GET.
    The status_code key is added to return the HTTPS status code.
    """
    # print(url_string)
    setup_authorization2(url_string, user, password, cacerts)
    status_code = 666
    try:
        logger.debug("HTTPS GET: %s", url_string)
        response = urllib2.urlopen(url_string)
        status_code = response.getcode()
        logger.debug("Status code: %d", status_code)
        res = response.read()
    except urllib2.HTTPError as ex:
        logger.error(ex.msg)
        logger.error(str(ex))
        return {"status_code":ex.code, "error_message":ex.msg}

    # Not every URL returns something
    if res:
        # Guard against invalid result returned by URL
        try:
            # In Python2 JSON produces Unicode output, not string output.
            j = json.loads(res)
        except:
            logger.error("HTTPS GET: %s", url_string)
            logger.error("Status code: %d", status_code)
            logger.error("Returned invalid/unexpected JSON response: %s", res)
            j = {"bad_payload": res}
        j["status_code"] = status_code
    else:
        j = {"status_code" : status_code}
    # print (j)
    return j
