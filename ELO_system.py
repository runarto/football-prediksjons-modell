import math
import random
from collections import deque
import helper
import data_manager

"""
* TODO: In the simulate games, we need to add the predicted result such that we can include it in the form calculation.
* This might however cause a serial prediction error, but when simulating a lot of outcomes it might give a better overall prediction.
* TODO: Fetch games from OBOS-ligaen and generate Elo ratings for the teams in the league. We need to find a method to scale the ratings to take into consideration the level difference.
* TODO: Take previous head-to-head games into consideration when calculating the probabilities for a specific game.
? How can we implement more features on the Elo syste to attempt to make better predictions? 
"""


class EloRatingSystem:
    def __init__(self, initial_rating=1500, k_factor=10):
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.DataManager = data_manager.DataManager()
        self.team_form, self.gains = self.init_form()
        print(self.gains) 

    @property
    def fixtures(self):
        return self.DataManager.fixtures

    @property
    def future_matches(self):
        return self.DataManager.future_matches

    @property
    def home_strength(self):
        return self.DataManager.home_strength

    @property
    def away_strength(self):
        return self.DataManager.away_strength

    @property
    def team_ratings(self):
        return self.DataManager.team_elo

    def initialize_team_ratings(self):
        """Initialize team ratings with the initial rating."""
        for team in self.home_strength.keys():
            self.team_ratings[team] = self.initial_rating

    def calculate_expected_score(self, rating_a, rating_b, home_field_advantage):
        """Calculate the expected score for a team."""
        exponent = (rating_b - rating_a + home_field_advantage) / 400
        expected_score_a = 1 / (1 + 10 ** exponent)
        return expected_score_a

    def update_rating(self, current_rating, actual_score, expected_score):
        """Update the Elo rating for a team."""
        return current_rating + self.k_factor * (actual_score - expected_score)

    def process_game(self, game):
        """Process a single game and update team ratings."""
        home_team = game['home_team']
        away_team = game['away_team']
        home_score = game['score']['home']
        away_score = game['score']['away']

        # Initialize team ratings if they don't exist
        for team in [home_team, away_team]:
            if team not in self.team_ratings:
                self.team_ratings[team] = self.initial_rating

        # Get current ratings
        rating_home = self.team_ratings[home_team]
        rating_away = self.team_ratings[away_team]

        # Home field advantage
        hfa = self.home_strength.get(home_team, 0) * 100
        afa = self.away_strength.get(away_team, 0) * 100
        hfa_adjusted = hfa + (hfa - afa) / 2

        # Calculate expected scores
        expected_home = self.calculate_expected_score(rating_home, rating_away, hfa_adjusted)
        expected_away = 1 - expected_home  # Expected score for away team

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
        new_rating_home = self.update_rating(rating_home, actual_home, expected_home)
        new_rating_away = self.update_rating(rating_away, actual_away, expected_away)

        # Save updated ratings
        self.team_ratings[home_team] = new_rating_home
        self.team_ratings[away_team] = new_rating_away

        # Print match result and rating updates (optional)
        print(f"    {home_team} {home_score} - {away_score} {away_team}")
        print(f"      {home_team} rating: {rating_home:.2f} -> {new_rating_home:.2f}")
        print(f"      {away_team} rating: {rating_away:.2f} -> {new_rating_away:.2f}")

    def process_round(self, games_list):
        """Process all games in a round."""
        for game in games_list:
            self.process_game(game)

    def process_season(self):
        """Process all seasons in the fixtures."""
        for season, season_data in self.fixtures.items():
            print(f"Processing Season: {season}")
            for round_name, games_list in season_data.items():
                print(f"  Processing Round: {round_name}")
                self.process_round(games_list)

    def run_elo_rating_system(self):
        """Run the Elo rating system."""
        self.initialize_team_ratings()
        self.process_season()
        print("\nFinal Team Ratings:")
        for team, rating in sorted(self.team_ratings.items(), key=lambda x: x[1], reverse=True):
            print(f"{team}: {rating:.2f}")

    def calculate_match_probabilities(self, rating_home, rating_away, home_advantage, theta=200, K=0.22):
        """Calculate match outcome probabilities."""
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

    def init_form(self):
        """Calculate the form of each team based on recent performance."""
        # Initialize form tracking
        form = {team: deque(maxlen=3) for team in self.team_ratings.keys()}

        temp_ratings = self.team_ratings.copy()

        for season, rounds in self.fixtures.items():

            for round_name, matches in rounds.items():
                for match in matches:
                    home_team = match['home_team']
                    away_team = match['away_team']

                    initial_elo_home = self.team_ratings[home_team]
                    initial_elo_away = self.team_ratings[away_team]

                    self.process_game(match)

                    home_gain = self.team_ratings[home_team] - initial_elo_home
                    away_gain = self.team_ratings[away_team] - initial_elo_away

                    # Reset team ratings to true values:
                    self.team_ratings[home_team] = initial_elo_home
                    self.team_ratings[away_team] = initial_elo_away

                    # Update temp ratings with form gains
                    temp_ratings[home_team] = self.team_ratings[home_team] + home_gain
                    temp_ratings[away_team] = self.team_ratings[away_team] + away_gain

                    form[home_team].append(home_gain)
                    form[away_team].append(away_gain)

        # Calculate weighted form
        weights = [math.log(i**2 + 1) for i in range(1, 4)]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        team_gains = {team: deque(maxlen=3) for team in self.team_ratings.keys()}

        for team in self.team_ratings.keys():
            gains = list(form[team])
            team_gains[team] = gains
            if len(gains) < 3:
                gains = [0] * (3 - len(gains)) + gains  # Pad with zeros if less than 5 games
            weighted_sum = sum(gain * weight for gain, weight in zip(gains, normalized_weights))
            form[team] = weighted_sum

        # Print team forms (optional)
        for team, form_value in form.items():
            print(f"{team}: Form = {form_value:.2f}")

        print(form)
        print(gains)
        return form, team_gains
    
    def update_form(self, match, home_team, away_team):
        """Update the form of a team."""

        initial_elo_home = self.team_ratings[home_team]
        initial_elo_away = self.team_ratings[away_team]

        self.process_game(match)

        home_gain = self.team_ratings[home_team] - initial_elo_home
        away_gain = self.team_ratings[away_team] - initial_elo_away

        # Add the gains to the form tracking
        self.gains[home_team].append(home_gain)
        self.gains[away_team].append(away_gain)

        # Calculate weighted form
        weights = [math.log(i**2 + 1) for i in range(1, 4)]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        for team in [home_team, away_team]:
            gains = list(self.gains[team])
            if len(gains) < 3:
                gains = [0] * (3 - len(gains)) + gains
            weighted_sum = sum(gain * weight for gain, weight in zip(gains, normalized_weights))
            self.team_form[team] = weighted_sum
        
    def simulate_season_outcome_n_times(self, N=1000):
        """Simulate future games N times."""
        all_simulations = []
        true_ratings = self.team_ratings.copy()
        true_form = self.team_form.copy()
        true_gains = self.gains.copy()

        for _ in range(N):
            team_points = helper.get_table()
            self.team_ratings.update(true_ratings.copy())
            self.team_form.update(true_form.copy())
            self.gains.update(true_gains.copy())

            for season, rounds in self.future_matches.items():
                for round_name, matches in rounds.items():
                    for match in matches:
                        home_team = match['home_team']
                        away_team = match['away_team']

                        home_rating = self.team_ratings[home_team] + self.team_form[home_team]*5
                        away_rating = self.team_ratings[away_team] + self.team_form[away_team]*5

                        # Home field advantage
                        hfa = self.home_strength[home_team] * 100
                        afa = self.away_strength[away_team] * 100
                        home_advantage = hfa - (afa - hfa) / 2

                        probabilities = self.calculate_match_probabilities(home_rating, away_rating, home_advantage)
                        prob_home_win = probabilities['home_win']
                        prob_draw = probabilities['draw']
                        prob_away_win = probabilities['away_win']

                        # Simulate match outcome
                        rand = random.random()
                        if rand < prob_home_win:
                            team_points[home_team] += 3
                            match = {
                                'home_team': home_team,
                                'away_team': away_team,
                                'score': {'home': 2, 'away': 1},
                                'result': 'Home'
                            }

                            self.update_form(match, home_team, away_team)

                            
                        elif rand < prob_home_win + prob_draw:
                            team_points[home_team] += 1
                            team_points[away_team] += 1

                            match = {
                                'home_team': home_team,
                                'away_team': away_team,
                                'score': {'home': 1, 'away': 1},
                                'result': 'Draw'
                            }

                            self.update_form(match, home_team, away_team)

                            
                        else:
                            team_points[away_team] += 3

                            match = {
                                'home_team': home_team,
                                'away_team': away_team,
                                'score': {'home': 1, 'away': 2},
                                'result': 'Away'
                            }

                            self.update_form(match, home_team, away_team)

            all_simulations.append(team_points)

        print(f"Simulated {N} remaining outcomes.")
        print(helper.print_season_outcomes(all_simulations))
        
    def calculate_specific_game(self, home_team, away_team):
        
        """Calculate the probabilities for a specific game."""
        home_rating = self.team_ratings.get(home_team, self.initial_rating) + self.team_form.get(home_team, 0)
        away_rating = self.team_ratings.get(away_team, self.initial_rating) + self.team_form.get(away_team, 0)

        hfa = self.home_strength.get(home_team, 0) * 100
        afa = self.away_strength.get(away_team, 0) * 100
        home_advantage = hfa - (afa - hfa) / 2

        probabilities = self.calculate_match_probabilities(home_rating, away_rating, home_advantage)

        # Print the probabilities
        print(f"Probabilities for {home_team} vs {away_team}:")
        print(f"  Home Win: {probabilities['home_win'] * 100:.2f}%")
        print(f"  Draw: {probabilities['draw'] * 100:.2f}%")
        print(f"  Away Win: {probabilities['away_win'] * 100:.2f}%")



elo = EloRatingSystem()
elo.run_elo_rating_system()
elo.simulate_season_outcome_n_times(1000)