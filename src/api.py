import requests
import helper
from migration import migrate_fixtures_to_sqlite, migrate_future_to_sqlite
import data_manager
from config import API_TOKEN

def get_previous_matches(seasons: list, league_id: int):
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
                round = fixture['league']['round']
                if round == "Relegation Round":
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
                    'home_team': home_team,
                    'away_team': away_team,
                    'score': fixture['score']['fulltime'],
                    'result': result
                }
                round_matches.setdefault(round, []).append(match_info)

            season_matches[season] = round_matches
        else:
            print(f"Failed to fetch data for season {season}: {response.status_code}")

    migrate_fixtures_to_sqlite(league_id, season_matches)
    return season_matches

def get_future_matches(seasons: list, league_id: int):

    dm = data_manager.DataManager(league_id)
    home_strength = dm.get_team_strengths()
    away_strength = home_strength  # same source
    elo = dm.get_team_elos()

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
                round = fixture['league']['round']
                home_team = fixture['teams']['home']['name'].upper()
                away_team = fixture['teams']['away']['name'].upper()

                result = helper.determine_result(fixture)
                result_mapping = {"NaN": "NaN", True: "Home", False: "Away", None: "Draw"}
                if result_mapping[result] != "NaN":
                    continue

                match_info = {
                    'date': fixture['fixture']['date'],
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_strength': home_strength.get(home_team, {}).get("home", 1),
                    'away_strength': away_strength.get(away_team, {}).get("away", 1),
                    'home_team_elo': elo.get(home_team, 1500),
                    'away_team_elo': elo.get(away_team, 1500)
                }
                round_matches.setdefault(round, []).append(match_info)

            season_matches[season] = round_matches
        else:
            print(f"Failed to fetch data for season {season}: {response.status_code}")

    migrate_future_to_sqlite(league_id, season_matches)
    return season_matches

def get_league_table(league_id: int, season: str):
    import sqlite3
    conn = sqlite3.connect("football.db")
    c = conn.cursor()

    c.execute("""
        SELECT team, position, played_games, won, draw, lost,
               goals_for, goals_against, points
        FROM table_standings
        WHERE league_id = ?
        ORDER BY position ASC
    """, (league_id,))

    result = c.fetchall()
    conn.close()

    table = {}
    for row in result:
        table[row[0]] = {
            'position': row[1],
            'played_games': row[2],
            'won': row[3],
            'draw': row[4],
            'lost': row[5],
            'goals_for': row[6],
            'goals_against': row[7],
            'points': row[8]
        }

    return table
