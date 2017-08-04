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
# See the LICENSE.md file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program (the LICENSE.md file).  If not, see <http://www.gnu.org/licenses/>.
#

from intrinio_app_logger import AppLogger

# Logger init
the_app_logger = AppLogger("intrinio-extension")
logger = the_app_logger.getAppLogger()


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


class HistoricalPricesCache:
    """
    Used to track historical price queries
    """
    # The key is a compound value consisting of all of the parameters
    # that are used in the API call.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, start_date, end_date, frequency, page_number):
        return identifier + "_" + str(start_date) + "_" + str(end_date) + "_" + str(frequency) + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, identifier, start_date, end_date, frequency, page_number):
        key = HistoricalPricesCache._query_key(identifier, start_date, end_date, frequency, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, start_date, end_date, frequency, page_number):
        key = HistoricalPricesCache._query_key(identifier, start_date, end_date, frequency, page_number)
        # This returns the entire API call result (which is a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, start_date, end_date, frequency, page_number):
        key = HistoricalPricesCache._query_key(identifier, start_date, end_date, frequency, page_number)
        cls.query_values[key] = query_value


class HistoricalDataCache:
    """
    Used to track historical data queries
    """
    # The key is a compound value consisting of all of the parameters
    # that are used in the API call.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, item, start_date, end_date, frequency, period_type, page_number):
        return identifier + "_" + item + "_" + str(start_date) + "_" + str(end_date) + "_" + str(frequency) + "_" + \
               str(period_type) + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, identifier, item, start_date, end_date, frequency, period_type, page_number):
        key = cls._query_key(identifier, item, start_date, end_date, frequency, period_type, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, item, start_date, end_date, frequency, period_type, page_number):
        key = cls._query_key(identifier, item, start_date, end_date, frequency, period_type, page_number)
        # This returns the entire API call result (which is a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, item, start_date, end_date, frequency, period_type, page_number):
        key = cls._query_key(identifier, item, start_date, end_date, frequency, period_type, page_number)
        cls.query_values[key] = query_value


class IntrinioNewsCache:
    """
    Used to track news queries
    """
    # The key is a compound value consisting of the ticker and page number.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, page_number):
        return identifier + str(page_number)

    @classmethod
    def is_query_value_cached(cls, identifier, page_number):
        key = cls._query_key(identifier, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, page_number):
        key = cls._query_key(identifier, page_number)
        # This returns the entire API call result (which can be a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, page_number):
        key = cls._query_key(identifier, page_number)
        cls.query_values[key] = query_value


class FundamentalsCache:
    """
    Used to track fundamental data queries
    """
    # The key is a compound value consisting of all of the parameters
    # that are used in the API call.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, statement, period_type, page_number):
        return identifier + "_" + statement + "_" + str(period_type) + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, identifier, statement, period_type, page_number):
        key = cls._query_key(identifier, statement, period_type, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, statement, period_type, page_number):
        key = cls._query_key(identifier, statement, period_type, page_number)
        # This returns the entire API call result (which is a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, statement, period_type, page_number):
        key = cls._query_key(identifier, statement, period_type, page_number)
        cls.query_values[key] = query_value


class IntrinioTagsCache:
    """
    Used to track news queries
    """
    # The key is a compound value consisting of the ticker, statement and page number.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, statement, page_number):
        return identifier + "_" + statement + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, identifier, statement, page_number):
        key = cls._query_key(identifier, statement, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, statement, page_number):
        key = cls._query_key(identifier, statement, page_number)
        # This returns the entire API call result (which can be a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, statement, page_number):
        key = cls._query_key(identifier, statement, page_number)
        cls.query_values[key] = query_value


class FinancialsDataCache:
    """
    Used to track financials data queries
    """
    # The key is a compound value consisting of all of the parameters
    # that are used in the API call.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, statement, fiscal_year, fiscal_period, tag):
        return identifier + "_" + statement + "_" + str(fiscal_year) + "_" + str(fiscal_period) + "_" + tag

    @classmethod
    def is_query_value_cached(cls, identifier, statement, fiscal_year, fiscal_period, tag):
        key = cls._query_key(identifier, statement, fiscal_year, fiscal_period, tag)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, statement, fiscal_year, fiscal_period, tag):
        key = cls._query_key(identifier, statement, fiscal_year, fiscal_period, tag)
        # This returns the entire API call result (which is a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, statement, fiscal_year, fiscal_period, tag):
        key = cls._query_key(identifier, statement, fiscal_year, fiscal_period, tag)
        cls.query_values[key] = query_value


class FinancialsQueryCache:
    """
    Used to track financials queries. This is so we can know that specific query has
    already been run and avoid running it more than once.
    """
    # The key is a compound value consisting of all of the parameters
    # that are used in the API call.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, statement, fiscal_year, fiscal_period):
        return identifier + "_" + statement + "_" + str(fiscal_year) + "_" + str(fiscal_period)

    @classmethod
    def is_query_value_cached(cls, identifier, statement, fiscal_year, fiscal_period):
        key = cls._query_key(identifier, statement, fiscal_year, fiscal_period)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, statement, fiscal_year, fiscal_period):
        key = cls._query_key(identifier, statement, fiscal_year, fiscal_period)
        # This returns the entire API call result (which is a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, statement, fiscal_year, fiscal_period):
        key = cls._query_key(identifier, statement, fiscal_year, fiscal_period)
        cls.query_values[key] = query_value


class ReportedFundamentalsCache:
    """
    Used to track reported fundamental data queries
    """
    # The key is a compound value consisting of all of the parameters
    # that are used in the API call.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, statement, period_type, page_number):
        return identifier + "_" + statement + "_" + str(period_type) + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, identifier, statement, period_type, page_number):
        key = cls._query_key(identifier, statement, period_type, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, statement, period_type, page_number):
        key = cls._query_key(identifier, statement, period_type, page_number)
        # This returns the entire API call result (which is a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, statement, period_type, page_number):
        key = cls._query_key(identifier, statement, period_type, page_number)
        cls.query_values[key] = query_value


class ReportedTagsCache:
    """
    Used to track news queries
    """
    # The key is a compound value consisting of the ticker, statement and page number.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, statement, fiscal_year, fiscal_period, page_number):
        return identifier + "_" + statement + "_" + str(fiscal_year) + "_" + fiscal_period + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, identifier, statement, fiscal_year, fiscal_period, page_number):
        key = cls._query_key(identifier, statement, fiscal_year, fiscal_period, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, statement, fiscal_year, fiscal_period, page_number):
        key = cls._query_key(identifier, statement, fiscal_year, fiscal_period, page_number)
        # This returns the entire API call result (which can be a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, statement, fiscal_year, fiscal_period, page_number):
        key = cls._query_key(identifier, statement, fiscal_year, fiscal_period, page_number)
        cls.query_values[key] = query_value
