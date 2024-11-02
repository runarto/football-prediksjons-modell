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



def print_season_outcomes(simulated_seasons):
    from collections import defaultdict

    def bold_text(text):
        return f"\033[1m{text}\033[0m"

    analyzed_data = analyze_simulations(simulated_seasons)

    # Create a dictionary to store the highest probability for each position
    highest_probabilities = defaultdict(list)

    for team, positions in analyzed_data.items():
        for position, probability in positions.items():
            highest_probabilities[position].append((team, probability))

    # Sort the teams for each position by the highest probability
    for position in highest_probabilities:
        highest_probabilities[position].sort(key=lambda x: x[1], reverse=True)

    # Print the teams in the order of the highest probability of ending up in each position
    printed_teams = set()
    for position in sorted(highest_probabilities.keys()):
        for team, probability in highest_probabilities[position]:
            if team not in printed_teams:
                printed_teams.add(team)
                print(f"{team}:")
                positions = dict(sorted(analyzed_data[team].items(), key=lambda x: x[0]))
                for pos, prob in positions.items():
                    if pos == position:
                        print(f"Position {pos}: {bold_text(f'{prob:.2f}%')}")
                    else:
                        print(f"Position {pos}: {prob:.2f}%")
                print()
                break


