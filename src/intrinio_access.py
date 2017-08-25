#
# intrinio_lib - Reusable classes and functions for accessing Intrinio
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
from extn_helper import normalize_date
from intrinio_cache import IdentifierCache, DataPointCache, UsageDataCache, HistoricalPricesCache, \
    HistoricalDataCache, IntrinioNewsCache, FundamentalsCache, IntrinioTagsCache, FinancialsDataCache, \
    FinancialsQueryCache, ReportedFundamentalsCache, ReportedTagsCache, ReportedFinancialsCache, \
    ReportedFinancialsQueryCache
from intrinio_lib import IntrinioCompanies, IntrinioSecurities, IntrinioBanks, \
    IntrinioDataPoint, IntrinioFinancials, IntrinioFundamentals, IntrinioHistoricalData, \
    IntrinioHistoricalPrices, IntrinioNews, IntrinioReportedFinancials, IntrinioReportedFundamentals, \
    IntrinioReportedTags, IntrinioTags, IntrinioBase

# Logger init
the_app_logger = AppLogger("intrinio-extension")
logger = the_app_logger.getAppLogger()


def is_valid_identifier(identifier):
    """
    Answer the question: Is this identifier believed to be valid?
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :return: Returns True if the identifier is believed to be valid.
    """

    # Weed out empty/blank identifiers
    if not identifier:
        return False

    id = identifier.upper()

    if not IdentifierCache.is_known_identifier(id):
        # This set of tests was adapted from the Excel addin
        if id.startswith("FRED.") or id == "DMD.ERP" or ":" in id or id.startswith("$"):
            IdentifierCache.add_identifier(id, True)
        else:
            if IntrinioCompanies.verify_company(id):
                IdentifierCache.add_identifier(id, True)
            elif IntrinioSecurities.verify_security(id):
                IdentifierCache.add_identifier(id, True)
            elif IntrinioBanks.verify_bank(id):
                IdentifierCache.add_identifier(id, True)
            else:
                # This identifier failed all of the tests
                IdentifierCache.add_identifier(id, False)

    return IdentifierCache.is_valid_identifier(id)


def get_usage(access_code, key):
    """
    Return current usage data
    :param access_code:
    :param key:
    :return:
    """
    if not UsageDataCache.is_usage_data():
        usage_data = IntrinioBase.get_usage(access_code)
        if "access_code" in usage_data:
            UsageDataCache.add_usage_data(usage_data)
            if key in usage_data:
                return usage_data[key]
            else:
                return ""
        else:
            return IntrinioBase.status_code_message(usage_data["status_code"])

    usage_data = UsageDataCache.get_usage_data()
    if key in usage_data:
        logger.debug("Cache hit for usage data %s %s", access_code, key)
        return usage_data[key]
    return ""


def get_data_point(identifier, item):
    """
    Return a data point value for a given identifer and item/tag.
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :param item: tag or series ID (e.g. close_price)
    :return: The data point value or a message
    """
    if DataPointCache.is_value_cached(identifier, item):
        logger.debug("Cache hit for data point %s %s", identifier, item)
        return DataPointCache.get_value(identifier, item)
    res = IntrinioDataPoint.get_data_point(identifier, item)
    if "value" in res:
        v = res["value"]
        DataPointCache.add_value(identifier, item, v)
        # After a successful API call, the usage stats are stale
        UsageDataCache.clear()
        if str(v).isnumeric():
            return float(v)
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_historical_prices(identifier, item, sequence, start_date=None, end_date=None, frequency=None):
    """
    Returns professional-grade historical stock prices for a security or stock market index.
    Reference: http://docs.intrinio.com/?javascript--api#prices
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :param item: date | open | high | low | close | volume | ex_dividend | split_ratio | adj_open | adj_high | adj_low | adj_close | adj_volume
    :param sequence: index of desired price within the entire set of data returned (0 to last available).
    :param start_date: First date for historical data.
    :param end_date: Last date for historical data.
    :param frequency: daily | weekly | monthly | quarterly | yearly
    :return: The data point value or a message
    """
    # TODO Consider validating the item

    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    # If dates are present, convert to ISO format
    try:
        n_start_date = normalize_date(start_date)
        n_end_date = normalize_date(end_date)
    except Exception as ex:
        logger.warning(str(ex))
        return str(ex)

    if HistoricalPricesCache.is_query_value_cached(identifier, n_start_date, n_end_date, frequency, page_number):
        logger.debug("Cache hit for historical price %s %s", identifier, item)
        query_value = HistoricalPricesCache.get_query_value(identifier, n_start_date, n_end_date, frequency, page_number)
        # Verify that item exists
        if len(query_value["data"]) > page_index:
            if item in query_value["data"][page_index]:
                v =  query_value["data"][page_index][item]
                if str(v).isnumeric():
                    return float(v)
            else:
                v = "Invalid item"
        else:
            v = "Sequence out of range"
        return v

    res = IntrinioHistoricalPrices.get_price_page(identifier, sequence, n_start_date, n_end_date, frequency)

    if "data" in res:
        HistoricalPricesCache.add_query_value(res, identifier, n_start_date, n_end_date, frequency, page_number)
        # After a successful API call, the usage stats are stale
        UsageDataCache.clear()
        # Verify that item exists
        if len(res["data"]) > page_index:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
                if str(v).isnumeric():
                    v = float(v)
            else:
                v = "Invalid item"
        else:
            v = "Sequence out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_historical_data(identifier, item, sequence, start_date=None, end_date=None, frequency=None,
                        period_type=None, show_date=False):
    """
    Returns the historical data for for a selected identifier (ticker symbol or index symbol) for a selected tag.
    Reference: http://docs.intrinio.com/?javascript--api#historical-data
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :param item: date | open | high | low | close | volume | ex_dividend | split_ratio | adj_open | adj_high | adj_low | adj_close | adj_volume
    :param sequence: index of desired price within the entire set of data returned (0 to last available).
    :param start_date: First date for historical data.
    :param end_date: Last date for historical data.
    :param frequency: daily | weekly | monthly | quarterly | yearly
    :param period_type:
    :param show_date:
    :return: The data point value or a message
    """
    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    # If dates are present, convert to ISO format
    try:
        n_start_date = normalize_date(start_date)
        n_end_date = normalize_date(end_date)
    except Exception as ex:
        logger.warning(str(ex))
        return str(ex)

    if HistoricalDataCache.is_query_value_cached(identifier, item, n_start_date, n_end_date, frequency, period_type, page_number):
        logger.debug("Cache hit for historical price %s %s", identifier, item)
        query_value = HistoricalDataCache.get_query_value(identifier, item, n_start_date, n_end_date, frequency, period_type, page_number)
        if len(query_value["data"]) > page_index:
            if show_date:
                v = query_value["data"][page_index]["date"]
            else:
                v =  query_value["data"][page_index]["value"]
                if str(v).isnumeric():
                    v = float(v)
        else:
            v = "Sequence out of range"
        return v

    res = IntrinioHistoricalData.get_historical_data_page(identifier, item, sequence, n_start_date, n_end_date,
                                                          frequency, period_type)

    if "data" in res:
        HistoricalDataCache.add_query_value(res, identifier, item, n_start_date, n_end_date, frequency, period_type, page_number)
        # After a successful API call, the usage stats are stale
        UsageDataCache.clear()
        if len(res["data"]) > page_index:
            if show_date:
                v = res["data"][page_index]["date"]
            else:
                v = res["data"][page_index]["value"]
                if str(v).isnumeric():
                    v = float(v)
        else:
            v = "Sequence is out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_news(identifier, item, sequence):
    """
    Returns company news for a selected identifier (ticker symbol or index symbol).
    Each sequence number represents a news article. The item is the desired news entry attribute.
    Reference: http://docs.intrinio.com/?javascript--api#company-news
    :param identifier: An Intrinio acceptable identifier (e.g a ticker symbol)
    :param item: title | publication_date | summary | url
    :param sequence: index of desired news entry within the entire set of data returned (0 to last available).
    :return: The data point value or a message
    """
    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    if IntrinioNewsCache.is_query_value_cached(identifier, page_number):
        logger.debug("Cache hit for company news %s %s %d", identifier, item, sequence)
        query_value = IntrinioNewsCache.get_query_value(identifier, page_number)
        if len(query_value["data"]) > page_index:
            if item in query_value["data"][page_index]:
                v =  query_value["data"][page_index][item]
            else:
                v = "Invalid item"
        else:
            v = "Sequence out of range"

        return v

    res = IntrinioNews.get_news_page(identifier, sequence)

    if "data" in res:
        IntrinioNewsCache.add_query_value(res, identifier, page_number)
        # After a successful API call, the usage stats are stale
        UsageDataCache.clear()
        if len(res["data"]) > page_index:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
            else:
                v = "Invalid item"
        else:
            v = "Sequence is out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_fundamentals_data(identifier, statement, period_type, sequence, item):
    """
    Returns a list of available standardized fundamentals (fiscal year and fiscal period)
    for a given ticker and statement.
    :param identifier:
    :param statement:
    :param period_type:
    :param sequence:
    :param item:
    :return:
    """
    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    if FundamentalsCache.is_query_value_cached(identifier, statement, period_type, page_number):
        logger.debug("Cache hit for fundamentals data %s %s %s %d", identifier, statement, period_type, sequence)
        query_value = FundamentalsCache.get_query_value(identifier, statement, period_type, page_number)
        if len(query_value["data"]) > page_index:
            if item in query_value["data"][page_index]:
                v =  query_value["data"][page_index][item]
            else:
                v = "Invalid item: " + item
        else:
            v = "Sequence out of range"
        return v

    res = IntrinioFundamentals.get_fundamentals_page(identifier, statement, period_type, sequence)

    if "data" in res:
        FundamentalsCache.add_query_value(res, identifier, statement, period_type, page_number)
        # After a successful API call, the usage stats are stale
        UsageDataCache.clear()
        if len(res["data"]) > page_index:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
            else:
                v = "Invalid item: " + item
        else:
            v = "Sequence is out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_tags(identifier, statement, sequence, item):
    """
    Returns the standardized tags and labels for a given ticker, statement, and date or fiscal year/fiscal quarter.
    :param identifier: Stock ticker symbol.
    :param statement: income_statement | balance_sheet | cash_flow_statement | calculations | current
    :param sequence: an integer whose value is 0-max available number of results.
    :param item: name | tag | parent | factor | balance | type | units
    :return:
    """
    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    if IntrinioTagsCache.is_query_value_cached(identifier, statement, page_number):
        logger.debug("Cache hit for standardized tags %s %s %s %d", identifier, statement, item, sequence)
        query_value = IntrinioTagsCache.get_query_value(identifier, statement, page_number)
        if len(query_value["data"]) > page_index:
            if item in query_value["data"][page_index]:
                v =  query_value["data"][page_index][item]
            else:
                v = "Invalid item: " + item
        else:
            v = "Sequence out of range"
        return v

    res = IntrinioTags.get_tags_page(identifier, statement, sequence)

    if "data" in res:
        IntrinioTagsCache.add_query_value(res, identifier, statement, page_number)
        # After a successful API call, the usage stats are stale
        UsageDataCache.clear()
        if len(res["data"]) > sequence:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
            else:
                v = "Invalid item: " + item
        else:
            v = "Sequence is out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_financials_data(identifier, statement, fiscal_year, fiscal_period, tag):
    """
    Returns professional-grade historical financial data for a specific data tag.
    :param identifier: Stock ticker symbol.
    :param statement:
    :param fiscal_year:
    :param fiscal_period:
    :param tag:
    :return:
    """
    logger.debug("get_financials_data: %s %s %d %s %s", identifier, statement, fiscal_year, fiscal_period, tag)
    # Translate fiscal year and period if required
    if int(fiscal_year) < 1900:
        # fiscal year is a sequence number and fiscal period is a type
        lookup_fp = fiscal_period
        lookup_fy = int(fiscal_year)
        fiscal_year = get_fundamentals_data(identifier, statement, lookup_fp, lookup_fy, "fiscal_year")
        fiscal_period = get_fundamentals_data(identifier, statement, lookup_fp, lookup_fy, "fiscal_period")
        logger.debug("Translated fy/fp from %d/%s to %d/%s", lookup_fy, lookup_fp, fiscal_year, fiscal_period)

    # Check cache for the specific tag
    if FinancialsDataCache.is_query_value_cached(identifier, statement, fiscal_year, fiscal_period, tag):
        logger.debug("Cache hit for financials data: %s %s %d %s %s",
                     identifier, statement, fiscal_year, fiscal_period, tag)
        v = FinancialsDataCache.get_query_value(identifier, statement, fiscal_year, fiscal_period, tag)
        return v

    # Before calling Intrinio API, check to see if we have already fetched the data for this query
    # If we have run the query, then the requested tag is not defined.
    if FinancialsQueryCache.is_query_value_cached(identifier, statement, fiscal_year, fiscal_period):
        logger.debug("Tag not defined for financials data %s %s %d %s %s",
                     identifier, statement, fiscal_year, fiscal_period, tag)
        v = "na"
        return v


    # We have to read ALL of the pages for the given parameters to get all of the tags available.
    # Essentially, we are building a big cache of all available data.
    total_pages = 1
    current_page = 1
    tag_found = False
    while current_page <= total_pages:
        res = IntrinioFinancials.get_financials_page(identifier, statement, fiscal_year, fiscal_period, current_page)
        # print (res)
        if "total_pages" in res:
            total_pages = int(res["total_pages"])
            logger.debug("Total financials pages: %d", total_pages)
        else:
            # This is an error
            return IntrinioBase.status_code_message(res["status_code"])
        # Cache each tag/value pair in this page
        if "data" not in res:
            logger.debug("Financials page contains no data")
        for tv in res["data"]:
            logger.debug("Adding to financials data cache: %s %s %s %d %s %s", tv["value"],
                   identifier, statement, fiscal_year, fiscal_period, tv["tag"])
            # Note that this overwrites an existing cache entry
            FinancialsDataCache.add_query_value(tv["value"], identifier, statement, fiscal_year, fiscal_period, tv["tag"])
            # After a successful API call, the usage stats are stale
            UsageDataCache.clear()
            # Note when we find the desired tag and its value
            if tv["tag"] == tag:
                tag_found = True
                v = tv["value"]
                logger.debug("Financial tag found: %s=%s", tv["tag"], tv["value"])

        # Mark this query as cached
        FinancialsQueryCache.add_query_value(True, identifier, statement, fiscal_year, fiscal_period)
        logger.debug("Added financials query to cache: %d %s %s %d %s", True, identifier, statement, fiscal_year, fiscal_period)

        # On to the next page
        current_page += 1

    if tag_found:
        return v

    # Prevent another API call for this tag
    FinancialsDataCache.add_query_value("na", identifier, statement, fiscal_year, fiscal_period, tag)
    logger.debug("Adding financials data cache: %s %s %d %s %s %s", "na", identifier, statement, fiscal_year, fiscal_period, tag)
    return "na"


def get_reported_fundamentals_data(identifier, statement, period_type, sequence, item):
    """
    Returns an as reported fundamental.
    :param identifier:
    :param statement:
    :param period_type:
    :param sequence:
    :param item:
    :return:
    """
    logger.debug("get_reported_fundamentals_data: %s %s %s %d %s", identifier, statement, period_type, sequence, item)

    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    if ReportedFundamentalsCache.is_query_value_cached(identifier, statement, period_type, page_number):
        logger.debug("Cache hit for fundamentals data %s %s %s %d %s", identifier, statement, period_type, sequence, item)
        query_value = ReportedFundamentalsCache.get_query_value(identifier, statement, period_type, page_number)
        if len(query_value["data"]) > page_index:
            if item in query_value["data"][page_index]:
                v =  query_value["data"][page_index][item]
            else:
                v = "na"
        else:
            v = "Sequence out of range"
        return v

    res = IntrinioReportedFundamentals.get_fundamentals_page(identifier, statement, period_type, sequence)

    if "data" in res:
        ReportedFundamentalsCache.add_query_value(res, identifier, statement, period_type, page_number)
        # After a successful API call, the usage stats are stale
        UsageDataCache.clear()
        if len(res["data"]) > page_index:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
            else:
                v = "Invalid item: " + item
        else:
            v = "Sequence is out of range"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_reported_tags(identifier, statement, fiscal_year, fiscal_period, sequence, item):
    """
    Returns the As Reported XBRL tags and labels for a given ticker, statement, and date or fiscal year/fiscal quarter.
    :param identifier:
    :param statement:
    :param fiscal_year:
    :param fiscal_period:
    :param sequence:
    :param item:
    :return:
    """
    logger.debug("get_reported_tags: %s %s %d %s %d %s", identifier, statement, fiscal_year, fiscal_period, sequence, item)

    page_number = IntrinioBase.get_page_number(sequence)
    page_index = IntrinioBase.get_page_index(sequence)

    # Translate fiscal year and period if required
    if int(fiscal_year) < 1900:
        # fiscal year is a sequence number and fiscal period is a type
        lookup_fp = fiscal_period
        lookup_fy = int(fiscal_year)
        fiscal_year = get_reported_fundamentals_data(identifier, statement, lookup_fp, lookup_fy, "fiscal_year")
        fiscal_period = get_reported_fundamentals_data(identifier, statement, lookup_fp, lookup_fy, "fiscal_period")

    if ReportedTagsCache.is_query_value_cached(identifier, statement, fiscal_year, fiscal_period, page_number):
        logger.debug("Cache hit for reported tags %s %s %d %s %s %d", identifier, statement, fiscal_year, fiscal_period, item, sequence)
        query_value = ReportedTagsCache.get_query_value(identifier, statement, fiscal_year, fiscal_period, page_number)
        if len(query_value["data"]) > page_index:
            v =  query_value["data"][page_index][item]
        else:
            v = "Sequence out of range"
        # Special case since domain_tag can be None (null)
        if item == "domain_tag" and not v:
            v = ""
        return v

    res = IntrinioReportedTags.get_tags_page(identifier, statement, fiscal_year, fiscal_period, sequence)

    if "data" in res:
        ReportedTagsCache.add_query_value(res, identifier, statement, fiscal_year, fiscal_period, page_number)
        # After a successful API call, the usage stats are stale
        UsageDataCache.clear()
        if len(res["data"]) > sequence:
            if item in res["data"][page_index]:
                v = res["data"][page_index][item]
            else:
                v = "na"
        else:
            v = "Sequence is out of range"
        # Special case since domain_tag can be None (null)
        if item == "domain_tag" and not v:
            v = ""
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def get_reported_financials_data(identifier, statement, fiscal_year, fiscal_period, tag, domain_tag=None):
    """
    Returns professional-grade historical financial data for a specific data tag.
    :param identifier: Stock ticker symbol.
    :param statement:
    :param fiscal_year:
    :param fiscal_period:
    :param tag:
    :return:
    """
    logger.debug("get_reported_financials_data: %s %s %d %s %s %s",
                 identifier, statement, fiscal_year, fiscal_period, tag, domain_tag)
    # Translate fiscal year and period if required
    if int(fiscal_year) < 1900:
        # fiscal year is a sequence number and fiscal period is a type
        lookup_fp = fiscal_period
        lookup_fy = int(fiscal_year)
        fiscal_year = get_reported_fundamentals_data(identifier, statement, lookup_fp, lookup_fy, "fiscal_year")
        fiscal_period = get_reported_fundamentals_data(identifier, statement, lookup_fp, lookup_fy, "fiscal_period")

    # Adapted from Intrinio Excel AddIn. Apparently abstract tags have no value.
    if tag.lower().endswith("abstract") or not tag:
        return ""

    # Check cache for the specific tag
    if ReportedFinancialsCache.is_query_value_cached(identifier, statement, fiscal_year, fiscal_period, tag, domain_tag):
        logger.debug("Cache hit for reported financials data: %s %s %d %s %s %s",
                     identifier, statement, fiscal_year, fiscal_period, tag, domain_tag)
        v = ReportedFinancialsCache.get_query_value(identifier, statement, fiscal_year, fiscal_period, tag, domain_tag)
        return v

    # Before calling Intrinio API, check to see if we have already fetched the data for this query
    # If we have run the query, then the requested tag is not defined.
    if ReportedFinancialsQueryCache.is_query_value_cached(identifier, statement, fiscal_year, fiscal_period):
        logger.debug("Tag not defined for reported financials data %s %s %d %s %s",
                     identifier, statement, fiscal_year, fiscal_period, tag)
        v = "na"
        return v

    # We have to read ALL of the pages for the given parameters to get all of the tags available.
    # Essentially, we are building a big cache of all available data.
    total_pages = 1
    current_page = 1
    tag_found = False
    v = "na"
    while current_page <= total_pages:
        res = IntrinioReportedFinancials.get_financials_page(identifier, statement, fiscal_year, fiscal_period, current_page)
        # print (res)
        if "total_pages" in res:
            total_pages = int(res["total_pages"])
            logger.debug("Total pages: %d", total_pages)
        else:
            # This is an error
            return IntrinioBase.status_code_message(res["status_code"])
        # Cache each tag/value pair in this page
        for tv in res["data"]:
            # Note that this overwrites an existing cache entry
            # If domain_tag key exists, make it part of the cache key
            ReportedFinancialsCache.add_query_value(tv["value"], identifier, statement, fiscal_year, fiscal_period,
                                                    tv["xbrl_tag"], tv["domain_tag"])
            logger.debug("Adding reported financials cache: %s %s %s %d %s %s %s", tv["value"],
                   identifier, statement, fiscal_year, fiscal_period, tv["xbrl_tag"], tv["domain_tag"])
            # After a successful API call, the usage stats are stale
            UsageDataCache.clear()
            # Note when we find the desired tag and its value
            if tv["xbrl_tag"] == tag:
                tag_found = True
                v = tv["value"]

        # Mark this query as cached
        ReportedFinancialsQueryCache.add_query_value(True, identifier, statement, fiscal_year, fiscal_period)

        # On to the next page
        current_page += 1

    # Prevent another API call for this tag
    if not tag_found:
        ReportedFinancialsCache.add_query_value("na", identifier, statement, fiscal_year, fiscal_period, tag)

    return v


#
# Intrinio login dialog
# Adapted from https://forum.openoffice.org/en/forum/viewtopic.php?f=45&t=56397#p248794
#


try:
    import uno
    logger.debug("Attempt to import uno succeeded")
    # logger.debug("sys.path = %s", sys.path)
except Exception as ex:
    logger.error("Attempt to import uno failed %s", str(ex))
try:
    # https://www.openoffice.org/api/docs/common/ref/com/sun/star/awt/PosSize.html
    from com.sun.star.awt.PosSize import POSSIZE # flags the x- and y-coordinate, width and height
    logger.debug("Attempt to import com.sun.star.awt.PosSize succeeded")
except Exception as ex:
    logger.error("Attempt to import com.sun.star.awt.PosSize failed %s", str(ex))


def _add_awt_model(dlg_model, srv, ctl_name, prop_list):
    """
    Helper function for building dialog
    Insert UnoControl<srv>Model into given DialogControlModel
    :param dlg_model: dialog model where control is to be added
    :param srv: control model type to be added
    :param ctl_name: name to be assigned to the control model
    :param prop_list: properties to be assigned to new control model
    :return: None
    """
    ctl_model = dlg_model.createInstance("com.sun.star.awt.UnoControl" + srv + "Model")
    while prop_list:
        prp = prop_list.popitem()
        uno.invoke(ctl_model,"setPropertyValue",(prp[0],prp[1]))
        #works with awt.UnoControlDialogElement only:
        ctl_model.Name = ctl_name
    dlg_model.insertByName(ctl_name, ctl_model)


def intrinio_login():
    """
    Ask user for Intrinio login credentials
    :return: If successful, returns username and password as a tuple (something truthy)
    If canceled, returns False.
    """
    # Reference: https://www.openoffice.org/api/docs/common/ref/com/sun/star/awt/module-ix.html
    global logger

    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager
    dlg_model = smgr.createInstance("com.sun.star.awt.UnoControlDialogModel")
    dlg_model.Title = 'Enter Intrinio Access Keys'

    _add_awt_model(dlg_model, 'FixedText', 'lblName', {
        'Label': 'User Name',
    }
                   )
    _add_awt_model(dlg_model, 'Edit', 'txtName', {})

    _add_awt_model(dlg_model, 'FixedText', 'lblPWD', {
        'Label': 'Password',
    }
                   )
    _add_awt_model(dlg_model, 'Edit', 'txtPWD', {
        'EchoChar': 42,
    }
                   )

    _add_awt_model(dlg_model, 'CheckBox', 'cbDoNotAsk', {
        'Label': 'Do not ask again',
    }
                   )

    _add_awt_model(dlg_model, 'Button', 'btnOK', {
        'Label': 'Save',
        'DefaultButton': True,
        'PushButtonType': 1,
    }
                   )
    _add_awt_model(dlg_model, 'Button', 'btnCancel', {
        'Label': 'Cancel',
        'PushButtonType': 2,
    }
                   )

    lmargin = 10  # left margin
    rmargin = 10  # right margin
    tmargin = 10  # top margin
    bmargin = 10  # bottom margin
    cheight = 25  # control height
    pad = 5  # top/bottom padding where needed
    theight = cheight + pad  # total height of a control

    # Poor man's grid
    # layout "control-name", [x, y, w, h]
    layout = {
        "lblName": [lmargin, tmargin, 100, cheight],
        "txtName": [lmargin + 100, tmargin, 250, cheight],
        "lblPWD": [lmargin, tmargin + (theight * 1), 100, cheight],
        "txtPWD": [lmargin + 100, tmargin + (theight * 1), 250, cheight],
        "cbDoNotAsk": [lmargin + 100, tmargin + (theight * 2), 200, cheight],
        "btnOK": [lmargin + 100, tmargin + (theight * 3), 100, cheight],
        "btnCancel": [lmargin + 200, tmargin + (theight * 3), 100, cheight]
    }

    dialog = smgr.createInstance("com.sun.star.awt.UnoControlDialog")
    dialog.setModel(dlg_model)
    name_ctl = dialog.getControl('txtName')
    pass_ctl = dialog.getControl('txtPWD')
    do_not_ask_ctl = dialog.getControl("cbDoNotAsk")

    # Apply layout to controls. Must be done within the dialog.
    for name, d in layout.items():
        ctl = dialog.getControl(name)
        ctl.setPosSize(d[0], d[1], d[2], d[3], POSSIZE)

    dialog.setPosSize(300, 300, lmargin + rmargin + 100 + 250, tmargin + bmargin + (theight * 4), POSSIZE)
    dialog.setVisible(True)

    # Run the dialog. Returns the value of the PushButtonType.
    # 1 = save
    # 2 = cancel
    button_id = dialog.execute()
    logger.debug("intrinio login dialog returned: %s", button_id)
    if button_id == 1:
        return (True, name_ctl.getText(), pass_ctl.getText())
    else:
        return (False, do_not_ask_ctl.getState())
