from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data import init_db
from vapi import router as vapi_router

# Initialize the vector database on startup
init_db()

app = FastAPI(title="Sahayak Voice Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vapi_router)

@app.get("/")
def root():
    return {"status": "Sahayak Backend is Running"}