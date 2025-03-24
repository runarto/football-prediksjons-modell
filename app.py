from flask import Flask, render_template, request, redirect, url_for
from src.api import get_previous_matches, get_future_matches
from src.elo_system import EloRatingSystem
from src.sim import Simulator
from src.migration import migrate_fixtures_to_sqlite, migrate_future_to_sqlite

app = Flask(__name__)

LEAGUES = {
    103: "Eliteserien",
    104: "OBOS-ligaen",
}

LEAGUE_IDS = [103, 104]

SEASONS = [2023, 2024, 2025]

@app.route('/')
def home():
    print("🔥 Home route reached")
    return render_template("home.html", leagues=LEAGUES)


@app.route('/league/<int:league_id>')
def league_overview(league_id):
    return render_template("league_overview.html", league_id=league_id, league_name=LEAGUES.get(league_id))

@app.route('/league/<int:league_id>/fetch')
def fetch_data(league_id):
    fixtures = get_previous_matches([2024])
    future = get_future_matches([2025])
    return f"✅ Data for league {LEAGUES.get(league_id)} fetched and saved to database."

@app.route('/league/<int:league_id>/elo')
def generate_elo(league_id):
    elo = EloRatingSystem(LEAGUE_IDS)
    elo.run_elo_rating_system()
    leaderboard = sorted(elo.team_ratings.items(), key=lambda x: x[1], reverse=True)
    return render_template("leaderboard.html", leaderboard=leaderboard, league_id=league_id, league_name=LEAGUES.get(league_id))

@app.route('/league/<int:league_id>/sim')
def simulate_season(league_id):
    sim = Simulator(league_id)
    results = sim.simulate_season_return_avg_points(100)
    labels = list(results.keys())
    data = list(results.values())
    return render_template("simulation_result.html",
                           league_id=league_id,
                           league_name=LEAGUES.get(league_id),
                           labels=labels,
                           data=data)

if __name__ == '__main__':
    app.run(debug=True)
