from module_app_sifi import generate_rentability_report
from module_database import read_database
from module_basica_fondos import generar_basica_fondos

periodo = '202501'
path = r"C:\TEMP\SFMCRENT20250409_152707.xls"

#path = generate_rentability_report('MICA7508', 'FdCmva_202503', '31/01/2025')
database = read_database(path)
generar_basica_fondos(database, periodo)


