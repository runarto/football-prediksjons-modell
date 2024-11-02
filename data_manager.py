import os
import json
from typing import Any, Dict
import API
from config import API_TOKEN
from config import ES_ID

class DataManager:
    def __init__(self, data_dir: str = 'jsonfiles'):
        """
        Initialize the DataManager with the directory containing the data files.

        Parameters:
            data_dir (str): The directory where data files are stored.
        """

        self.ES_ID = ES_ID
        self.API_TOKEN = API_TOKEN


        self.data_dir = data_dir
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
            print(f"Loaded data from {file_path}")
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
            raise IOError(f"Error saving data to {filename}: {e}")

    def get_future_matches(self, seasons: list, league_id: int=ES_ID, api_token: str=API_TOKEN) -> Dict[str, Any]:
        """
        Load and return the team data.

        Returns:
            Dict[str, Any]: A dictionary containing future games.
        """
        future_matches = API.get_future_matches(seasons, league_id, api_token)
        self.save_json_data(future_matches, 'future_matches.json')
        
    
    def get_previous_matches(self, seasons: list, league_id: int = None, api_token: str = None) -> Dict[str, Any]:
        """
        Load and return the previous matches data.

        Returns:
            Dict[str, Any]: A dictionary containing previous games played.
        """
        if league_id is None:
            league_id = self.ES_ID  # Access the class attribute
        if api_token is None:
            api_token = self.API_TOKEN  # Access the class attribute

        self.fixtures = API.get_previous_matches(seasons, league_id, api_token)
        self.save_json_data(self.fixtures, 'fixtures.json')

    
    def get_games_between_teams(self, team1: str, team2: str, files: list) -> list:
        """
        Get games between two teams.

        Returns:
            list: A list of games between the two teams.
        """
        games = []
    
        for file in files:
            data = self.load_json_data(file)
            for seasons, rounds in data.items():
                for round_name, matches in rounds.items():
                    for match in matches:
                        if (match['home_team'] == team1 and match['away_team'] == team2) or \
                           (match['home_team'] == team2 and match['away_team'] == team1):
                            games.append(match)
    
        return games






        

