import math
import random
from collections import deque
import helper
import data_manager

"""
This module contains the EloRatingSystem class, which implements an Elo rating system for football predictions.

Features:
- Processes historical match data to calculate team ratings.
- Adjusts ratings based on match outcomes, home advantage, and time decay.
- Incorporates team form and head-to-head adjustments into match probability calculations.
- Simulates future matches to predict season outcomes.
"""

class EloRatingSystem:
    def __init__(self, initial_rating=1500, k_factor=10):
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.DataManager = data_manager.DataManager()
        self.team_form, self.gains = self.init_form()
        # Uncomment the following line if you want to see the initial gains
        # print(self.gains)

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
        for team in self.home_strength:
            self.team_ratings[team] = self.initial_rating

    def calculate_expected_score(self, rating_a, rating_b, home_field_advantage):
        """Calculate the expected score for a team."""
        exponent = (rating_b - rating_a + home_field_advantage) / 400
        return 1 / (1 + 10 ** exponent)

    def update_rating(self, current_rating, actual_score, expected_score, decay_factor):
        """Update the Elo rating for a team."""
        return current_rating + self.k_factor * decay_factor * (actual_score - expected_score)

    def process_game(self, game):
        """Process a single game and update team ratings."""
        home_team = game['home_team']
        away_team = game['away_team']
        home_score = game['score']['home']
        away_score = game['score']['away']
        match_date = game['date']

        # Initialize team ratings if they don't exist
        for team in [home_team, away_team]:
            self.team_ratings.setdefault(team, self.initial_rating)

        # Get current ratings
        rating_home = self.team_ratings[home_team]
        rating_away = self.team_ratings[away_team]

        # Calculate home field advantage
        hfa = self.home_strength.get(home_team, 0) * 100
        afa = self.away_strength.get(away_team, 0) * 100
        home_advantage = hfa + (hfa - afa) / 2

        # Calculate expected scores
        expected_home = self.calculate_expected_score(rating_home, rating_away, home_advantage)
        expected_away = 1 - expected_home

        # Determine actual scores
        if home_score - away_score > 0.1:
            actual_home, actual_away = 1, 0
        elif home_score - away_score < -0.1:
            actual_home, actual_away = 0, 1
        else:
            actual_home = actual_away = 0.5

        # Calculate decay factor
        decay_factor = helper.get_decay_factor(self.k_factor, match_date)

        # Update ratings
        new_rating_home = self.update_rating(rating_home, actual_home, expected_home, decay_factor)
        new_rating_away = self.update_rating(rating_away, actual_away, expected_away, decay_factor)

        # Save updated ratings
        self.team_ratings[home_team] = new_rating_home
        self.team_ratings[away_team] = new_rating_away

        # Optional: Print match result and rating updates
        # print(f"{home_team} {home_score} - {away_score} {away_team}")
        # print(f"{home_team} rating: {rating_home:.2f} -> {new_rating_home:.2f}")
        # print(f"{away_team} rating: {rating_away:.2f} -> {new_rating_away:.2f}")

    def process_round(self, games_list):
        """Process all games in a round."""
        for game in games_list:
            self.process_game(game)

    def process_season(self):
        """Process all seasons in the fixtures."""
        for season, season_data in self.fixtures.items():
            for round_name, games_list in season_data.items():
                self.process_round(games_list)

    def run_elo_rating_system(self):
        """Run the Elo rating system."""
        self.initialize_team_ratings()
        self.process_season()
        print("\nFinal Team Ratings:")
        sorted_teams = sorted(self.team_ratings.items(), key=lambda x: x[1], reverse=True)
        for team, rating in sorted_teams:
            print(f"{team}: {rating:.2f}")

    def calculate_match_probabilities(self, rating_home, rating_away, home_advantage, h2h_adjustment=0, theta=200, K=0.22):
        """Calculate match outcome probabilities."""
        delta_R = rating_home + home_advantage + h2h_adjustment - rating_away
        exp_pos = math.exp(delta_R / theta)
        exp_neg = math.exp(-delta_R / theta)
        denominator = exp_pos + exp_neg + K
        prob_home_win = exp_pos / denominator
        prob_away_win = exp_neg / denominator
        prob_draw = K / denominator
        return {
            'home_win': prob_home_win,
            'draw': prob_draw,
            'away_win': prob_away_win
        }

    def init_form(self):
        """Calculate the initial form of each team based on recent performance."""
        # Initialize form tracking deques for each team
        form_deques = {team: deque(maxlen=3) for team in self.team_ratings}

        for season, rounds in self.fixtures.items():
            for round_name, matches in rounds.items():
                for match in matches:
                    home_team = match['home_team']
                    away_team = match['away_team']

                    initial_rating_home = self.team_ratings[home_team]
                    initial_rating_away = self.team_ratings[away_team]

                    self.process_game(match)

                    # Calculate gains
                    gain_home = self.team_ratings[home_team] - initial_rating_home
                    gain_away = self.team_ratings[away_team] - initial_rating_away

                    # Reset team ratings to initial values
                    self.team_ratings[home_team] = initial_rating_home
                    self.team_ratings[away_team] = initial_rating_away

                    # Append gains to form deques
                    form_deques[home_team].append(gain_home)
                    form_deques[away_team].append(gain_away)

        # Calculate weighted form for each team
        weights = [math.log(i ** 2 + 1) for i in range(1, 4)]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        team_form = {}
        team_gains = {}

        for team in self.team_ratings:
            gains = list(form_deques[team])
            team_gains[team] = gains.copy()

            # Pad gains with zeros if less than 3 games
            if len(gains) < 3:
                gains = [0] * (3 - len(gains)) + gains

            # Calculate weighted sum
            weighted_sum = sum(g * w for g, w in zip(gains, normalized_weights))
            team_form[team] = weighted_sum

        return team_form, team_gains

    def update_form(self, match, home_team, away_team):
        """Update the form of teams after a match."""
        initial_rating_home = self.team_ratings[home_team]
        initial_rating_away = self.team_ratings[away_team]

        self.process_game(match)

        # Calculate gains
        gain_home = self.team_ratings[home_team] - initial_rating_home
        gain_away = self.team_ratings[away_team] - initial_rating_away

        # Append gains to gains deques
        self.gains[home_team].append(gain_home)
        self.gains[away_team].append(gain_away)

        # Recalculate team form
        weights = [math.log(i ** 2 + 1) for i in range(1, 4)]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        for team in [home_team, away_team]:
            gains = list(self.gains[team])
            if len(gains) < 3:
                gains = [0] * (3 - len(gains)) + gains
            weighted_sum = sum(g * w for g, w in zip(gains, normalized_weights))
            self.team_form[team] = weighted_sum

    def simulate_season_outcome_n_times(self, N=1000):
        """Simulate future games N times."""
        all_simulations = []

        # Store the true values to reset after each simulation
        true_ratings = self.team_ratings.copy()
        true_form = self.team_form.copy()
        true_gains = {team: deque(self.gains[team], maxlen=3) for team in self.gains}

        for sim_number in range(1, N + 1):
            # Reset ratings, form, and gains to true values
            temp_ratings = true_ratings.copy()
            temp_form = true_form.copy()
            temp_gains = {team: deque(true_gains[team], maxlen=3) for team in true_gains}

            team_points = helper.get_table()

            print(f"Simulating outcome {sim_number}/{N}...")

            for season, rounds in self.future_matches.items():
                for round_name, matches in rounds.items():
                    for match in matches:
                        home_team = match['home_team']
                        away_team = match['away_team']

                        # Get H2H adjustment
                        adjustment_factor = self.DataManager.get_h2h_adjustment(home_team, away_team, self.k_factor)

                        # Calculate adjusted ratings
                        home_rating = temp_ratings[home_team] + temp_form.get(home_team, 0) * 5
                        away_rating = temp_ratings[away_team] + temp_form.get(away_team, 0) * 5

                        # Calculate home advantage
                        hfa = self.home_strength.get(home_team, 0) * 100
                        afa = self.away_strength.get(away_team, 0) * 100
                        home_advantage = hfa + (hfa - afa) / 2

                        # Calculate match probabilities
                        probabilities = self.calculate_match_probabilities(
                            home_rating, away_rating, home_advantage, adjustment_factor
                        )

                        # Simulate match outcome
                        rand = random.random()
                        if rand < probabilities['home_win']:
                            team_points[home_team] += 3
                            simulated_match = {
                                'date': match['date'],
                                'home_team': home_team,
                                'away_team': away_team,
                                'score': {'home': 2, 'away': 1},
                                'result': 'Home'
                            }
                        elif rand < probabilities['home_win'] + probabilities['draw']:
                            team_points[home_team] += 1
                            team_points[away_team] += 1
                            simulated_match = {
                                'date': match['date'],
                                'home_team': home_team,
                                'away_team': away_team,
                                'score': {'home': 1, 'away': 1},
                                'result': 'Draw'
                            }
                        else:
                            team_points[away_team] += 3
                            simulated_match = {
                                'date': match['date'],
                                'home_team': home_team,
                                'away_team': away_team,
                                'score': {'home': 1, 'away': 2},
                                'result': 'Away'
                            }

                        # Update ratings and form using the simulated match
                        # Update temp_ratings and temp_form instead of instance variables
                        initial_rating_home = temp_ratings[home_team]
                        initial_rating_away = temp_ratings[away_team]

                        # Process game to update ratings
                        expected_home = self.calculate_expected_score(home_rating, away_rating, home_advantage)
                        expected_away = 1 - expected_home

                        # Determine actual scores from simulated result
                        if simulated_match['result'] == 'Home':
                            actual_home, actual_away = 1, 0
                        elif simulated_match['result'] == 'Draw':
                            actual_home = actual_away = 0.5
                        else:
                            actual_home, actual_away = 0, 1

                        # Update ratings
                        decay_factor = helper.get_decay_factor(self.k_factor, simulated_match['date'])
                        new_rating_home = self.update_rating(
                            temp_ratings[home_team], actual_home, expected_home, decay_factor
                        )
                        new_rating_away = self.update_rating(
                            temp_ratings[away_team], actual_away, expected_away, decay_factor
                        )

                        temp_ratings[home_team] = new_rating_home
                        temp_ratings[away_team] = new_rating_away

                        # Calculate gains
                        gain_home = new_rating_home - initial_rating_home
                        gain_away = new_rating_away - initial_rating_away

                        # Update gains
                        temp_gains[home_team].append(gain_home)
                        temp_gains[away_team].append(gain_away)

                        # Recalculate team form
                        weights = [math.log(i ** 2 + 1) for i in range(1, 4)]
                        total_weight = sum(weights)
                        normalized_weights = [w / total_weight for w in weights]

                        for team in [home_team, away_team]:
                            gains = list(temp_gains[team])
                            if len(gains) < 3:
                                gains = [0] * (3 - len(gains)) + gains
                            weighted_sum = sum(g * w for g, w in zip(gains, normalized_weights))
                            temp_form[team] = weighted_sum

            all_simulations.append(team_points)

        print(f"Simulated {N} remaining outcomes.")
        print(helper.print_season_outcomes(all_simulations))

    def calculate_specific_game(self, home_team, away_team):
        """Calculate the probabilities for a specific game."""
        home_rating = self.team_ratings.get(home_team, self.initial_rating) + self.team_form.get(home_team, 0)
        away_rating = self.team_ratings.get(away_team, self.initial_rating) + self.team_form.get(away_team, 0)

        hfa = self.home_strength.get(home_team, 0) * 100
        afa = self.away_strength.get(away_team, 0) * 100
        home_advantage = hfa + (hfa - afa) / 2

        adjustment_factor = self.DataManager.get_h2h_adjustment(home_team, away_team, self.k_factor)

        probabilities = self.calculate_match_probabilities(
            home_rating, away_rating, home_advantage, adjustment_factor
        )

        # Print the probabilities
        print(f"Probabilities for {home_team} vs {away_team}:")
        print(f"  Home Win: {probabilities['home_win'] * 100:.2f}%")
        print(f"  Draw: {probabilities['draw'] * 100:.2f}%")
        print(f"  Away Win: {probabilities['away_win'] * 100:.2f}%")


elo = EloRatingSystem()
elo.run_elo_rating_system()
elo.simulate_season_outcome_n_times(1000)