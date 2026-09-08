![License](https://img.shields.io/github/license/RM503/Regen_analytics_app)
![Docker Pulls](https://img.shields.io/docker/pulls/rmahbub503/regen_organics_analytics_app)
![Docker Image Size](https://img.shields.io/docker/image-size/rmahbub503/regen_organics_analytics_app)
![Docker Stars](https://img.shields.io/docker/stars/rmahbub503/regen_organics_analytics_app)

<p align="center">
    <img src="logos/datakind_logo.png" alt="DK" style="width:15%; height:auto;">
    &nbsp;&nbsp;&nbsp;&nbsp
    <img src="logos/regen_logo.png" alt="RO" style="width:70%; height:auto;">
</p>

# Regen Organics analytics app

An agricultural analytics web application built by [DataKind](https://www.datakind.org/) volunteers for [Regen Organics](https://www.regenorganics.co/). It combines farm polygon mapping, satellite vegetation indices, soil data, and regional statistics to support farmland analysis in Kenya.

The app builds on the research, data preparation, and modeling in [DataKind_Geospatial](https://github.com/RM503/DataKind_Geospatial).

## Dashboards

| Dashboard | Route | Features |
| --- | --- | --- |
| Initial Market Data | `/initial_market_data/` | Sales, purchases, distributor activity, and lead conversion charts from prepared Plotly JSON files. |
| Polygon Generator | `/polygon_generator/` | Explore a map of Kenya, search coordinates, and draw up to five farm polygons with UUIDs, areas in acres, and geometry. |
| Farmland Characteristics | `/farmland_characteristics/` | Submit polygon WKT or upload farm data to retrieve NDVI/NDMI time series, calculate planting and moisture statistics, and query iSDA soil properties. Click NDVI points to retrieve satellite imagery. |
| Farmland Statistics | `/farmland_statistics/` | Compare regional planting peaks, moisture, vegetation indices, and soil characteristics from the database. |

Supabase authentication is available on the landing page. Database inserts require a signed-in user. The dashboard does not provide update or delete controls.

## Architecture

- **Flask and Dash** serve the landing page, authentication routes, and four dashboards; Plotly and Dash Leaflet provide charts and maps.
- **Celery and Redis** run Earth Engine time-series retrieval in a background worker. The dashboard polls task status and processes the returned data into charts and statistics.
- **Google Earth Engine** supplies Sentinel-2 NDVI and NDMI data. The time-series service defaults to a five-year lookback and accepts up to five polygons.
- **iSDA** supplies soil properties for queried farms.
- **Supabase and PostgreSQL/PostGIS** provide authentication, polygon storage, and regional analytics. SQL functions and triggers under `db/` maintain aggregate statistics.

## Setup

Use Python 3.11 or later for a native setup, or Docker with Docker Compose for the container setup. Both require configured external services and project data.

```sh
git clone https://github.com/RM503/Regen_analytics_app.git
cd Regen_analytics_app
cp .env_template .env
```

### Configuration

Populate `.env` for native execution or `.env.docker` for Compose. Variable names are case-sensitive, including the lowercase iSDA names.

| Variable | Purpose |
| --- | --- |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to the Earth Engine service-account JSON file; use `/app/credentials.json` in containers. |
| `EE_SERVICE_ACC_EMAIL` | Earth Engine service-account email; the time-series worker also accepts `EE_SERVICE_ACCOUNT`. |
| `GEE_PROJECT` | Earth Engine project setting included in the template. |
| `isda_username`, `isda_password` | iSDA account credentials. |
| `SUPABASE_URL`, `SUPABASE_KEY` | Supabase project URL and API key used by the application. |
| `DB_URL` | SQLAlchemy PostgreSQL connection URL used for database reads. |
| `SESSION_SECRET_KEY` | Secret used to sign Flask sessions. |
| `CELERY_BROKER_URL` | Redis broker URL; use `redis://localhost:6379/0` for native execution. |
| `CELERY_RESULT_BACKEND` | Redis result backend; use `redis://localhost:6379/1` for native execution. |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend-only key used by the service client and authentication administration helper. |

The template also includes `SUPABASE_USR_EMAIL` and `SUPABASE_USR_PASSWORD`; interactive login uses credentials entered on the landing page. Compose supplies both Celery URLs using the `redis` service hostname.

Create a root-level `config.py`, which is imported by the database modules but ignored by Git. For the default Supabase insert mode, a minimal configuration is:

```python
import os

USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "false").lower() == "true"
LOCAL_DB_CONFIG = {}
```

For local PostgreSQL inserts, set `USE_LOCAL_DB=true` and populate `LOCAL_DB_CONFIG` with the connection fields `host`, `port`, `database`, `user`, and `password`. Reads still use `DB_URL`, and authentication and region lookup still use Supabase. Compose does not include PostgreSQL.

### Required files and database data

- Supply your service-account key as `credentials.json` in the repository root. Both Dockerfiles copy this file into the image, so built images contain that credential and must be kept private.
- Obtain the prepared market-data JSON files and place them in `src/dashboards/initial_market_data/plots_json/`. This directory is ignored by Git; the expected filenames are listed in [dash0_main.py](src/dashboards/initial_market_data/dash0_main.py).
- Configure a PostgreSQL/PostGIS database with the farm tables and aggregate data expected by the dashboards. [db/create_tables.sql](db/create_tables.sql) contains local table definitions; `db/triggers_local/` and `db/triggers_supabase/` contain environment-specific functions and triggers. These are reference scripts, not a complete automated database bootstrap.
- Provide the Supabase `regionbboxes` table with `region`, `geometry`, and `centroid_point` fields for region maps and location selection. Its definition and seed data are not included in the table-creation script.
- Configure Supabase users and database access policies for authenticated inserts. The repository does not include a complete authentication or policy setup.

Keep environment files and credentials out of version control.

## Run with Docker Compose

After completing setup, create the container environment file and adjust the credentials path to `/app/credentials.json`:

```sh
cp .env .env.docker
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). Compose builds `Dockerfile.dev` for the web app and worker, starts Redis 7, and sets `PYTHONPATH=/app/src` for both Python services. Gunicorn listens on port 8080 by default, despite the development Dockerfile's `EXPOSE 8000` metadata.

```sh
docker compose logs -f app celery
docker compose down
```

Both Dockerfiles install `requirements.txt`. The root `Dockerfile` is intended for the web container in AWS Elastic Beanstalk; running that container alone does not start the Redis broker or Celery worker needed for time-series requests.

## Run natively

From the repository root, install the runtime dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Alternatively, use the committed uv lockfile with the runtime extras:

```sh
uv sync --extra worker --extra geo --extra analytics --extra cloud
source .venv/bin/activate
```

The base dependencies in `pyproject.toml` alone do not cover all dashboard imports. The `notebook` extra adds notebook tooling.

Set the two Celery URLs in `.env` as shown above. Start Redis locally, or use the Compose Redis service:

```sh
docker compose up -d redis
```

When using Compose for Redis, its configuration still expects `.env.docker` to exist. In separate terminals, activate the virtual environment and run these commands from the repository root:

```sh
# Background worker
PYTHONPATH=src celery -A regen_queue.celery_app worker --loglevel=info
```

```sh
# Development web server
PYTHONPATH=src python flask_app.py
```

Open [http://localhost:8080](http://localhost:8080). For Gunicorn instead of the Flask debug server:

```sh
PYTHONPATH=src gunicorn -c gunicorn.conf.py flask_app:app
```

### AWS configuration

`config_loader.py` detects Elastic Beanstalk using environment markers or `APP_ENV=eb` and loads a JSON secret from AWS Secrets Manager. Set `AWS_SECRETS_NAME`, provide permission to read that secret, and optionally set `AWS_REGION` (default `us-east-1`). A deployment must also supply reachable Redis and a Celery worker with the same broker and backend settings as the web app.

## Usage and repository layout

Start with Polygon Generator, then submit its farm geometry or exported CSV to Farmland Characteristics. CSV inputs should include `uuid`, `region`, `area (acres)`, and `geometry` (WKT). Sign in to save generated data, and use Farmland Statistics to compare regions.

See the [user manual](docs/regen_app_manual.pdf) and [video walkthrough](https://www.youtube.com/watch?v=c0UN69OeOIo) for dashboard usage.

```text
flask_app.py          Flask entry point and authentication routes
config_loader.py     Local, Docker, and AWS environment loading
src/dashboards/      Four Dash applications and their callbacks
src/regen_queue/     Celery app, time-series task, and job creation helper
src/services/        Earth Engine, iSDA, and region lookup integrations
src/analytics/       Vegetation preprocessing and farm statistics
src/auth/            Supabase authentication and service clients
src/db/              Database connections and insert helpers
db/                  SQL table definitions and aggregation triggers
static/, templates/  Landing page assets and template
docs/                User manual
scripts/             Development and deployment utilities
```

## Contributing

Fork the repository, create a feature branch, and submit a pull request describing your changes and validation. For dashboard changes, check the affected workflow with configured services, including the worker for time-series requests. Ruff settings are defined in `pyproject.toml`; no automated test suite is currently tracked in the repository.

Licensed under the [MIT License](LICENSE).

## Contact

For questions or suggestions regarding the app, please contact Rafid Mahbub (rmahbub503@gmail.com), Sheldon Waugh (waughsh@gmail.com) or Ratri Maria (ratri.maria@datakind.org).
