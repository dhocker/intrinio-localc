#
# Intrinio Indicies
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


class IntrinioIndices(IntrinioBase):
    def __init__(self):
        pass

    @staticmethod
    def get_indices_page(query, index_type, sequence):
        page_number = IntrinioIndices.get_page_number(sequence)

        template_url = "{0}/indices?page_size={1}&page_number={2}"
        url_string = template_url.format(QConfiguration.base_url, IntrinioIndices.page_size, page_number)
        if query:
            url_string += "&query=" + query
        if index_type:
            url_string += "&type=" + index_type

        # print (url_string)
        res = IntrinioIndices.exec_request(url_string)
        # print (res)
        return res

    @staticmethod
    def get_index_by_identifier(identifier):
        template_url = "{0}/indices?identifier={1}"
        url_string = template_url.format(QConfiguration.base_url, identifier)

        # print (url_string)
        res = IntrinioIndices.exec_request(url_string)
        # print (res)
        return res


class IndicesQueryCache:
    """
    Used to track news queries
    """
    # The key is a compound value consisting of the ticker, statement and page number.
    query_values = {}

    def __init__(self):
        pass

    @staticmethod
    def _query_key(query, index_type, page_number):
        return query + "_" + index_type + "_" + str(page_number)

    @classmethod
    def is_query_value_cached(cls, query, index_type, page_number):
        key = cls._query_key(query, index_type, page_number)
        return key in cls.query_values

    @classmethod
    def get_query_value(cls, query, index_type, page_number):
        key = cls._query_key(query, index_type, page_number)
        # This returns the entire API call result (which can be a large dict)
        return cls.query_values[key]

    @classmethod
    def add_query_value(cls, query_value, query, index_type, page_number):
        key = cls._query_key(query, index_type, page_number)
        cls.query_values[key] = query_value


class IndexCache:
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


def get_indices_by_query(query, index_type, sequence, item):
    logger.debug("get_indices_by_query: %s %s %d %s", query, index_type, sequence, item)

    page_index = IntrinioBase.get_page_index(sequence)

    res = __get_indices(query, index_type, sequence)

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


def __get_indices(query, index_type, sequence):
    page_number = IntrinioBase.get_page_number(sequence)

    if IndicesQueryCache.is_query_value_cached(query, index_type, page_number):
        logger.debug("Cache hit for __get indices %s %s %d", query, index_type, page_number)
        query_value = IndicesQueryCache.get_query_value(query, index_type, page_number)
    else:
        query_value = IntrinioIndices.get_indices_page(query, index_type, sequence)
        if "data" in query_value:
            IndicesQueryCache.add_query_value(query_value, query, index_type, page_number)
    return query_value


def get_indices_by_query_count(query, index_type):
    """
    Get the result count for a given query. Intrinio does not support a
    large number of indices (at the time of development 8). Currently,
    this is a zero-cost query.
    :param query:
    :param index_type:
    :return:
    """
    logger.debug("get_indices_by_query_count: %s %s", query, index_type)

    res = __get_indices(query, index_type, 0)

    if "result_count" in res:
        return res["result_count"]

    return IntrinioBase.status_code_message(res["status_code"])


def get_indices_by_query_tag_count(query, index_type):
    tags = get_indices_items(query, index_type)
    return len(tags)


def get_indices_by_query_tag(query, index_type, sequence):
    tags = get_indices_items(query, index_type)
    if sequence in range(len(tags)):
        t = tags[sequence]
    else:
        t = ""
    return t


def get_index_by_identifier(identifier, item):
    """
    Return a data item for a given index identifier.
    :param identifier:
    :param item:
    :return:
    """
    logger.debug("get_index_by_identifier: %s %s", identifier, item)

    res = __get_index(identifier)

    if res:
        if item in res:
            v = res[item]
        else:
            v = "na"
        return v

    return IntrinioBase.status_code_message(res["status_code"])


def __get_index(identifier):
    if IndexCache.is_query_value_cached(identifier):
        logger.debug("Cache hit for __get index by identifier %s", identifier)
        query_value = IndexCache.get_query_value(identifier)
    else:
        query_value = IntrinioIndices.get_index_by_identifier(identifier)
        if query_value:
            IndexCache.add_query_value(query_value, identifier)
    return query_value


def get_index_by_identifier_tag_count():
    tags = get_index_items()
    return len(tags)


def get_index_by_identifier_tag(sequence):
    tags = get_index_items()
    if sequence in range(len(tags)):
        t = tags[sequence]
    else:
        t = ""
    return t


def get_indices_items(query, index_type):
    """
    The list of tags/items returned by  an indecies query
    :return:
    """
    # Get the first index and use its keys for the items
    # Note that the available tags varies with query and index_type
    res = __get_indices(query, index_type, 0)
    if "data" in res and len(res["data"]) > 0:
        sample = res["data"][0]
        items = list(sample.keys())
    else:
        items = []
    # for i in items:
    #     print (i)
    return items


def get_index_items():
    """
    The list of tags/items returned by an index identifier query
    :return:
    """
    # Use S&P 500 as the benchmark for tags
    sample = __get_index("$SPX")
    if "status_code" in sample:
        del sample["status_code"]
    return list(sample.keys())

#####################################

def test_query():
    print ()
    print ("Intrinio Indicies")
    print ()

    # type is stock_market, economic or sector
    index_type = "stock_market"
    #index_type = "sector"
    # query is a case insensitive text substring matched against the index_name field
    # *query*
    query = ""
    indicies = []

    item_count = get_indices_by_query_tag_count(query, index_type)
    items = []
    print ("Available tags:", item_count)
    for i in range(item_count):
        item = get_indices_by_query_tag(query, index_type, i)
        items.append(item)
        print ("  ", item)

    result_count = get_indices_by_query_count(query, index_type)
    print ("result count:", result_count)
    if result_count > 100:
        result_count = 100

    # Basically testing code
    print ("All indicies")
    for s in range (0, result_count):
        print (s)
        for i in items:
            r = get_indices_by_query(query, index_type, s, i)
            print("  ", i, ":", r)
            # Accumulate list of indices found
            if i == "symbol":
                indicies.append(r)


def test_indentifier():
    indicies = ["$SPX", "$SSEC"]
    item_count = get_index_by_identifier_tag_count()
    items = []
    for i in range(item_count):
        items.append(get_index_by_identifier_tag(i))

    print ("Individual index list")
    for index in indicies:
        print (index)
        for item in items:
            r = get_index_by_identifier(index, item)
            print("  ", item, ":", r)


if __name__ == '__main__':
    # test_query()
    test_indentifier()