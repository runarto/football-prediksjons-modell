from typing import Any, Dict, List
import helper
import sqlite3

class DataManager:
    def __init__(self, league_id: int, db_path: str = 'football.db'):
        self.db_path = db_path
        self.league_id = league_id

    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def get_team_elos(self) -> Dict[str, float]:
        query = "SELECT name, elo_rating FROM teams WHERE league_id = ?"
        with self._connect() as conn:
            cur = conn.execute(query, (self.league_id,))
            return {row[0]: row[1] for row in cur.fetchall()}
        
    def get_team_strengths(self) -> Dict[str, Dict[str, float]]:
        query = "SELECT name, home_strength, away_strength FROM teams WHERE league_id = ?"
        with self._connect() as conn:
            cur = conn.execute(query, (self.league_id,))
            return {
                row[0]: {"home": row[1], "away": row[2]}
                for row in cur.fetchall()
            }

    def get_future_matches(self) -> Dict[str, Dict[str, List[Dict]]]:
        query = "SELECT season, round, date, home_team, away_team, home_strength, away_strength, home_team_elo, away_team_elo FROM future_matches WHERE league_id = ?"
        future = {}
        with self._connect() as conn:
            cur = conn.execute(query, (self.league_id,))
            for row in cur.fetchall():
                season, rnd = row[0], row[1]
                if season not in future:
                    future[season] = {}
                if rnd not in future[season]:
                    future[season][rnd] = []
                future[season][rnd].append({
                    "date": row[2],
                    "home_team": row[3],
                    "away_team": row[4],
                    "home_strength": row[5],
                    "away_strength": row[6],
                    "home_team_elo": row[7],
                    "away_team_elo": row[8]
                })
        return future

    def get_fixtures(self) -> Dict[str, Dict[str, List[Dict]]]:
        query = "SELECT season, round, date, home_team, away_team, home_score, away_score, result FROM matches WHERE league_id = ?"
        fixtures = {}
        with self._connect() as conn:
            cur = conn.execute(query, (self.league_id,))
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
                    "result": row[7]
                })
        return fixtures

    def get_games_between_teams(self, team1: str, team2: str) -> List[Dict[str, Any]]:
        """
        Get games between two teams from the matches table.

        Parameters:
            team1 (str): Name of the first team.
            team2 (str): Name of the second team.

        Returns:
            List[Dict[str, Any]]: A list of matches between the two teams.
        """
        query = """
        SELECT season, round, date, home_team, away_team, home_score, away_score, result
        FROM matches
        WHERE league_id = ?
        AND ((home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?))
        ORDER BY date DESC
        """
        with self._connect() as conn:
            cur = conn.execute(query, (self.league_id, team1, team2, team2, team1))
            return [
                {
                    "season": row[0],
                    "round": row[1],
                    "date": row[2],
                    "home_team": row[3],
                    "away_team": row[4],
                    "score": {"home": row[5], "away": row[6]},
                    "result": row[7]
                }
                for row in cur.fetchall()
            ]

    def get_h2h_adjustment(self, home_team: str, away_team: str, k_factor: float, h2h_factor: float = 8) -> float:
        """
        Calculate the head-to-head adjustment factor between two teams.

        Parameters:
            team1 (str): Name of the home team.
            team2 (str): Name of the away team.
            k_factor (float): K-factor used in Elo calculations.
            h2h_factor (float): Scaling factor for H2H adjustment.

        Returns:
            float: The head-to-head adjustment value.
        """
        games = self.head2head(home_team, away_team)
        total_games = len(games)
        if total_games == 0:
            return 0  # No adjustment if no previous matches

        h2h_score = 0  # Initialize H2H score

        for game in games:
            result = helper.get_match_result(game, home_team)  # +1 win, 0 draw, -1 loss
            decay = helper.get_decay_factor(k_factor, game['date'])
            h2h_score += result * decay

        # Normalize the H2H score
        normalized_score = h2h_score / total_games  # Range between -1 and +1

        # Scale the adjustment
        adjustment = normalized_score * h2h_factor  # Adjust h2h_factor as needed

        return adjustment

    def set_strength(self) -> None:

        """
        Set the home strength values for teams.

        Parameters:
            home_strength (Dict[str, float]): A dictionary of home strength values for teams.
        """

        fixtures = self.load_json_data('fixtures.json')
        
        home_wins = {}
        away_wins = {}
        total_home_matches = {}
        total_away_matches = {}
        
        for season, round_matches in fixtures.items():
            for round, matches in round_matches.items():
                for match in matches:
                    home_team = match['home_team']
                    away_team = match['away_team']
        
                    if home_team not in home_wins:
                        home_wins[home_team] = 0
                    if away_team not in away_wins:
                        away_wins[away_team] = 0
                    if home_team not in total_home_matches:
                        total_home_matches[home_team] = 0
                    if away_team not in total_away_matches:
                        total_away_matches[away_team] = 0
        
                    total_home_matches[home_team] += 1
                    total_away_matches[away_team] += 1
        
                    if match['result'] == 'Home':
                        home_wins[home_team] += 1
                    elif match['result'] == 'Away':
                        away_wins[away_team] += 1
        
        # Calculate the fraction of wins for each team
        home_strength = {}
        for team, wins in home_wins.items():
            total_home = total_home_matches[team]
            if total_home > 0:
                win_fraction = wins / total_home
                home_strength[team] = win_fraction

        away_strength = {}
        for team, wins in away_wins.items():
            total_away = total_away_matches[team]
            if total_away > 0:
                win_fraction = wins / total_away
                away_strength[team] = win_fraction


        self.home_strength = home_strength
        self.save_json_data(home_strength, 'home_strength.json')

        self.away_strength = away_strength
        self.save_json_data(away_strength, 'away_strength.json')

    def set_elo(self, elo: Dict[str, float]) -> None:
        """
        Set the Elo ratings for teams.

        Parameters:
            team_elo (Dict[str, float]): A dictionary of Elo ratings for teams.
        """
        self.team_elo = elo
        self.save_json_data(elo, 'team_elo.json')
