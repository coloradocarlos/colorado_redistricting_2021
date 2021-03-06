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
    2018: {
        'governor': r'Governor',
        'sec_of_state': r'Secretary of State',
        'treasurer': r'Treasurer',
        'attorney_general': r'Attorney General',
        'regent_at_large': r'Regent Of The University Of Colorado - At Large',
    },
    2016: {
        'us_president': r'President/Vice President',
        'us_senator': r'United States Senator',
        'regent_at_large': r'Regent Of The University Of Colorado - At Large',
    },
    2014: {
        'us_senator': r'United States Senator',
        'governor': r'Governor/Lieutenant Governor',
        'sec_of_state': r'Secretary of State',
        'treasurer': r'Treasurer',
        'attorney_general': r'Attorney General',
    },
    2012: {
        'us_president': r'President/Vice President',
        'regent_at_large': r'Regent Of The University Of Colorado - At Large',
    },
}

# These are low count precincts that are provisional and not assigned a precinct number presumably to preserve the privacy of the voters.
# Let's make an educated guess based on the contents of the SOS file.
provisional_precincts = {
    2016: {
        'Larimer': {
            'us_house': 2,
            'co_senate': 14,  # Could also be 52, 53
            'co_house': 49,
            'co_county': 35,
        },
    },
    2014: {
        'Larimer': {
            'us_house': 2,
            'co_senate': 15,
            'co_house': 49,  # Could also be 52, 53
            'co_county': 35,
        },
        'Summit': {
            'us_house': 2,
            'co_senate': 8,
            'co_house': 61,
            'co_county': 59,
        },
        'Rio Grande': {
            'us_house': 3,
            'co_senate': 35,
            'co_house': 62,
            'co_county': 53,
        },
    },
    2012: {
        'Archuleta': {
            'us_house': 3,
            'co_senate': 6,
            'co_house': 59,
            'co_county': 4,
        },
        'Broomfield': {
            'us_house': 2,
            'co_senate': 23,
            'co_house': 33,
            'co_county': 64,
        },
        'Clear Creek': {
            'us_house': 2,
            'co_senate': 2,
            'co_house': 13,
            'co_county': 10,
        },
        'Conejos': {
            'us_house': 3,
            'co_senate': 35,
            'co_house': 62,
            'co_county': 11,
        },
        'Delta': {
            'us_house': 3,
            'co_senate': 5,
            'co_house': 61,  # Could be 54
            'co_county': 15,
        },
        'Dolores': {
            'us_house': 3,
            'co_senate': 6,
            'co_house': 58,
            'co_county': 17,
        },
        'Douglas': {
            'us_house': 6,  # Could be 4
            'co_senate': 30,  # Could be 4
            'co_house': 43,  # Could be 39, 44, 45
            'co_county': 18,
        },
        'Fremont': {
            'us_house': 5,
            'co_senate': 2,
            'co_house': 60,  # Could be 47
            'co_county': 22,
        },
        'Grand': {
            'us_house': 2,
            'co_senate': 8,
            'co_house': 13,
            'co_county': 25,
        },
        'Gunnison': {
            'us_house': 3,
            'co_senate': 5,
            'co_house': 61,  # Could be 59
            'co_county': 26,
        },
        'Jackson': {
            'us_house': 3,
            'co_senate': 8,
            'co_house': 13,
            'co_county': 29,
        },
        'Kit Carson': {
            'us_house': 4,
            'co_senate': 1,
            'co_house': 65,
            'co_county': 32,
        },
        'Larimer': {
            'us_house': 2,
            'co_senate': 14,  # Could be 23
            'co_house': 52,  # Could be 49, 51, 53
            'co_county': 35,
        },
        'Moffat': {
            'us_house': 3,
            'co_senate': 8,
            'co_house': 57,
            'co_county': 41,
        },
        'Montrose': {
            'us_house': 3,
            'co_senate': 6,
            'co_house': 58,
            'co_county': 43,
        },
        'Pitkin': {
            'us_house': 3,
            'co_senate': 5,
            'co_house': 61,
            'co_county': 49,
        },
        'Rio Blanco': {
            'us_house': 3,
            'co_senate': 8,
            'co_house': 57,
            'co_county': 52,
        },
        'Summit': {
            'us_house': 2,
            'co_senate': 8,
            'co_house': 61,
            'co_county': 59,
        },
        'Weld': {
            'us_house': 4,
            'co_senate': 23,
            'co_house': 63,  # Could be 48, 49, 50
            'co_county': 62,
        },
        'Yuma': {
            'us_house': 4,
            'co_senate': 1,
            'co_house': 65,
            'co_county': 63,
        },
    },
}

# SOS election results column names changed over time for some reason
csv_column_names = {
    2020: {
        'office_column_name': 'Office/Issue/Judgeship',
        'vote_count_column_name': 'Candidate Votes',
    },
    2018: {
        'office_column_name': 'Office/Issue/Judgeship',
        'vote_count_column_name': 'Candidate Votes',
    },
    2016: {
        'office_column_name': 'Office/Issue/Judgeship',
        'vote_count_column_name': 'Candidate Votes',
    },
    2014: {
        'office_column_name': 'Office/Ballot Issue',
        'vote_count_column_name': 'Yes Votes/Percentage',
    },
    2012: {
        'office_column_name': 'Office/Ballot Issue',
        'vote_count_column_name': 'Yes Votes/Percentage',
    },
}


def race_matcher(year, row):
    for race in statewide_races_by_year[year].keys():
        if row[csv_column_names[year]['office_column_name']] == statewide_races_by_year[year][race]:
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


def precinct_number_matcher(precinct_number, year, county):
    # https://www.sos.state.co.us/pubs/elections/FAQs/VoterFAQs.html
    # ??? First digit ??? Congressional District
    # ??? Second and third digits ??? State Senate District
    # ??? Fourth and fifth digits ??? State Representative District
    # ??? Sixth and seventh digits ??? County Number
    # ??? Last three digits ??? Precinct

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
    elif precinct_number == 'Provisional':
        # For provisional precincts, we use the County name and Year to determine the districts they voted in
        precinct_dict = dict()
        for district_type in district_types.keys():
            precinct_dict[district_type] = provisional_precincts[year][county][district_type]
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
                district_numbers = precinct_number_matcher(row['Precinct'], year, row['County'])
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
                    results_row[party] += locale.atoi(row[csv_column_names[year]['vote_count_column_name']])
                    # Update county list for this district
                    if row['County'] not in results_row['county_list']:
                        results_row['county_list'].append(row['County'])
        # After processing all rows in the precinct level CSV, output the results by district
        write_csv_files(year, results)


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # For parsing numbers with comma separators

    years = {
        2020: {'csvin': '2020GEPrecinctLevelResultsPosted.csv'},
        2018: {'csvin': '2018GEPrecinctLevelResults.csv'},
        2016: {'csvin': '2016GeneralResultsPrecinctLevel.csv'},
        2014: {'csvin': '2014GeneralPrecinctResults.csv'},
        2012: {'csvin': '2012GeneralPrecinctLevelResults.csv'},
    }

    for year in years.keys():
        csvin = "./sos_files/{csvin}".format(csvin=years[year]['csvin'])
        print(f"Processing {csvin}...")
        process_precinct_level_results(year, csvin)
