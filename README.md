# Regen Organics app
## What is this app for?
This is an analytics app designed by DataKind for Regen Organics, serving two primary purposes:

* Generate key statistics related to planting cycles and crop growth using vegetation indices (NDVI and NDMI) with the help of Google Earth Engine (GEE) backend
* Serve as an analytics dashboard containing data and visualizations from pre-existing analyses and trained models which can be further supplement by queries from the end-user(s)

The design and functionality of this app relies heavily on the workflow carried out during the research phases of the project - which includes data generation, visualization, ETL and ML model training. The codebase can be accessed through the following link

https://github.com/RM503/DataKind_Geospatial/

## How to use this app?

At the moment, the app is mostly meant for querying farm polygons, extracting information about and them and (possibly) updating the existing database with the new information. The app is divided into multiple dashboards, each serving different purposes. This can be seen upon launching the app, taking the user to the landing page. The following contains detailed information regarding each dashboar:

* **Polygon generator:** This dashboard contains an interactive tile map which the user can use to explore regions on interest in Kenya, identify farms (at least visually) and draw polygons around them. Once a polygon is drawn, information on it will be generated, which contain a unique identifier (uuid), area in acres and polygon geometry. The data table will be updated upon each query. Note, however, that the app will only allow a maximum of five polygons to be queried at a given time before refreshing.

* **Farmland characteristics:** The user(s) can use the polygons generated in the previous dashboard to obtain NDVI-NDMI time series curves. These indices are extremely important for assessing crop/vegetation health and moisture levels. Furthermore, this dashboard also yields tabulated data that returns information on peak crop growing seasons, number of planting cycles, moisture level and important soil characteristics.

* **Main analytics dashboard:** This dashboard contains analyses results obtained from the research phase of the project, containing region-aggregated statistics on various metrics that have been deemed important for the project. Any newly queried polygons that have been pushed into the database will be added to the dashboard. Importantly, this dashboard can be used as a means of comparing farmland performance of various distributor locations.