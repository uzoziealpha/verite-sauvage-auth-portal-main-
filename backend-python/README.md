# Backend (FastAPI)

## Quick Start

```bash
cd backend-python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
# Edit .env as needed

# Copy contract artifact from solidity step:
# cp ../solidity/dist/FakeProdDetector.json contracts/FakeProdDetector.json

uvicorn app.main:app --reload --port 4000
```
Health: http://localhost:4000/health

## Endpoints
- `GET /health` — okay
- `GET /artifact` — serves contract artifact JSON
- `GET /verify/{productId}` — reads product from chain
- `GET /qr/{productId}.png` — PNG for QR (use `?save=1` to store under export/)
