import pandas as pd
import calendar
import datetime

class BasicaFondos(object):
    def __init__(self, database, periodo):
        self.database = database
        self.periodo = periodo
    
    def generar_superfinanciera(self):
        fecha_corte = self.dar_fecha_corte()
        nombres = {71197: 'FONDO DE INVERSIÓN COLECTIVA ABIERTO FIC AVANZAR VISTA',
                   76989: 'FONDO DE INVERSION COLECTIVA ABIERTO CON PACTO DE PERMANENCIA AVANZAR 365 DIAS',
                   82379: 'FIC ABIERTO CON PACTO DE PERMANENCIA AVANZAR 90 DIAS'
                     }
        df = pd.DataFrame(index=range(16), columns=['Fecha corte'])
        df['Fecha corte'] = fecha_corte
        df['Tipo Entidad'] = 5
        df['Cód. Entidad'] = 62
        df['Nombre Entidad'] = 'FIDUCOOMEVA'
        df['Cód. Negocio'] = [71197,71197,71197,71197,71197,71197,71197,71197,76989,76989,76989,76989,82379,82379,82379,82379]
        df['Nombre Negocio'] = df['Cód. Negocio'].map(nombres)
        df['Subtipo Negocio'] = 'FIC DE TIPO GENERAL'
        df['Principal / Compart.'] = 'Principal'
        df['Tipo Part. <sup>1<sup/>'] = 5
        df['Cons. id Part.'] = [1,2,3,26,15,16,17,18,1,2,3,5,11,12,13,14]

        df['Núm. unidades'] = self.database.table_smfcrent['Nro Inicial Unidades del Fondo']
        df['Valor unidad para las operaciones del día t'] = self.database.table_smfcrent['Valor Unidad Neta Final']
        df['Valor fondo al cierre del día t'] = self.database.table_smfcrent['Nuevo Valor del Fondo']
        df['Núm. Invers.'] = self.database.table_smfcrent['Numero de Inversionistas a la Fecha']
        df['Rentab. dia'] = self.database.table_smfcrent['Rentabilidad del Dia']
        df['Rentab. mes'] = self.database.table_smfcrent['Rentabilidad Mensual']
        df['Rentab. sem'] = self.database.table_smfcrent['Rentabilidad 7 Dias']
        df['Rentab. año'] = self.database.table_smfcrent['Rentabilidad 365 Dias']

        return df

    def dar_fecha_corte(self):
        # Extraer año y mes del string
        year_str = self.periodo[0:4]
        month_str = self.periodo[4:6]

        # Convertir a enteros
        year = int(year_str)
        month = int(month_str)

        # Encontrar el número de días en ese mes y año específico
        _, num_dias = calendar.monthrange(year, month)

        # Crear el objeto de fecha para el último día del mes
        fecha_ultimo_dia = datetime.date(year, month, num_dias)

        # Formatear la fecha como string 'dd/mm/yyyy'
        fecha_formateada = fecha_ultimo_dia.strftime('%d/%m/%Y')

        return fecha_formateada

    def generar_info_participacion(self):
        pass
    
def generar_basica_fondos(database, periodo):
    basica_fondos = BasicaFondos(database, periodo)
    sfc = basica_fondos.generar_superfinanciera()
    basica_fondos.generar_info_participacion()

