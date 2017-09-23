#
# SEC filings for a company
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


class IntrinioCompanyFilings(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_filings_page(identifier, report_type, start_date, end_date, sequence):
        page_number = IntrinioCompanyFilings.get_page_number(sequence)

        template_url = "{0}/companies/filings?page_size={1}&page_number={2}&identifier={3}"
        url_string = template_url.format(QConfiguration.base_url, IntrinioCompanyFilings.page_size, page_number,
                                         identifier)
        if report_type:
            url_string += "&report_type=" + report_type
        if start_date:
            url_string += "&start_date=" + start_date
        if end_date:
            url_string += "&end_date=" + end_date

        # print (url_string)
        res = IntrinioCompanyFilings.exec_request(url_string)
        # print (res)
        return res


class CompanyFilingsCache:
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(identifier, report_type, start_date, end_date, page_number):
        if not start_date:
            start_date = "n1"
        if not end_date:
            end_date = "n2"
        return identifier + "_" + report_type + "_" + start_date + "_" + end_date + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, identifier, report_type, start_date, end_date, page_number):
        key = cls._query_key(identifier, report_type, start_date, end_date, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, identifier, report_type, start_date, end_date, page_number):
        key = cls._query_key(identifier, report_type, start_date, end_date, page_number)
        # This returns the entire API call result (which can be a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, identifier, report_type, start_date, end_date, page_number):
        key = cls._query_key(identifier, report_type, start_date, end_date, page_number)
        cls.query_values[key] = query_value


def get_company_sec_filings(identifier, report_type, start_date, end_date, sequence, item):
    """
    Returns a data item from the list of SEC filings for a company
    :param identifier: The stock market ticker symbol associated with the company's common stock
    :param report_type: See https://en.wikipedia.org/wiki/SEC_filing#All_filing_types
    :param start_date:
    :param end_date:
    :param sequence: 0-(n-1) where n is the number of filings in the result
    :param item: The data item to be returned
    :return:
    """
    logger.debug("get_company_sec_filings: %s %s %s %s %d %s", identifier, report_type,
                 start_date, end_date, sequence, item)

    page_index = IntrinioBase.get_page_index(sequence)

    res = __get_company_filings(identifier, report_type, start_date, end_date, sequence)

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


def __get_company_filings(identifier, report_type, start_date, end_date, sequence):
    page_number = IntrinioBase.get_page_number(sequence)

    # Normalize dates
    try:
        start_date = normalize_date(start_date)
        end_date = normalize_date(end_date)
    except Exception as ex:
        logger.warning(str(ex))
        return str(ex)

    if CompanyFilingsCache.is_query_value_cached(identifier, report_type, start_date, end_date, page_number):
        logger.debug("Cache hit for __get company filings %s %s %s %s %d", identifier, report_type, start_date, end_date, sequence)
        query_value = CompanyFilingsCache.get_query_value(identifier, report_type, start_date, end_date, page_number)
    else:
        query_value = IntrinioCompanyFilings.get_filings_page(identifier, report_type, start_date, end_date, sequence)
        if "data" in query_value:
            CompanyFilingsCache.add_query_value(query_value, identifier, report_type, start_date, end_date, page_number)

    return query_value


def get_company_sec_filings_count(identifier, report_type, start_date, end_date):
    """
    Returns the result count for a given query
    :param identifier: The stock market ticker symbol associated with the company's common stock
    :param report_type: See https://en.wikipedia.org/wiki/SEC_filing#All_filing_types
    :param start_date:
    :param end_date:
    :return:
    """
    logger.debug("get_company_sec_filings_count: %s %s %s %s", identifier, report_type, start_date, end_date)

    res = __get_company_filings(identifier, report_type, start_date, end_date, 0)

    if "result_count" in res:
        return res["result_count"]

    return IntrinioBase.status_code_message(res["status_code"])


def get_company_sec_filings_tag_count():
    """
    Returns the number of tags that are available for a filing
    :return:
    """
    tags = get_company_filing_items()
    return len(tags)


def get_company_sec_filings_tag(sequence):
    """
    Returns a tag name for a filing
    :param sequence: 0-(n-1) where n is the number of available tags
    :return:
    """
    tags = get_company_filing_items()
    if sequence in range(len(tags)):
        t = tags[sequence]
    else:
        t = ""
    return t


def get_company_filing_items():
    # Use IBM as the benchmark.
    # This technique costs an API call, but it is maintenance proof
    res = __get_company_filings("IBM", "10-Q", "2016-01-01", "2017-01-01", 0)
    sample = res["data"][0]
    return list(sample.keys())


#####################################


def test_company_filings_count():
    print ("Intrinio Company Filings Count for AAPL")
    c = get_company_sec_filings_count("AAPL", "", "", "")
    print ("Count:", c)


def test_tags():
    print ("Intrinio Company Filings Tags")
    tag_count = get_company_sec_filings_tag_count()
    print ("Filing tag count:", tag_count)
    print ("Tags")
    for s in range(0, tag_count):
        tag = get_company_sec_filings_tag(s)
        print ("  ", tag)


def test_company_filings():
    items = get_company_filing_items()
    identifier = "AAPL"
    report_type = "10-Q"
    start_date = ""
    end_date = ""

    print ()
    print ("Intrinio Company SEC Filings for", identifier)
    print ("Report:", report_type)
    print ("Start date:", start_date)
    print ("End date:", end_date)
    print ()

    result_count = get_company_sec_filings_count(identifier, report_type, start_date, end_date)
    print ("result count:", result_count)
    if result_count > 10:
        result_count = 10

    # Basically testing code
    print ("All SEC Filings for a Company")
    for s in range (0, result_count):
        print (s)
        for i in items:
            r = get_company_sec_filings(identifier, report_type, start_date, end_date, s, i)
            print("  ", i, ":", r)


if __name__ == '__main__':
    test_company_filings_count()
    test_tags()
    test_company_filings()
