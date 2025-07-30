![Static Badge](https://img.shields.io/badge/alpha_version-1.0.0-blue)

# Regen Organics app
## What is this app for?
This is an analytics app designed by DataKind for Regen Organics, serving two primary purposes:

* Generate key statistics related to planting cycles and crop growth using vegetation indices (NDVI and NDMI) with the help of Google Earth Engine (GEE) backend
* Serve as an analytics dashboard containing data and visualizations from initial market data, pre-existing analyses and trained models. Future upades will include write functionalities of newly aquired data to the database.

The design and functionality of this app relies heavily on the workflow carried out during the research phases of the project - which includes data generation, visualization, ETL and ML model training. The codebase can be accessed through the following link

https://github.com/RM503/DataKind_Geospatial/

Even though the app was designed for a particular organization, it can be adapted to needs of other users.

## Building and running the app

The complete list of libraries required for running the app can be found in the `requirements.txt` or `pyproject.toml` files. To adapt the app for similar agricultural use cases, please clone the repository to your local device using


<pre>
```
git clone https://github.com/RM503/Regen_analytics_app.git
```
</pre>
It is understood that further modifications will require the user's own data. Regen Organics staff with access to API keys can user the app by first pulling it from Docker Hub using the following command
<pre>
```
docker pull rmahbub503/regen_app:v1
```
</pre>
Use the Docker file to first build the app
<pre>
```
docker build -t <whatever_name_you_want:version> .
```
</pre>
and run
<pre>
```
docker run --env-file .env.docker -p 8000:8000 <whatever_name_you_want:version>>
```
</pre>
In the run command, we explicitly inject the environment variables through a `.env.docker` file. A simpler method is to user the `docker-compose.yaml` file using the following command
<pre>
```
docker compose up
```
</pre>
 After the preceding steps have been completed, the app can be run locally at http://0.0.0.0:8000. The app, at the moment, uses the following APIs and services

* Google Earth Engine (GEE) Python API for calculating NDVI-NDMI curves from queried polygons
* iSDA API for extracting soil quantities for queried polygons
* Supabase for retrieving pre-existing data (write functionality has not been incorporated yet)

These services have their own API keys and URLs, which need to be provided for the app to work. The following is a skeleton for what the `.env` file should look like

```
GEE_PROJECT=... 
GOOGLE_APPLICATION_CREDENTIALS=...
EE_SERVICE_ACC_EMAIL=...
ISDA_USERNAME=...
ISDA_PASSWORD=...
SUPABASE_URL=...
```
For a complete set of instructions on how to use the app, please check the `docs` folder.

## How to use this app?

At the moment, the app is mostly meant for querying farm polygons, extracting information about and them. Write functionalities will be added in the future. The app is divided into multiple dashboards, each serving different purposes. This can be seen upon launching the app, taking the user to the landing page. The following contains detailed information regarding each dashboard:
* **Initial Market Data:** This dashboard contains exploratory data analysis using initial sales and leads data provided by Regen Organics. 

* **Polygon Generator:** This dashboard contains an interactive tile map which the user can use to explore regions on interest in Kenya, identify farms (at least visually) and draw polygons around them. Once a polygon is drawn, information on it will be generated, which contain a unique identifier (uuid), area in acres and polygon geometry. Note, however, that the app will only allow a maximum of five polygons to be queried at a given time before refreshing.

* **Farmland Characteristics:** The user(s) can use the polygons generated in the previous dashboard to obtain NDVI-NDMI time series curves. These indices are extremely important for assessing crop/vegetation health and moisture levels. Furthermore, this dashboard also yields tabulated data that returns information on peak crop growing seasons, number of planting cycles, moisture level and important soil characteristics.

* **Farmland Statistics:** This dashboard contains analyses results obtained from the research phase of the project, containing region-aggregated statistics on various metrics that have been deemed important for the project. Importantly, this dashboard can be used as a means of comparing farmland performance of various distributor locations.

## Contact

For questions or suggestions regarding the app, please contact rmahbub503@proton.me.