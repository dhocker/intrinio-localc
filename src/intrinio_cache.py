#
# intrinio_cache - cache stores for various Intrinio data
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

from app_logger import AppLogger

# Logger init
app_logger = AppLogger("intrinio-extension")
logger = app_logger.getAppLogger()


class UsageDataCache:
    """
    Used to track the Intrinio API usage data
    """
    usage_data = None

    def __init__(self):
        pass

    @classmethod
    def is_usage_data(cls):
        return cls.usage_data is not None

    @classmethod
    def get_usage_data(cls):
        return cls.usage_data

    @classmethod
    def clear(cls):
        cls.usage_data = None

    @classmethod
    def add_usage_data(cls, data):
        cls.usage_data = data


class IdentifierCache:
    """
    Used to track identifiers (ticker symbols, etc.)
    The dict consists of identifier/boolean pairs where
    the boolean indicates if the identifier is valid or invalid.
    """
    known_identifiers = {}

    def __init__(self):
        pass

    @classmethod
    def is_valid_identifier(cls, identifier):
        if identifier in cls.known_identifiers:
            return cls.known_identifiers[identifier]
        raise ValueError()

    @classmethod
    def is_known_identifier(cls, identifier):
        return identifier in cls.known_identifiers

    @classmethod
    def add_identifier(cls, identifier, valid):
        cls.known_identifiers[identifier] = valid

    @classmethod
    def remove_identifier(cls, identifier):
        del cls.known_identifiers[identifier]


class DataPointCache:
    """
    Used to track data point values
    """
    # The key is the identifier_item (e.g. GOOG_52_week_high
    id_values = {}

    def __init__(self):
        pass

    @classmethod
    def is_value_cached(cls, identifier, item):
        key = identifier + "_" + item
        return key in cls.id_values

    @classmethod
    def get_value(cls, identifier, item):
        key = identifier + "_" + item
        return cls.id_values[key]

    @classmethod
    def add_value(cls, identifier, item, value):
        key = identifier + "_" + item
        cls.id_values[key] = value
