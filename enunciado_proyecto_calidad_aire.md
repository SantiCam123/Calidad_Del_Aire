# Proyecto Big Data — Calidad del Aire en València

## 1) Objetivo
Construir un **proyecto reproducible** que:
- **Obtenga** datos de calidad del aire del *Ayuntamiento de València* (endpoint oficial).
- **Ingestione** y **actualice** una base de datos **PostgreSQL** (en **Docker**) **solo si hay datos nuevos**.
- **Genere informes** “Actual” e “Histórico” desde un **script Python** ejecutable por CLI.
- Entregue un **repositorio limpio**, documentado y listo para ejecutar con **conda**.

Trabajo **por equipos de 2–3 personas**.

---

## 2) Fuente de datos
Endpoint (GET):  
`https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records`

**Snippet de arranque (referencia mínima):**
```python
import requests

url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/estacions-contaminacio-atmosferiques-estaciones-contaminacion-atmosfericas/records"
response = requests.get(url, timeout=30)
response.raise_for_status()
data = response.json()  # dict con keys como 'results', 'total_count'
```
> Nota: añadid gestión de errores, timeouts, y validaciones mínimas.

---

## 3) Flujo y entregables

### 3.1. Preparación (en **Notebook**)
1. **Conexión con la API** y exploración inicial.
2. **Selección de columnas relevantes** y carga en un **DataFrame de pandas**.  
   Sugeridas (mínimas):  
   - `fiwareid` (id único de estación)  
   - `nombre`, `direccion`, `tipozona`, `tipoemisio`  
   - Contaminantes: `no2`, `o3`, `so2`, `co`, `pm10`, `pm25` (y cualesquiera presentes)  
   - `calidad_am`  
   - `fecha_carg` (timestamp de la medición)  
   - Coordenadas: `geo_point_2d.lat`, `geo_point_2d.lon`
3. **Primera carga** a PostgreSQL (Docker).  
   - Crear esquema y tabla(s).  
   - Cargar un primer “snapshot” para dejar la BBDD lista.

### 3.2. Ingesta/actualización (en **script .py**)
Implementad la lógica siguiente:
- **Chequear el último valor por estación** en la BBDD (p.ej., SELECT por `fiwareid` ordenado por `fecha_carg` desc).
- **Comparar** con lo que devuelve la API.  
  - **Si hay nuevos registros** (por `fiwareid`, `fecha_carg`): **apendizad**.  
  - **Si no hay novedades**: **no insertéis** duplicados.
- **Persistir a CSV** **toda la respuesta** de la API **en crudo** (foto del momento) con **timestamp en el nombre**.  
  - Guardadlo en `data/raw/` y **sobrescribid** el symlink o el “último.csv” si queréis, pero el CSV con timestamp debe quedar.
- Se recomienda **SQLAlchemy** + `pd.read_sql()` / `df.to_sql()`.

### 3.3. Informes (vía **argparse** en el mismo script)
- **`--modo actual`**  
  - Usa **el CSV más reciente** (“foto” actual).  
  - Genera **1 tablita** (resumen por estación) y **al menos 2 gráficas** (ej.: barras por NO₂/PM10; mapa simple opcional).  
  - Guarda en `output/actual/`.
- **`--modo historico`**  
  - Lee de **BBDD** y genera **al menos 1 gráfica temporal** por contaminante/estación (o global agregada).  
  - Guarda en `output/historico/`.

**Ejemplos de ejecución:**
```bash
# Ingesta + informe actual
python app/main.py --modo actual

# Ingesta + informe histórico
python app/main.py --modo historico

# Opcionales útiles
python app/main.py --since "2025-10-01" --estacion "A05_POLITECNIC_60m"
```

---

## 4) Requisitos técnicos

### 4.1. Docker + Postgres
- Proveed un `docker` con un servicio `postgres`.
- docker run --name my-postgres -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres



### 4.2. Entorno Python (conda)
- `requirements.txt` con al menos:  
  `pandas`, `requests`, `sqlalchemy`, `psycopg2-binary` (o `psycopg`), `matplotlib` (o `plotly`).
- README con:
  - Creación de entorno (`conda create ...` y `pip install -r requirements.txt`).
  - Arranque de Docker 
  - Ejemplos de ejecución del script y **expectativas de salida** (carpetas generadas).

---

## 5) Estructura del repositorio (propuesta)
```
proyecto-calidad-aire/
├─ app/
│  ├─ app.py                  # script CLI con argparse
├─ notebooks/
│  └─ 00_ingesta_inicial.ipynb # conexión API, EDA rápida y primera carga
├─ data/
│  └─ raw/                     # CSVs con timestamp
├─ output/
│  ├─ actual/
│  └─ historico/
├─ README.md
├─ requirements.txt 
└─ LICENSE (opcional)
```

---

## 6) Reglas funcionales imprescindibles
- **Idempotencia de ingesta**: nunca duplicar (`fiwareid`, `fecha_carg`).
- **Robustez de red**: reintentos (exponencial backoff simple) y `timeout`.
- **Logs claros**: informad qué se insertó y cuántos registros se saltaron por “ya existentes”.
- **CSV con timestamp** siempre que se llame a la API (p. ej., `data/raw/airsnap_2025-10-14T12-00-00Z.csv`).
- **Gráficas reproducibles**: que el script **no requiera** abrir el notebook para generarlas.

---

## 7) Informe “Actual”
Mínimos:
- Tabla por estación con: `fiwareid`, `nombre`, `no2`, `pm10`, `pm25`, `calidad_am`, `fecha_carg`.
- Dos gráficas:
  1. **Barras** comparando `no2` por estación (o contaminante que esté más presente).
  2. **Barras** para `pm10` y/o `pm25` por estación.
- Guardado en `output/actual/` con nombres consistentes (`tabla_actual.csv`, `no2_por_estacion.png`, etc.).

## 8) Informe “Histórico”
- Gráfica temporal (línea) de **al menos un contaminante** (ej. `no2`) por estación o global agregada.  
- Rango temporal configurable (opcional `--since` / `--until`).  
- Guardado en `output/historico/`.

---

## 9) README (contenido mínimo)
- **Descripción** del proyecto y objetivo.
- **Arquitectura** (diagrama simple y breve explicación del flujo).
- **Requisitos** (Docker, conda).
- **Uso** (comandos de ejemplo, modos `actual`/`historico`, parámetros).
- **Estructura** del repo.
- **Limitaciones** conocidas y trabajos futuros.
- **Feature sorpresa** (describirla).

---

## 10) Feature sorpresa (obligatoria, libre elección)
Ideas (escoged **una** o proponed otra):
- **Alerta simple**: si `no2` o `pm10` exceden un umbral, generar un aviso en `output/actual/alertas.json`.
- **Ranking** de estaciones por calidad del aire y tendencia respecto a la “foto” previa.
- **Mapa estático** (con `matplotlib`) situando estaciones coloreadas por `no2`.
- **API cache**: evitad llamadas si ya hay un CSV reciente (< N minutos).

---

## 11) Criterios de evaluación (orientativos)
- **Correctitud funcional** (ingesta idempotente, informes, CSV con timestamp): **35%**
- **Calidad del código** (modularidad, tipado opcional, manejo de errores, logs): **20%**
- **Arquitectura y reproducibilidad** (Docker, conda, README claro): **20%**
- **Claridad analítica** (tablas/gráficas legibles, títulos/ejes/unidades): **15%**
- **Feature sorpresa** (utilidad y ejecución): **10%**

---

## 12) Pautas de trabajo en equipo
- Definid **roles** (Ingesta/API, BBDD/SQLAlchemy, Reporting/Gráficas, DevOps/README).
- **Issues** y **milestones** en el repositorio para coordinaros.
- Haced **commits pequeños** y mensajes claros.

---

## 13) Checklist de entrega
- [ ] Levantar Postgres.  
- [ ] `requirements.txt` 
- [ ] **Notebook** con la ingesta inicial y carga a BBDD.  
- [ ] **Script CLI** (`app/app.py`) con `--modo actual` y `--modo historico`.  
- [ ] CSVs en `data/raw/` con timestamp.  
- [ ] Salidas en `output/actual/` y `output/historico/`.  
- [ ] README completo.  
- [ ] **Feature sorpresa** descrita y funcionando.

---

## 14) Notas finales
- Sois un equipo: **delegad** y **comunicaos**.
- Grandes proyectos = **muchas piezas pequeñas bien hechas**.
- Entended bien los datos y **lo que se os pide** antes de picar código.
- Apoyaos en material de clase. **Preguntad** si os bloqueáis.
- Evitad el **síndrome del cuaderno mágico**: todo debe correr desde el **script**.

¡A por ello!
