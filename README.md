# Colorado Redistricting 2021
Miscellaneous tools for analyzing election data and district maps.

Opinions expressed here are my own and do not represent the Colorado Independent Legislative or Congressional Redistricting Commissions.

To learn more, go to https://redistricting.colorado.gov

Contact: Carlos Perez <commissioner.carlos.perez@gmail.com>

## Datasets

Need Colorado election data that has been normalized from the SOS website? Just go to [election_data](election_data) folder for the CSV files.

## Screen Scrapper for SoS Election Archives

Upstream data: https://www.sos.state.co.us/pubs/elections/Results/Archives.html

I found the historical election results on the SoS website unsuitable. So here is a basic tool to convert their HTML tables to a CSV file.

Usage:

```bash
$ curl -o sos_files/stateRepresentatives.2016.html https://www.sos.state.co.us/pubs/elections/Results/Abstract/2016/general/stateRepresentatives.html
$ ... download all ...
$ python3 sos_screen_scraper.py
```

Generated CSV output is written to election_data directory.

## Abstract Data SoS Election Archives

The SoS also provides XLSX files with General Election and Precinct Level Turnout. Rather than using the HTML screen scrapper, these files can be converted to equivalent CSV's and with a little processing can be turned into useful formats.

Be careful, each XLSX is slightly different for the total rows and has different column headings (UPPER vs title case).

Usage:

```bash
$ curl -o 2020StateAbstractResultsReport.xlsx https://www.sos.state.co.us/pubs/elections/Results/2020/StateAbstractResultsReport.xlsx
$ curl -o 2020GEPrecinctLevelTurnoutPosted.xlsx https://www.sos.state.co.us/pubs/elections/Results/2020/2020GEPrecinctLevelTurnoutPosted.xlsx
$ ... download all ...
$ ... convert xlsx to csv...
$ ... manually fix first row column header in csv to match the 2020 format...
$ python3 sos_abstract.py
```
## Precinct Level Results Rollup

This rolls up the precinct level results for statewide offices into districts results. For the case of counties, the district number is the SOS county number.

* 2020: US President, US Senator
* 2018: Governor, Secretary of State, Treasurer, Attorney General, CU Regent at Large
* 2016: President, US Senate, CU Regent at Large
* 2014: US Senator, Governor, Secretary of State, Treasurer, Attorney General
* 2012: US President, CU Regent at Large

```bash
$ cd sos_files
$ curl 2020GEPrecinctLevelResultsPosted.xlsx -o https://www.sos.state.co.us/pubs/elections/Results/2020/2020GEPrecinctLevelResultsPosted.xlsx
$ ... convert xlsx to csv..
$ python3 sos_precinct_level_results.py
```

### Provisional precincts

2016, 2014, and 2012 have "provisional precincts" in their totals. There is no precinct number and therefore we don't know which distict these voters cast a ballot in. So the totals match up with the county totals, these provisional precincts were assigned a congressional district, state senate district, and state house district. The totals appear low enough that this should not skew the data significantly.
