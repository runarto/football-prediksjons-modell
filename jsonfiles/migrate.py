import sqlite3
import json
from pathlib import Path

# Connect to SQLite database
conn = sqlite3.connect("football.db")
c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    league_id INTEGER,
    home_strength REAL,
    away_strength REAL,
    elo_rating REAL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER,
    season TEXT,
    round TEXT,
    date TEXT,
    home_team TEXT,
    away_team TEXT,
    home_score INTEGER,
    away_score INTEGER,
    result TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS future_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER,
    season TEXT,
    round TEXT,
    date TEXT,
    home_team TEXT,
    away_team TEXT,
    home_strength REAL,
    away_strength REAL,
    home_team_elo REAL,
    away_team_elo REAL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS table_standings (
    league_id INTEGER,
    team TEXT,
    position INTEGER,
    played_games INTEGER,
    won INTEGER,
    draw INTEGER,
    lost INTEGER,
    goals_for INTEGER,
    goals_against INTEGER,
    points INTEGER
)
''')

# Load data files (assume they're in the same directory)
with open("team_elo.json") as f:
    elo = json.load(f)
with open("home_strength.json") as f:
    home_strength = json.load(f)
with open("away_strength.json") as f:
    away_strength = json.load(f)
with open("fixtures.json") as f:
    fixtures = json.load(f)
with open("future_matches.json") as f:
    future = json.load(f)
with open("table.json") as f:
    standings = json.load(f)

league_id = 103  # Eliteserien

# Insert into teams
for team in elo:
    c.execute("INSERT INTO teams (name, league_id, home_strength, away_strength, elo_rating) VALUES (?, ?, ?, ?, ?)",
              (team, league_id, home_strength.get(team, 0), away_strength.get(team, 0), elo[team]))

# Insert into matches
for season, rounds in fixtures.items():
    for round_name, games in rounds.items():
        for game in games:
            c.execute('''
                INSERT INTO matches (league_id, season, round, date, home_team, away_team, home_score, away_score, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                league_id, season, round_name, game["date"],
                game["home_team"], game["away_team"],
                game["score"]["home"], game["score"]["away"],
                game["result"]
            ))

# Insert into future_matches
for season, rounds in future.items():
    for round_name, games in rounds.items():
        for game in games:
            c.execute('''
                INSERT INTO future_matches (league_id, season, round, date, home_team, away_team, home_strength, away_strength, home_team_elo, away_team_elo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                league_id, season, round_name, game["date"],
                game["home_team"], game["away_team"],
                game["home_strength"], game["away_strength"],
                game["home_team_elo"], game["away_team_elo"]
            ))

# Insert into table_standings
for team, row in standings.items():
    c.execute("""
        INSERT INTO table_standings (league_id, team, position, played_games, won, draw, lost, goals_for, goals_against, points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        league_id, team, row["position"], row["played_games"], row["won"],
        row["draw"], row["lost"], row["goals_for"], row["goals_against"], row["points"]
    ))

# Commit and close
conn.commit()
conn.close()
