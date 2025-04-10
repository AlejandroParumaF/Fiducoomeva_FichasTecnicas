import oracledb
import pandas as pd
import warnings

class Database:
    def __init__(self, path_smfcrent):
        self.connection = self.create_connection()
        warnings.simplefilter(action='ignore', category=UserWarning)

    def create_connection(self):
        config_sifi = {
                    'user'           : "SIFI_RPT",
                    'pwd'            : 'C00m3v4123*',
                    'host'           : 'BDCDPORA11.INTRACOOMEVA.COM.CO',
                    'port'           :  1554,
                    'service_name'   : 'CDPORA11'
                    }
            
        con_params = oracledb.ConnectParams(host = config_sifi['host'], port = config_sifi['port'], service_name = config_sifi['service_name'])
        connection = oracledb.connect(user = config_sifi['user'],  password = config_sifi['pwd'], params = con_params)
        print("Connection established")
        return connection
    
    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("Connection closed") 

    def execute_query(self, name, query, params=None):
            df = pd.read_sql(query, self.connection, params = params)
            print(f"Query executed: {name}")
            return df

    def query_coin(self, date):
        query = """
            SELECT 
                a.COIN_CIAS AS Empresa,
                a.COIN_FUENTE AS Fuente,
                a.COIN_CODIGO AS Número_de_Título,
                a.COIN_TPPA AS Tipo_Papel,
                REGEXP_SUBSTR(a.COIN_NIT_EMIS, '[^-]+', 1, 1) AS Emisor1,
                REGEXP_SUBSTR(a.COIN_NIT_EMIS, '[^-]+', 1, 2) AS Emisor2,
                REGEXP_SUBSTR(a.COIN_NIT_EMIS, '[^-]+', 1, 3) AS Emisor3,
                a.COIN_FVTO AS Fecha_Vencimiento,
                a.COIN_FECHA AS Fecha_Valoracion,
                a.COIN_DIAS_FVTO AS Días_Vencimiento,
                CASE WHEN a.COIN_PORT IS NULL THEN '' 
                ELSE (SELECT 	titu_tasa 
                    FROM 		pi_ttitu 
                    WHERE 	CAST(titu_port as VARCHAR2(4000))= a.COIN_PORT and titu_titu = a.COIN_CODIGO )  
                END AS Código_Tasas,
                a.COIN_CALI AS Calificación_Corto_Plazo ,
                a.COIN_CALI_LP AS Calificación_Largo_Plazo,
                a.COIN_MONE AS Moneda,
                a.COIN_VALO_MERC_MNAL AS Valor_Mercado_Local,
                a.COIN_VALO_DURA AS Duración ,
                a.COIN_VALO_DURA_MOD AS Duración_Modificada
            FROM 
                pi_vcoin a
            WHERE 
                to_date(a.COIN_FECHA,'dd/mm/yyyy') = to_date(substr(:date_start, 1, 10) || '00:00:00','YYYYMMDD hh24:mi:ss')
                AND a.COIN_CIAS IN(101,501,301)
        """
        df = self.execute_query('coin', query, [date])
        self.table_coin = df
        
    def query_inci(self, init_date, end_date):
        query = """
                SELECT * 
                FROM
                    sf_tinci
                WHERE 
                    inci_feccie  BETWEEN to_Date(:init_date,'dd/mm/yyyy') AND to_Date(:end_date,'dd/mm/yyyy')
                   """
        df = self.execute_query('inci', query, [init_date, end_date])
        self.table_inci = df

    def read_sfrent(self, path_smfcrent):
        df = pd.read_excel(path_smfcrent, skiprows=4)
        
        df = df[df['Descripción Opción Inversión'] != "OPCION GENERAL"]
        df = df[df['Nro Inicial Unidades del Fondo'] != 0]
        df = df.drop(columns=["Tipo de Negocio", "SubTipo de Negocio", "Valor Aportes del Dia", "Valor Redenciones del Dia", "Valor Anulaciones del Dia", "Rendimientos Brutos del Dia", "Rendimientos Netos del Dia", "Pre-cierre del Fondo del Dia", "Valor del Fondo Final del Dia Unidades"])
        df = df.reset_index(drop=True)
        self.table_smfcrent = df

def read_database(path_smfcrent):
    database = Database(path_smfcrent)
    database.query_coin('20250131')
    database.query_inci('01/01/2025', '31/01/2025')
    database.close_connection()

    database.read_sfrent(path_smfcrent)

    with pd.ExcelWriter("Datos_SIFI.xlsx", engine='openpyxl') as writer:
        database.table_coin.to_excel(writer, sheet_name='COIN', index=False)
        database.table_inci.to_excel(writer, sheet_name='INCI', index=False)
        database.table_smfcrent.to_excel(writer, sheet_name='SMFCRENT', index=False)
   
    return database