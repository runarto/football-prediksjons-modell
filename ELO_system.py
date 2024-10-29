import file
import math
from collections import deque
import random
import helper

def find_fraction_of_home_wins():
    fixtures = file.load_json_data('jsonfiles/fixtures.json')
    team_wins = {}
    team_home_games = {}

    for season, rounds in fixtures.items():
        for round, matches in rounds.items():
            for match in matches:
                home_team = match['home_team']
                result = match['result']

                if home_team in team_home_games:
                    team_home_games[home_team] += 1
                else:
                    team_home_games[home_team] = 1

            
                if result == 'Home':
                    if home_team in team_wins:
                        team_wins[home_team] += 1
                    else:
                        team_wins[home_team] = 1


    team_home_win_fraction = {}
    for team in team_home_games:
        wins = team_wins.get(team, 0)
        total_games = team_home_games[team]
        team_home_win_fraction[team] = wins / total_games

    return team_home_win_fraction

def find_fraction_of_away_wins():
    fixtures = file.load_json_data('jsonfiles/fixtures.json')
    team_wins = {}
    team_away_games = {}

    for season, rounds in fixtures.items():
        for round, matches in rounds.items():
            for match in matches:
                away_team = match['away_team']
                result = match['result']

                # Increment the total number of away games for the away team
                if away_team in team_away_games:
                    team_away_games[away_team] += 1
                else:
                    team_away_games[away_team] = 1

                # Increment the number of away wins for the away team
                if result == 'Away':
                    if away_team in team_wins:
                        team_wins[away_team] += 1
                    else:
                        team_wins[away_team] = 1

    
    team_away_win_fraction = {}
    for team in team_away_games:
        wins = team_wins.get(team, 0)
        total_games = team_away_games[team]
        team_away_win_fraction[team] = wins / total_games

    return team_away_win_fraction

def initialize_team_ratings(initial_rating=1500):
    """Initialize an empty dictionary for team ratings."""
    return {}

def calculate_expected_score(rating_a, rating_b, home_field_advantage):
    """Calculate the expected score for a team."""
    exponent = (rating_b - rating_a + home_field_advantage) / 400
    expected_score_a = 1 / (1 + 10 ** exponent)
    return expected_score_a

def update_rating(current_rating, actual_score, expected_score, k_factor=10):
    """Update the Elo rating for a team."""
    return current_rating + k_factor * (actual_score - expected_score)

def process_game(game, team_ratings, k_factor=10):
    """Process a single game and update team ratings."""
    # Extract game details
    home_team = game['home_team']
    away_team = game['away_team']
    home_score = game['score']['home']
    away_score = game['score']['away']
    result = game['result']
    
    # Initialize team ratings if they don't exist
    for team in [home_team, away_team]:
        if team not in team_ratings:
            team_ratings[team] = 1500  # Initial rating

    # Get current ratings
    rating_home = team_ratings[home_team]
    rating_away = team_ratings[away_team]

    # Home field advantage applies to the home team
    home_strenth = file.load_json_data('jsonfiles/home_strength.json')
    hfa = home_strenth.get(home_team, 0)*100
    away_strenth = file.load_json_data('jsonfiles/away_strength.json')
    afa = away_strenth.get(away_team, 0)*100
    hfa = hfa + (hfa - afa)/2
    afa = afa + (afa - hfa)/2

    # Calculate expected scores
    expected_home = calculate_expected_score(rating_home, rating_away, hfa)
    expected_away = calculate_expected_score(rating_away, rating_home, afa)

    # Determine actual scores
    if home_score > away_score:
        actual_home = home_score
        actual_away = away_score
    elif home_score < away_score:
        actual_home = away_score
        actual_away = home_score
    else:
        actual_home = home_score
        actual_away = away_score

    # Update ratings
    new_rating_home = update_rating(rating_home, actual_home, expected_home, k_factor)
    new_rating_away = update_rating(rating_away, actual_away, expected_away, k_factor)

    # Save updated ratings
    team_ratings[home_team] = new_rating_home
    team_ratings[away_team] = new_rating_away

    # Print match result and rating updates (optional)
    print(f"    {home_team} {home_score} - {away_score} {away_team}")
    print(f"      {home_team} rating: {rating_home:.2f} -> {new_rating_home:.2f}")
    print(f"      {away_team} rating: {rating_away:.2f} -> {new_rating_away:.2f}")

def process_round(games_list, team_ratings, k_factor=20):
    """Process all games in a round."""
    for game in games_list:
        process_game(game, team_ratings, k_factor)

def process_year(year_data, team_ratings, k_factor=20):
    """Process all rounds in a year."""
    for round_name, games_list in year_data.items():
        print(f"  Processing Round: {round_name}")
        process_round(games_list, team_ratings, k_factor)

def run_elo_rating_system(json_file_path, initial_rating=1500, k_factor=20):
    """Main function to run the Elo rating system."""
    data = file.load_json_data(json_file_path)

    # Initialize team ratings
    team_ratings = initialize_team_ratings(initial_rating)


    for year, year_data in data.items():
        print(f"Processing Year: {year}")
        process_year(year_data, team_ratings, k_factor)

    print("\nFinal Team Ratings:")
    for team, rating in sorted(team_ratings.items(), key=lambda x: x[1], reverse=True):
        print(f"{team}: {rating:.2f}")

    return team_ratings


def calculate_match_probabilities(rating_home, rating_away, home_advantage, theta=200, K=0.22):
    delta_R = rating_home + home_advantage - rating_away

    exp_positive = math.exp(delta_R / theta)
    exp_negative = math.exp(-delta_R / theta)

    denominator = exp_positive + exp_negative + K

    prob_home_win = exp_positive / denominator
    prob_away_win = exp_negative / denominator
    prob_draw = K / denominator

    return {
        'home_win': prob_home_win,
        'draw': prob_draw,
        'away_win': prob_away_win
    }


def calculate_form():
    fixtures = file.load_json_data('jsonfiles/fixtures.json')
    elo = file.load_json_data('jsonfiles/team_elo.json')
    team_form = {}

    init_elos = elo.copy()  # Make a copy of the initial ELO ratings
    
    # Initialize deques for storing the most recent five games' form gains
    form = {team: deque(maxlen=5) for team in elo.keys()}
    
    for season, rounds in fixtures.items():
        for round_name, matches in rounds.items():
            for match in matches:
                home_team = match['home_team']
                away_team = match['away_team']
                
                initial_elo_home = init_elos[home_team]
                initial_elo_away = init_elos[away_team]

                print(f"Old elo rating (H): {elo[home_team]}")
                print(f"Old elo rating (A): {elo[away_team]}")
                
                process_game(match, elo)

                print(f"New elo rating (H): {elo[home_team]}")
                print(f"New elo rating (A): {elo[away_team]}")
                
                home_gain = elo[home_team] - initial_elo_home
                away_gain = elo[away_team] - initial_elo_away

                init_elos[home_team] = elo[home_team]
                init_elos[away_team] = elo[away_team]
                
                form[home_team].append(home_gain)
                form[away_team].append(away_gain)
    
    # Calculate the average form gain for the most recent five games
    for team in elo.keys():
        team_form[team] = {
            'Form': sum(form[team]) / len(form[team]) if form[team] else 0,
        }

    for team, form in team_form.items():
        print(f"{team}: {form}")
    
    return team_form
                

            
def iterate_games():
    future_games = file.load_json_data('jsonfiles/future_matches.json')
    team_form = calculate_form()
    for season, rounds in future_games.items():
        print(f"Season: {season}")
        for round, matches in rounds.items():
            print(f"  Round: {round}")
            for match in matches:
                home_team = match['home_team']
                away_team = match['away_team']
                home_team_elo_rating = match['home_team_elo'] + team_form[home_team]['home_form']
                away_team_elo_rating = match['away_team_elo'] + team_form[away_team]['away_form']
                home_team_strength = match['home_strength']
                away_team_strength = match['away_strength']
                home_advantage = home_team_strength - (away_team_strength - home_team_strength) / 2

                probabilities = calculate_match_probabilities(home_team_elo_rating, away_team_elo_rating, home_advantage)
                print(f"{home_team} vs {away_team}: {probabilities}")



def simulate_games(N=1000):
    future_games = file.load_json_data('jsonfiles/future_matches.json')
    form = calculate_form()
    all_simulations = []



    for _ in range(N):
        team_points = helper.get_table()

        # Simulate each game
        for season, rounds in future_games.items():
            for game_round, matches in rounds.items():
                for match in matches:
                    home_team = match['home_team']
                    away_team = match['away_team']
                    home_team_elo_rating = match['home_team_elo'] + form[home_team]['Form']
                    away_team_elo_rating = match['away_team_elo'] + form[away_team]['Form']
                    home_team_strength = match['home_strength']
                    away_team_strength = match['away_strength']
                    home_advantage = home_team_strength - (away_team_strength - home_team_strength) / 2

                    probabilities = calculate_match_probabilities(home_team_elo_rating, away_team_elo_rating, home_advantage)
                    prob_home_win = round(probabilities['home_win'] * 1000)
                    prob_draw = round(probabilities['draw'] * 1000)
                    prob_away_win = round(probabilities['away_win'] * 1000)

                    # Pick a random number between 0 and 999
                    random_number = random.randint(0, 999)

                    # Determine the outcome based on the random number
                    if random_number < prob_home_win:
                        # Home win
                        team_points[home_team] += 3
                    elif random_number < prob_home_win + prob_draw:
                        # Draw
                        team_points[home_team] += 1
                        team_points[away_team] += 1
                    else:
                        # Away win
                        team_points[away_team] += 3

        # Store the result of this simulation
        all_simulations.append(team_points)

    print(f"Simulated {N} remaining outcomes.")

    return all_simulations


def calculate_specific_game(home_team, away_team):
    team_elo = file.load_json_data('jsonfiles/team_elo.json')
    home_strength = file.load_json_data('jsonfiles/home_strength.json')
    away_strength = file.load_json_data('jsonfiles/away_strength.json')
    home_team_elo = team_elo.get(home_team)
    away_team_elo = team_elo.get(away_team)
    home_team_strength = home_strength.get(home_team)
    away_team_strength = away_strength.get(away_team)
    home_advantage = home_team_strength - (away_team_strength - home_team_strength) / 2

    form = calculate_form()
    home_team_elo_rating = home_team_elo + form[home_team]['Form']
    away_team_elo_rating = away_team_elo + form[away_team]['Form']

    probabilities = calculate_match_probabilities(home_team_elo_rating, away_team_elo_rating, home_advantage)

    # Print the probabilities in a nice format
    print(f"Probabilities for {home_team} vs {away_team}:")
    print(f"  Home Win: {probabilities['home_win'] * 100:.2f}%")
    print(f"  Draw: {probabilities['draw'] * 100:.2f}%")
    print(f"  Away Win: {probabilities['away_win'] * 100:.2f}%")

# Example usage
calculate_specific_game('TROMSO', 'HAM-KAM')     






