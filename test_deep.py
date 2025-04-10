import requests

# 1. Configuración de la API
API_KEY = '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'
BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'

# 2. Headers (incluyendo la API Key)
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 3. Datos que enviamos a DeepSeek (cuerpo de la solicitud)
data = {
    "model": "deepseek/deepseek-chat:free",
    "messages": [{"role": "user", "content": "Resultado más probable Colombia vs Perú, dame únicamente el % de quien gana"}]
}

# 4. Hacemos la petición POST a la API
response = requests.post(BASE_URL, headers=headers, json=data)

# 5. Verificamos si la solicitud fue exitosa (código 200)
if response.status_code == 200:
    respuesta = response.json()
    # Extraemos y mostramos el contenido de la respuesta
    mensaje_respuesta = respuesta["choices"][0]["message"]["content"]
    print("🤖 DeepSeek dice:")
    print(mensaje_respuesta)
else:
    print("❌ Error al consultar la API:")
    print(f"Código de error: {response.status_code}")
    print(response.text)  # Mensaje de error detallado