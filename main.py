import pandas as pd

def get_matches(file_path):
    matches = pd.read_csv(file_path, index_col=0)
    return matches


def modify_data(matches):
    matches['date'] = pd.to_datetime(matches['date'])
    matches['year'] = matches['date'].dt.year
    matches['month'] = matches['date'].dt.month
    matches['day'] = matches['date'].dt.day
    matches['venue_code'] = matches['venue'].apply(lambda x: 1 if x == 'Home' else 0)
    return matches


def main():
    file_path = 'matches.csv'
    matches = get_matches(file_path)
    matches = modify_data(matches)
    print(matches)