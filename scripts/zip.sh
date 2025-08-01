#!/bin/bash 

SOURCE_PATH="/Users/rafidmahbub/Desktop/regen_analytics_app"
OUTPUT_ZIP_NAME="regen_analytics_app"

zip -r $OUTPUT_ZIP_NAME $SOURCE_PATH

echo "Files/directory zipped successfully to $OUTPUT_ZIP_NAME"