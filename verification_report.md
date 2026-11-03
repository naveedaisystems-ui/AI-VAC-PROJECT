# Verification Report

Source: https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv  
Dataset rows after cleaning: 50,411  
Measure: `co2`  
Verification year: 2024

## Independent checks

- PASS — KPI total matches direct source sum
- PASS — Country ranking matches independent grouping
- PASS — Year-over-year change matches annual totals
- PASS — Chart annual totals match source aggregation

Recomputed reported World total: **38,598.578000** million tonnes of CO₂.  
Dashboard KPI total: **38,598.578000** million tonnes of CO₂.

## Top country-level values

| country | value |
|---|---:|
| China | 12,289.037000 |
| United States | 4,904.120000 |
| India | 3,193.478000 |
| Russia | 1,780.524000 |
| Japan | 961.867000 |
| Indonesia | 812.220000 |
| Iran | 792.631000 |
| Saudi Arabia | 692.133000 |
| South Korea | 583.679000 |
| Germany | 572.319000 |

## Aggregate comparison

Reported World total: 38,598.578000 million tonnes of CO₂.  
Sum of coded country rows: 37,398.067000 million tonnes of CO₂.  
Difference (World minus country sum): **+1,200.511000 million tonnes of CO₂**. This is flagged for review as a difference between source aggregations; it is not treated as a failed arithmetic check and no cause is inferred.

## Methodology

The unfiltered total/time series uses the dataset's explicit World aggregate when it has observations; otherwise it sums country rows. Country rankings and selected-country comparisons exclude OWID_ aggregate codes and, when ISO codes are present, rows with missing ISO codes. Missing metric values are excluded, not imputed. Year-over-year changes follow the same selected total
series. Chart data and KPI values are reconciled to the cleaned dataset. A passing
arithmetic check does not establish causation or validate the source's definitions.
