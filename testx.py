import requests
import json
from datetime import date
import os # Optional: To load API key from environment variable

# --- Configuration ---
# IMPORTANT: Replace 'YOUR_API_FOOTBALL_KEY' with the actual key you copied!
# Best practice: Store sensitive keys as environment variables, not directly in code.
# Example using environment variable (run 'export API_FOOTBALL_KEY=your_key' in terminal first):
# API_KEY = os.getenv("API_FOOTBALL_KEY", "YOUR_API_FOOTBALL_KEY_FALLBACK")
API_KEY = "51c958f3c3dc64a884e05b468daba097" # <-- PASTE YOUR KEY HERE FOR NOW

API_HOST = "v3.football.api-sports.io"

# Check if the API key is still the placeholder
if API_KEY == "YOUR_API_FOOTBALL_KEY" or not API_KEY:
    print("ERROR: Please replace 'YOUR_API_FOOTBALL_KEY' with your actual API key.")
    exit() # Stop the script if the key isn't set

# Get today's date in YYYY-MM-DD format
today_date_str = date.today().strftime("%Y-%m-%d")
print(f"Fetching matches for date: {today_date_str}\n")

# --- API Endpoint and Headers ---
url = f"https://{API_HOST}/fixtures"

# Parameters for the request (getting fixtures for today)
querystring = {
    "date": today_date_str
    # Optional: Filter by league, status, etc.
    # "league": "39", # Example: English Premier League ID
    # "status": "NS" # Example: Not Started matches only
}

# Headers required by API-Football
headers = {
    'x-rapidapi-host': API_HOST,
    'x-rapidapi-key': API_KEY
}

# --- Make the API Request ---
try:
    response = requests.get(url, headers=headers, params=querystring, timeout=20) # Increased timeout
    response.raise_for_status() # Raise an HTTPError for bad responses (4XX or 5XX)

    # --- Process the Response ---
    data = response.json()

    # Check for API errors within the JSON response itself
    if data.get('errors'):
         print("API Error(s):")
         for key, value in data['errors'].items():
             print(f"- {key.capitalize()}: {value}")
         exit()

    # Check if any matches were returned
    if data['results'] > 0:
        print(f"--- Found {data['results']} Matches ---")
        for fixture_info in data['response']:
            league = fixture_info['league']['name']
            country = fixture_info['league']['country']
            home_team = fixture_info['teams']['home']['name']
            away_team = fixture_info['teams']['away']['name']
            match_datetime_str = fixture_info['fixture']['date'] # Usually ISO 8601 format (UTC)
            status_short = fixture_info['fixture']['status']['short']
            status_long = fixture_info['fixture']['status']['long']

            # Extract score if available (might be None for not started matches)
            score_home = fixture_info['score']['fulltime'].get('home')
            score_away = fixture_info['score']['fulltime'].get('away')

            # Format output
            time_str = match_datetime_str.split('T')[1][:5] # Extract HH:MM from ISO string (assumes format like '2023-10-27T19:00:00+00:00')

            print(f"\nLeague: {league} ({country})")
            print(f" Match: {home_team} vs {away_team}")
            print(f"  Time: {time_str} (UTC - adjust for your timezone)") # Remind user time is likely UTC
            print(f"Status: {status_long} ({status_short})")
            if score_home is not None and score_away is not None:
                 print(f" Score: {score_home} - {score_away}")

        print("\n--- End of Matches ---")

    else:
        print(f"No matches found for {today_date_str} with the current filters.")

# --- Handle Potential Errors ---
except requests.exceptions.Timeout:
    print("Error: The request timed out. The API might be slow.")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the API. Check your internet connection.")
except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
    # You might want to print response.text here to see the error details from the API
    # print(response.text)
except requests.exceptions.RequestException as req_err:
    print(f"An ambiguous request error occurred: {req_err}")
except json.JSONDecodeError:
    print("Error: Could not decode the JSON response from the API.")
    print("Raw Response Text:", response.text) # Print raw text to help debug
except KeyError as key_err:
    print(f"Error: Missing expected key '{key_err}' in the API response. The response structure might have changed.")
    # print("Problematic Fixture Data:", fixture_info) # Uncomment to see the specific data causing issues
except Exception as e:
    print(f"An unexpected error occurred: {e}")