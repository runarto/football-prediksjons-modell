import sqlite3
from typing import Dict, List

def migrate_fixtures_to_sqlite(league_id: int, fixtures: Dict[str, Dict[str, List[Dict]]], db_path: str = "football.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for season, rounds in fixtures.items():
        for round_name, games in rounds.items():
            for game in games:
                c.execute('''
                    INSERT INTO matches (
                        league_id, season, round, date, home_team, away_team, home_score, away_score, result
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    league_id,
                    season,
                    round_name,
                    game["date"],
                    game["home_team"],
                    game["away_team"],
                    game["score"]["home"],
                    game["score"]["away"],
                    game["result"]
                ))

    conn.commit()
    conn.close()

def migrate_future_to_sqlite(league_id: int, future_matches: Dict[str, Dict[str, List[Dict]]], db_path: str = "football.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for season, rounds in future_matches.items():
        for round_name, games in rounds.items():
            for game in games:
                c.execute('''
                    INSERT INTO future_matches (
                        league_id, season, round, date, home_team, away_team, home_strength, away_strength, home_team_elo, away_team_elo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    league_id,
                    season,
                    round_name,
                    game["date"],
                    game["home_team"],
                    game["away_team"],
                    game["home_strength"],
                    game["away_strength"],
                    game["home_team_elo"],
                    game["away_team_elo"]
                ))

    conn.commit()
    conn.close()
