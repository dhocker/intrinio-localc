#
# Intrinio Companies
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
from extn_helper import normalize_date

# Logger init
app_logger = AppLogger("intrinio-extension")
logger = app_logger.getAppLogger()


class IntrinioCompanies(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_companies_page(query, latest_filing_date, sequence):
        page_number = IntrinioCompanies.get_page_number(sequence)

        template_url = "{0}/companies?page_size={1}&page_number={2}"
        url_string = template_url.format(QConfiguration.base_url, IntrinioCompanies.page_size, page_number)
        if query:
            url_string += "&query=" + query
        if latest_filing_date:
            url_string += "&latest_filing_date=" + latest_filing_date

        # print (url_string)
        res = IntrinioCompanies.exec_request(url_string)
        # print (res)
        return res

    @staticmethod
    def get_company_by_identifier(identifier):
        template_url = "{0}/companies?identifier={1}"
        url_string = template_url.format(QConfiguration.base_url, identifier)

        # print (url_string)
        res = IntrinioCompanies.exec_request(url_string)
        # print (res)
        return res


class CompaniesQueryCache:
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(query, latest_filing_date, page_number):
        if not query:
            query = "n1"
        if not latest_filing_date:
            latest_filing_date = "n3"
        return query + "_" + latest_filing_date + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, query, latest_filing_date, page_number):
        key = cls._query_key(query, latest_filing_date, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, query, latest_filing_date, page_number):
        key = cls._query_key(query, latest_filing_date, page_number)
        # This returns the entire API call result (which can be a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, query, latest_filing_date, page_number):
        key = cls._query_key(query, latest_filing_date, page_number)
        cls.query_values[key] = query_value


class CompaniesCache:
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


def get_companies_by_query(query, latest_filing_date, sequence, item):
    """
    No cost query for securities info. See http://docs.intrinio.com/?javascript--api#securities.
    :param query: a string query search of security name or ticker symbol with the returned
    results being the relevant securities in compacted list format.
    :param latest_filing_date: a date value that returns the list of companies whose latest SEC filing was
    filed on or after this date. ISO date format.
    :param sequence: 0-(n-1), where n is the number of companies returned by the query.
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
    logger.debug("get_companies_by_query: %s %s %d %s", query, latest_filing_date, sequence, item)

    page_index = IntrinioBase.get_page_index(sequence)

    res = __get_companies(query, latest_filing_date, sequence)

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


def __get_companies(query, latest_filing_date, sequence):
    page_number = IntrinioBase.get_page_number(sequence)

    # Normalize latest filing date
    try:
        latest_filing_date = normalize_date(latest_filing_date)
    except Exception as ex:
        logger.warning(str(ex))
        return str(ex)

    if CompaniesQueryCache.is_query_value_cached(query, latest_filing_date, page_number):
        logger.debug("Cache hit for __get companies %s %s %d", query, latest_filing_date, sequence)
        query_value = CompaniesQueryCache.get_query_value(query, latest_filing_date, page_number)
    else:
        query_value = IntrinioCompanies.get_companies_page(query, latest_filing_date, sequence)
        if "data" in query_value:
            CompaniesQueryCache.add_query_value(query_value, query, latest_filing_date, page_number)

    return query_value


def get_companies_by_query_count(query, latest_filing_date):
    """
    No cost query for securities info. See http://docs.intrinio.com/?javascript--api#securities.
    :param query: a string query search of security name or ticker symbol with the returned
    results being the relevant securities in compacted list format.
    :param latest_filing_date:
    prices due to a corporate event after this date. ISO date format.
    :return: The result count for the query.
    """
    logger.debug("get_companies_by_query_count: %s %s", query, latest_filing_date)

    res = __get_companies(query, latest_filing_date, 0)

    if "result_count" in res:
        return res["result_count"]

    return IntrinioBase.status_code_message(res["status_code"])


def get_companies_by_query_tag_count():
    tags = get_companies_items()
    return len(tags)


def get_companies_by_query_tag(sequence):
    tags = get_companies_items()
    if sequence in range(len(tags)):
        t = tags[sequence]
    else:
        t = ""
    return t


def get_company_by_identifier(identifier, item):
    """
    No cost lookup of security by identifier. See http://docs.intrinio.com/?javascript--api#securities.
    :param identifier:  the identifier for the legal entity or a security associated with
    the company: TICKER SYMBOL | FIGI | OTHER IDENTIFIER
    :param item:
    "ticker": "AA",
    "name": "Alcoa Inc",
    "lei": "ABPN11VOHLHX6QR7XQ48",
    "legal_name": "Alcoa Inc.",
    "stock_exchange": "NYSE",
    "sic": 3350,
    "short_description": "Alcoa Inc. ...",
    "long_description": "Alcoa Inc. engages ...",
    "ceo": "Klaus-Christian Kleinfeld",
    "company_url": "http://www.alcoa.com",
    "business_address": "390 PARK AVENUE, NEW YORK, NY 10022-4608",
    "mailing_address": "390 PARK AVENUE, NEW YORK, NY 10022-4608",
    "business_phone_no": "2128362732",
    "hq_address1": "390 Park Avenue",
    "hq_address2": null,
    "hq_address_city": "New York",
    "hq_address_postal_code": "10022",
    "entity_legal_form": "INCORPORATED",
    "securities": [
        {
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
        },
        ...
    ],
    "cik": "0000004281",
    "latest_filing_date": "2017-02-06",
    "hq_state": "New York",
    "hq_country": "United States of America",
    "inc_state": "Pennsylvania",
    "inc_country": "United States of America",
    "employees": 60000,
    "entity_status": "ACTIVE",
    "sector": "Basic Materials",
    "industry_category": "Metals & Mining",
    "industry_group": "Aluminum",
    "template": "industrial",
    "standardized_active": true
    :return: item value or "na" if not available
    """
    logger.debug("get_company_by_identifier: %s %s", identifier, item)

    res = __get_company(identifier)

    if res:
        if item in res:
            v = res[item]
        else:
            v = "na"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def __get_company(identifier):
    if CompaniesCache.is_query_value_cached(identifier):
        logger.debug("Cache hit for __get company by identifier %s", identifier)
        query_value = CompaniesCache.get_query_value(identifier)
    else:
        query_value = IntrinioCompanies.get_company_by_identifier(identifier)
        if query_value:
            CompaniesCache.add_query_value(query_value, identifier)
    return query_value


def get_company_by_identifier_tag_count():
    tags = get_company_items()
    return len(tags)


def get_company_by_identifier_tag(sequence):
    tags = get_company_items()
    if sequence in range(len(tags)):
        t = tags[sequence]
    else:
        t = ""
    return t


def get_company_items():
    """
    Gets maximal list of items available for a company.
    :return: A list of potentially available items for a security query
    """
    # Use IBM as the benchmark.
    sample = __get_company("IBM")
    if "status_code" in sample:
        del sample["status_code"]
    return list(sample.keys())


def get_companies_items():
    """
    Gets maximal list of items available for a company.
    :return: A list of potentially available items for a company
    """
    # Use IBM as the benchmark.
    res = __get_companies("IBM", "", 0)
    sample = res["data"][0]
    return list(sample.keys())

#####################################

def test_companies_query_count():
    print ("Intrinio Companies Count")
    c = get_companies_by_query_count("AAPL", "")
    print ("Count:", c)


def test_companies_query():
    print ()
    print ("Intrinio Companies")
    print ()

    items = get_companies_items()

    # the Intrinio Stock Exchange Symbol used as an identifier on the Intrinio API.
    # ^XNYS, ^XNAS
    exchange_symbol = "^XNAS"
    # query is a case insensitive text substring matched against the index_name field
    # *query*
    query = "apple"
    securities = []

    result_count = get_companies_by_query_count(query, "")
    print ("result count:", result_count)
    if result_count > 10:
        result_count = 10

    # Basically testing code
    print ("All securities")
    for s in range (0, result_count):
        print (s)
        for i in items:
            r = get_companies_by_query(query, "", s, i)
            print("  ", i, ":", r)
            # Accumulate list of securities found
            if i == "ticker":
                securities.append(r)


import textwrap


def test_company_by_identifier():
    print ()
    print ("Intrinio Company by Identifier")
    print ()

    items = get_company_items()
    print ("Available items:", get_company_by_identifier_tag_count())

    identifiers = ["AAPL"]

    for identifier in identifiers:
        print (identifier)
        for i in items:
            r = get_company_by_identifier(identifier, i)
            if i in ["short_description", "long_description"]:
                print ("  ", i, ":")
                wrapped = textwrap.wrap(r)
                for line in wrapped:
                    print ("    ", line)
            elif type(r) == type([]):
                # The item is a list of items (securities)
                # How to handle this case in the context of a spreadsheet function???
                print("  ", i, ":")
                for s in r:
                    print ("    ", s["ticker"])
                    for k in s.keys():
                        print ("      ", k, ":", s[k])
            else:
                print("  ", i, ":", r)


if __name__ == '__main__':
    # test_companies_query()
    test_company_by_identifier()
    # test_companies_query_count()