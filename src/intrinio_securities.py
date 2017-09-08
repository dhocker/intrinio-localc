#
# Intrinio Securities
# Copyright (C) 2017  Dave Hocker (email: qalydon17@gmail.com)
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
from intrinio_lib import QConfiguration, IntrinioBase

# Logger init
app_logger = AppLogger("intrinio-extension")
logger = app_logger.getAppLogger()


# Warning: This class already exists, so these methods will be added to the existing class
class IntrinioSecurities(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_securities_page(query, exchange_symbol, last_crsp_adj_date, sequence):
        page_number = IntrinioSecurities.get_page_number(sequence)

        template_url = "{0}/securities?page_size={1}&page_number={2}"
        url_string = template_url.format(QConfiguration.base_url, IntrinioSecurities.page_size, page_number)
        if query:
            url_string += "&query=" + query
        if exchange_symbol:
            url_string += "&exch_symbol=" + exchange_symbol
        if last_crsp_adj_date:
            url_string += "&last_crsp_adj_date=" + last_crsp_adj_date

        # print (url_string)
        res = IntrinioSecurities.exec_request(url_string)
        # print (res)
        return res

    @staticmethod
    def get_security_by_identifier(identifier):
        template_url = "{0}/securities?identifier={1}"
        url_string = template_url.format(QConfiguration.base_url, identifier)

        # print (url_string)
        res = IntrinioSecurities.exec_request(url_string)
        # print (res)
        return res


class SecuritiesQueryCache:
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(query, exchange_symbol, last_crsp_adj_date, page_number):
        if not query:
            query = "n1"
        if not exchange_symbol:
            exchange_symbol = "n2"
        if not last_crsp_adj_date:
            last_crsp_adj_date = "n3"
        return query + "_" + exchange_symbol + "_" + last_crsp_adj_date + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, query, exchange_symbol, last_crsp_adj_date, page_number):
        key = cls._query_key(query, exchange_symbol, last_crsp_adj_date, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, query, exchange_symbol, last_crsp_adj_date, page_number):
        key = cls._query_key(query, exchange_symbol, last_crsp_adj_date, page_number)
        # This returns the entire API call result (which can be a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, query, exchange_symbol, last_crsp_adj_date, page_number):
        key = cls._query_key(query, exchange_symbol, last_crsp_adj_date, page_number)
        cls.query_values[key] = query_value


class SecuritiesCache:
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier):
        return identifier

    @classmethod
    def is_query_value_cached(cls, identifier):
        key = cls._query_key(identifier)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier):
        key = cls._query_key(identifier)
        # This returns the entire API call result (which can be a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier):
        key = cls._query_key(identifier)
        cls.query_values[key] = query_value


def get_securities_by_query(query, exchange_symbol, last_crsp_adj_date, sequence, item):
    """
    No cost query for securities info. See http://docs.intrinio.com/?javascript--api#securities.
    :param query: a string query search of security name or ticker symbol with the returned
    results being the relevant securities in compacted list format.
    :param exchange_symbol: the Intrinio Stock Market Symbol, to specify the exchange for the list of securities
    :param last_crsp_adj_date: a date value that returns the list of securities that have had adjusted stock
    prices due to a corporate event after this date. ISO date format.
    :param sequence: 0-(n-1), where n is the number of securities returned by the query.
    :param item:
        "ticker": "AA",
        "figi_ticker": "AA:US",
        "figi": "BBG000B9WH86",
        "security_name": "ALCOA INC",
        "market_sector": "Equity",
        "security_type": "Common Stock",
        "stock_exchange": "NYSE",
        "last_crsp_adj_date": "2016-10-06",
        "composite_figi": "BBG000B9WH86",
        "figi_uniqueid": "EQ0010004600001000",
        "share_class_figi": "BBG001S5C3C2",
        "figi_exch_cntry": "US",
        "currency": "USD",
        "mic": "XNYS",
        "exch_symbol": "^XNYS",
        "etf": false,
        "delisted_security": false,
        "primary_listing": true
    :return: the value of the item or "na" if not available.
    """
    logger.debug("get_securities_by_query: %s %s %s %d %s", query, exchange_symbol, last_crsp_adj_date, sequence, item)

    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    res = __get_securities(query, exchange_symbol, last_crsp_adj_date, sequence)

    if "data" in res:
        if len(res["data"]) > sequence:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
            else:
                v = "na"
        else:
            v = ""
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def __get_securities(query, exchange_symbol, last_crsp_adj_date, sequence):
    page_number = IntrinioBase.get_page_number(sequence)

    if SecuritiesQueryCache.is_query_value_cached(query, exchange_symbol, last_crsp_adj_date, page_number):
        logger.debug("Cache hit for query securities %s %s %s %d", query, exchange_symbol, last_crsp_adj_date, sequence)
        query_value = SecuritiesQueryCache.get_query_value(query, exchange_symbol, last_crsp_adj_date, page_number)
    else:
        query_value = IntrinioSecurities.get_securities_page(query, exchange_symbol, last_crsp_adj_date, sequence)
        if "data" in query_value:
            SecuritiesQueryCache.add_query_value(query_value, query, exchange_symbol, last_crsp_adj_date, page_number)

    return query_value


def get_securities_by_query_count(query, exchange_symbol, last_crsp_adj_date):
    """
    No cost query for securities info. See http://docs.intrinio.com/?javascript--api#securities.
    :param query: a string query search of security name or ticker symbol with the returned
    results being the relevant securities in compacted list format.
    :param exchange_symbol: the Intrinio Stock Market Symbol, to specify the exchange for the list of securities
    :param last_crsp_adj_date: a date value that returns the list of securities that have had adjusted stock
    prices due to a corporate event after this date. ISO date format.
    :return: The result count for the query.
    """
    logger.debug("get_securities_by_query_count: %s %s %s", query, exchange_symbol, last_crsp_adj_date)

    res = __get_securities(query, exchange_symbol, last_crsp_adj_date, 0)

    if "result_count" in res:
        return res["result_count"]

    return IntrinioBase.status_code_message(res["status_code"])


def get_securities_by_query_tag_count():
    tags = get_securities_items()
    return len(tags)


def get_securities_by_query_tag(sequence):
    tags = get_securities_items()
    if sequence in range(len(tags)):
        t = tags[sequence]
    else:
        t = ""
    return t


def get_security_by_identifier(identifier, item):
    """
    No cost lookup of security by identifier. See http://docs.intrinio.com/?javascript--api#securities.
    :param identifier:  the identifier for the legal entity or a security associated with
    the company: TICKER SYMBOL | FIGI | OTHER IDENTIFIER
    :param item:
        "ticker": "AA",
        "figi_ticker": "AA:US",
        "figi": "BBG000B9WH86",
        "security_name": "ALCOA INC",
        "market_sector": "Equity",
        "security_type": "Common Stock",
        "stock_exchange": "NYSE",
        "last_crsp_adj_date": "2016-10-06",
        "composite_figi": "BBG000B9WH86",
        "figi_uniqueid": "EQ0010004600001000",
        "share_class_figi": "BBG001S5C3C2",
        "figi_exch_cntry": "US",
        "currency": "USD",
        "mic": "XNYS",
        "exch_symbol": "^XNYS",
        "etf": false,
        "delisted_security": false,
        "primary_listing": true
    :return: item value or "na" if not available
    """
    logger.debug("get_security_by_identifier: %s %s", identifier, item)

    res = __get_security(identifier)

    if res:
        if item in res:
            v = res[item]
        else:
            v = "na"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def __get_security(identifier):
    if SecuritiesCache.is_query_value_cached(identifier):
        logger.debug("Cache hit for security by identifier %s", identifier)
        query_value = SecuritiesCache.get_query_value(identifier)
    else:
        query_value = IntrinioSecurities.get_security_by_identifier(identifier)
        if query_value:
            SecuritiesCache.add_query_value(query_value, identifier)

    return query_value


def get_security_identifier_tag_count():
    tags = get_security_items()
    return len(tags)


def get_security_identifier_tag(sequence):
    tags = get_security_items()
    if sequence in range(len(tags)):
        t = tags[sequence]
    else:
        t = ""
    return t


def get_securities_items():
    # Use IBM as the benchmark query.
    res = __get_securities("IBM", "", "", 0)
    sample = res["data"][0]
    return list(sample.keys())


def get_security_items():
    """
    Gets maximal list of items available for a security.
    :return: A list of potentially available items for a security query
    """
    # Use IBM as the benchmark query.
    sample = __get_security("IBM")
    if "status_code" in sample:
        del sample["status_code"]
    return list(sample.keys())

#####################################

def test_securities_query_count():
    print ("Intrinio Securities Count")
    c = get_securities_by_query_count("AAPL", "^XNAS", "")
    print ("Count:", c)


def test_securities_query():
    print ()
    print ("Intrinio Securities")
    print ()

    # A test of the tag functions
    item_count = get_securities_by_query_tag_count()
    items = []
    for i in range(item_count):
        items.append(get_securities_by_query_tag(i))

    # The Intrinio Stock Exchange Symbol used as an identifier on the Intrinio API.
    # ^XNYS, ^XNAS
    exchange_symbol = "^XNAS"
    # query is a case insensitive text substring matched against the index_name field
    # *query*
    query = "apple"
    securities = []

    res = IntrinioSecurities.get_securities_page(query, exchange_symbol, "", 0)
    # print (res)
    result_count = int(res["result_count"])
    print ("result count:", result_count)
    if result_count > 10:
        result_count = 10

    # Basically testing code
    print ("All securities")
    for s in range (0, result_count):
        print (s)
        for i in items:
            r = get_securities_by_query(query, exchange_symbol, "", s, i)
            print("  ", i, ":", r)
            # Accumulate list of securities found
            if i == "ticker":
                securities.append(r)


def test_security_by_identifier():
    print ()
    print ("Intrinio Secrurity by Identifier")
    print ()

    item_count = get_security_identifier_tag_count()
    identifiers = ["AAPL", "MMM"]

    for identifier in identifiers:
        print (identifier)
        for ix in range(item_count):
            i = get_security_identifier_tag(ix)
            r = get_security_by_identifier(identifier, i)
            print("  ", i, ":", r)


if __name__ == '__main__':
    # test_securities_query()
    test_security_by_identifier()
    # test_securities_query_count()