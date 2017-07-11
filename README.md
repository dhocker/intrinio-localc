# LibreOffice Calc Extension for Intrinio Marketplace
Copyright © 2017 by Dave Hocker

## Overview
This project implements a LibreOffice Calc (LOCalc) addin extension that can
retrieve data from the Intrinio Marketplace service. It provides a
similar set of functions as the
[Intrinio Excel AddIn](https://github.com/intrinio/intrinio-excel).

The addin should work on the Windows, macOS and Ubuntu versions of
LibreOffice (version >= 5.0).

## License
GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. Refer to the LICENSE
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
[IntrinioHistoricalData](http://docs.intrinio.com/excel-addin#intriniohistoricalprices)
Excel AddIn function.
```
=IntrinioHistoricalPrices(ticker, item, sequence, start_date, end_date, frequency)
```

### IntrinioHistoricalData
TBI.

### IntrinioNews
TBI.

### IntrinioStandardizedFundamentals
TBI.

### IntrinioFundamentals
TBI.

### IntrinioTags
TBI.

### IntrinioFinancials
TBI.

