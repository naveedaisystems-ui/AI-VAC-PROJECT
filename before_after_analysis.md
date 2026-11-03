# Before/After Data Cleaning Analysis

Source: https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv

| Measure | Before cleaning | After cleaning |
|---|---:|---:|
| Rows | 50,411 | 50,411 |
| Columns | 79 | 79 |
| Missing cells | 2,105,184 | 2,105,184 |
| Exact duplicate rows | 0 | 0 |

## Cleaning operations

- No rows were removed; measurement missing values were retained rather than imputed.

Invalid entity/year rows removed: 0. Exact duplicates
removed: 0. Measurement gaps were retained rather than
imputed. Removing duplicate records prevents repeat counting; preserving gaps avoids
inventing measurements. These operations do not correct source coverage or reporting
method differences.
