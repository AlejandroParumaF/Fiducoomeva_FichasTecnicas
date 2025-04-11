# -*- coding: utf-8 -*- # Para asegurar compatibilidad con caracteres especiales

import requests
import json
from datetime import date, datetime, timedelta, time
import pandas as pd
import pytz
import re
from typing import Optional, Tuple, Dict, Any, List # Tipos necesarios
from tqdm import tqdm # Barra de progreso
from time import sleep

# FUNCIÓN 1: OBTENER PARTIDOS DE API-FOOTBALL (PARA HOY LOCAL)
# ==============================================================================

def get_football_matches_today_local( # Cambiado nombre para claridad
    api_host: str,
    api_key: str,
    target_timezone: str = 'America/Bogota'
    ) -> Optional[pd.DataFrame]:
    """
    Obtiene los partidos de fútbol 'No Iniciados' (NS) que ocurren DURANTE el día
    de HOY según la zona horaria local especificada (target_timezone).
    Filtra solo las ligas cuyos IDs están en la lista predefinida interna.

    Args:
        api_host: Host de la API de Football.
        api_key: Clave API de Football.
        target_timezone: Zona horaria local para definir "hoy" (ej: 'America/Bogota').

    Returns:
        Un DataFrame con partidos de HOY (hora local), o None si hay error crítico,
        o DataFrame vacío si no hay partidos que cumplan los criterios.
    """
    # --- Validaciones y Configuración de Zona Horaria ---
    if not api_key or api_key == "YOUR_API_FOOTBALL_KEY":
        print("ERROR (get_matches_today): API key de Football no proporcionada.")
        return None
    if not api_host:
        print("ERROR (get_matches_today): Host de API Football no proporcionado.")
        return None
    try:
        local_tz = pytz.timezone(target_timezone)
        utc_tz = pytz.utc
    except pytz.exceptions.UnknownTimeZoneError:
        print(f"ERROR (get_matches_today): Zona horaria '{target_timezone}' inválida.")
        return None

    # --- Lista de Ligas Permitidas (Definida internamente) ---
    ligas_ids_permitidas = [39, 40, 135, 136, 78, 79, 140, 141, 61, 62, 94, 71, 72, 88, 253, 179, 128, 1032, 144, 262, 235, 203, 239, 240, 268, 270, 283, 333, 242, 281, 200, 233, 186, 292, 98, 119, 113, 162, 396, 234, 345, 265, 103, 244, 188, 169, 288, 399, 570, 299, 344, 250, 252, 304, 164, 218, 332, 373, 197, 286, 2, 3, 11, 12, 13, 15, 16, 17, 20]
    target_league_ids = set(ligas_ids_permitidas)
    print(f"INFO (get_matches_today): Filtrando por {len(target_league_ids)} IDs de liga predefinidos.")


    # --- Determinar Fechas UTC para Consultar ---
    # 1. Obtener fecha de "hoy" en la zona local
    now_local = datetime.now(local_tz)
    today_local_date = now_local.date() # Fecha local objetivo es HOY

    # 2. Determinar las DOS fechas UTC que necesitamos consultar en la API
    #    Necesitamos la fecha UTC de HOY y la de MAÑANA UTC.
    system_today = date.today()
    utc_date_1 = system_today.strftime("%Y-%m-%d") # HOY UTC
    utc_date_2 = (system_today + timedelta(days=1)).strftime("%Y-%m-%d") # MAÑANA UTC
    dates_to_query = [utc_date_1, utc_date_2]

    print(f"INFO (get_matches_today): Hoy ({target_timezone}) es {today_local_date}.")
    print(f"INFO (get_matches_today): Consultando API para fechas UTC: {dates_to_query}")

    # --- Realizar Consultas a la API para ambas fechas ---
    all_fixtures_raw = []
    headers = {'x-rapidapi-host': api_host, 'x-rapidapi-key': api_key}
    call_success_count = 0

    for query_date_str in dates_to_query:
        url = f"https://{api_host}/fixtures"
        # Obtener TODOS los partidos de la fecha, incluyendo los ya iniciados o finalizados
        # Si solo quieres los "No Iniciados" (NS) A PARTIR de ahora, usa "status": "NS"
        # Si quieres TODOS los del día local, independientemente de su estado, no pongas status.
        # Vamos a mantener "NS" por ahora, asumiendo que buscas partidos futuros del día de hoy.
        querystring = {"date": query_date_str, "status": "NS"}
        print(f"INFO (get_matches_today): Consultando fecha UTC {query_date_str}...")
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=60)
            response.raise_for_status()
            data = response.json()

            api_errors = data.get('errors')
            if isinstance(api_errors, (dict, list)) and len(api_errors) > 0:
                 # Verificar si es error de plan (aunque no debería ocurrir para hoy/mañana UTC)
                 is_plan_error = False
                 error_msg_str = str(api_errors).lower()
                 if "'plan':" in error_msg_str and "do not have access" in error_msg_str:
                      is_plan_error = True
                 if is_plan_error:
                      print(f"WARN (get_matches_today): Error de acceso API para fecha {query_date_str} (¿problema de plan inesperado?): {api_errors}")
                 else:
                      print(f"ERROR (get_matches_today): Errores API para fecha {query_date_str}: {api_errors}")
                 continue # Continuar con la siguiente fecha

            if data.get('results', 0) > 0 and 'response' in data:
                call_success_count += 1
                num_found = len(data['response'])
                all_fixtures_raw.extend(data['response'])
                print(f"INFO (get_matches_today): {num_found} partidos encontrados para {query_date_str}.")
            else:
                 print(f"INFO (get_matches_today): No se encontraron partidos para {query_date_str} en la respuesta.")

        except requests.exceptions.HTTPError as e:
             # Manejar errores HTTP, incluyendo posibles errores de plan inesperados
             response_text = ""
             if e.response is not None: response_text = e.response.text.lower()
             if "do not have access" in response_text:
                  print(f"WARN (get_matches_today): Error de acceso (¿plan?) para fecha {query_date_str} (HTTPError: {e}).")
             else:
                  print(f"ERROR (get_matches_today): Error HTTP para fecha {query_date_str}: {e}")
             continue
        except requests.exceptions.RequestException as e:
            print(f"ERROR (get_matches_today): Falló la consulta para fecha {query_date_str}: {e}")
            continue
        except Exception as e:
            print(f"ERROR (get_matches_today): Error inesperado procesando fecha {query_date_str}: {e}")
            continue

    # --- Comprobar si se obtuvieron datos ---
    if call_success_count == 0 and not all_fixtures_raw:
        print("ERROR (get_matches_today): Ninguna llamada a API tuvo éxito o devolvió datos.")
        expected_cols = ['Home', 'Away', 'League', 'Country', 'Time']
        return pd.DataFrame(columns=expected_cols)


    # --- Filtrado Local por Fecha Local y Liga ---
    matches_data_final = []
    if not all_fixtures_raw:
        print("INFO (get_matches_today): No se obtuvieron partidos válidos de la API después de las consultas.")
        expected_cols = ['Home', 'Away', 'League', 'Country', 'Time']
        return pd.DataFrame(columns=expected_cols)

    print(f"INFO (get_matches_today): Total {len(all_fixtures_raw)} partidos brutos obtenidos de API. Filtrando por fecha local ({today_local_date}) y liga...")

    # Contadores para depuración
    processed_count = 0
    filtered_out_by_date = 0
    filtered_out_by_league = 0
    filtered_out_by_parse_error = 0

    for fixture_info in all_fixtures_raw:
        try:
            league_info = fixture_info.get('league', {})
            league_id = league_info.get('id')
            fixture_details = fixture_info.get('fixture', {})
            match_datetime_utc_str = fixture_details.get('date')

            # 1. Filtrar por Liga
            if league_id is None or league_id not in target_league_ids:
                filtered_out_by_league += 1
                continue

            # 2. Filtrar por Fecha Local
            if not match_datetime_utc_str:
                filtered_out_by_parse_error += 1
                continue

            try:
                # Convertir y localizar UTC
                match_dt_utc = datetime.fromisoformat(match_datetime_utc_str.replace('Z', '+00:00'))
                if match_dt_utc.tzinfo is None:
                    match_dt_utc = utc_tz.localize(match_dt_utc)

                # Convertir a Local
                match_dt_local = match_dt_utc.astimezone(local_tz)
                match_local_date_part = match_dt_local.date()

                # Comparar SOLO la fecha local con la fecha local objetivo (HOY)
                if match_local_date_part == today_local_date:
                    # Si la fecha coincide, procesar y añadir
                    processed_count += 1
                    country = league_info.get('country', 'N/A')
                    teams_info = fixture_info.get('teams', {})
                    time_local_str = match_dt_local.strftime('%H:%M')

                    matches_data_final.append({
                        'Home': teams_info.get('home', {}).get('name', 'N/A'),
                        'Away': teams_info.get('away', {}).get('name', 'N/A'),
                        'League': league_info.get('name', 'N/A'),
                        'Country': country,
                        'Time': time_local_str,
                        # 'League_ID': league_id # Descomentar si quieres el ID
                    })
                else:
                     filtered_out_by_date += 1

            except (ValueError, TypeError) as date_err:
                # print(f"WARN (get_matches_today): Error parseando fecha '{match_datetime_utc_str}', omitido: {date_err}")
                filtered_out_by_parse_error += 1
                continue

        except Exception as e_fixture:
            fixture_id_log = fixture_info.get('fixture', {}).get('id', 'N/A')
            print(f"WARN (get_matches_today): Error procesando fixture {fixture_id_log} durante filtrado, omitido: {e_fixture}")
            continue

    # --- Crear DataFrame Final ---
    df_matches = pd.DataFrame(matches_data_final)

    print(f"\nINFO (get_matches_today): Filtrado completado.")
    print(f"  - Partidos totales brutos de API: {len(all_fixtures_raw)}")
    print(f"  - Omitidos por liga: {filtered_out_by_league}")
    print(f"  - Omitidos por error fecha/parseo: {filtered_out_by_parse_error}")
    print(f"  - Omitidos por no ser de fecha local ({today_local_date}): {filtered_out_by_date}")
    print(f"  - Partidos finales añadidos (HOY {target_timezone}): {len(df_matches)}")

    # Asegurar columnas finales
    final_cols = ['Home', 'Away', 'League', 'Country', 'Time']
    for col in final_cols:
        if col not in df_matches.columns:
            df_matches[col] = pd.Series(dtype='object')

    return df_matches[final_cols]
# ==============================================================================
# FUNCIÓN 2: CONSULTAR AL MODELO DE LENGUAJE (LLM)
# ==============================================================================

def ask_language_model(
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    timeout: int = 90 # Timeout más generoso para LLMs
    ) -> str:
    """
    Envía un prompt a una API de modelo de lenguaje y devuelve la respuesta.

    Args:
        prompt: La pregunta o instrucción para el modelo.
        api_key: La clave API para el servicio del LLM.
        base_url: La URL base del endpoint de la API del LLM.
        model: El identificador del modelo a usar.
        timeout: Segundos de espera para la respuesta de la API.

    Returns:
        La respuesta del modelo como string, o una cadena vacía ("") si
        ocurre cualquier error.
    """
    if not all([prompt, api_key, base_url, model]):
        print("ERROR (ask_language_model): Faltan argumentos (prompt, api_key, base_url, model).")
        return ""

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"model": model, "messages": [{"role": "user", "content": prompt.strip()}]}

    try:
        response = requests.post(base_url, headers=headers, json=data, timeout=timeout)

        if response.status_code == 200:
            try:
                respuesta_json = response.json()
                choices = respuesta_json.get("choices")
                if choices and len(choices) > 0:
                    message = choices[0].get("message")
                    if message:
                        content = message.get("content")
                        if content:
                            return content.strip()
                # Si la estructura es inesperada
                print(f"WARN (ask_language_model): Estructura JSON inesperada: {respuesta_json}")
                return ""
            except json.JSONDecodeError:
                print(f"ERROR (ask_language_model): Respuesta exitosa (200) pero no es JSON válido: {response.text}")
                return ""
        else:
            # Error HTTP != 200
            print(f"ERROR (ask_language_model): API devolvió estado {response.status_code}. Respuesta: {response.text}")
            return ""

    except requests.exceptions.Timeout:
        print(f"ERROR (ask_language_model): Timeout ({timeout}s) esperando respuesta de la API.")
        return ""
    except requests.exceptions.RequestException as e:
        print(f"ERROR (ask_language_model): Error de conexión/solicitud a la API LLM: {e}")
        return ""
    except Exception as e:
        print(f"ERROR (ask_language_model): Error inesperado: {e}")
        return ""

# ==============================================================================
# FUNCIÓN 3: ORQUESTADOR - AÑADIR PREDICCIONES AL DATAFRAME
# ==============================================================================

def add_llm_predictions_to_matches(
    matches_df: pd.DataFrame,
    llm_api_key: str,
    llm_base_url: str,
    llm_model: str,
    pause_between_requests: float = 1.5 # Pausa para evitar rate limits
    ) -> Optional[pd.DataFrame]:
    """
    Toma un DataFrame de partidos, consulta a un LLM para obtener predicciones
    de probabilidad (Local, Visitante, Empate) y las añade como nuevas columnas.

    Args:
        matches_df: DataFrame obtenido de get_football_matches.
        llm_api_key: Clave API del servicio LLM.
        llm_base_url: URL base de la API del LLM.
        llm_model: Identificador del modelo LLM.
        pause_between_requests: Segundos de pausa entre consultas al LLM.

    Returns:
        Una COPIA del DataFrame original con las columnas 'Home_Win_%',
        'Away_Win_%', 'Draw_%' añadidas, o None si el DataFrame de entrada
        es inválido. Los valores de predicción serán float o pd.NA.
    """
    # --- Validaciones ---
    if not isinstance(matches_df, pd.DataFrame):
        print("ERROR (add_llm_predictions): Se esperaba un DataFrame.")
        return None
    if matches_df.empty:
        print("INFO (add_llm_predictions): El DataFrame de partidos está vacío, no hay nada que predecir.")
        # Añadir columnas vacías para consistencia de schema si se desea
        df_copy = matches_df.copy()
        df_copy['Home_Win_%'] = pd.Series(dtype='float64')
        df_copy['Away_Win_%'] = pd.Series(dtype='float64')
        df_copy['Draw_%'] = pd.Series(dtype='float64')
        return df_copy
    required_cols = ['Home', 'Away', 'League']
    if not all(col in matches_df.columns for col in required_cols):
        print(f"ERROR (add_llm_predictions): Faltan columnas requeridas en el DataFrame: {required_cols}")
        return None
    if not llm_api_key:
         print("ERROR (add_llm_predictions): Falta la API Key del LLM.")
         return None

    # --- Preparación ---
    home_preds, away_preds, draw_preds = [], [], []
    print(f"INFO (add_llm_predictions): Iniciando predicciones para {len(matches_df)} partidos...")

    # --- Iteración y Consulta ---
    for index, row in tqdm(matches_df.iterrows(), total=matches_df.shape[0], desc="Prediciendo"):
        home_team = row['Home']
        away_team = row['Away']
        league = row['League']

        # Generar Prompt Específico
        prompt = (
            f"Para el partido de fútbol en la competición '{league}' entre "
            f"{home_team} (equipo local) y {away_team} (equipo visitante), "
            f"estima la probabilidad porcentual de los tres resultados posibles: "
            f"1) Victoria de {home_team}, 2) Victoria de {away_team}, 3) Empate. "
            f"IMPORTANTE: Tu respuesta DEBE contener únicamente tres números (0-100), "
            f"separados por comas, en el orden exacto [Probabilidad Victoria Local, Probabilidad Victoria Visitante, Probabilidad Empate]. "
            f"Usa punto '.' como separador decimal si es necesario. No incluyas '%', texto adicional ni explicaciones. "
            f"Ejemplo de respuesta válida: 40.5, 30, 29.5"
        )

        # Consultar al LLM
        llm_response = ask_language_model(
            prompt=prompt,
            api_key=llm_api_key,
            base_url=llm_base_url,
            model=llm_model
        )

        # Parsear la respuesta (usando una función helper interna o externa)
        home_pct, away_pct, draw_pct = parse_llm_prediction_response(llm_response)

        # Almacenar (usar pd.NA para nulos en Pandas)
        home_preds.append(home_pct if home_pct is not None else pd.NA)
        away_preds.append(away_pct if away_pct is not None else pd.NA)
        draw_preds.append(draw_pct if draw_pct is not None else pd.NA)

        # Pausa
        sleep(pause_between_requests)

    # --- Añadir columnas al DataFrame (copia) ---
    df_with_predictions = matches_df.copy()
    df_with_predictions['Home_Win_%'] = home_preds
    df_with_predictions['Away_Win_%'] = away_preds
    df_with_predictions['Draw_%'] = draw_preds

    # Asegurar tipo numérico (maneja pd.NA correctamente)
    df_with_predictions['Home_Win_%'] = pd.to_numeric(df_with_predictions['Home_Win_%'], errors='coerce')
    df_with_predictions['Away_Win_%'] = pd.to_numeric(df_with_predictions['Away_Win_%'], errors='coerce')
    df_with_predictions['Draw_%'] = pd.to_numeric(df_with_predictions['Draw_%'], errors='coerce')


    print("INFO (add_llm_predictions): Predicciones añadidas exitosamente.")
    return df_with_predictions

# --- Helper para parsear la respuesta del LLM (puede estar dentro o fuera) ---
def parse_llm_prediction_response(response: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Parsea la respuesta string del LLM esperando 'num, num, num',
    opcionalmente rodeada de corchetes [].

    Returns:
        Una tupla (local_win_pct, visitor_win_pct, draw_pct) con floats,
        o (None, None, None) si el parseo falla.
    """
    if not response:
        return None, None, None

    try:
        # Limpieza inicial: quitar espacios extra, %, saltos de línea
        cleaned = response.strip().replace('%', '').replace('\n', ' ')

        # --- NUEVO: Pre-procesamiento para quitar corchetes ---
        # Si la cadena empieza con '[' y termina con ']', quítalos.
        if cleaned.startswith('[') and cleaned.endswith(']'):
            cleaned = cleaned[1:-1].strip() # Quita el primer y último char, y espacios internos

        # --- Aplicar el Regex a la cadena ya sin corchetes ---
        # El regex busca el patrón 'numero, numero, numero'
        # Los anclajes ^ y $ aseguran que *solo* contenga eso después de la limpieza.
        match = re.search(r'^\s*(\d{1,3}(?:[.,]\d+)?)\s*,\s*(\d{1,3}(?:[.,]\d+)?)\s*,\s*(\d{1,3}(?:[.,]\d+)?)\s*$', cleaned)

        if match:
            # Extraer, asegurar punto decimal, convertir a float
            h_str = match.group(1).replace(',', '.')
            a_str = match.group(2).replace(',', '.')
            d_str = match.group(3).replace(',', '.')

            h = float(h_str)
            a = float(a_str)
            d = float(d_str)

            # Validación de rango (opcional pero recomendada)
            if 0 <= h <= 100 and 0 <= a <= 100 and 0 <= d <= 100:
                # Validación de suma (aún más opcional, puede fallar por redondeo)
                # total = h + a + d
                # if 98 < total < 102: # Margen de tolerancia
                #    return h, a, d
                # else:
                #    print(f"WARN (Parse): Suma no cercana a 100 ({total}) para respuesta '{response}'")
                #    return None, None, None # O devolver los valores si prefieres ser menos estricto
                return h, a, d # Devolver si los rangos son válidos
            else:
                print(f"WARN (Parse): Valores parseados fuera de rango [0-100] en respuesta '{response}': {h}, {a}, {d}")
                return None, None, None
        else:
            # Si el regex no coincide DESPUÉS de quitar corchetes
            print(f"WARN (Parse): Respuesta '{response}' (limpia: '{cleaned}') no coincide con el patrón esperado 'num, num, num'.")
            return None, None, None

    except (ValueError, TypeError) as e:
        # Error durante la conversión a float, etc.
        print(f"ERROR (Parse): Parseando respuesta '{response}': {e}")
        return None, None, None
    except Exception as e:
        # Otro error inesperado durante el parseo
        print(f"ERROR (Parse): Inesperado parseando '{response}': {e}")
        return None, None, None

# ==============================================================================
# BLOQUE PRINCIPAL DE EJECUCIÓN (EJEMPLO)
# ==============================================================================

# Credenciales API Football
FOOTBALL_API_HOST = "v3.football.api-sports.io"
FOOTBALL_API_KEY = "51c958f3c3dc64a884e05b468daba097"

# Credenciales LLM (DeepSeek en este caso)
LLM_API_KEY = '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'
LLM_BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'
LLM_MODEL = "deepseek/deepseek-chat:free"

# --- Verificar Configuración Mínima ---
if not FOOTBALL_API_KEY or not LLM_API_KEY:
    print("CRITICAL ERROR: Faltan claves API (API_FOOTBALL_KEY o DEEPSEEK_API_KEY).")
    print("Asegúrate de configurarlas como variables de entorno o en un archivo .env")
else:
    # --- Paso 1: Obtener Partidos ---
    print("\n--- PASO 1: Obteniendo Partidos ---")
    df_partidos = get_football_matches_today_local(
        api_host=FOOTBALL_API_HOST,
        api_key=FOOTBALL_API_KEY,
        target_timezone='America/Bogota' # O la zona que necesites
    )

    # --- Paso 2: Añadir Predicciones (si hay partidos) ---
    if df_partidos is not None:
        df_partidos.to_excel("API_results.xlsx", index=False)
        print("\n--- PASO 2: Añadiendo Predicciones ---")
        df_final = add_llm_predictions_to_matches(
            matches_df=df_partidos,
            llm_api_key=LLM_API_KEY,
            llm_base_url=LLM_BASE_URL,
            llm_model=LLM_MODEL,
            pause_between_requests=1.5 # Ajusta según rate limits de tu API
        )

        # --- Mostrar Resultado Final ---
        if df_final is not None:
            print("\n--- RESULTADO FINAL ---")
            print(df_final.to_string()) # .to_string() para ver todo el DF
            try:
                df_final.to_excel("predictions.xlsx", index=False)
                print("\nINFO: DataFrame guardado en predictions.xlsx")
            except Exception as e:
                print(f"ERROR: No se pudo guardar el archivo: {e}")
        else:
            print("\n--- No se pudo generar el DataFrame final con predicciones (error en Paso 2). ---")
    else:
        print("\n--- No se pudo obtener la lista de partidos (error en Paso 1). ---")