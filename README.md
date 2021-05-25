# Colorado Redistricting 2021
Miscellaneous tools for analyzing election data and district maps.

Opinions expressed here are my own and do not represent the Colorado Independent Legislative or Congressional Redistricting Commissions.

To learn more, go to https://redistricting.colorado.gov

Contact: Carlos Perez <commissioner.carlos.perez@gmail.com>

## Screen Scrapper for SoS Election Archives

Upstream data: https://www.sos.state.co.us/pubs/elections/Results/Archives.html

I found the historical election results on the SoS website unsuitable. So here is a basic tool to convert their HTML tables to a CSV file.

Usage:

```bash
$ curl -o sos_files/stateRepresentatives.2016.html https://www.sos.state.co.us/pubs/elections/Results/Abstract/2016/general/stateRepresentatives.html
$ ... edit sos_screen_scraper.py ...
$ python3 sos_screen_scraper.py
```

Generated CSV output is written to election_data directory.
