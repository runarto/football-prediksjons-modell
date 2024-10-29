import json

def load_json_data(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)
    
def write_json_data(data, file_path):
    """Write JSON data to a file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)