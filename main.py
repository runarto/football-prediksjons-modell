# Import necessary libraries
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

# Step 1: Load the data
def load_data(file_path):
    # Assuming data is in CSV format
    data = pd.read_csv(file_path)
    return data

# Step 2: Preprocess the data
def preprocess_data(data):
    # Handle missing values
    data.fillna(0, inplace=True)
    
    # Example of encoding categorical variables (e.g., team names)
    le = LabelEncoder()
    data['HomeTeam'] = le.fit_transform(data['HomeTeam'])
    data['AwayTeam'] = le.fit_transform(data['AwayTeam'])

    # Convert target variable to numerical (e.g., HomeWin = 1, Draw = 0, AwayWin = -1)
    result_mapping = {'H': 1, 'D': 0, 'A': -1}
    data['Result'] = data['FTR'].map(result_mapping)  # 'FTR' stands for Full Time Result in some datasets

    return data

# Step 3: Feature Engineering (example features)
def create_features(data):
    # Example feature set
    features = data[['HomeTeam', 'AwayTeam', 'HomeGoals', 'AwayGoals', 'HomeShots', 'AwayShots', 'HomePossession', 'AwayPossession']]
    labels = data['Result']
    
    return features, labels

# Step 4: Train-Test Split
def split_data(features, labels):
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test

# Step 5: Model Selection (Random Forest example)
def select_model():
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    return model

# Step 6: Model Training
def train_model(model, X_train, y_train):
    model.fit(X_train, y_train)
    return model

# Step 7: Model Evaluation
def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    
    # Model performance metrics
    accuracy = accuracy_score(y_test, y_pred)
    print(f'Accuracy: {accuracy:.2f}')
    print('Confusion Matrix:')
    print(confusion_matrix(y_test, y_pred))
    print('Classification Report:')
    print(classification_report(y_test, y_pred))

# Step 8: Predict new outcomes
def predict_outcome(model, new_data):
    prediction = model.predict(new_data)
    return prediction

# Main function to execute the pipeline
if __name__ == "__main__":
    # Load the data (assume you have a CSV with relevant features)
    file_path = 'football_matches.csv'
    data = load_data(file_path)

    # Preprocess the data
    processed_data = preprocess_data(data)

    # Create features and labels
    features, labels = create_features(processed_data)

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = split_data(features, labels)

    # Select and train the model
    model = select_model()
    trained_model = train_model(model, X_train, y_train)

    # Evaluate the model
    evaluate_model(trained_model, X_test, y_test)

    # Example of predicting the outcome for new match data (input new features as a DataFrame)
    new_match_data = pd.DataFrame([[team1, team2, goals1, goals2, shots1, shots2, possession1, possession2]])
    outcome = predict_outcome(trained_model, new_match_data)
    print(f"Predicted outcome: {outcome}")
