# LibreOffice Calc Extension for Intrinio Marketplace
Copyright © 2017 by Dave Hocker as Qalydon

## Overview
This project implements a LibreOffice Calc (LOCalc) addin extension that can
retrieve data from the Intrinio Marketplace service. It provides a
subset of the functions implemented by the
[Intrinio Excel AddIn](https://github.com/intrinio/intrinio-excel).
Currently, only functions that will work with a basic, free Intrinio
account have been implemented. In the future, the function set may be
expanded to provide parity with the Intrinio Excel AddIn.

The addin works on the Windows, macOS and Ubuntu versions of
[LibreOffice (version >= 5.0)](https://www.libreoffice.org/).

## License
GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. Refer to the
[LICENSE.md](https://github.com/dhocker/intrinio-localc/blob/master/README.md)
file for complete details.

## Installation
1. Download the latest intrinio.oxt (the add-in file) from
[here](https://github.com/qalydon/intrinio-localc/releases).
1. Start LibreOffice or LibreOffice Calc.
1. From the Tools menu, open the Extension Manager.
1. Look through the list of installed add-ins for Intrinio Fintech
Marketplace. If you find it, click the Remove button to remove it.
For best results, **remove an existing Intrinio Fintech Markeplace
add-in first**.
1. Click the Add button.
1. Navigate to the location where you downloaded intrinio.oxt. Select
it.
1. Choose if you want the add-in installed for you or everyone.
1. Click the Close button.
1. If LibreOffice asks to restart, do so.

It is recommended that you always remove an existing version of the
add-in before installing an update. Othwerwise, your results may be
unpredictable.

## Example Files
You can find a number of example files in the examples folder. The
examples are mostly LO conversions/derivatives of template files from the
[Intrinio Excel AddIn.](https://github.com/intrinio/intrinio-excel)
These files show you how most of the LOCalc Extension functions
can be used.

## LOCalc Functions
The addin provides a number of functions for retrieving data from
the Intrinio Marketplace service. To the degree possible, these functions
work like the similarly named
[Intrinio Excel Addin functions](http://docs.intrinio.com/excel-addin#intrinio-excel-functions).

### IntrinoUsage
Use IntrinioUsage to retrieve information about how much of the Intrinio
service you have used.
```
=IntrinioUsage(access_code, item)
```
[access_code list](http://docs.intrinio.com/?javascript--api#usage): The com_fin_data
access_code covers most of the basic, free Intrinio service.

item: current | percent | limit | status_code

### IntrinioDataPoint
This function works like the equivalent
[IntrinioDataPoint](http://docs.intrinio.com/excel-addin#intriniodatapoint)
Excel AddIn function.
```
=IntrinioDataPoint(identifier, item)
```

### IntrinioHistoricalPrices
This function works like the equivalent
[IntrinioHistoricalPrices](http://docs.intrinio.com/excel-addin#intriniohistoricalprices)
Excel AddIn function.
```
=IntrinioHistoricalPrices(ticker, item, sequence, start_date, end_date, frequency)
```

### IntrinioHistoricalData
This function works like the equivalent
[IntrinioHistoricalDate](http://docs.intrinio.com/excel-addin#intriniohistoricaldata)
Excel AddIn function.
```
=IntrinioHistoricalData(ticker, item, sequence, start_date, end_date, frequency, data_type)
```

### IntrinioNews
This function works like the equivalent
[IntrinioNews](http://docs.intrinio.com/excel-addin#intrinionews)
Excel AddIn function.
```
=IntrinioNews(identifier, item, sequence)
```

### IntrinioFundamentals
This function works like the equivalent
[IntrinioFundamentals](http://docs.intrinio.com/excel-addin#intriniofundamentals)
Excel AddIn function.
```
=IntrinioFundamentals(identifier, statement, type, sequence, item)
```

### IntrinioTags
This function works like the equivalent
[IntrinioTags](http://docs.intrinio.com/excel-addin#intriniotags)
Excel AddIn function.
```
=IntrinioTags(identifier, statement, sequence, item)
```

### IntrinioFinancials
This function works like the equivalent
[IntrinioFinancials](http://docs.intrinio.com/?javascript--api#standardized-financials)
Excel AddIn function.
```
=IntrinioFinancials(identifier, statement, fiscal_year, fiscal_period, tag, rounding)
OR
=IntrinioFinancials(identifier, statement, sequence, type, tag, rounding)
```
Some explanation is in order as the Intrinio documentation does not really clarify
exactly how the parameters work.

The IntrinioFinancials function starts by assuming that the first form
is being used. However, if the fiscal_year parameter is a value
less than 1900, the value is treated as a sequence number. This
implies that the second form is being used.

In this case, the sequence and type parameters are translated to
a fiscal_year and fiscal_period value by using the IntrinioFundamentals
function.
```
fiscal_year = IntrinioFundamentals(ticker, statement, type, sequence, "fiscal_year")
fiscal_period = IntrinioFundamentals(ticker, statement, type, sequence, "fiscal_period")
```
Essentially, this maps the sequence parameter to a year in an inverse order.
Sequence value 0 will correspond to the most recent fundamental while
value 1 will be back one increment. For example, if the type value is "FY",
then the sequence number will be the relative fiscal year.

### IntrinioReportedFundamentals
This function works like the equivalent
[IntrinioReportedFundamentals](http://docs.intrinio.com/excel-addin#intrinioreportedfundamentals)
Excel AddIn function.
```
=IntrinioReportedFundamentals(identifier, statement, type, sequence, item)
```

### IntrinioReportedTags
This function works like the equivalent
[IntrinioReportedTags](http://docs.intrinio.com/excel-addin#intrinioreportedtags)
Excel AddIn function.
```
=IntrinioReportedTags(identifier, statement, sequence, item)
```

### IntrinioReportedFinancials
This function works like the equivalent
[IntrinioReportedFinancials](http://docs.intrinio.com/excel-addin#intrinioreportedfinancials)
Excel AddIn function.
```
=IntrinioReportedFinancials(identifier, statement, fiscal_year, fiscal_period, xbrl_tag, domain_tag)
OR
=IntrinioFinancials(identifier, statement, sequence, type, xbrl_tag, domain_tag)
```
Some explanation is in order as the Intrinio documentation does not really clarify
exactly how the parameters work.

The IntrinioReportedFinancials function starts by assuming that the first form
is being used. However, if the fiscal_year parameter is a value
less than 1900, the value is treated as a sequence number. This
implies that the second form is being used.

In this case, the sequence and type parameters are translated to
a fiscal_year and fiscal_period value by using the IntrinioReportedFundamentals
function.
```
fiscal_year = IntrinioReportedFundamentals(identifier, statement, type, sequence, "fiscal_year")
fiscal_period = IntrinioReportedFundamentals(identifier, statement, type, sequence, "fiscal_period")
```
Essentially, this maps the sequence parameter to a year in an inverse order.
Sequence value 0 will correspond to the most recent fundamental while
value 1 will be back one increment. For example, if the type value is "FY",
then the sequence number will be the relative fiscal year.

## References
* [Intrinio Web Site](https://intrinio.com)
* [Intrinio Excel AddIn](http://docs.intrinio.com/excel-addin#intrinionews)
* [LibreOffice Web Site](https://www.libreoffice.org/)