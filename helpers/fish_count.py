import json
import os
import json
SESSION_NAME = os.getenv('SESSION_NAME')


def count_fish(pokemon_info):
    # Create the folder if it doesn't exist
    os.makedirs('json_info', exist_ok=True)

    # Define pokemon_counts before the try/except statement
    pokemon_counts = {}

    # Load the existing counts from the file
    try:
        # Open or create the file fish_counts.json in the json_info folder
        with open(f'json_info/fish_counts_{SESSION_NAME}.json', 'r') as f:
            pokemon_counts = json.load(f)
    except FileNotFoundError:
        pass  # Do nothing if the file doesn't exist

    # Increment the count for this pokemon
    pokemon_name = pokemon_info["Name"]
    pokemon_counts[pokemon_name] = pokemon_counts.get(pokemon_name, 0) + 1

    # Save the counts back to the file in the json_info folder
    with open(f'json_info/fish_counts_{SESSION_NAME}.json', 'w') as f:
        json.dump(pokemon_counts, f)