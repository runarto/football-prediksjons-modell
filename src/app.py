from flask import Flask, render_template, request, redirect, url_for
from api import get_historic_fixtures, get_future_fixtures
from elo_system import EloRatingSystem
from sim import Simulator
from migration import migrate_fixtures_to_sqlite, migrate_future_to_sqlite

app = Flask(__name__)

LEAGUES = {
    103: "Eliteserien",
    104: "OBOS-ligaen",
    105: "PostNord-ligaen"
}

@app.route('/')
def home():
    return render_template("home.html", leagues=LEAGUES)

@app.route('/league/<int:league_id>')
def league_overview(league_id):
    return render_template("league_overview.html", league_id=league_id, league_name=LEAGUES.get(league_id))

@app.route('/league/<int:league_id>/fetch')
def fetch_data(league_id):
    fixtures = get_historic_fixtures(league_id)
    future = get_future_fixtures(league_id)
    migrate_fixtures_to_sqlite(league_id, fixtures)
    migrate_future_to_sqlite(league_id, future)
    return f"✅ Data for league {LEAGUES.get(league_id)} fetched and saved to database."

@app.route('/league/<int:league_id>/elo')
def generate_elo(league_id):
    elo = EloRatingSystem(league_id)
    elo.run_elo_rating_system()
    leaderboard = sorted(elo.team_ratings.items(), key=lambda x: x[1], reverse=True)
    return render_template("leaderboard.html", leaderboard=leaderboard, league_id=league_id, league_name=LEAGUES.get(league_id))

@app.route('/league/<int:league_id>/sim')
def simulate_season(league_id):
    sim = Simulator(league_id)
    sim.simulate_season_outcome_n_times(100)
    return f"✅ Simulated 100 outcomes for {LEAGUES.get(league_id)}. Check console/logs for output."

if __name__ == '__app__':
    app.run(debug=True)