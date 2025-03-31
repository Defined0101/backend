from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router

app = FastAPI(
    title="FRS API",
    description="Food Recipe System API",
    version="1.0.0"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme ortamı için. Prodüksiyonda spesifik originler belirtilmeli
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router'ı ekle
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to FRS API"} 