import requests
import json
from datetime import date, datetime
import pandas as pd
import pytz # Import the pytz library for timezones
import ssl
from typing import Optional # Para type hints (buena práctica)

def get_todays_matches_df(api_host: str, api_key: str) -> Optional[pd.DataFrame]:
    """
    Fetches today's 'Not Started' football matches from the API Football API,
    converts times to Bogota timezone, and returns them as a Pandas DataFrame.

    Args:
        api_host: The API host (e.g., "v3.football.api-sports.io").
        api_key: Your API Football API key.

    Returns:
        A Pandas DataFrame containing the match data (Home, Away, League,
        Country, Time in Bogota) if successful, otherwise None if any error
        occurs during the process (API connection, API error response,
        data parsing, etc.). Returns an empty DataFrame if no matches are found
        but no errors occurred.
    """
    # --- Input Validation ---
    # Using a placeholder name that's less likely to be a real key
    if not api_key or api_key == "YOUR_API_KEY_PLACEHOLDER":
        print("ERROR: API key is missing or still set to the placeholder value.")
        return None

    # --- Get Today's Date ---
    today_date_str = date.today().strftime("%Y-%m-%d")

    # --- API Request Setup ---
    url = f"https://{api_host}/fixtures"
    querystring = {
        "date": today_date_str,
        "status": "NS" # Only fetch 'Not Started' matches
    }
    headers = {
        'x-rapidapi-host': api_host,
        'x-rapidapi-key': api_key
    }

    # --- List to store match data ---
    matches_list = []

    try:
        print(f"Fetching matches for {today_date_str} from {api_host}...")

        # --- SSL Context Workaround (from original code) ---
        # Note: This might be needed in specific environments with SSL issues.
        # It's generally better to fix the underlying SSL/certificate problem if possible.
        # Consider if this line is truly necessary for your current environment.
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
             # Legacy Python that doesn't verify HTTPS certificates by default
             pass
        else:
            # Handle target environment that doesn't support HTTPS verification
            ssl._create_default_https_context = _create_unverified_https_context
            # You might need this line instead depending on the exact issue:
            # ssl._create_default_https_context = ssl._create_stdlib_context


        # --- Make API Request ---
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        response.raise_for_status() # Raises HTTPError for bad responses (4XX, 5XX)

        # --- Parse JSON Response ---
        data = response.json()

        # --- Check for API Level Errors (within JSON) ---
        # Handles both list and dict format for errors
        api_errors = data.get('errors')
        if api_errors and (isinstance(api_errors, (dict, list)) and len(api_errors) > 0):
            print("API Error(s) reported in response:")
            if isinstance(api_errors, dict):
                for key, value in api_errors.items():
                    print(f"- {key.capitalize()}: {value}")
            elif isinstance(api_errors, list):
                 # Handle list of strings or list of dicts if structure varies
                 for error_item in api_errors:
                     if isinstance(error_item, dict):
                         # Attempt to print key-value pairs if it's a dict
                         for key, value in error_item.items():
                             print(f"- {key}: {value}")
                     else:
                         print(f"- {error_item}") # Assume it's a string message
            return None # Return None on API-reported errors

        # --- Process Matches ---
        if data.get('results', 0) > 0 and 'response' in data:
            print(f"Found {data['results']} matches. Processing...")

            bogota_tz = pytz.timezone('America/Bogota')
            utc_tz = pytz.utc

            for fixture_info in data['response']:
                # Inner try-except to catch errors for a *single* fixture
                # According to the requirement, *any* error should return None overall.
                # If you wanted to skip bad fixtures instead, you'd put a
                # 'continue' here in the except blocks instead of 'return None'.
                try:
                    league_info = fixture_info.get('league', {})
                    teams_info = fixture_info.get('teams', {})
                    fixture_details = fixture_info.get('fixture', {})

                    league = league_info.get('name', 'N/A')
                    country = league_info.get('country', 'N/A')
                    home_team = teams_info.get('home', {}).get('name', 'N/A')
                    away_team = teams_info.get('away', {}).get('name', 'N/A')
                    match_datetime_utc_str = fixture_details.get('date')

                    time_bogota_str = "N/A"
                    if match_datetime_utc_str:
                        # Nested try-except specifically for date parsing/conversion
                        try:
                            match_datetime_utc = datetime.fromisoformat(match_datetime_utc_str.replace('Z', '+00:00'))
                            if match_datetime_utc.tzinfo is None:
                                match_datetime_utc = utc_tz.localize(match_datetime_utc)
                            match_datetime_bogota = match_datetime_utc.astimezone(bogota_tz)
                            time_bogota_str = match_datetime_bogota.strftime('%H:%M')
                        except (ValueError, TypeError) as date_err:
                             # Handle specific errors during date processing
                             print(f"Error processing date '{match_datetime_utc_str}' for {home_team} vs {away_team}: {date_err}. Aborting.")
                             return None # Abort all if one date fails as requested
                        # Removed the generic Exception catch here as it's too broad for just dates

                    matches_list.append({
                        'Home': home_team,
                        'Away': away_team,
                        'League': league,
                        'Country': country,
                        'Time': time_bogota_str
                    })

                except KeyError as key_err:
                    print(f"Data Error: Missing expected key '{key_err}' in fixture data. Aborting.")
                    # print("Problematic Fixture Data:", fixture_info) # Uncomment to debug
                    return None # Abort all if structure is wrong
                except Exception as inner_e:
                    # Catch unexpected errors during single fixture processing
                    print(f"Unexpected Error processing fixture ({home_team} vs {away_team}): {inner_e}. Aborting.")
                    return None # Abort all if one fixture causes unexpected error

            # --- Create DataFrame (if loop finished without returning None) ---
            df = pd.DataFrame(matches_list)
            print("\n--- Matches DataFrame Created (Bogota Time) ---")
            if not df.empty:
                 print(df.to_string())
            else:
                 # This case handles when API returns results: 0, but no errors occurred
                 print("No matches found for today, but the request was successful.")
            print("\n--- End of Processing ---")
            return df # Return the DataFrame (might be empty)

        else:
            # Case: API call successful, but results = 0 or 'response' key missing
            print(f"No matches found for {today_date_str} with the status 'NS' (or unexpected response structure).")
            # Return an empty DataFrame to signify success but no data
            return pd.DataFrame(matches_list) # matches_list will be empty here

    # --- Handle Exceptions during Request or Top-Level Processing ---
    except requests.exceptions.Timeout:
        print("Error: The request timed out. API might be slow or unreachable.")
        return None
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Error: Could not connect to the API ({conn_err}). Check connection or API host.")
        return None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        # Attempt to print API error details from response if possible
        try:
            error_details = response.json()
            print("API Response Error Details:", error_details)
        except (json.JSONDecodeError, NameError, AttributeError): # Handle cases where response might not exist or not be JSON
             # Check if response exists before trying to access its text
             if 'response' in locals() and hasattr(response, 'text'):
                print("Raw Response Text:", response.text)
             else:
                 print("Could not retrieve detailed response text.")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"An ambiguous request error occurred: {req_err}")
        return None
    except json.JSONDecodeError:
        print("Error: Could not decode the JSON response from the API.")
        if 'response' in locals() and hasattr(response, 'text'):
            print("Raw Response Text:", response.text)
        return None
    except KeyError as key_err:
        # This might catch errors if top-level keys like 'results' or 'response' are missing unexpectedly
        print(f"Data Error: Missing expected key '{key_err}' in the main API response structure.")
        if 'data' in locals():
            print("API Response Structure:", data)
        return None
    except pytz.exceptions.UnknownTimeZoneError:
        print("Error: Invalid timezone specified ('America/Bogota'). Check pytz installation/timezone name.")
        return None
    except Exception as e:
        # Catch-all for any other unexpected error
        import traceback
        print(f"An unexpected error occurred: {e}")
        print("Traceback:")
        traceback.print_exc() # Print detailed traceback for debugging
        return None

def ask_deep_seek(
    prompt: str,
    api_key: str,
    base_url: str = "https://api.deepseek.com/v1/chat/completions", # URL por defecto
    model: str = "deepseek-chat" # Modelo por defecto (ajusta si es necesario)
    ) -> str:
    """
    Envía un prompt a la API de DeepSeek y devuelve la respuesta del modelo.

    Args:
        prompt: La pregunta o instrucción para el modelo de IA.
        api_key: Tu clave API de DeepSeek.
        base_url: La URL base del endpoint de la API de DeepSeek Chat Completions.
        model: El identificador del modelo a usar (ej: "deepseek-chat", "deepseek-coder").

    Returns:
        La respuesta del modelo como una cadena de texto si la solicitud es exitosa,
        o una cadena vacía ("") si ocurre cualquier tipo de error (conexión,
        API, error de parseo, etc.).
    """
    # --- Validación de Entradas Básica ---
    if not api_key:
        print("Error: La API Key no puede estar vacía.")
        return ""
    if not prompt:
        print("Error: El prompt no puede estar vacío.")
        return ""
    if not base_url:
        print("Error: La URL base no puede estar vacía.")
        return ""

    # --- Preparar Headers y Data ---
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt.strip()}], # Usamos el prompt y quitamos espacios extra
        # "temperature": 0.7, # Puedes añadir otros parámetros opcionales aquí
        # "max_tokens": 1024,
    }

    # --- Realizar la Petición y Manejar Errores ---
    try:
        response = requests.post(base_url, headers=headers, json=data, timeout=60) # Timeout más largo para IA

        # --- Manejar Errores HTTP (4xx, 5xx) ---
        # Usar raise_for_status() es bueno, pero aquí queremos devolver "" en lugar de lanzar excepción
        if response.status_code != 200:
            print(f"Error: La API devolvió un código de estado no exitoso: {response.status_code}")
            try:
                # Intentar mostrar el detalle del error JSON si está disponible
                error_details = response.json()
                print(f"Detalles del error API: {error_details}")
            except json.JSONDecodeError:
                # Si no es JSON, mostrar texto plano
                print(f"Respuesta de error (no JSON): {response.text}")
            return "" # Devolver cadena vacía en caso de error HTTP

        # --- Procesar Respuesta Exitosa (Código 200) ---
        try:
            respuesta_json = response.json()

            # Extraer la respuesta de forma segura usando .get() para evitar KeyErrors
            choices = respuesta_json.get("choices")
            if choices and isinstance(choices, list) and len(choices) > 0:
                message = choices[0].get("message")
                if message and isinstance(message, dict):
                    content = message.get("content")
                    if content and isinstance(content, str):
                        return content.strip() # Devolver el contenido limpio

            # Si la estructura no es la esperada o falta el contenido
            print("Error: La respuesta JSON no tiene la estructura esperada o falta contenido.")
            print(f"Respuesta JSON recibida: {respuesta_json}")
            return ""

        except json.JSONDecodeError:
            print("Error: No se pudo decodificar la respuesta JSON de la API.")
            print(f"Respuesta recibida (texto plano): {response.text}")
            return "" # Devolver cadena vacía si el JSON es inválido

    # --- Manejar Errores de Red/Conexión ---
    except requests.exceptions.Timeout:
        print("Error: La solicitud a la API tardó demasiado (timeout).")
        return ""
    except requests.exceptions.ConnectionError as e:
        print(f"Error: No se pudo conectar a la API. Verifica la red y la URL base. ({e})")
        return ""
    except requests.exceptions.RequestException as e:
        # Captura otros errores relacionados con requests (ej: SSL, URL inválida)
        print(f"Error durante la solicitud a la API: {e}")
        return ""
    # --- Captura General (inesperada) ---
    except Exception as e:
        import traceback
        print(f"Error inesperado procesando la solicitud: {e}")
        traceback.print_exc() # Imprime el traceback completo para depuración
        return ""

API_KEY = "51c958f3c3dc64a884e05b468daba097"
API_HOST = "v3.football.api-sports.io"

matches_df = get_todays_matches_df(api_host=API_HOST, api_key=API_KEY)

API_KEY = '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'
BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'



# Check the result
if matches_df is not None:
    if not matches_df.empty:
        print("\n--- Function executed successfully ---")
        matches_df.to_excel("matches.xlsx", index=False)
    else:
        print("\n--- Function executed successfully, but no matches were found for today. ---")
else:
     print("\n--- Function failed. No DataFrame was returned. Check logs above for errors. ---")