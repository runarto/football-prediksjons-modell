import math
import random
from collections import deque
import helper
import data_manager as DataManager

"""
This module contains the EloRatingSystem class, which implements an Elo rating system for football predictions.

Features:
- Processes historical match data to calculate team ratings.
- Adjusts ratings based on match outcomes, home advantage, and time decay.
- Incorporates team form and head-to-head adjustments into match probability calculations.
- Simulates future matches to predict season outcomes.
"""

class EloRatingSystem:
    def __init__(self, league_id, initial_rating=1500, k_factor=5):

        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.DataManager = DataManager(league_id)

        self.team_ratings = self.DataManager.get_team_elos() # Elo ratings for teams in league
        self.team_strengths = self.DataManager.get_team_strengths() # Home and away strengths for teams in league
        self.fixtures = self.DataManager.get_fixtures() # Historical match data
        self.future_matches = self.DataManager.get_future_matches() # Future match data
        self.team_form, self.gains = self.init_form() # Form tracking for teams


    def initialize_team_ratings(self):
        for team in self.team_strengths:
            self.team_ratings[team] = self.initial_rating

    def update_rating(self, current_rating, actual_score, expected_score, decay_factor):
        """Update the Elo rating for a team."""
        return current_rating + self.k_factor * decay_factor * (actual_score - expected_score)

    def process_game(self, game):
        home = game['home_team']
        away = game['away_team']
        home_score = game['score']['home']
        away_score = game['score']['away']

        if home not in self.team_ratings or away not in self.team_ratings:
            return

        result = 1 if home_score > away_score else 0 if home_score < away_score else 0.5

        rating_home = self.team_ratings[home]
        rating_away = self.team_ratings[away]

        home_advantage = 100  # could be adjusted based on strengths
        expected_home = self.calculate_expected_score(rating_home, rating_away, home_advantage)
        decay_factor = helper.get_decay_factor(game['date'])

        self.team_ratings[home] = self.update_rating(rating_home, result, expected_home, decay_factor)
        self.team_ratings[away] = self.update_rating(rating_away, 1 - result, 1 - expected_home, decay_factor)

        self.team_form[home].append(result)
        self.team_form[away].append(1 - result)

    def process_round(self, games_list):
        for game in games_list:
            self.process_game(game)

    def process_season(self):
        for season in self.fixtures:
            for rnd in self.fixtures[season]:
                self.process_round(self.fixtures[season][rnd])

    def run_elo_rating_system(self):
        self.initialize_team_ratings()
        self.process_season()

    def calculate_match_probabilities(self, home_team, away_team):
        rating_home = self.team_ratings.get(home_team, self.initial_rating)
        rating_away = self.team_ratings.get(away_team, self.initial_rating)

        form_home = sum(self.team_form[home_team]) / len(self.team_form[home_team]) if self.team_form[home_team] else 0.5
        form_away = sum(self.team_form[away_team]) / len(self.team_form[away_team]) if self.team_form[away_team] else 0.5

        advantage = 100
        base_prob = self.calculate_expected_score(rating_home, rating_away, advantage)
        adjusted = base_prob * 0.7 + form_home * 0.15 + (1 - form_away) * 0.15

        return {
            'home_win': round(adjusted, 3),
            'draw': round(1 - abs(0.5 - adjusted), 3),
            'away_win': round(1 - adjusted, 3)
        }

    def init_form(self):
        """Calculate the initial form of each team based on recent performance."""
        # Initialize form tracking deques for each team
        form_deques = {team: deque(maxlen=3) for team in self.team_ratings}

        for season, rounds in self.fixtures.items():
            for round_name, matches in rounds.items():

                if len(rounds) < 3: # If the current season has less than three rounds played, ignore form. 
                    return {team: 0 for team in self.team_ratings}, {team: deque(maxlen=3) for team in self.team_ratings}

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
        print(all_simulations)
        print(helper.print_rank_probability_distribution(all_simulations))

    def calculate_specific_game(self, home_team, away_team):
        """Calculate the probabilities for a specific game."""
        home_rating = self.team_ratings.get(home_team, self.initial_rating) + self.team_form.get(home_team, 0)
        away_rating = self.team_ratings.get(away_team, self.initial_rating) + self.team_form.get(away_team, 0)

        hfa = self.home_strength.get(home_team, 0) * 100
        afa = self.away_strength.get(away_team, 0) * 100
        home_advantage = hfa + (hfa - afa) / 2

        adjustment_factor = self.DataManager.get_h2h_adjustment(home_team, away_team, self.k_factor)*25

        probabilities = self.calculate_match_probabilities(
            home_rating, away_rating, home_advantage, adjustment_factor
        )

        # Print the probabilities
        print(f"Probabilities for {home_team} vs {away_team}:")
        print(f"  Home Win: {probabilities['home_win'] * 100:.2f}%")
        print(f"  Draw: {probabilities['draw'] * 100:.2f}%")
        print(f"  Away Win: {probabilities['away_win'] * 100:.2f}%")


