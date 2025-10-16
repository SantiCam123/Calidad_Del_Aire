import requests
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import os
import json

url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records"


def cargar_datos(url):
    print("--- Iniciando carga de datos desde la API ---")

    try:

        response = requests.get(url, timeout=30)
        if response.status_code != 200: # Si la respuesta no es 200, hubo un error
            print(f"\ERROR: {response.status_code}\n")

        else:

            response.raise_for_status()
            data = response.json()
            print(f"\nCarga de datos existosa desde la API\n")

            print("--- Procesando datos ---\n")

            data2 = {"fiwareid": [], 
                     "nombre": [], 
                     "direccion": [], 
                     "tipozona": [], 
                     "tipoemisio": [], 
                     "no2": [], 
                     "pm10": [], 
                     "pm25": [], 
                     "calidad_am": [],
                     "fecha_carg": [], 
                     "longitud": [], 
                     "latitud": []}

            for columns in data['results']:

                if columns["nombre"] == "Patraix": # Patraix tiene datos erróneos, se salta
                    print("Patraix encontrado, saltando registro...\n") 
                    continue
            
                #Guardamos los datos en el diccionario
                else:
                    data2["fiwareid"].append(columns['fiwareid'])
                    data2["nombre"].append(columns['nombre'])
                    data2["direccion"].append(columns['direccion'])
                    data2["tipozona"].append(columns['tipozona'])
                    data2["tipoemisio"].append(columns['tipoemisio'])
                    data2["no2"].append(columns['no2'])
                    data2["pm10"].append(columns['pm10'])
                    data2["pm25"].append(columns['pm25'])
                    data2["calidad_am"].append(columns['calidad_am'])
                    data2["fecha_carg"].append(columns['fecha_carg'])
                    data2["longitud"].append(columns['geo_point_2d']["lon"])
                    data2["latitud"].append(columns['geo_point_2d']["lat"])

            df = pd.DataFrame(data2) #Creamos el DataFrame

            print(f"Datos procesados exitosamente. Vista previa:\n{df.head()}\n")

            print("--- Guardando datos en CSV ---\n")

            #Buscamos y borramos los CSV previos en data/raw/
            for file in os.listdir("data/raw/"):
                if file.startswith("calidad_aire_raw_") and file.endswith(".csv"):
                    os.remove(os.path.join("data/raw/", file))

            df_json = pd.json_normalize(data['results']) #Usamos json_normalize para guardar solo el apartado de 'results' en bruto

            fecha = data['results'][1]['fecha_carg']
            fecha_limpia = fecha.replace(":", "-").replace("+", "").replace("T", "_") #Para evitar problemas con los dos puntos y el + en Windows

            df_json.to_csv(f"calidad_aire_raw_{fecha_limpia}.csv", index=False) #Guardamos el CSV en la carpeta raíz temporalmente

            os.replace(f"calidad_aire_raw_{fecha_limpia}.csv", f"data/raw/calidad_aire_raw_{fecha_limpia}.csv") #No funciona con Path, hay que forzar el movimiento con os

            print(f"Datos de la API guardados en data/raw/calidad_aire_raw_{fecha_limpia}.csv\n")

            return df #Devolvemos el DataFrame limpio para cargar a la base de datos


    except requests.exceptions.Timeout:

        print(f"ERROR: Timed Out\n")

def cargar_a_base_de_datos(df):
    print("--- Iniciando carga de datos a la base de datos ---\n")

    try:

        churro = "postgresql://postgres:mysecretpassword@localhost:5432/postgres"
        engine = create_engine(churro)

        if engine.connect():
            print("Conexión a la base de datos exitosa\n")

        else:
            print("ERROR: No hay conexión a la base de datos\n")
            return #Salimos de la función si no hay conexión
            
        print("--- Verificando datos en la base de datos ---\n")

        #Imprimimos la última fecha de modificación de cada dirección
        print("Última fecha de modificación de cada dirección:\n")
        print(pd.read_sql("SELECT nombre, MAX(fecha_carg) FROM calidad_aire GROUP BY nombre", engine), "\n")

        #Comprobamos si hay datos nuevos comparando la última fecha del DataFrame con la de la base de datos
        nueva_fecha = df['fecha_carg'].max()
        fecha_vieja = pd.read_sql("SELECT MAX(fecha_carg) FROM calidad_aire", engine)

        print("--- Comparando fechas para determinar si hay datos nuevos ---\n")

        if nueva_fecha != fecha_vieja.values[0][0]:
            print("HAY DATOS NUEVOS PARA CARGAR. Cargando...\n")
            df.to_sql('calidad_aire', engine, if_exists='append', index=False)

            df_db = pd.read_sql("SELECT * FROM calidad_aire", engine)
            print(f"Datos en la base de datos:\n{df_db}\n")
            print("Datos nuevos cargados\n")
        
        else:
            print("NO HAY DATOS NUEVOS PARA CARGAR\n")
            
            df_db = pd.read_sql("SELECT * FROM calidad_aire", engine)
            print(f"Datos en la base de datos:\n{df_db}\n")

        print("Datos cargados a la base de datos exitosamente\n")

    except Exception as e:
        print(f"ERROR: Fallo en la carga de datos a la base de datos: {e}\n")

def generar_alertas(df):
    print("--- Generando alertas de calidad del aire ---\n")

    alertas = {} #Diccionario para guardar las alertas

    for row in df.itertuples():
        if row.no2 > 200 or row.pm10 > 50 or row.pm25 > 25: #Umbrales de alerta
            print(f"ALERTA: Alta contaminación en {row.nombre}\n")

            alertas[row.nombre] = {
                "no2": row.no2,
                "pm10": row.pm10,
                "pm25": row.pm25,
            }

        else:
            print(f"Calidad del aire en {row.nombre} ... NORMAL\n") #No hay alerta, por lo que se muestra "normal"
        
    #Guardamos las alertas en un archivo JSON si hay alguna
    if len(alertas) != 0:
        json_alertas = json.dumps(alertas, indent=4)
        with open("../output/actual/alertas_calidad_aire.json", "w") as f:
            f.write(json_alertas)
        
        print("Archivo de alertas generado en output/actual/alertas_calidad_aire.json\n")



def main():

    data = cargar_datos(url)

    generar_alertas(data)
    
    if data is not None:
        cargar_a_base_de_datos(data)

    else:
        print("No se cargaron datos\n")

    

if __name__ == "__main__":
    main()