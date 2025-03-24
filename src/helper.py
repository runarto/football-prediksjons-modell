from collections import defaultdict
import math
from datetime import datetime
import sqlite3
from datetime import date


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

def percentage_of_draws(league_id: int) -> float:
    conn = sqlite3.connect("football.db")
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*) FROM matches
        WHERE league_id = ?
    """, (league_id,))
    total_games = c.fetchone()[0]

    c.execute("""
        SELECT COUNT(*) FROM matches
        WHERE league_id = ? AND result = 'Draw'
    """, (league_id,))
    draws = c.fetchone()[0]

    conn.close()

    return draws / total_games if total_games else 0.0

def get_table(league_id: int):
    standings = {}
    conn = sqlite3.connect("football.db")
    c = conn.cursor()

    c.execute("""
        SELECT team, points FROM table_standings
        WHERE league_id = ?
    """, (league_id,))

    for row in c.fetchall():
        team, points = row
        standings[team.upper()] = points

    conn.close()
    return standings

def analyze_simulations(all_simulations):
    # Step 1: Aggregate Position Counts
    position_counts = defaultdict(lambda: defaultdict(int))
    total_simulations = len(all_simulations)

    # Count occurrences of each position for each team
    for simulation in all_simulations:
        sorted_teams = sorted(simulation.items(), key=lambda x: x[1], reverse=True)
        for position, (team, points) in enumerate(sorted_teams, start=1):
            position_counts[team][position] += 1

    # Step 2: Calculate Position Probabilities
    position_probabilities = defaultdict(dict)
    for team, positions in position_counts.items():
        for position, count in positions.items():
            position_probabilities[team][position] = (count / total_simulations) * 100

    # Step 3: Ensure all positions have values (fill in missing ranks with 0.0%)
    max_positions = 16  # Assuming there are 16 ranks
    for team in position_probabilities:
        for pos in range(1, max_positions + 1):
            position_probabilities[team].setdefault(pos, 0.0)

    return position_probabilities

def get_match_result(game, team):
    """Get the match result from the perspective of the given team."""
    home_team = game['home_team']
    away_team = game['away_team']
    home_score = game['score']['home']
    away_score = game['score']['away']

    if home_team == team:
        team_goals = home_score
        opponent_goals = away_score
    elif away_team == team:
        team_goals = away_score
        opponent_goals = home_score
    else:
        return 0  # The team did not participate in this match

    if team_goals > opponent_goals:
        return 1  # Win
    elif team_goals < opponent_goals:
        return -1  # Loss
    else:
        return 0  # Draw



def get_decay_factor(k_factor, game_date_str, use_fixed_reference_date=False):
    game_date = datetime.fromisoformat(game_date_str).date()
    reference_date = date(2024, 12, 10) if use_fixed_reference_date else datetime.now().date()
    days = max((reference_date - game_date).days, 1)
    return k_factor / math.log(days + 10)



def print_rank_probability_distribution(data):
    data = analyze_simulations(data)
    # Calculate the dash line length dynamically based on column width
    dash_line_length = 20 + (17 * 7) + 10
    dash_line = "-" * dash_line_length

    # Sort teams by the probability of finishing first, then first or second, etc.
    sorted_teams = sorted(
        data.items(),
        key=lambda item: [-(item[1].get(rank, 0)) for rank in range(1, 17)]
    )

    # Header for the table
    output = f"{dash_line}\n"
    output += "ELITESERIEN 2024 - SIMULATED FINAL RANK PROBABILITY DISTRIBUTION:\n"
    output += f"{dash_line}\n"
    output += "{:<20} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7}\n".format(
        "Team", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16
    )
    output += f"{dash_line}\n"

    # Iterate over each team in sorted order and print their position probabilities
    for team, positions in sorted_teams:
        probabilities = []
        
        # Check each position from 1 to 16
        for rank in range(1, 17):
            probability = positions.get(rank, 0)
            
            # Only add the probability to the output if it's greater than zero
            if probability >= 0.1:
                probabilities.append(f"{probability:.1f}%")
            else:
                probabilities.append("-")

        # Construct the output row for the team
        output += "{:<20} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7} {:>7}\n".format(
            team, *probabilities
        )

    output += f"{dash_line}\n"
    return output



