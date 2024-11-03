import os
import json
from typing import Any, Dict, List
import API
from config import API_TOKEN, ES_ID
import helper

class DataManager:
    def __init__(self, data_dir: str = 'jsonfiles'):
        """
        Initialize the DataManager with the directory containing the data files.

        Parameters:
            data_dir (str): The directory where data files are stored.
        """
        self.data_dir = data_dir
        self.ES_ID = ES_ID
        self.API_TOKEN = API_TOKEN

        # Load data files
        self.fixtures = self.load_json_data('fixtures.json')
        self.future_matches = self.load_json_data('future_matches.json')
        self.home_strength = self.load_json_data('home_strength.json')
        self.away_strength = self.load_json_data('away_strength.json')
        self.team_elo = self.load_json_data('team_elo.json')

    def load_json_data(self, filename: str) -> Any:
        """
        Load JSON data from a file.

        Parameters:
            filename (str): The name of the JSON file to load.

        Returns:
            Any: The data loaded from the JSON file.
        """
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from {file_path}: {e}")

    def save_json_data(self, data: Any, filename: str) -> None:
        """
        Save data to a JSON file.

        Parameters:
            data (Any): The data to save.
            filename (str): The name of the JSON file to save data to.
        """
        file_path = os.path.join(self.data_dir, filename)
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Saved data to {file_path}")
        except IOError as e:
            raise IOError(f"Error saving data to {file_path}: {e}")

    def get_future_matches(self, seasons: List[str], league_id: int = None, api_token: str = None) -> Dict[str, Any]:
        """
        Fetch and save future matches data.

        Parameters:
            seasons (List[str]): List of seasons to fetch data for.
            league_id (int): League ID. Defaults to class attribute ES_ID.
            api_token (str): API token. Defaults to class attribute API_TOKEN.

        Returns:
            Dict[str, Any]: A dictionary containing future games.
        """
        if league_id is None:
            league_id = self.ES_ID
        if api_token is None:
            api_token = self.API_TOKEN

        future_matches = API.get_future_matches(seasons, league_id, api_token)
        self.save_json_data(future_matches, 'future_matches.json')
        self.future_matches = future_matches  # Update the instance variable
        return future_matches

    def get_previous_matches(self, seasons: List[str], league_id: int = None, api_token: str = None) -> Dict[str, Any]:
        """
        Fetch and save previous matches data.

        Parameters:
            seasons (List[str]): List of seasons to fetch data for.
            league_id (int): League ID. Defaults to class attribute ES_ID.
            api_token (str): API token. Defaults to class attribute API_TOKEN.

        Returns:
            Dict[str, Any]: A dictionary containing previous games played.
        """
        if league_id is None:
            league_id = self.ES_ID
        if api_token is None:
            api_token = self.API_TOKEN

        fixtures = API.get_previous_matches(seasons, league_id, api_token)
        self.save_json_data(fixtures, 'fixtures.json')
        self.fixtures = fixtures  # Update the instance variable
        return fixtures

    def get_games_between_teams(self, team1: str, team2: str, files: List[str]) -> List[Dict[str, Any]]:
        """
        Get games between two teams from specified data files.

        Parameters:
            team1 (str): Name of the first team.
            team2 (str): Name of the second team.
            files (List[str]): List of JSON file names to search in.

        Returns:
            List[Dict[str, Any]]: A list of games between the two teams.
        """
        games = []
        for filename in files:
            data = self.load_json_data(filename)
            for season_data in data.values():
                for matches in season_data.values():
                    for match in matches:
                        home_team = match.get('home_team')
                        away_team = match.get('away_team')
                        if {home_team, away_team} == {team1, team2}:
                            games.append(match)
        return games

    def head2head(self, team1: str, team2: str) -> List[Dict[str, Any]]:
        """
        Get head-to-head games between two teams.

        Parameters:
            team1 (str): Name of the first team.
            team2 (str): Name of the second team.

        Returns:
            List[Dict[str, Any]]: A list of head-to-head games between the two teams.
        """
        files = ['fixtures.json']
        return self.get_games_between_teams(team1, team2, files)

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
