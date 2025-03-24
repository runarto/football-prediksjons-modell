import math
import random
from collections import deque
from . import helper
from .data_manager import DataManager
import logging

"""
This module contains the EloRatingSystem class, which implements an Elo rating system for football predictions.

Features:
- Processes historical match data to calculate team ratings.
- Adjusts ratings based on match outcomes, home advantage, and time decay.
- Incorporates team form and head-to-head adjustments into match probability calculations.
- Simulates future matches to predict season outcomes.
"""

class EloRatingSystem:
    def __init__(self, league_ids, initial_rating=1500, k_factor=3):

        self.league_initial_ratings = {
            103: 1500,  # Eliteserien
            104: 1300,   # OBOS-ligaen
            105: 1250   # 2. divisjon
        }

        self.league_weights = {
            103: 1.0,   # Eliteserien
            104: 0.75   # OBOS-ligaen
        }

        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.DataManager = DataManager(league_ids)

        self.team_ratings = self.DataManager.get_team_elos() # Elo ratings for teams in league
        self.team_strengths = self.DataManager.get_team_strengths() # Home and away strengths for teams in league
        self.fixtures = self.DataManager.get_fixtures() # Historical match data
        self.future_matches = self.DataManager.get_future_matches() # Future match data
        self.team_form, self.gains = self.init_form() # Form tracking for teams


    def initialize_team_ratings(self):
        """Initialize team ratings based on their league (tier) and print them."""

        # Step 1: Gather all teams
        all_teams = set(self.team_strengths.keys())
        for season in self.fixtures.values():
            for round_matches in season.values():
                for match in round_matches:
                    all_teams.update([match['home_team'], match['away_team']])
        for season in self.future_matches.values():
            for round_matches in season.values():
                for match in round_matches:
                    all_teams.update([match['home_team'], match['away_team']])

        # Step 2: Get team league mappings
        team_league_map = {}

        season_2024 = self.fixtures.get("2024", {})

        for round_data in season_2024.values():
            for match in round_data:
                league_id = match.get("league_id", 105)  # Default to Eliteserien
                home_team = match["home_team"].upper()
                away_team = match["away_team"].upper()

                team_league_map[home_team] = league_id
                team_league_map[away_team] = league_id

        # Step 3: Assign rating based on league
        for team in sorted(all_teams):
            league_id = team_league_map.get(team, 105)  # Default to top league if unknown
            base_rating = self.league_initial_ratings.get(league_id, self.initial_rating)
            self.team_ratings[team] = base_rating

        print("\n📊 Team Elo Ratings (By Division):")
        for team, rating in sorted(self.team_ratings.items(), key=lambda x: x[1], reverse=True):
            print(f" - {team:<20} {rating:.2f}")


    def update_rating(self, adjusted_k, current_rating, actual_score, expected_score, decay_factor):
        """Update the Elo rating for a team."""
        return current_rating + adjusted_k * decay_factor * (actual_score - expected_score)

    def process_game(self, game):
         """Process a single game and update team ratings."""
         home_team = game['home_team']
         away_team = game['away_team']
         home_score = game['score']['home']
         away_score = game['score']['away']
         match_date = game['date']
         league_id = game['league_id']

         scaling_factor = 1 if league_id == 103 else 0.9
 
         # Initialize team ratings if they don't exist
         for team in [home_team, away_team]:
             if team not in self.team_ratings:
                 self.team_ratings[team] = self.initial_rating
             self.team_ratings.setdefault(team, self.initial_rating)
 
         # Get current ratings
         rating_home = self.team_ratings[home_team]
         rating_away = self.team_ratings[away_team]
 
         # Calculate home field advantage
         hfa = self.team_strengths.get(home_team, {}).get('home', 1) * 100
         afa = self.team_strengths.get(away_team, {}).get('away', 1) * 100
         hfa_adjusted = hfa + (hfa - afa) / 2
         home_advantage = hfa + (hfa - afa) / 2
 
         # Calculate expected scores
         expected_home = self.calculate_expected_score(rating_home, rating_away, hfa_adjusted)
         expected_away = 1 - expected_home  # Expected score for away team
         expected_home = self.calculate_expected_score(rating_home, rating_away, home_advantage)
         expected_away = 1 - expected_home
 
         # Determine actual scores
         if home_score > away_score:
             actual_home = 1
             actual_away = 0
         elif home_score < away_score:
             actual_home = 0
             actual_away = 1
         if home_score - away_score > 0.12:
             actual_home, actual_away = 1, 0
         elif home_score - away_score < -0.12:
             actual_home, actual_away = 0, 1
         else:
             actual_home = actual_away = 0.5
 
         # Calculate decay factor
         weight = self.league_weights.get(league_id, 1.0)

         adjusted_k = self.k_factor * weight
         decay_factor = helper.get_decay_factor(adjusted_k, match_date, True)

         new_rating_home = self.update_rating(adjusted_k, rating_home, actual_home, expected_home, decay_factor)
         new_rating_away = self.update_rating(adjusted_k, rating_away, actual_away, expected_away, decay_factor)
 
         # Save updated ratings
         self.team_ratings[home_team] = new_rating_home
         self.team_ratings[away_team] = new_rating_away
 
         # Print match result and rating updates (optional)
        #  print(f"    {home_team} {home_score} - {away_score} {away_team}")
        #  print(f"      {home_team} rating: {rating_home:.2f} -> {new_rating_home:.2f}")
        #  print(f"      {away_team} rating: {rating_away:.2f} -> {new_rating_away:.2f}")

    def process_round(self, games):
        for game in games:
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
        logging.basicConfig(level=logging.INFO)
        """Calculate the initial form of each team based on recent performance."""
        form_deques = {team: deque(maxlen=3) for team in self.team_ratings}

        for season, rounds in self.fixtures.items():
            if len(rounds) < 3:
                logging.warning(f"⏸ Season {season} has fewer than 3 rounds — skipping form calc.")
                return (
                    {team: 0.0 for team in self.team_ratings},
                    {team: deque(maxlen=3) for team in self.team_ratings}
                )

            for round_name, matches in rounds.items():
                for match in matches:
                    home_team = match['home_team']
                    away_team = match['away_team']

                    if home_team not in self.team_ratings or away_team not in self.team_ratings:
                        logging.warning(f"⚠️ Skipping match {home_team} vs {away_team} — team(s) missing rating.")
                        continue

                    initial_rating_home = self.team_ratings[home_team]
                    initial_rating_away = self.team_ratings[away_team]

                    self.process_game(match)

                    gain_home = self.team_ratings[home_team] - initial_rating_home
                    gain_away = self.team_ratings[away_team] - initial_rating_away

                    self.team_ratings[home_team] = initial_rating_home
                    self.team_ratings[away_team] = initial_rating_away

                    form_deques[home_team].append(gain_home)
                    form_deques[away_team].append(gain_away)

        weights = [math.log(i ** 2 + 1) for i in range(1, 4)]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        team_form = {}
        team_gains = {}

        for team in self.team_ratings:
            gains = list(form_deques.get(team, deque()))
            team_gains[team] = deque(gains, maxlen=3)

            if len(gains) < 3:
                logging.info(f"ℹ️ Padding form for {team} with zeros — only {len(gains)} games.")
                gains = [0] * (3 - len(gains)) + gains

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

    def calculate_expected_score(self, rating_a, rating_b, home_field_advantage):
         """Calculate the expected score for a team."""
         exponent = (rating_b - rating_a + home_field_advantage) / 400
         expected_score_a = 1 / (1 + 10 ** exponent)
         return expected_score_a
