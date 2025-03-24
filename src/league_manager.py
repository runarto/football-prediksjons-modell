from .elo_system import EloRatingSystem

class LeagueManager:
    def __init__(self, league_ids):
        self.leagues = {
            league_id: EloRatingSystem(league_id) for league_id in league_ids
        }
        for elo in self.leagues.values():
            elo.run_elo_rating_system()

    def get_elo(self, league_id):
        return self.leagues.get(league_id)

    def all_leagues(self):
        return list(self.leagues.keys())