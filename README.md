# Calidad_Del_Aire

# 🌬️ Proyecto Big Data — Calidad del Aire en València

## 🧠 Descripción del Proyecto

Este proyecto tiene como objetivo construir un **sistema reproducible de adquisición y análisis de datos de calidad del aire** en la ciudad de València.  
El flujo completo incluye:

- **Obtención automática de datos** desde la API pública del Ayuntamiento de València.  
- **Procesamiento y limpieza** de los registros recibidos, descartando datos erróneos (por ejemplo, la estación “Patraix”).  
- **Almacenamiento persistente** en una base de datos **PostgreSQL** en **Docker**, actualizando solo cuando hay nuevos datos.  
- **Generación de informes automáticos** en dos modos:
  - `--modoactual`: resumen del estado actual de las estaciones (gráficas, mapas, tablas).  
  - `--modohistorico`: evolución temporal de contaminantes a partir de los datos guardados en la base de datos.  
- **Creación de alertas** cuando los niveles de **NO₂**, **PM10** o **PM2.5** superan los límites establecidos.

En conjunto, este sistema permite **automatizar la ingesta, análisis y visualización de la calidad del aire**, integrando APIs, bases de datos y visualización geográfica.

## 🏗️ Arquitectura del Proyecto

La arquitectura del proyecto sigue una estructura **modular y reproducible**, basada en la integración de **API → Procesamiento → Base de datos → Informes**.

### 🔁 Flujo General de Datos

```text
        ┌────────────────────┐
        │   API Ayuntamiento │
        │  (Datos abiertos)  │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  app/app.py        │
        │ - Llama a la API   │
        │ - Limpia y valida  │
        │ - Guarda CSV       │
        │ - Carga a Postgres │
        │ - Genera informes  │
        └────────┬───────────┘
                 │
        ┌────────────────────┐
        │   PostgreSQL (DB)  │
        │ - Docker container │
        │ - Tabla: calidad_aire │
        └────────┬───────────┘
                 │
     ┌───────────┴────────────┐
     │                        │
     ▼                        ▼
┌──────────────┐       ┌──────────────┐
│ output/actual│       │output/historico│
│ - Gráficas   │       │ - Tendencias │
│ - Mapa       │       │ - Series     │
│ - Alertas    │       │   temporales │
└──────────────┘       └──────────────┘
```

### 💡 Descripción del flujo

1. API → Ingesta
El script app.py consulta la API del Ayuntamiento de València y descarga los datos más recientes sobre calidad del aire.
Se limpia la información, eliminando registros inválidos y normalizando los campos relevantes.

2. Procesamiento → CSV
Los datos procesados se guardan con timestamp en data/raw/, garantizando trazabilidad y control histórico.

3. Persistencia → PostgreSQL
Si los datos son nuevos (comparando fecha_carg), se insertan en la base de datos en Docker mediante SQLAlchemy.

4. Generación de informes
Dependiendo del modo seleccionado por el usuario:

--modoactual: genera gráficos de contaminantes, mapa interactivo y alertas.

--modohistorico: crea visualizaciones temporales de la evolución del aire.

5. Feature sorpresa
Durante la ejecución del modo actual, se evalúan los niveles de contaminantes.
Si NO₂ > 200, PM10 > 50 o PM2.5 > 25, se genera un archivo alertas_calidad_aire.json con las estaciones afectadas.

## ⚙️ Requisitos del Proyecto

### 🐳 Docker

Para la persistencia de los datos, el proyecto utiliza una base de datos **PostgreSQL** desplegada mediante Docker.

**Comando de inicio rápido:**

    docker run --name postgres-air -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres

**Verificación:**

    docker ps

Deberías ver el contenedor **postgres-air** en ejecución.

---

### 🐍 Entorno Conda

El entorno de Python se gestiona con **Conda**, garantizando la reproducibilidad del proyecto.

**Creación del entorno:**

    conda create -n calidad_aire_env python=3.11
    conda activate calidad_aire_env

**Instalación de dependencias:**

    pip install -r requirements.txt

**Dependencias mínimas requeridas:**
- pandas  
- requests  
- sqlalchemy  
- psycopg2-binary  
- matplotlib  
- folium  

---

### 💾 Comprobaciones iniciales

- `python -V` → debe devolver **3.11.x**  
- `docker ps` → contenedor de PostgreSQL en ejecución  
- `python -c "import pandas, requests, sqlalchemy; print('ok')"` → salida esperada: **ok**

## 🧠 Uso del Proyecto

El script principal `app/app.py` permite ejecutar la ingesta de datos, el almacenamiento en base de datos y la generación de informes mediante distintos **modos de ejecución**.

---

### ▶️ Ejecución general

Para ejecutar el proyecto, sitúate en la raíz del repositorio y ejecuta:

    python app/app.py

Esto iniciará la descarga de datos desde la API, su procesamiento y el guardado de resultados.

---

### ⚙️ Parámetros disponibles

| Parámetro | Descripción |
|------------|-------------|
| `--modoactual` | Genera un informe con el estado actual de la calidad del aire. Incluye gráficas, mapa y alertas. |
| `--modohistorico` | Genera un informe histórico basado en los registros almacenados en la base de datos. |
| *(sin argumentos)* | Ejecuta solo la ingesta de datos y actualización de la base de datos. |

---

### 📄 Ejemplos de ejecución

**1. Ingesta + informe actual**

    python app/app.py --modoactual

**2. Ingesta + informe histórico**

    python app/app.py --modohistorico

**3. Ingesta sin informes**

    python app/app.py

---

### 🧩 Modo Actual

- Descarga los datos más recientes desde la API.  
- Genera gráficos de barras con niveles de NO₂ y PM10 por estación.  
- Crea un mapa interactivo con las estaciones y sus valores.  
- Genera un informe HTML en `output/actual/informe_a.html`.  
- Si se superan umbrales críticos, se genera `output/actual/alertas_calidad_aire.json`.

---

### 📈 Modo Histórico

- Recupera los registros almacenados en PostgreSQL.  
- Genera gráficas temporales para analizar la evolución de contaminantes.  
- Crea un informe HTML en `output/historico/informe_h.html`.  

---

### 📂 Salidas esperadas

- `data/raw/`: CSVs con timestamp de cada llamada a la API.  
- `output/actual/`: informes, gráficos y alertas del estado actual.  
- `output/historico/`: informes y gráficas de tendencias históricas.  

## 📁 Estructura del Repositorio

La organización del proyecto sigue un esquema claro para facilitar su mantenimiento, ejecución y comprensión.

    proyecto-calidad-aire/
    ├── app/
    │   └── app.py                   → Script principal con la lógica de ingesta, análisis y generación de informes
    ├── notebooks/
    │   └── 00_ingesta_inicial.ipynb → Exploración inicial de la API y carga de datos en la base de datos
    ├── data/
    │   └── raw/                     → CSVs con timestamp que almacenan los datos obtenidos de la API
    ├── output/
    │   ├── actual/                  → Informes, mapas y alertas del estado actual
    │   └── historico/               → Informes y gráficas de evolución temporal
    ├── requirements.txt             → Dependencias del entorno Python
    ├── enunciado_proyecto_calidad_aire.md → Documento original del enunciado del proyecto
    ├── README.md                    → Documentación general del proyecto
    └── LICENSE (opcional)

---

### 🗂️ Descripción de las carpetas

- **app/** → Contiene el script CLI con `argparse` para ejecutar el flujo completo del proyecto.  
- **notebooks/** → Jupyter Notebook para la fase inicial de análisis y prueba de la API.  
- **data/raw/** → Almacena los snapshots de los datos obtenidos en formato CSV con fecha y hora.  
- **output/** → Guarda los resultados generados: informes HTML, gráficos, mapas y alertas.  
- **requirements.txt** → Lista de librerías necesarias para reproducir el entorno.  
- **README.md** → Documentación principal con instrucciones de uso y detalles técnicos.

---  

## ⚠️ Limitaciones Conocidas y Trabajos Futuros

### 🔧 Limitaciones actuales

- **Dependencia de la conexión a Internet:**  
  La API del Ayuntamiento de València requiere conexión activa; si el servicio está caído, el script no puede recuperar datos.

- **Sin gestión avanzada de errores de red:**  
  Aunque se maneja `timeout`, no se implementa un sistema de reintentos o backoff exponencial.

- **Datos incompletos o erróneos:**  
  Algunas estaciones, como *Patraix*, presentan valores inconsistentes y deben excluirse manualmente.

- **Escalabilidad limitada:**  
  El procesamiento y la generación de informes se ejecutan de forma secuencial en un solo hilo.  
  No se ha optimizado para ejecución concurrente ni grandes volúmenes de datos.

- **Alertas locales:**  
  Las alertas se guardan solo como archivo JSON local y no se integran con notificaciones externas o dashboards en tiempo real.

---

### 🚀 Trabajos futuros

- **Implementar caché de API:**  
  Evitar llamadas repetitivas si el CSV más reciente tiene menos de N minutos de antigüedad.

- **Mejorar la visualización:**  
  Integrar herramientas interactivas como *Plotly* o *Dash* para informes dinámicos.

- **Integrar alertas en tiempo real:**  
  Enviar notificaciones por correo o Slack cuando los niveles de contaminación excedan los umbrales.

- **Agregar control de logs y monitoreo:**  
  Incorporar un sistema de logging persistente y métricas básicas de ejecución.

- **Optimizar la base de datos:**  
  Implementar índices y vistas materializadas para mejorar las consultas históricas.

---

## 🎁 Feature Sorpresa — Sistema de Alertas Automáticas

El proyecto incorpora una **función adicional de alerta** que detecta automáticamente niveles peligrosos de contaminación en las estaciones monitorizadas.

---

### 🚨 Descripción

Durante la ejecución del modo **actual**, el script evalúa los niveles de los contaminantes principales (`no2`, `pm10`, `pm25`) para cada estación de medición.  
Si alguno de los valores supera los **umbrales definidos**, se genera un archivo JSON con las alertas correspondientes.

**Umbrales de activación:**
- `NO₂ > 200`
- `PM10 > 50`
- `PM2.5 > 25`

---

### 🧾 Salida generada

Cuando se detecta una superación de límites, el sistema crea:

- Archivo: `output/actual/alertas_calidad_aire.json`
- Contenido: listado de estaciones afectadas y los valores excedidos.

**Ejemplo:**

```json
{
    "Olivereta": {
        "no2": 210.3,
        "pm10": 48.1,
        "pm25": 22.5
    },
    "Pista de Silla": {
        "no2": 198.7,
        "pm10": 55.4,
        "pm25": 27.0
    }
}
```

### 💡 Utilidad

Este sistema permite:

- Identificar de forma inmediata las zonas con aire contaminado.

- Generar reportes automáticos para análisis o decisiones rápidas.

- Integrar, en futuras versiones, un sistema de alertas en tiempo real o visualización en dashboards.