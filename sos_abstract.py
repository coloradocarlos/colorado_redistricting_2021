"""
This script takes the XLSX files that have been converted to CSV files and generates the
state representatives and state senate election summary CSV.
There are 2 inputs:
- The General Election Statewide Abstract results
- The General Election Precinct Level Turnout results
The output is placed in election_data directory.
"""
import locale
import csv
import re
import pprint


def process_precinct_file(csvin_precinct, district_type):
    with open(csvin_precinct, 'r') as fp1:
        precinct_data = dict()
        csvreader = csv.DictReader(fp1)
        county_map = dict()
        for row in csvreader:
            # https://www.sos.state.co.us/pubs/elections/FAQs/VoterFAQs.html
            # • First digit – Congressional District
            # • Second and third digits – State Senate District
            # • Fourth and fifth digits – State Representative District
            # • Sixth and seventh digits – County Number
            # • Last three digits – Precinct
            matches = re.match(r'^(\d{1})(\d{2})(\d{2})(\d{2})(\d{3})$', row['Precinct'])
            if matches:
                if district_type == 'REP':
                    district = int(matches.groups()[2])
                elif district_type == 'SEN':
                    district = int(matches.groups()[1])
                else:
                    raise Exception(f"Invalid district_type {district_type}")
                county_number = int(matches.groups()[3])
                county = row['County'].title()
                if district not in precinct_data:
                    precinct_data[district] = dict(total_voters=0, ballots_cast=0)
                if county_number not in county_map:
                    county_map[county_number] = county
                # Sanity check
                if county_map[county_number] != county:
                    raise Exception(f"County ({county}) or county_number ({county_number}) changed unexpectedly for precinct {row['Precinct']}")
                # Update totals
                precinct_data[district]['total_voters'] += locale.atoi(row['Total Voters'])
                precinct_data[district]['ballots_cast'] += locale.atoi(row['Ballots Cast'])
            else:
                raise Exception(r"Unable to parse precinct number: {row['Precinct']}")
        # pp = pprint.PrettyPrinter()
        # pp.pprint(precinct_data)
        return precinct_data


def init_row():
    return {'district': 0, 'counties': '', 'registered_voters': 0, 'ballots_cast': 0, 'democrat': 0, 'republican': 0, 'other': 0,
            'total': 0, 'dem_winner': 0, 'rep_winner': 0, 'landslide_d': 0, 'landslide_r': 0}


def emit_row(csvwriter, csvout_row, county_list, precinct_data):
    csvout_row['counties'] = ' - '.join(county_list)
    district = csvout_row['district']
    csvout_row['ballots_cast'] = precinct_data[district]['ballots_cast']
    csvout_row['registered_voters'] = precinct_data[district]['total_voters']
    csvout_row['total'] = csvout_row['democrat'] + csvout_row['republican'] + csvout_row['other']

    # For 2018 and 2016 data, we have to decide who the winner is, unlike 2020 data
    if not any([csvout_row['dem_winner'], csvout_row['rep_winner']]):
        if csvout_row['democrat'] > csvout_row['republican'] and csvout_row['democrat'] > csvout_row['other']:
            csvout_row['dem_winner'] = 1
            csvout_row['rep_winner'] = 0
        elif csvout_row['republican'] > csvout_row['democrat'] and csvout_row['republican'] > csvout_row['other']:
            csvout_row['dem_winner'] = 0
            csvout_row['rep_winner'] = 1
        else:
            print(csvout_row)
            raise Exception("Election tie or other won!")

    # Is this a landslide district?
    landslide_percentage = 0.6  # 60%
    if csvout_row['dem_winner'] == 1:
        csvout_row['landslide_d'] = int(csvout_row['democrat'] / csvout_row['total'] >= landslide_percentage)
        csvout_row['landslide_r'] = 0
    elif csvout_row['rep_winner']:
        csvout_row['landslide_r'] = int(csvout_row['republican'] / csvout_row['total'] >= landslide_percentage)
        csvout_row['landslide_d'] = 0
    else:
        raise Exception("No winner found!")
    csvwriter.writerow(csvout_row)


def match_total_row(row, year):
    if year == 2020:
        return row['Candidate/Judge/Ballot Issue Title'].endswith('Total Votes')
    elif year == 2018:
        return row['County'] == 'TOTAL'
    elif year == 2016:
        return row['Candidate/Judge/Ballot Issue Title'].endswith('TOTAL')
    elif year == 2014 or year == 2012:
        return True
    else:
        raise Exception(f"Invalid year for match_total_row: {year}")


def process_election_file(csvin, csvout, precinct_data, district_type, year):
    with open(csvin, 'r') as fp1, open(csvout, 'w') as fp2:
        csvreader = csv.DictReader(fp1)
        csvout_row = init_row()
        csvwriter = csv.DictWriter(fp2, fieldnames=csvout_row.keys())
        csvwriter.writeheader()
        county_list = []
        for row in csvreader:
            if district_type == 'REP':
                matches = re.match(r'^State Representative - District (\d+)$', row['Office/Ballot Issue'])
            elif district_type == 'SEN':
                matches = re.match(r'^State Senate - District (\d+)$', row['Office/Ballot Issue'])
            if matches:
                new_district = int(matches.groups()[0])
                if new_district != csvout_row['district']:
                    if csvout_row['district'] != 0:
                        emit_row(csvwriter, csvout_row, county_list, precinct_data)
                        csvout_row = init_row()
                        county_list = []
                    csvout_row['district'] = new_district
                if match_total_row(row, year):
                    votes = locale.atoi(row['Yes Votes/Percentage'])
                    if row['Party'] == 'Democratic Party':
                        csvout_row['democrat'] += votes
                    elif row['Party'] == 'Republican Party':
                        csvout_row['republican'] += votes
                    else:
                        csvout_row['other'] += votes
                elif row['Candidate/Judge/Ballot Issue Title'].endswith('(WINNER)'):
                    # This match applies to 2020 data
                    if row['Party'] == 'Democratic Party':
                        csvout_row['dem_winner'] = 1
                        if csvout_row['rep_winner'] == 1:
                            raise Exception("We already have a REP winner!")
                    elif row['Party'] == 'Republican Party':
                        csvout_row['rep_winner'] = 1
                        if csvout_row['dem_winner'] == 1:
                            raise Exception("We already have a DEM winner!")
                    else:
                        raise Exception(f"Another party won in district {csvout_row['district']}!")
                if row['County'] != '' and row['County'] != 'TOTAL':
                    county = row['County'].title()
                    if county not in county_list:
                        county_list.append(county)
            elif csvout_row['district'] != 0:
                emit_row(csvwriter, csvout_row, county_list, precinct_data)
                csvout_row = init_row()


def sort_csv_by_district(csvfile):
    # Need to sort by district numerically because the SOS XLSX is sorted alphabetically this:
    #  State Representative - District 1
    #  State Representative - District 10
    #  State Representative - District 11
    #  ...
    #  State Representative - District 2
    #  State Representative - District 20
    #  ...
    election_results = None
    # Read in unsorted CSV
    with open(csvfile, 'r') as fp1:
        csvreader = csv.DictReader(fp1)
        election_results = list(csvreader)
    # election_results is a list of OrderedDict's
    # pp = pprint.PrettyPrinter()
    # pp.pprint(election_results)

    # Sort list by district numerically, not alphabetically
    new_election_results = sorted(election_results, key=lambda x: int(x['district']))
    # pp = pprint.PrettyPrinter()
    # pp.pprint(new_election_results)

    # Writer out sorted CSV
    with open(csvfile, 'w') as fp2:
        csvwriter = csv.DictWriter(fp2, fieldnames=new_election_results[0].keys())
        csvwriter.writeheader()
        csvwriter.writerows(new_election_results)


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # For parsing numbers with comma separators

    # Results by year: https://www.sos.state.co.us/pubs/elections/resultsData.html
    # Note 1: some input CVS column headers were change from the original SOS files to normalize the names.
    # Note 2: Office/Ballot Issue is sorted alphabetically for 2014 and 2012 and needs to be post processed.
    # Note 3: 2012 is sorted by Precinct and was resorted in LibreOffice Calc by Office/Ballot Issue to process the districts in groups.
    years = {
        2020: {'csvin': '2020StateAbstractResultsReport.csv', 'csvin_precinct': '2020GEPrecinctLevelTurnoutPosted.csv', 'post_sort': False},
        2018: {'csvin': '2018GeneralResults.csv', 'csvin_precinct': '2018GEPrecinctLevelTurnout.csv', 'post_sort': False},
        2016: {'csvin': '2016GEstatewideAbstractResults.csv', 'csvin_precinct': '2016GeneralTurnoutPrecinctLevel.csv', 'post_sort': False},
        2014: {'csvin': '2014GeneralPrecinctResults.csv', 'csvin_precinct': '2014GeneralPrecinctTurnout.csv', 'post_sort': True},
        2012: {'csvin': '2012GeneralPrecinctLevelResults.csv', 'csvin_precinct': '2012GeneralPrecinctLevelTurnout.csv', 'post_sort': True},
    }
    district_types = ['REP', 'SEN']

    for year in years.keys():
        for district_type in district_types:  # REP or SEN
            csvin = "./sos_files/{csvin}".format(csvin=years[year]['csvin'])
            csvin_precinct = "./sos_files/{csvin_precinct}".format(csvin_precinct=years[year]['csvin_precinct'])

            if district_type == 'REP':
                csvout = f"./election_data/{year}/stateRepresentatives.{year}.csv"  # REP
            elif district_type == 'SEN':
                csvout = f"./election_data/{year}/stateSenate.{year}.csv"  # SEN
            else:
                raise Exception(f"Invalid district_type {district_type}")

            print(f"Processing {csvin_precinct}")
            precinct_data = process_precinct_file(csvin_precinct, district_type)
            print(f"Processing {csvin}")
            process_election_file(csvin, csvout, precinct_data, district_type, year)
            print(f"CSV written to {csvout}")

            # We are not done. Need to sort the output for certain years
            if years[year]['post_sort']:
                print(f"Sorting {csvout}")
                sort_csv_by_district(csvout)
