# LibreOffice Calc Extension for Intrinio Marketplace
Copyright © 2017 by Dave Hocker as TheAgency

## Overview
This project implements a LibreOffice Calc (LOCalc) addin extension that can
retrieve data from the Intrinio Marketplace service. It provides a
subset of the functions implemented by the
[Intrinio Excel AddIn](https://github.com/intrinio/intrinio-excel).
Currently, only functions that will work with a basic, free Intrinio
account have been implemented. In the future, the function set may be
expanded to provide parity with the Intrinio Excel AddIn.

The addin should work on the Windows, macOS and Ubuntu versions of
[LibreOffice (version >= 5.0)](https://www.libreoffice.org/).

## License
GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. Refer to the
[LICENSE.md](https://github.com/dhocker/intrinio-localc/blob/master/README.md)
file for complete details.


## LOCalc Functions
The addin provides a number of functions for retrieving data from
the Intrinio Marketplace service. To the degree possible, these functions
work like the similarly named Intrinio Excel Addin functions.

### IntrinoUsage
Use IntrinioUsage to retrieve information about how much of the Intrinio
service you have used.
```
=IntrinioUsage(access_code, item)
```
[access_code list](http://docs.intrinio.com/?javascript--api#usage)

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
Some expalnation is in order as the Intrinio documentation does not really clarify
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

## References
* [Intrinio Web Site](https://intrinio.com)
* [Intrinio Excel AddIn](http://docs.intrinio.com/excel-addin#intrinionews)
* [LibreOffice Web Site](https://www.libreoffice.org/)