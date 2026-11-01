from fastapi import FastAPI

app = FastAPI(title="TxnWeave API")

@app.get("/api/hello")
def hello_world():
    return {"message": "Hello World"}