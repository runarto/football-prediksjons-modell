from typing import Any, Dict, List
from . import helper
import sqlite3

class DataManager:
    def __init__(self, league_ids: List[int], db_path: str = 'football.db'):
        self.db_path = db_path
        self.league_ids = league_ids
        

    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def get_team_elos(self) -> Dict[str, float]:
        """
        Fetch the ELO ratings for all teams across the specified league IDs.
        """
        query = (
            f"SELECT name, elo_rating FROM teams "
            f"WHERE league_id IN ({','.join(['?'] * len(self.league_ids))})"
        )
        with self._connect() as conn:
            cur = conn.execute(query, self.league_ids)
            return {row[0]: row[1] for row in cur.fetchall()}
      
    def get_team_strengths(self) -> Dict[str, Dict[str, float]]:
        """
        Fetch home and away strength values for all teams in the specified leagues.
        """
        placeholders = ','.join(['?'] * len(self.league_ids))
        query = f"""
            SELECT name, home_strength, away_strength
            FROM teams
            WHERE league_id IN ({placeholders})
        """
        with self._connect() as conn:
            cur = conn.execute(query, self.league_ids)
            return {
                row[0]: {
                    "home": row[1],
                    "away": row[2]
                }
                for row in cur.fetchall()
            }


    def get_future_matches(self) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Fetch future matches across multiple leagues, grouped by season and round.
        Each match includes its league_id.
        The season is hardcoded as '2025'.
        """
        placeholders = ','.join(['?'] * len(self.league_ids))
        query = f"""
            SELECT round, date, home_team, away_team,
                home_strength, away_strength, home_team_elo, away_team_elo, league_id
            FROM future_matches
            WHERE league_id IN ({placeholders})
            ORDER BY date ASC
        """

        future = {"2025": {}}
        with self._connect() as conn:
            cur = conn.execute(query, self.league_ids)
            for row in cur.fetchall():
                rnd = row[0]
                if rnd not in future["2025"]:
                    future["2025"][rnd] = []
                future["2025"][rnd].append({
                    "date": row[1],
                    "home_team": row[2],
                    "away_team": row[3],
                    "home_strength": row[4],
                    "away_strength": row[5],
                    "home_team_elo": row[6],
                    "away_team_elo": row[7],
                    "league_id": row[8]
                })
        return future

    def get_fixtures(self) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Fetch historical fixtures from multiple leagues, grouped by season and round.
        Each match includes its league_id.
        """
        placeholders = ','.join(['?'] * len(self.league_ids))
        query = f"""
            SELECT season, round, date, home_team, away_team,
                home_score, away_score, result, league_id
            FROM matches
            WHERE league_id IN ({placeholders})
            ORDER BY date ASC
        """

        fixtures = {}
        with self._connect() as conn:
            cur = conn.execute(query, self.league_ids)
            for row in cur.fetchall():
                season, rnd = row[0], row[1]
                if season not in fixtures:
                    fixtures[season] = {}
                if rnd not in fixtures[season]:
                    fixtures[season][rnd] = []
                fixtures[season][rnd].append({
                    "date": row[2],
                    "home_team": row[3],
                    "away_team": row[4],
                    "score": {"home": row[5], "away": row[6]},
                    "result": row[7],
                    "league_id": row[8]
                })
        return fixtures

    def get_games_between_teams(self, team1: str, team2: str) -> List[Dict[str, Any]]:
        """
        Get all matches between two teams across all configured leagues.

        Parameters:
            team1 (str): Name of the first team.
            team2 (str): Name of the second team.

        Returns:
            List[Dict[str, Any]]: A list of match dictionaries between the two teams.
        """
        placeholders = ','.join(['?'] * len(self.league_ids))
        query = f"""
            SELECT season, round, date, home_team, away_team, home_score, away_score, result, league_id
            FROM matches
            WHERE league_id IN ({placeholders})
            AND (
                (home_team = ? AND away_team = ?) OR
                (home_team = ? AND away_team = ?)
            )
            ORDER BY date DESC
        """
        params = self.league_ids + [team1, team2, team2, team1]

        with self._connect() as conn:
            cur = conn.execute(query, params)
            return [
                {
                    "season": row[0],
                    "round": row[1],
                    "date": row[2],
                    "home_team": row[3],
                    "away_team": row[4],
                    "score": {"home": row[5], "away": row[6]},
                    "result": row[7],
                    "league_id": row[8]
                }
                for row in cur.fetchall()
            ]

    def get_h2h_adjustment(self, home_team: str, away_team: str, k_factor: float, h2h_factor: float = 8) -> float:
        """
        Calculate the head-to-head adjustment factor between two teams.

        Parameters:
            home_team (str): Name of the home team.
            away_team (str): Name of the away team.
            k_factor (float): K-factor used in Elo calculations.
            h2h_factor (float): Scaling factor for H2H adjustment.

        Returns:
            float: The head-to-head adjustment value.
        """
        games = self.get_games_between_teams(home_team, away_team)
        total_games = len(games)
        if total_games == 0:
            return 0  # No adjustment if no previous matches

        h2h_score = 0  # Initialize H2H score

        for game in games:
            result = helper.get_match_result(game, home_team)  # +1 win, 0 draw, -1 loss
            decay = helper.get_decay_factor(k_factor, game['date'])
            h2h_score += result * decay

        normalized_score = h2h_score / total_games
        adjustment = normalized_score * h2h_factor

        return adjustment

    def set_strength(self) -> None:
        """
        Calculate and update home/away strengths for all teams into the database.
        """
        fixtures = self.get_fixtures()

        home_wins = {}
        away_wins = {}
        total_home_matches = {}
        total_away_matches = {}

        for season, round_matches in fixtures.items():
            for round_name, matches in round_matches.items():
                for match in matches:
                    home_team = match['home_team']
                    away_team = match['away_team']

                    home_wins.setdefault(home_team, 0)
                    away_wins.setdefault(away_team, 0)
                    total_home_matches.setdefault(home_team, 0)
                    total_away_matches.setdefault(away_team, 0)

                    total_home_matches[home_team] += 1
                    total_away_matches[away_team] += 1

                    if match['result'] == 'Home':
                        home_wins[home_team] += 1
                    elif match['result'] == 'Away':
                        away_wins[away_team] += 1

        home_strength = {
            team: wins / total_home_matches[team]
            for team, wins in home_wins.items() if total_home_matches[team] > 0
        }
        away_strength = {
            team: wins / total_away_matches[team]
            for team, wins in away_wins.items() if total_away_matches[team] > 0
        }

        with self._connect() as conn:
            for team, strength in home_strength.items():
                conn.execute("UPDATE teams SET home_strength = ? WHERE name = ?", (strength, team))
            for team, strength in away_strength.items():
                conn.execute("UPDATE teams SET away_strength = ? WHERE name = ?", (strength, team))
            conn.commit()

    def set_elo(self, elo: Dict[str, float]) -> None:
        """
        Update the Elo ratings for teams in the database.

        Parameters:
            elo (Dict[str, float]): A dictionary of Elo ratings for teams.
        """
        with self._connect() as conn:
            for team, rating in elo.items():
                conn.execute("UPDATE teams SET elo_rating = ? WHERE name = ?", (rating, team))
            conn.commit()


