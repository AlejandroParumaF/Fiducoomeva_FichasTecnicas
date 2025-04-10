import http.client
import json
import pandas as pd

# Configuración de la conexión
conn = http.client.HTTPSConnection("v3.football.api-sports.io")

headers = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': "51c958f3c3dc64a884e05b468daba097"
}

# Realizar la solicitud
conn.request("GET", "/leagues", headers=headers)

res = conn.getresponse()
data = res.read()

# Decodificar la respuesta JSON
json_data = json.loads(data.decode("utf-8"))

# Verificar si la respuesta contiene datos
if 'response' in json_data:
    # Extraer la lista de ligas
    leagues_list = json_data['response']
    
    # Crear DataFrame
    df = pd.json_normalize(leagues_list)
    
    # Seleccionar columnas relevantes (puedes ajustar esto)
    columns_to_keep = ['league.id', 'league.name', 'league.type', 'league.logo', 
                      'country.name', 'country.code', 'country.flag',
                      'seasons']
    df = df[columns_to_keep]
    
    # Guardar en archivo Excel
    df.to_excel('leagues.xlsx', index=False)
    print("Archivo leagues.xlsx guardado exitosamente!")
    
    # Opcional: Mostrar las primeras filas
    print(df.head())
else:
    print("Error en la respuesta de la API:")
    print(json_data)