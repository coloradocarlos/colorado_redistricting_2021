"""
A screenscraper that parses the Colorado Secretary of State (SOS) online HTML pages with election summaries
and puts them in a easier to use CSV format.
Go here do download HTML files for 2016: https://www.sos.state.co.us/pubs/elections/Results/Abstract/2016/general/index.html
"""
import locale
import csv
import re


def total_matcher(line, col_title):
    # Example
    # <td style="text-align: right;"><span class="ADAhidden">Registered voters </span>53,662</td>
    # <td style="text-align: right;"><strong><span class="ADAhidden">Registered voters </span>41,604</strong></td>
    # <td style="text-align: right;"><span class="ADAhidden">Steve Zorn (DEM) (Write-In) </span>10</td>
    # <td style="text-align: right;"><strong><span class="ADAhidden">Kara Leach Palfy (REP) (Write-In)</span>352</strong></td>
    # <td style="text-align: right;"><span class="ADAhidden">Hans V. Romer (LIB) </span><strong>5,112</strong></td>
    digits = r'(\d{1,3}(,\d{1,3})?)'
    pat = r'^<td style="text-align: right;">(?:<strong>)?<span class="ADAhidden">{col_title}(?:\s)?</span>(?:<strong>)?{digits}(?:</strong>)?</td>$'.format(col_title=col_title, digits=digits)
    matches = re.match(pat, line)
    if matches:
        # Totals may have commas for thousands separator
        total = locale.atoi(matches.groups()[0])
        return total
    else:
        return None


def process_election_file(htmlfile, csvfile):
    fields = {'district': 0, 'counties': '', 'registered_voters': 0, 'ballots_cast': 0,
              'democrat': 0, 'republican': 0, 'other': 0, 'total': 0, 'dem_winner': 0, 'rep_winner': 0,
              'landslide_d': 0, 'landslide_r': 0}
    with open(htmlfile, 'r') as fp1, open(csvfile, 'w') as fp2:
        csvwriter = csv.DictWriter(fp2, fieldnames=fields.keys())
        csvwriter.writeheader()
        county_list = []
        total_found = False
        # print("district,counties,registered_voters,ballots_cast,democrat,republican,other,total,dem_winner,rep_winner,landslide_d, landslide_r")

        for line in fp1.readlines():
            # District heading
            matches = re.match(r'^<h2 class="w3-toppad"><a id="(?:d)?(?:\d+)" name="(?:d)?(?:\d+)"></a>(?:State Senate - )?District (\d+)</h2>$', line)
            if matches:
                fields['district'] = int(matches.groups()[0])
                county_list = []
                continue

            # Total
            # <td><strong><span class="ADAhidden">County </span>Total</strong></td>
            matches = re.match(r'<td>(?:<strong>)?<span class="ADAhidden">County </span>(?:<strong>)?([\w\s]+)(?:</strong>)?</td>', line)
            if matches:
                if matches.groups()[0] == 'Total':
                    total_found = True
                else:
                    county_list.append(matches.groups()[0])
                continue

            if not total_found:
                continue

            # Registered voters
            total = total_matcher(line, "Registered voters")
            if total and total_found:
                fields['registered_voters'] = total
                continue

            # Ballots cast
            total = total_matcher(line, "Ballots cast")
            if total:
                fields['ballots_cast'] = total
                continue

            # Other
            total = total_matcher(line, r'(?:.+)\((?!(?:DEM|REP))\w+\)')
            if total:
                fields['other'] += total  # Sum
                continue

            # Democrat
            total = total_matcher(line, r'(?:.+)\(DEM\)(?: \(Write-In\))?')
            if total:
                fields['democrat'] += total  # Sum because of write-in Democrat
                continue

            # Republican
            total = total_matcher(line, r'(?:.+)\(REP\)(?: \(Write-In\))?')
            if total:
                fields['republican'] += total  # Sum because of write-in Republicans
                continue

            # Total
            total = total_matcher(line, "Total")
            if total:
                fields['total'] = total

                # Determine party that prevailed
                if fields['democrat'] > fields['republican']:
                    fields['dem_winner'] = 1
                    fields['rep_winner'] = 0
                elif fields['republican'] > fields['democrat']:
                    fields['dem_winner'] = 0
                    fields['rep_winner'] = 1
                else:
                    raise Exception("Election tie!")

                # Is this a landslide district?
                landslide_percentage = 0.6  # 60%
                if fields['dem_winner'] == 1:
                    fields['landslide_d'] = int(fields['democrat'] / fields['total'] >= landslide_percentage)
                    fields['landslide_r'] = 0
                elif fields['rep_winner']:
                    fields['landslide_r'] = int(fields['republican'] / fields['total'] >= landslide_percentage)
                    fields['landslide_d'] = 0
                else:
                    raise Exception("No winner found!")

                # Sanity check
                party_total = fields['democrat'] + fields['republican'] + fields['other']
                if party_total != fields['total']:
                    raise Exception(f"Total mismatch for {fields['district']}: computed {party_total} != SOS {fields['total']}")

                # Flatten county list
                fields['counties'] = ' - '.join(county_list)

                # Emit CSV row
                csvwriter.writerow(fields)

                # Reset totals
                fields['democrat'] = 0
                fields['republican'] = 0
                fields['other'] = 0
                total_found = False


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # For parsing numbers with comma separators
    # https://www.sos.state.co.us/pubs/elections/Results/Abstract/2016/general/stateRepresentatives.html
    htmlfile = './sos_files/stateSenate.2016.html'
    csvfile = './election_data/stateSenate.2016.csv'
    process_election_file(htmlfile, csvfile)
