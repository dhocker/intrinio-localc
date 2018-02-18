# show_stats - OS independent script to display Intrinio usage stats for com_fin_data
# Copyright (C) 2018  Dave Hocker (email: qalydon17@gmail.com)
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
# Run this script with the available python 3 interpreter
#   python show_stats.py
#


if __name__ == '__main__':
    import os
    import sys

    # Change current directory to src
    cwd = os.getcwd()
    os.chdir("src")
    sys.path.insert(0, os.getcwd())

    # Run the stats script
    import intrinio_stats
    intrinio_stats.print_stats()

    # Restore current directory
    os.chdir(cwd)
