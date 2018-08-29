#! /usr/local/bin/python3
#
# Package extension files into an .oxt file
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
# References
# https://wiki.openoffice.org/wiki/Calc/Add-In/Python_How-To
# http://www.biochemfusion.com/doc/Calc_addin_howto.html
# https://github.com/madsailor/SMF-Extension
#

import os
import sys
import subprocess
import shutil
from xcu_file import XCUFile
import xml.etree.ElementTree as etree

# Set up environment vars
if sys.platform == 'darwin':
    # macOS
    os.environ["PATH"] = os.environ["PATH"] + ":/usr/lib/ure/bin/"
    # os.environ["PATH"] = os.environ["PATH"] + ":/Users/dhocker/LibreOffice5.4_SDK/bin"
    os.environ["PATH"] = os.environ["PATH"] + ":" + os.environ["OO_SDK_HOME"] + "/bin"
    os.environ["DYLD_LIBRARY_PATH"] = os.environ["OO_SDK_URE_LIB_DIR"]
elif sys.platform == 'win32':
    # Windows
    # Nothing special requited beyond running setsdkenv_windows.bat
    pass
else:
    print ("Platform {0} is not supported by this build script".format(sys.platform))
    exit(1)
#subprocess.call("env")
#print (os.environ["DYLD_LIBRARY_PATH"])

# Extract version from description.xml
tree = etree.parse("src/description.xml")
root = tree.getroot()
nodes = root.findall('{http://openoffice.org/extensions/description/2006}version')
build_version = nodes[0].attrib["value"]
print ("=============================")
print ("Building Version:", build_version)
print ("=============================")

# Clean build folder
print ("Cleaning build folder")
if os.path.exists("build"):
    shutil.rmtree("build")

# Create required build folders
if not os.path.exists("build"):
    print ("Creating new build folder")
    os.mkdir("build")
if not os.path.exists("build/META-INF"):
    print ("Creating build/META-INF folder")
    os.mkdir("build/META-INF")

# Compile idl
subprocess.run(["idlc", "-w", "idl/xintrinio.idl"], stdout=sys.stdout, stderr=sys.stderr)
subprocess.run(["regmerge", "-v", "build/xintrinio.rdb", "UCR", "idl/xintrinio.urd"])
os.remove("idl/xintrinio.urd")

# Copy all required files to build folder
print ("Copying files to build folder")
shutil.copy("src/manifest.xml", "build/META-INF/")
shutil.copy("src/description-en-US.txt", "build/")
shutil.copy("src/description.xml", "build/")
shutil.copy("src/intrinio_impl.py", "build/")
shutil.copy("src/intrinio_app_logger.py", "build/")
shutil.copy("src/intrinio_lib.py", "build/")
shutil.copy("src/intrinio_cache.py", "build/")
shutil.copy("src/intrinio_access.py", "build/")
shutil.copy("src/intrinio_indices.py", "build/")
shutil.copy("src/intrinio_companies.py", "build/")
shutil.copy("src/intrinio_securities.py", "build/")
shutil.copy("src/intrinio_company_sec_filings.py", "build/")
shutil.copy("src/extn_helper.py", "build/")
shutil.copy("certifi/cacert.pem", "build/")

# Generate the XCU file
print ("Generating intrinio.xcu")
xcu = XCUFile("com.intrinio.fintech.localc.python.IntrinioImpl", "XIntrinio")
#
# Note: DO NOT use underscores in parameter names. LO does not accept them.
#
xcu.add_function("IntrinioUsage", "Get Intrinio usage satistics",
                 [
                     ('a', 'The access code ID.'),
                     ('b', 'The statistic key name.')
                 ])
xcu.add_function("IntrinioDataPoint", "Get Intrinio data point",
                 [
                     ('identifier', 'Identifier (e.g. ticker symbol).'),
                     ('item', 'item (e.g. tag or series id).')
                 ])
xcu.add_function("IntrinioHistoricalPrices", "Get Intrinio historical price data",
                 [
                     ('ticker', 'Ticker symbol.'),
                     ('item', 'The selected observation of the historical price (e.g. open, close, etc.).'),
                     ('sequencenumber', 'An integer, 0-last available data point.'),
                     ('startdate', 'Optional, first date of prices.'),
                     ('enddate', 'Optional, last date of prices.'),
                     ('frequency', 'Periodicity of data points (e.g. daily, weekly, monthly, quarterly, yearly).')
                 ])
xcu.add_function("IntrinioHistoricalData", "Get the historical data for a selected identifier",
                 [
                     ('identifier', 'Ticker symbol.'),
                     ('item', 'The specified standardized tag requested'),
                     ('sequencenumber', 'An integer, 0-last available data point'),
                     ('startdate', 'Optional, first date of data'),
                     ('enddate', 'Optional, last date of data'),
                     ('frequency', 'Periodicity of data points (e.g. daily, weekly, monthly, quarterly, yearly).'),
                     ('periodtype', 'The type of periods requested (e.g. FY, QTR, TTM, YTD  or count, sum, max, 75thpctl, mean, median, 25thpctl, min'),
                     ('showdate', 'Show date (True) or show data (false, default).')
                 ])
xcu.add_function("IntrinioNews", "Get news for the selected identifier",
                 [
                     ('identifier', 'Ticker symbol.'),
                     ('item', 'News attribute: title, publicationdate, summary, url'),
                     ('sequencenumber', 'An integer, 0-last available data point')
                 ])
xcu.add_function("IntrinioFundamentals", "Returns a list of available standardized fundamentals",
                 [
                     ('ticker', 'Ticker symbol.'),
                     ('statement', 'The financial statement requested (e.g.incomestatement, balancesheet, cashflowstatement, calculations)'),
                     ('periodtype', 'The type of periods requested (e.g. FY, QTR, TTM, YTD)'),
                     ('sequencenumber', 'An integer, 0-last available data point'),
                     ('item', 'The return value for the fundamental (e.g. fiscalyear, fiscalperiod, enddate, startdate)')
                 ])
xcu.add_function("IntrinioTags", "Returns the standardized tags and labels for a given ticker, statement, and date or fiscal year/fiscal quarter.",
                 [
                     ('identifier', 'Ticker symbol.'),
                     ('statement', 'The financial statement requested (e.g. incomestatement, balancesheet, cashflowstatement, calculations, current)'),
                     ('sequencenumber', 'An integer, 0-last available data point'),
                     ('item', 'The return value for the tag (e.g. name, tag, parent, factor, balance, type, units')
                 ])
xcu.add_function("IntrinioFinancials", "Returns professional-grade historical financial data.",
                 [
                     ('ticker', 'The stock market ticker symbol.'),
                     ('statement',
                      'The financial statement requested (e.g.incomestatement, balancesheet, cashflowstatement, calculations)'),
                     ('fiscalyear', 'the fiscal year associated with the fundamental OR the sequence of the requested fundamental'),
                     ('fiscalperiod', 'the fiscal period associated with the fundamental, or the fiscal period type'),
                     ('tag', 'The specified standardized tag'),
                     ('rounding', 'Round the returned value (e.g. A, K, M, B)')
                 ])
xcu.add_function("IntrinioReportedFundamentals", "Returns a list of available as reported fundamentals",
                 [
                     ('ticker', 'Ticker symbol.'),
                     ('statement', 'The financial statement requested (e.g.incomestatement, balancesheet, cashflowstatement)'),
                     ('periodtype', 'The type of periods requested (e.g. FY, QTR)'),
                     ('sequencenumber', 'An integer, 0-last available data point'),
                     ('item', 'The return value for the fundamental (e.g. fiscalyear, fiscalperiod, enddate, startdate, filingdate)')
                 ])
xcu.add_function("IntrinioReportedTags", "Returns the as reported XBRL tags and labels for a given ticker, statement, and date or fiscal year/fiscal quarter.",
                 [
                     ('identifier', 'Ticker symbol.'),
                     ('statement', 'The financial statement requested (e.g. incomestatement, balancesheet, cashflowstatement)'),
                     ('sequencenumber', 'An integer, 0-last available data point'),
                     ('item', 'The return value for the tag (e.g. name, tag, balance, unit, domaintag, abstract, sequence, depth, factor)')
                 ])
xcu.add_function("IntrinioReportedFinancials", "Returns the As Reported Financials directly from the financial statements of the XBRL filings from the company.",
                 [
                     ('identifier', 'The stock market ticker symbol.'),
                     ('statement',
                      'The financial statement requested (e.g.incomestatement, balancesheet, cashflowstatement)'),
                     ('fiscalyear', 'the fiscal year associated with the fundamental OR the sequence of the requested fundamental'),
                     ('fiscalperiod', 'the fiscal period associated with the fundamental, or the fiscal period type'),
                     ('xbrltag', 'The specified XBRL tag'),
                     ('domaintag', 'The specified domain XBRL tag')
                 ])
xcu.add_function("IntrinioBankFundamentals", "Returns a list of available standardized fundamentals",
                 [
                     ('identifier', 'Ticker symbol.'),
                     ('statement', 'The Call Report/UBPR/Y-9C financial statement requested'),
                     ('periodtype', 'The type of periods requested (e.g. FY, QTR)'),
                     ('sequencenumber', 'An integer, 0-last available data point'),
                     ('item', 'The return value for the fundamental (e.g. statementcode, enddate, startdate, months, fiscalyear, fiscalperiod, report)')
                 ])
xcu.add_function("IntrinioBankTags", "Returns the Bank Call Report or UBPR Report XBRL tags and labels",
                 [
                     ('identifier', 'Ticker symbol.'),
                     ('statement', 'The Call Report/UBPR/Y-9C financial statement requested'),
                     ('sequencenumber', 'An integer, 0-last available data point'),
                     ('item', 'The return value for the tag (e.g. name, tag, unit, sequence, depth, abstract)')
                 ])
xcu.add_function("IntrinioBankFinancials", "Returns professional-grade historical financial data for bank and bank holding companies",
                 [
                     ('identifier', 'The stock market ticker symbol.'),
                     ('statement',
                      'The Call Report/UBPR/Y-9C financial statement requested'),
                     ('fiscalyear', 'The fiscal year associated with the fundamental OR the sequence of the requested fundamental'),
                     ('fiscalperiod', 'The fiscal period associated with the fundamental, or the fiscal period type'),
                     ('tag', 'The specified Call Report/UBPR/Y-9C XBRL Tag requested'),
                     ('rounding', 'Round the returned value (e.g. A, K, M, B)')
                 ])

xcu.add_function("IntrinioIndicesQuery", "Returns indices information for all indices covered by Intrinio.",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('indextype', 'The type of indices specified (e.g. stock_market)'),
                     ('sequencenumber', 'An integer, 0-last available index'),
                     ('item', 'The name of the item/tag to be returned')
                 ])
xcu.add_function("IntrinioIndicesQueryCount", "Returns the result count for an indices query.",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('indextype', 'The type of indices specified (e.g. stock_market)')
                 ])
xcu.add_function("IntrinioIndicesQueryTagCount", "Returns the number of items available for an indeces query",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('indextype', 'The type of indices specified (e.g. stock_market)')
                 ])
xcu.add_function("IntrinioIndicesQueryTag", "Returns an item/tag name for a queried index.",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('indextype', 'The type of indices specified (e.g. stock_market)'),
                     ('sequencenumber', 'An integer, 0-last available item/tag')
                 ])
xcu.add_function("IntrinioIndex", "Returns indices information for a specific index covered by Intrinio.",
                 [
                     ('identifier', 'The Intrinio symbol associated with the index.'),
                     ('item', 'The name of the item/tag to be returned')
                 ])
xcu.add_function("IntrinioIndexTagCount", "Returns the number of items available for an index",
                 [
                     ('identifier', 'The Intrinio symbol associated with the index.')
                 ])
xcu.add_function("IntrinioIndexTag", "Returns an item/tag name for an index.",
                 [
                     ('identifier', 'The Intrinio symbol associated with the index.'),
                     ('sequencenumber', 'An integer, 0-last available item/tag')
                 ])

xcu.add_function("IntrinioCompaniesQuery", "Returns company list and information for all companies covered by Intrinio.",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('latestfilingdate', 'A date value that returns the list of companies whose latest SEC filing was filed on or after this date'),
                     ('sequencenumber', 'An integer, 0-last available index'),
                     ('item', 'The name of the item/tag to be returned')
                 ])
xcu.add_function("IntrinioCompaniesQueryCount", "Returns the result count for a companies query.",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('latestfilingdate', 'A date value that returns the list of companies whose latest SEC filing was filed on or after this date')
                 ])
xcu.add_function("IntrinioCompaniesQueryTagCount", "Returns the number of items available for a companies query",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('latestfilingdate', 'A date value that returns the list of companies whose latest SEC filing was filed on or after this date')
                 ])
xcu.add_function("IntrinioCompaniesQueryTag", "Returns an item/tag name for a queried company.",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('latestfilingdate', 'A date value that returns the list of companies whose latest SEC filing was filed on or after this date'),
                     ('sequencenumber', 'An integer, 0-last available item/tag')
                 ])
xcu.add_function("IntrinioCompany", "Returns company information.",
                 [
                     ('identifier', 'The stock market ticker symbol.'),
                     ('item', 'The name of the item/tag to be returned')
                 ])
xcu.add_function("IntrinioCompanyTagCount", "Returns the number of items available for a company",
                 [
                     ('identifier', 'The stock market ticker symbol.')
                 ])
xcu.add_function("IntrinioCompanyTag", "Returns an item/tag name for a company.",
                 [
                     ('identifier', 'The stock market ticker symbol.'),
                     ('sequencenumber', 'An integer, 0-last available item/tag')
                 ])

xcu.add_function("IntrinioSecuritiesQuery", "Returns company list and information for securities covered by Intrinio.",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('exchangesymbol', 'The Intrinio Stock Market Symbol, to specify the exchange for the list of securities'),
                     ('lastcrspadjdate', 'A date value that returns the list of securities that have had adjusted stock prices due to a corporate event after this date'),
                     ('sequencenumber', 'An integer, 0-last available index'),
                     ('item', 'The name of the item/tag to be returned')
                 ])
xcu.add_function("IntrinioSecuritiesQueryCount", "Returns the result count for a companies query.",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('exchangesymbol', 'The Intrinio Stock Market Symbol, to specify the exchange for the list of securities'),
                     ('lastcrspadjdate', 'A date value that returns the list of securities that have had adjusted stock prices due to a corporate event after this date')
                 ])
xcu.add_function("IntrinioSecuritiesQueryTagCount", "Returns the number of items available for a companies query",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('exchangesymbol', 'The Intrinio Stock Market Symbol, to specify the exchange for the list of securities'),
                     ('lastcrspadjdate', 'A date value that returns the list of securities that have had adjusted stock prices due to a corporate event after this date')
                 ])
xcu.add_function("IntrinioSecuritiesQueryTag", "Returns an item/tag name for a queried company.",
                 [
                     ('query', 'The stock market ticker symbol.'),
                     ('exchangesymbol', 'The Intrinio Stock Market Symbol, to specify the exchange for the list of securities'),
                     ('lastcrspadjdate', 'A date value that returns the list of securities that have had adjusted stock prices due to a corporate event after this date'),
                     ('sequencenumber', 'An integer, 0-last available item/tag')
                 ])
xcu.add_function("IntrinioSecurity", "Returns security information.",
                 [
                     ('identifier', 'The stock market ticker symbol.'),
                     ('item', 'The name of the item/tag to be returned')
                 ])
xcu.add_function("IntrinioSecurityTagCount", "Returns the number of items available for a security",
                 [
                     ('identifier', 'The stock market ticker symbol.')
                 ])
xcu.add_function("IntrinioSecurityTag", "Returns an item/tag name for a security.",
                 [
                     ('identifier', 'The stock market ticker symbol.'),
                     ('sequencenumber', 'An integer, 0-last available item/tag')
                 ])
xcu.add_function("IntrinioCompanySECFilings", "Returns information about SEC filings for a company.",
                 [
                     ('identifier', 'The stock market ticker symbol.'),
                     ('reporttype', 'See https://en.wikipedia.org/wiki/SEC_filing#All_filing_types'),
                     ('startdate', 'The starting date for SEC filings'),
                     ('enddate', 'The ending date for SEC filings'),
                     ('sequencenumber', 'An integer, 0-last available filing'),
                     ('item', 'The name of the item/tag to be returned')
                 ])
xcu.add_function("IntrinioCompanySECFilingsCount", "Returns the result count for SEC filings.",
                 [
                     ('identifier', 'The stock market ticker symbol.'),
                     ('reporttype', 'See https://en.wikipedia.org/wiki/SEC_filing#All_filing_types'),
                     ('startdate', 'The starting date for SEC filings'),
                     ('enddate', 'The ending date for SEC filings')
                 ])
xcu.add_function("IntrinioCompanySECFilingsTagCount", "Returns the number of tags that are available for a filing",
                 [
                 ])
xcu.add_function("IntrinioCompanySECFilingsTag", "Returns an item/tag name for a company filing.",
                 [
                     ('sequencenumber', 'An integer, 0-last available item/tag')
                 ])

xcu.generate("build/intrinio.xcu")
xcu.dump_functions()

# Zip contents of build folder and rename it to .oxt
print ("Zipping build files into intrinio.oxt file")
os.chdir("build/")
for f in os.listdir("./"):
    if os.path.isfile(f) or os.path.isdir(f):
        subprocess.run(["zip", "-r", "intrinio.zip", f])
os.chdir("..")
shutil.move("build/intrinio.zip", "intrinio.oxt")
print ("Extension file intrinio.oxt created")

print ("============================================")
print ("Build complete for version:", build_version)
print ("============================================")
