from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os, json

router = APIRouter()

@router.get("/artifact")
def artifact():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "contracts", "FakeProdDetector.json")
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Artifact not found. Copy it to backend-python/contracts/FakeProdDetector.json")
    with open(path, "r") as f:
        data = json.load(f)
    return JSONResponse(content=data)