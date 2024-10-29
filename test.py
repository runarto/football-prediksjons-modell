import json
import file

def initialize_team_ratings(initial_rating=1500):
    """Initialize an empty dictionary for team ratings."""
    return {}

def calculate_expected_score(rating_a, rating_b, home_field_advantage):
    """Calculate the expected score for a team."""
    exponent = (rating_b - rating_a + home_field_advantage) / 400
    expected_score_a = 1 / (1 + 10 ** exponent)
    return expected_score_a

def update_rating(current_rating, actual_score, expected_score, k_factor=20):
    """Update the Elo rating for a team."""
    return current_rating + k_factor * (actual_score - expected_score)

def process_game(game, team_ratings, k_factor=20):
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

    # Calculate expected scores
    expected_home = calculate_expected_score(rating_home, rating_away, hfa)
    expected_away = calculate_expected_score(rating_away, rating_home, afa)

    # Determine actual scores
    if home_score > away_score:
        actual_home = 1
        actual_away = 0
    elif home_score < away_score:
        actual_home = 0
        actual_away = 1
    else:
        actual_home = 0.5
        actual_away = 0.5

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


if __name__ == "__main__":
    ratings = run_elo_rating_system('jsonfiles/fixtures.json')
    file.write_json_data(ratings, 'jsonfiles/team_elo.json')
    


