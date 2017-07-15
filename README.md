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
=IntrinioFundamentals(ticker, statement, type, sequence, item)
```

### IntrinioTags
TBI.

### IntrinioFinancials
TBI.

## References
* [Intrinio Web Site](https://intrinio.com)
* [Intrinio Excel AddIn](http://docs.intrinio.com/excel-addin#intrinionews)
* [LibreOffice](https://www.libreoffice.org/)