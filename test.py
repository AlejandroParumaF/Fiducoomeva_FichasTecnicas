import datetime
import calendar

# Tu variable de entrada
periodo = '202501'

# 1. Extraer año y mes del string
year_str = periodo[0:4]
month_str = periodo[4:6]

# Convertir a enteros
year = int(year_str)
month = int(month_str)

# 2. Encontrar el número de días en ese mes y año específico
# calendar.monthrange(año, mes) devuelve una tupla: (día_semana_primer_día, num_días_en_mes)
# Nos interesa el segundo valor: el número de días.
_, num_dias = calendar.monthrange(year, month)

# 3. Crear el objeto de fecha para el último día del mes
# Usamos el año, mes y el número de días que calculamos
fecha_ultimo_dia = datetime.date(year, month, num_dias)

# 4. (Opcional) Formatear la fecha como string 'dd/mm/yyyy' si lo necesitas así
fecha_formateada = fecha_ultimo_dia.strftime('%d/%m/%Y')

# --- Mostrar resultados ---
print(f"Periodo original: {periodo}")
print(f"Objeto de fecha (último día): {fecha_ultimo_dia}")
print(f"Tipo de la variable fecha_ultimo_dia: {type(fecha_ultimo_dia)}")
print(f"Fecha formateada: {fecha_formateada}")

# Asignar a la variable 'fecha' que mencionaste (si quieres el string formateado)
fecha = fecha_formateada
print(f"Variable 'fecha' (string formateado): {fecha}")

# O si prefieres que 'fecha' sea el objeto date:
# fecha = fecha_ultimo_dia
# print(f"Variable 'fecha' (objeto date): {fecha}")