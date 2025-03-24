import random
import math
from collections import deque
from . import helper
from .elo_system import EloRatingSystem

class Simulator:
    def __init__(self, league_id):
        self.elo_model = EloRatingSystem(league_id)
        self.elo_model.run_elo_rating_system()
        self.league_id = league_id
        self.k_factor = self.elo_model.k_factor
        self.DataManager = self.elo_model.DataManager
        self.future_matches = self.elo_model.future_matches
        self.home_strength = {
            team: values['home'] for team, values in self.elo_model.team_strengths.items()
        }
        self.away_strength = {
            team: values['away'] for team, values in self.elo_model.team_strengths.items()
        }

    def simulate_season_outcome_n_times(self, N=1000):
        all_simulations = []

        true_ratings = self.elo_model.team_ratings.copy()
        true_form = self.elo_model.team_form.copy()
        true_gains = {team: deque(self.elo_model.gains[team], maxlen=3) for team in self.elo_model.gains}

        for sim_number in range(1, N + 1):
            temp_ratings = true_ratings.copy()
            temp_form = true_form.copy()
            temp_gains = {team: deque(true_gains[team], maxlen=3) for team in true_gains}

            team_points = helper.get_table(self.league_id)
            print(f"Simulating outcome {sim_number}/{N}...")

            for season, rounds in self.future_matches.items():
                for round_name, matches in rounds.items():
                    for match in matches:
                        home_team = match['home_team']
                        away_team = match['away_team']

                        adjustment_factor = self.DataManager.get_h2h_adjustment(home_team, away_team, self.k_factor)

                        home_rating = temp_ratings[home_team] + temp_form.get(home_team, 0) * 5
                        away_rating = temp_ratings[away_team] + temp_form.get(away_team, 0) * 5

                        hfa = self.home_strength.get(home_team, 0) * 100
                        afa = self.away_strength.get(away_team, 0) * 100
                        home_advantage = hfa + (hfa - afa) / 2

                        probabilities = self.elo_model.calculate_match_probabilities(
                            home_team, away_team, home_advantage, adjustment_factor
                        )

                        rand = random.random()
                        if rand < probabilities['home_win']:
                            team_points[home_team] += 3
                            simulated_match = {'result': 'Home'}
                        elif rand < probabilities['home_win'] + probabilities['draw']:
                            team_points[home_team] += 1
                            team_points[away_team] += 1
                            simulated_match = {'result': 'Draw'}
                        else:
                            team_points[away_team] += 3
                            simulated_match = {'result': 'Away'}

                        expected_home = self.elo_model.calculate_expected_score(
                            home_rating, away_rating, home_advantage)
                        expected_away = 1 - expected_home

                        if simulated_match['result'] == 'Home':
                            actual_home, actual_away = 1, 0
                        elif simulated_match['result'] == 'Draw':
                            actual_home = actual_away = 0.5
                        else:
                            actual_home, actual_away = 0, 1

                        decay_factor = helper.get_decay_factor(self.k_factor, match['date'])
                        new_rating_home = self.elo_model.update_rating(
                            temp_ratings[home_team], actual_home, expected_home, decay_factor)
                        new_rating_away = self.elo_model.update_rating(
                            temp_ratings[away_team], actual_away, expected_away, decay_factor)

                        initial_rating_home = temp_ratings[home_team]
                        initial_rating_away = temp_ratings[away_team]
                        gain_home = new_rating_home - initial_rating_home
                        gain_away = new_rating_away - initial_rating_away

                        temp_ratings[home_team] = new_rating_home
                        temp_ratings[away_team] = new_rating_away

                        temp_gains[home_team].append(gain_home)
                        temp_gains[away_team].append(gain_away)

                        weights = [math.log(i ** 2 + 1) for i in range(1, 4)]
                        total_weight = sum(weights)
                        normalized_weights = [w / total_weight for w in weights]

                        for team in [home_team, away_team]:
                            gains = list(temp_gains[team])
                            if len(gains) < 3:
                                gains = [0] * (3 - len(gains)) + gains
                            temp_form[team] = sum(g * w for g, w in zip(gains, normalized_weights))

            all_simulations.append(team_points)

        print(f"Simulated {N} remaining outcomes.")
        print(all_simulations)
        print(helper.print_rank_probability_distribution(all_simulations))

    def calculate_specific_game(self, home_team, away_team):
        home_rating = self.elo_model.team_ratings.get(home_team, self.elo_model.initial_rating) + self.elo_model.team_form.get(home_team, 0)
        away_rating = self.elo_model.team_ratings.get(away_team, self.elo_model.initial_rating) + self.elo_model.team_form.get(away_team, 0)

        hfa = self.home_strength.get(home_team, 0) * 100
        afa = self.away_strength.get(away_team, 0) * 100
        home_advantage = hfa + (hfa - afa) / 2

        adjustment_factor = self.DataManager.get_h2h_adjustment(home_team, away_team, self.k_factor) * 25

        probabilities = self.elo_model.calculate_match_probabilities(
            home_team, away_team, home_advantage, adjustment_factor
        )

        print(f"Probabilities for {home_team} vs {away_team}:")
        print(f"  Home Win: {probabilities['home_win'] * 100:.2f}%")
        print(f"  Draw: {probabilities['draw'] * 100:.2f}%")
        print(f"  Away Win: {probabilities['away_win'] * 100:.2f}%")
