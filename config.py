import os 
from dotenv import load_dotenv

#load_dotenv()

USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "false").lower() == "true"

LOCAL_DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "dash_local",
    "user": "dash_user",
    "password": "Thelookingglass*6"
}