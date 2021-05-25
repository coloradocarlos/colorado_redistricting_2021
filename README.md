# Colorado Redistricting 2021
Miscellaneous tools for analyzing election data and district maps.

Opinions expressed here are my own and do not represent the Colorado Independent Legislative Redistricting Commissions.

To learn more, go to https://redistricting.colorado.gov

# SoS Screen Scrapper

A basic tool to convert HTML to a CSV file.

Usage:

```bash
$ curl -o sos_files/stateRepresentatives.2016.html https://www.sos.state.co.us/pubs/elections/Results/Abstract/2016/general/stateRepresentatives.html
$ ... edit sos_screen_scraper.py ...
$ python3 sos_screen_scraper.py
```

Generated CSV goes to election_data directory.
