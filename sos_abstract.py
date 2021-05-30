"""

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
                precinct_data[district]['total_voters'] += int(row['Total Voters'])
                precinct_data[district]['ballots_cast'] += int(row['Ballots Cast'])
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

    # For 2018 data, we have to decide who the winner is, unlike 2020 data
    if not any([csvout_row['dem_winner'], csvout_row['rep_winner']]):
        if csvout_row['democrat'] > csvout_row['republican']:
            csvout_row['dem_winner'] = 1
            csvout_row['rep_winner'] = 0
        elif csvout_row['republican'] > csvout_row['democrat']:
            csvout_row['dem_winner'] = 0
            csvout_row['rep_winner'] = 1
        else:
            raise Exception("Election tie!")

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


def process_election_file(csvin, csvout, precinct_data, district_type):
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
                if row['Candidate/Judge/Ballot Issue Title'].endswith('Total Votes') or row['County'] == 'TOTAL':
                    votes = locale.atoi(row['Yes Votes/Percentage'])
                    if row['Party'] == 'Democratic Party':
                        csvout_row['democrat'] += votes
                    elif row['Party'] == 'Republican Party':
                        csvout_row['republican'] += votes
                    else:
                        csvout_row['other'] += votes
                elif row['Candidate/Judge/Ballot Issue Title'].endswith('(WINNER)'):
                    if row['Party'] == 'Democratic Party':
                        csvout_row['dem_winner'] = 1
                        if csvout_row['rep_winner'] == 1:
                            raise Exception("We already have another REP winner!")
                    elif row['Party'] == 'Republican Party':
                        csvout_row['rep_winner'] = 1
                        if csvout_row['dem_winner'] == 1:
                            raise Exception("We already have another DEM winner!")
                    else:
                        raise Exception(f"Another party won in district {csvout_row['district']}!")
                elif row['County'] != '' and row['County'] != 'TOTAL':
                    county = row['County'].title()
                    if county not in county_list:
                        county_list.append(county)
            elif (district_type == 'REP' and csvout_row['district'] == 65) or \
                 (district_type == 'SEN' and csvout_row['district'] == 35):
                emit_row(csvwriter, csvout_row, county_list, precinct_data)
                csvout_row = init_row()


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # For parsing numbers with comma separators
    # https://www.sos.state.co.us/pubs/elections/Results/2020/StateAbstractResultsReport.xlsx
    csvin = './sos_files/2020StateAbstractResultsReport.csv'  # 2018GeneralResults.csv
    csvin_precinct = './sos_files/2020GEPrecinctLevelTurnoutPosted.csv'  # 2018GEPrecinctLevelTurnout.csv
    district_type = 'SEN'  # REP or SEN
    if district_type == 'REP':
        csvout = './election_data/stateRepresentatives.2020.csv'  # REP
    elif district_type == 'SEN':
        csvout = './election_data/stateSenate.2020.csv'  # SEN
    else:
        raise Exception(f"Invalid district_type {district_type}")
    print(f"Processing {csvin_precinct}")
    precinct_data = process_precinct_file(csvin_precinct, district_type)  # REP or SEN
    print(f"Processing {csvin}")
    process_election_file(csvin, csvout, precinct_data, district_type)  # REP or SEN
    print(f"CSV written to {csvout}")
