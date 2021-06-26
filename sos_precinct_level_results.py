"""
This script takes the precinct-level XLSX files that have been converted to CSV files and generates the partisan victor for:

- Congressional District: [1 - 7]
- Colorado Senate District: [1 - 35]
- Colorado House District: [1 - 65]

There is 1 inputs for years [2020]:
- The General Election Precinct Level results

Statewide races:
- 2020: President, US Senate

The output is placed in election_data directory.
"""

import locale
import csv
import re
import pprint
from collections import OrderedDict

# Colorado has 3 types of districts: Congressional districts, State Senate districts, and State House districts
district_types = {
    'us_house': {
        'districts': tuple(range(1, 8)),   # 7 congressional districts
        'precinct_match_group_number': 0,  # for regex
    },
    'co_senate': {
        'districts': tuple(range(1, 36)),  # 35 state senate districts
        'precinct_match_group_number': 1,  # for regex
    },
    'co_house': {
        'districts': tuple(range(1, 66)),  # 65 state house districts
        'precinct_match_group_number': 2,  # for regex
    },
    'co_county': {
        'districts': tuple(range(1, 65)),  # 64 counties
        'precinct_match_group_number': 3,  # for regex
    },
}

# Define the statewide races for each year
statewide_races_by_year = {
    2020: {
        'us_president': r'President/Vice President',
        'us_senator': r'United States Senator',
    },
}


def race_matcher(year, row):
    for race in statewide_races_by_year[year].keys():
        if row['Office/Issue/Judgeship'] == statewide_races_by_year[year][race]:
            # Return 'us_president' or 'us_senator'
            return race
    return None


def init_results_dict(year):
    """
    Initialize statewide races by district with dictionary of party counts by Democrat, Republican, and Other
    {
    'us_president':
        {
        'us_house': {
            1: {'democrat': 0, ...},
            2: {'democrat': 0, ...}},
            3: ...
        'co_senate': ...,
        'co_house': ...,
        'co_county': ...
    'us_senate': ...,
    }
    """
    results = dict()
    for race in statewide_races_by_year[year].keys():
        results[race] = dict()
        for district_type in district_types.keys():
            district_results = OrderedDict()
            for district in district_types[district_type]['districts']:
                district_results[district] = dict(county_list=[], democrat=0, republican=0, other=0)
            results[race][district_type] = district_results
    return results


def precinct_number_matcher(precinct_number):
    # https://www.sos.state.co.us/pubs/elections/FAQs/VoterFAQs.html
    # • First digit – Congressional District
    # • Second and third digits – State Senate District
    # • Fourth and fifth digits – State Representative District
    # • Sixth and seventh digits – County Number
    # • Last three digits – Precinct

    # County Number (ID #) can be found here: https://www.sos.state.co.us/pubs/elections/Resources/files/CountyClerkRosterWebsite.pdf

    matches = re.match(r'^(\d{1})(\d{2})(\d{2})(\d{2})(\d{3})$', precinct_number)
    if matches:
        # Need to lookup the group number, 0 = Congressional District, 1 = State Senate, 2 = State Representative
        precinct_dict = dict()
        for district_type in district_types.keys():
            group_number = district_types[district_type]['precinct_match_group_number']
            precinct_dict[district_type] = int(matches.groups()[group_number])
        # Example: {'us_house': 1, 'co_senate': 2, 'co_house': 3, 'co_county': 4}
        return precinct_dict
    else:
        raise Exception(f"Unable to match precinct number {precinct_number}!")


def write_csv_files(year, results):
    """
    Write the results for each year and statewide office by district type
    For 2020, there are 2 statewide offices, 4 district types, for a total of 8 CSV files
    """
    header = ('district', 'counties', 'democrat', 'republican', 'other')
    for race in results.keys():
        for district_type in results[race].keys():
            csvout = f"./election_data/{year}/{year}_{race}_by_{district_type}.csv"
            print(f"Writing {csvout}")
            with open(csvout, 'w') as fp2:
                csvwriter = csv.DictWriter(fp2, fieldnames=header, extrasaction='ignore')
                csvwriter.writeheader()
                for district_number in results[race][district_type].keys():
                    row = results[race][district_type][district_number]
                    row['district'] = district_number
                    row['counties'] = ' - '.join(row['county_list'])
                    csvwriter.writerow(row)


def process_precinct_level_results(year, csvin):
    results = init_results_dict(year)
    # pp = pprint.PrettyPrinter()
    # pp.pprint(results)
    with open(csvin, 'r') as fp1:
        csvreader = csv.DictReader(fp1)
        for row in csvreader:
            # race_match is 'us_president' or 'us_senator'
            race_match = race_matcher(year, row)
            if race_match:
                # district_numbers is a dict parsed from Precinct: {'us_house': 1, 'co_senate': 2, 'co_house': 3, 'co_county': 4}
                district_numbers = precinct_number_matcher(row['Precinct'])
                # district_type will be 'us_house', 'co_senate', 'co_house', 'co_county'
                for district_type in results[race_match]:
                    if row['Party'] == 'Democratic Party':
                        party = 'democrat'
                    elif row['Party'] == 'Republican Party':
                        party = 'republican'
                    else:
                        party = 'other'
                    # district_number depends on type
                    district_number = district_numbers[district_type]
                    # Update vote totals for this district
                    results_row = results[race_match][district_type][district_number]
                    results_row[party] += locale.atoi(row['Candidate Votes'])
                    # Update county list for this district
                    if row['County'] not in results_row['county_list']:
                        results_row['county_list'].append(row['County'])
        # After processing all rows in the precinct level CSV, output the results by district
        write_csv_files(year, results)


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # For parsing numbers with comma separators

    years = {
        2020: {'csvin': '2020GEPrecinctLevelResultsPosted.csv'},
    }

    for year in years.keys():
        csvin = "./sos_files/{csvin}".format(csvin=years[year]['csvin'])
        print(f"Processing {csvin}...")
        process_precinct_level_results(year, csvin)
