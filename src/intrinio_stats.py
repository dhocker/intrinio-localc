#
# intrinio_stats - Display Intrinio usage stats for com_fin_data
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

from http import HTTPStatus
from intrinio_lib import IntrinioBase, QConfiguration
from intrinio_app_logger import AppLogger

# Logger init
the_app_logger = AppLogger("intrinio-extension")
logger = the_app_logger.getAppLogger()
logger.debug("Logger running...")


if __name__ == '__main__':
    # Inject certificate file location
    QConfiguration.cacerts = "../certifi/cacert.pem"

    r = IntrinioBase.get_usage("com_fin_data")
    if r["status_code"] == HTTPStatus.OK:
        print ("Stats for Intrinio account with username", QConfiguration.get_masked_user())
        for k, v in r.items():
            print ("  ", k, ":", v)
    else:
        print ("Intrinio stats call failed: %d", r["status_code"])

    r = IntrinioBase.get_excel_version()
    if r["status_code"] == HTTPStatus.OK:
        print ("Excel version info")
        for k, v in r.items():
            print ("  ", k, ":", v)
    else:
        print ("Intrinio excel call failed: %d", r["status_code"])
