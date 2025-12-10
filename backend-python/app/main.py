# backend-python/app/main.py

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from backend-python/.env
load_dotenv()

# Routers
from app.routes.health import router as health_router
from app.routes.qr import router as qr_router
from app.routes.verify import router as verify_router
from app.routes.artifact import router as artifact_router
from app.routes.debug import router as debug_router
from app.routes.codes import router as codes_router
from app.routes.customer_verify import router as customer_verify_router


app = FastAPI(title="Fake QR Code Detector API")

# CORS — allow your local frontend + any extra you add in CORS_ORIGINS
origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Simple index with a map of important endpoints."""
    return {
        "message": "Vérité Sauvage backend is running",
        "endpoints": {
            "health": "/health",
            "artifact": "/artifact",
            "qr_png": "/qr/{product_id}.png",
            "verify_admin": "/verify/{product_id}",
            "codes_register": "/codes/register",
            "codes_get": "/codes/{product_id}",
            "customer_verify_post": "/customer-verify",
            "customer_verify_get": "/customer-verify?code=VSXXXX",
            "debug_contract": "/debug/contract",
        },
    }


# Attach routers
app.include_router(health_router)
app.include_router(artifact_router, prefix="")
app.include_router(qr_router, prefix="/qr")
app.include_router(verify_router, prefix="/verify")
app.include_router(codes_router, prefix="/codes")
app.include_router(customer_verify_router, prefix="")  # POST /customer-verify, GET /customer-verify
app.include_router(debug_router, prefix="/debug")
