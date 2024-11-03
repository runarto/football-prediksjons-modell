import requests
import json
import helper
import file

from config import API_TOKEN, ES_ID

def get_previous_matches(seasons: list, league_id: int, api_token: str):
    """
    Fetches the played matches for the given seasons and league.
    """

    season_matches = {}

    for season in seasons:
        api_url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": api_token  # Be cautious with your API key
        }
        query_fixtures = {
            "league": league_id,
            "season": season,
            "timezone": "Europe/Oslo",
        }
        
        response = requests.get(api_url, headers=headers, params=query_fixtures)
        if response.status_code == 200:
            data = response.json()
            round_matches = {}
            for fixture in data['response']:
                round = fixture['league']['round']

                if round == "Relegation Round":
                    continue

                home_team = fixture['teams']['home']['name'].upper()
                away_team = fixture['teams']['away']['name'].upper()
                if home_team == "VIKING" and away_team == "SANDEFJORD":
                    print("breakpoint")

                result = helper.determine_result(fixture)

                result_mapping = {
                    "NaN": "NaN",
                    True: "Home",
                    False: "Away",
                    None: "Draw"
                }

                if result_mapping[result] == "NaN":
                    continue
                else:
                    result = result_mapping[result]


                match_info = {
                    'date': fixture['fixture']['date'],
                    'home_team': fixture['teams']['home']['name'].upper(),
                    'away_team': fixture['teams']['away']['name'].upper(),
                    'score': fixture['score']['fulltime'],
                    'result': result
                }
                if round in round_matches:
                    round_matches[round].append(match_info)
                else:
                    round_matches[round] = [match_info]
            season_matches[season] = round_matches
        else:
            print(f"Failed to fetch data for season {season}: {response.status_code}")
    
    return season_matches


def get_future_matches(seasons: list, league_id: int, api_token: str):
    """
    Fetches the future matches for the given seasons and league.
    """

    home_strength = file.load_json_data('jsonfiles/home_strength.json')
    away_strength = file.load_json_data('jsonfiles/away_strength.json')
    elo = file.load_json_data('jsonfiles/team_elo.json')

    season_matches = {}
    for season in seasons:
        api_url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": api_token  # Be cautious with your API key
        }
        query_fixtures = {
            "league": league_id,
            "season": season,
            "timezone": "Europe/Oslo",
        }
        
        response = requests.get(api_url, headers=headers, params=query_fixtures)
        if response.status_code == 200:
            data = response.json()
            round_matches = {}
            for fixture in data['response']:
                round = fixture['league']['round']
                home_team = fixture['teams']['home']['name'].upper()
                away_team = fixture['teams']['away']['name'].upper()

                if home_team == "VIKING" and away_team == "SANDEFJORD":
                    print("breakpoint")

                result = helper.determine_result(fixture)

                result_mapping = {
                    "NaN": "NaN",
                    True: "Home",
                    False: "Away",
                    None: "Draw"
                }

                if result_mapping[result] != "NaN":
                    continue
                else:
                    result = result_mapping[result]


                match_info = {
                    'date': fixture['fixture']['date'],
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_strength': home_strength.get(home_team, 1),
                    'away_strength': away_strength.get(away_team, 1),
                    'home_team_elo': elo.get(home_team, 1),
                    'away_team_elo': elo.get(away_team, 1)
                }
                if round in round_matches:
                    round_matches[round].append(match_info)
                else:
                    round_matches[round] = [match_info]
            season_matches[season] = round_matches
        else:
            print(f"Failed to fetch data for season {season}: {response.status_code}")
    
    return season_matches


def get_eliteserien_table(api_token: str, league_id: int, season: str):
    """
    Fetches the current table from the season and league specified by league_id.
    """

 
    api_url = "https://v3.football.api-sports.io/standings"
    headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": api_token  # Be cautious with your API key
    }

    query_fixtures = {
            "league": league_id,
            "season": season
        }

    response = requests.get(api_url, headers=headers, params=query_fixtures)

    if response.status_code == 200:
        data = response.json()

        # Extract the standings
        standings = data['response'][0]['league']['standings'][0]
        print(standings)

        # Create a dictionary to store the standings
        eliteserien_table = {}
        for team_info in standings:
            team_name = team_info['team']['name']
            position = team_info['rank']
            played_games = team_info['all']['played']
            won = team_info['all']['win']
            draw = team_info['all']['draw']
            lost = team_info['all']['lose']
            goals_for = team_info['all']['goals']['for']
            goals_against = team_info['all']['goals']['against']
            points = team_info['points']

            # Add the team's data to the dictionary
            eliteserien_table[team_name] = {
                'position': position,
                'played_games': played_games,
                'won': won,
                'draw': draw,
                'lost': lost,
                'goals_for': goals_for,
                'goals_against': goals_against,
                'points': points
            }

        return eliteserien_table
    else:
        print(f"Failed to retrieve data: {response.status_code} - {response.reason}")
        return None


