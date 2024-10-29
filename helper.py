import file
from collections import defaultdict


def determine_result(fixture):
    home_win = fixture['teams']['home']['winner']

    if fixture['fixture']['status']['short'] != "FT":
        return "NaN"
    
    if home_win is True:
        return True 
    elif home_win is False:
        return False
    else:
        return None 
    

def percentage_of_draws():
    fixtures = file.load_json_data('jsonfiles/fixtures.json')
    draws = 0
    total_games = 0

    for season, rounds in fixtures.items():
        for round, matches in rounds.items():
            for match in matches:
                result = match['result']
                total_games += 1
                if result == 'Draw':
                    draws += 1

    return draws / total_games


def get_table():
    standings = {}
    table = file.load_json_data('jsonfiles/table.json')
    for team, info in table.items():
        standings[team.upper()] = info.get('points')

    return standings


def analyze_simulations(all_simulations):
    position_counts = defaultdict(lambda: defaultdict(int))
    total_simulations = len(all_simulations)

    # Count the number of times each team finishes in each position
    for simulation in all_simulations:
        sorted_teams = sorted(simulation.items(), key=lambda x: x[1], reverse=True)
        for position, (team, points) in enumerate(sorted_teams, start=1):
            position_counts[team][position] += 1

    # Convert counts to probabilities
    position_probabilities = defaultdict(lambda: defaultdict(float))
    for team, positions in position_counts.items():
        for position, count in positions.items():
            position_probabilities[team][position] = (count / total_simulations) * 100

    return position_probabilities

