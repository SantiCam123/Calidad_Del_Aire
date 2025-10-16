import requests
import argparse
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import os
import json
import matplotlib.pyplot as plt
import pandas as pd
import folium
from datetime import datetime

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

def generar_informes():
    print("--- Generando informes de calidad del aire ---\n")
    with open("./output/actual/informe_a.html", "w") as archivo:
        archivo.write("<html>")
        archivo.write("<head>")
        archivo.write("<title>Informe actual de Calidad del Aire</title>")
        archivo.write("</head>")


    with open("./output/historico/informe_h.html", "w") as archivo:
        archivo.write("<html>")
        archivo.write("<head>")
        archivo.write("<title>Informe historico de Calidad del Aire</title>")
        archivo.write("</head>")

def main():

    data = cargar_datos(url)

    generar_alertas(data)
    
    if data is not None:
        cargar_a_base_de_datos(data)

    else:
        print("No se cargaron datos\n")

    parser = argparse.ArgumentParser(
        description="Filtra pedidos y genera un resumen de KPIs."
    )
    # TODO: añade argumentos:
    parser.add_argument("--modoactual", action="store_true", required=False, help="Informe del estado actual por estacion.")
    parser.add_argument("--modohistorico", action="store_true", required=False, help="Informe historico de la evolucion temporal por estacion.")

    args = parser.parse_args()
    print("[INFO] Args:", args)  # TEMP: borra al finalizar

    generar_informes()

    if args.modoactual:
        plt.figure(figsize=(15, 6))
        plt.bar(data['nombre'], data['no2'], color='skyblue')
        plt.xlabel('Barrio')
        plt.ylabel('NO2 Levels')
        plt.title('Niveles de NO2 por Barrio')
        plt.grid(axis='y')
        # guardar figura png
        plt.savefig('./output/actual/no2_barrio.png') 

        plt.figure(figsize=(15, 6))
        plt.bar(data['nombre'], data['pm10'], color='skyblue')
        plt.xlabel('Barrio')
        plt.ylabel('PM10 Levels')
        plt.title('Niveles de PM10 por Barrio')
        plt.grid(axis='y')
        plt.savefig('./output/actual/pm10_barrio.png')

        # mapa valencia
        mapa = folium.Map(location=[39.46975, -0.37739], zoom_start=13)
        # puntos interes
        puntos_interes = []

        # Iterate through DataFrame rows to create markers
        for idx, row in data.iterrows():
            folium.Marker(
                location=[row['latitud'], row['longitud']],
                popup=row['nombre'],
                tooltip=f"Nombre: {row['nombre']}, NO2: {row['no2']}<br>PM10: {row['pm10']}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(mapa)
            
        PistaSilla = data[data['nombre'] == 'Pista de Silla'].drop(columns=['direccion', 'tipozona', 'tipoemisio',  'latitud', 'longitud'])
        mapa.save('./output/actual/mapa_estaciones.html')

        #Combinamos el html del mapa con el informe actual

        with open("./output/actual/informe_a.html", "a") as archivo:

            archivo.write("<body>")
            archivo.write("<h1>Informe actual de Calidad del Aire</h1>\n")
            archivo.write("<h2>Gráfica de los niveles de NO2 por barrios de Valencia<h2>\n")
            archivo.write('<img src="no2_barrio.png" alt="Niveles de NO2 por Barrio">\n')
            archivo.write("<h2>Gráfica de los niveles de PM10 por barrios de Valencia<h2>\n")
            archivo.write('<img src="pm10_barrio.png" alt="Niveles de PM10 por Barrio">\n')
            archivo.write("<h2>Mapa de las estaciones de calidad del aire en Valencia<h2>\n")
            archivo.write('<iframe src="mapa_estaciones.html" width="100%" height="600"></iframe>\n')
            archivo.write("<h2>Datos de la estación Pista de Silla</h2>\n")
            archivo.write(PistaSilla.to_html(index=False))
            archivo.write("</body>")
            archivo.write("</html>")

        print("Generando informe del estado actual por estacion...")
    
    df_db = pd.read_sql("SELECT * FROM calidad_aire", create_engine("postgresql://postgres:mysecretpassword@localhost:5432/postgres"))

    if args.modohistorico:
        # 2025-10-14T09:00:00+00:00
        # pasar timestamp a datetime
        for time in df_db['fecha_carg']:
            df_db['fecha'] = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S%z')
        plt.figure(figsize=(15, 6))
        dfOlivereta = df_db[df_db['nombre'] == 'Olivereta']
        plt.plot(dfOlivereta['fecha'], dfOlivereta['no2'], marker='o', linestyle='-', color='b')
        plt.title('Niveles de NO2 a lo largo del tiempo')
        plt.xticks(rotation=30, ha='right')
        plt.xlabel('Fecha')
        plt.ylabel('Niveles de NO2')
        plt.grid()
        plt.savefig('./output/historico/no2_olivereta.png')

        plt.figure(figsize=(15, 6))
        dfOlivereta = df_db[df_db['nombre'] == 'Olivereta']
        plt.plot(dfOlivereta['fecha'], dfOlivereta['pm10'], marker='o', linestyle='-', color='b')
        plt.title('Niveles de pm10 a lo largo del tiempo')
        plt.xticks(rotation=30, ha='right')
        plt.xlabel('Fecha')
        plt.ylabel('Niveles de PM10')
        plt.grid()
        plt.savefig('./output/historico/pm10_olivereta.png')

        with open("./output/historico/informe_h.html", "a") as archivo:

            archivo.write("<body>")
            archivo.write("<h1>Informe historico de Calidad del Aire</h1>\n")
            archivo.write("<h2>Evolucion de los niveles de NO2 de Olivereta<h2>\n")
            archivo.write('<img src="no2_olivereta.png" alt="Niveles de NO2 Olivereta">\n')
            archivo.write("<h2>Evolucion de los niveles de PM10 de Olivereta<h2>\n")
            archivo.write('<img src="pm10_olivereta.png" alt="Niveles de PM10 Olivereta">\n')
            archivo.write("</body>")
            archivo.write("</html>")

        print("Generando informe historico de la evolucion temporal por estacion...")

    

if __name__ == "__main__":
    main()