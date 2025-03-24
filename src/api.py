import requests
import re
from . import helper
from .migration import migrate_fixtures_to_sqlite, migrate_future_to_sqlite
from . import data_manager
from .config import API_TOKEN

NORWAY_LEAGUES = [103, 104]


def clean_round_label(round_str: str) -> str | None:
    """
    Extracts the numeric round from a round string.
    Skips rounds related to promotion/relegation play-offs.
    """
    if any(x in round_str for x in ["Play-off", "Relegation"]):
        return None
    match = re.search(r"(\d+)$", round_str)
    return match.group(1) if match else round_str


def get_previous_matches(seasons: list, country_league_ids: list = NORWAY_LEAGUES):
    for league_id in country_league_ids:
        season_matches = {}

        for season in seasons:
            api_url = "https://v3.football.api-sports.io/fixtures"
            headers = {
                "x-rapidapi-host": "v3.football.api-sports.io",
                "x-rapidapi-key": API_TOKEN
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
                    raw_round = fixture['league']['round']
                    gw = clean_round_label(raw_round)

                    if gw is None:
                        continue

                    home_team = fixture['teams']['home']['name'].upper()
                    away_team = fixture['teams']['away']['name'].upper()

                    result = helper.determine_result(fixture)
                    result_mapping = {"NaN": "NaN", True: "Home", False: "Away", None: "Draw"}
                    result = result_mapping[result]
        
                    if result == "NaN":
                        continue

                    match_info = {
                        'date': fixture['fixture']['date'],
                        'season': season,
                        'league_id': league_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'score': fixture['score']['fulltime'],
                        'result': result
                    }

                    round_matches.setdefault(gw, []).append(match_info)

                season_matches[season] = round_matches
            else:
                print(f"Failed to fetch data for season {season} (league {league_id}): {response.status_code}")

        migrate_fixtures_to_sqlite(league_id, season_matches)


def get_future_matches(seasons: list, country_league_ids: list = NORWAY_LEAGUES):
    dm = data_manager.DataManager(country_league_ids)
    home_strength = dm.get_team_strengths()
    away_strength = home_strength
    elo = dm.get_team_elos()

    for league_id in country_league_ids:
        season_matches = {}
        for season in seasons:
            api_url = "https://v3.football.api-sports.io/fixtures"
            headers = {
                "x-rapidapi-host": "v3.football.api-sports.io",
                "x-rapidapi-key": API_TOKEN
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
                    raw_round = fixture['league']['round']
                    gw = clean_round_label(raw_round)
                    if gw is None:
                        continue

                    home_team = fixture['teams']['home']['name'].upper()
                    away_team = fixture['teams']['away']['name'].upper()

                    result = helper.determine_result(fixture)
                    result_mapping = {"NaN": "NaN", True: "Home", False: "Away", None: "Draw"}
                    if result_mapping[result] != "NaN":
                        continue

                    match_info = {
                        'date': fixture['fixture']['date'],
                        'season': season,
                        'league_id': league_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_strength': home_strength.get(home_team, {}).get("home", 1),
                        'away_strength': away_strength.get(away_team, {}).get("away", 1),
                        'home_team_elo': elo.get(home_team, 1500),
                        'away_team_elo': elo.get(away_team, 1500)
                    }
                    round_matches.setdefault(gw, []).append(match_info)

                season_matches[season] = round_matches
            else:
                print(f"Failed to fetch future data for season {season} (league {league_id}): {response.status_code}")

        migrate_future_to_sqlite(league_id, season_matches)
