from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from datetime import datetime
import databases
import sqlalchemy
from typing import Optional
from sqlalchemy import MetaData

DATABASE_URL = "sqlite:///./gemini_proxy.db"
database = databases.Database(DATABASE_URL)
metadata = MetaData()

requests_table = sqlalchemy.Table(
    "requests",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("query", sqlalchemy.String),
    sqlalchemy.Column("response", sqlalchemy.Text),
    sqlalchemy.Column("timestamp", sqlalchemy.DateTime),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

app = FastAPI()

class Query(BaseModel):
    text: str

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
API_KEY = "PROVIDE API KEY" #For getting API Key read instructions  

# Establishing database connection
@app.on_event("startup")
async def startup():
    await database.connect()

# For Closing database
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Storing response and query with timestamp
async def store_request(query: str, response: str):
    query = {
        "query": query,
        "response": response,
        "timestamp": datetime.utcnow()
    }
    await database.execute(requests_table.insert().values(query))

# Handeling queries and storing
@app.post("/query")
async def process_query(query: Query):
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY
    }

    payload = {
        "contents": [{
            "parts": [{
                "text": query.text
            }]
        }]
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GEMINI_API_URL,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Gemini API error")

            response_data = response.json()
            await store_request(query.text, str(response_data))
            return response_data

        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=str(e))

# Retrieves history , queries and responses from the database
@app.get("/history")
async def get_history():
    query = requests_table.select()
    return await database.fetch_all(query)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)