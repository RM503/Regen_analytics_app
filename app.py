import uvicorn 
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from src.dash1.dash1_main import app as dash1

app = FastAPI()
app.mount("/dash1", WSGIMiddleware(dash1.server))

@app.get("/")
def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")