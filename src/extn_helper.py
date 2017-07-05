#
# LO Calc extension helpers
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

import datetime


def float_to_date_str(float_date):
    """
    Magic algorithm to convert float date
    LibreOffice date as a float (actually the format used by Excel)
    base_date = 1899-12-30 = the float value 0.0
    see this reference: http://www.cpearson.com/excel/datetime.htm
    :param float_date: ddddd.tttttt where d is days from 1899-12-30 and .tttttt is fraction of 24 hours
    :return:
    """
    seconds = (int(float_date) - 25569) * 86400
    d = datetime.datetime.utcfromtimestamp(seconds)
    eff_date = d.strftime("%Y-%m-%d")
    return eff_date
