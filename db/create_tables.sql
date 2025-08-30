CREATE EXTENSION postgis;

-tables for local testing
CREATE TABLE farmpolygons (
	uuid VARCHAR(36) PRIMARY KEY,
	region VARCHAR(50),
	area FLOAT8,
	geometry GEOMETRY,
	created_at TIMESTAMP
);

CREATE TABLE highndmidays (
	uuid VARCHAR(36),
	region VARCHAR(50),
	year INT2,
	high_ndmi_days INT2,
	created_at TIMESTAMP,
	PRIMARY KEY (uuid, year)
);

CREATE TABLE moisturecontent (
	id serial PRIMARY KEY,
	region VARCHAR(50),
	moisture_content VARCHAR(50),
	counts INT4
);

CREATE TABLE ndvipeaksannual (
	id serial PRIMARY KEY,
	ndvi_peak_year INT2,
	region VARCHAR(50),
	number_of_peaks_per_farm INT2,
	uuid_count INT4
);

CREATE TABLE ndvipeaksmonthly (
	id serial PRIMARY KEY,
	region VARCHAR(50),
	ndvi_peak_month VARCHAR(20),
	ndvi_peak_year INT2,
	ndvi_peaks_per_month INT4
);

CREATE TABLE ndvipeaksperfarm (
	uuid VARCHAR(36),
	region VARCHAR(50),
	ndvi_peak_date TIMESTAMP,
	ndvi_peak_value FLOAT8,
	peak_position INT2,
	created_at TIMESTAMP,
	PRIMARY KEY (uuid, ndvi_peak_date)
);

CREATE TABLE peakvidistribution (
	uuid VARCHAR(36),
	year INT2, 
	region VARCHAR(36),
	ndvi_max FLOAT8,
	ndmi_max FLOAT8,
	created_at TIMESTAMP,
	PRIMARY KEY (uuid, year)
);

CREATE TABLE soildata (
	uuid VARCHAR(36) PRIMARY KEY,
	region VARCHAR(50),
	bulk_density FLOAT4,
	calcium_extractable FLOAT4,
	carbon_organic FLOAT4,
	carbon_total FLOAT4,
	clay_content FLOAT4,
	iron_extractable FLOAT4,
	magnesium_extractable FLOAT4,
	nitrogen_total FLOAT4,
	ph FLOAT4,
	phosphorous_extractable FLOAT4, 
	potassium_extractable FLOAT4,
	sand_content FLOAT4,
	silt_content FLOAT4,
	stone_content FLOAT4,
	sulphur_extractable FLOAT4,
	texture_class INT2,
	zinc_extractable FLOAT4,
	geometry GEOMETRY
);
