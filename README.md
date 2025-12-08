# Fake QR Code Detector — Full Stack

This monorepo ships a complete app: **React** (Vite + TS) frontend + **FastAPI** backend + a minimal **Solidity** contract with **Hardhat** for local deploy.

## Quick Start

### 1) Start a local chain & deploy the contract

```bash
# Terminal A — local chain
cd solidity
npm install
npm run node
```

```bash
# Terminal B — compile & deploy
cd solidity
npm run compile
npm run deploy:local
# artifact written to: solidity/dist/FakeProdDetector.json
```

### 2) Wire the artifact to backend (and optional FE fallback)

```bash
# from repo root
cp solidity/dist/FakeProdDetector.json backend-python/contracts/FakeProdDetector.json
cp solidity/dist/FakeProdDetector.json frontend/public/contracts/FakeProdDetector.json  # optional fallback
```

### 3) Run the backend

```bash
cd backend-python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# edit .env (RPC_URL=http://127.0.0.1:8545, BACKEND_BASE_URL=http://localhost:4000)
uvicorn app.main:app --reload --port 4000
```

Health: http://localhost:4000/health  
Artifact: http://localhost:4000/artifact

### 4) Run the frontend

```bash
cd frontend
cp .env.example .env
# edit if needed: VITE_BACKEND_URL=http://localhost:4000
npm install
npm run dev
```

Open http://localhost:5173

### 5) Use it
1. **Connect MetaMask** (button handles localhost network 31337).  
2. Enter product details → **Register + Generate QR** → approve tx → QR appears.  
3. Scan the QR (or open) → it hits backend `/verify/{productId}` which reads on-chain data.  
4. You can also open the **server-generated** QR at `/qr/{productId}.png` (download/exportable).

## Notes
- Frontend loads the ABI/address from **backend `/artifact`**. If that fails, it falls back to `public/contracts/FakeProdDetector.json`.  
- Backend auto-detects contract address from artifact using `chain_id`. You can override with `.env: CONTRACT_ADDRESS=`.  
- Mobile-friendly layout: responsive grid and scalable QR.  
- To use Ganache instead of Hardhat, just deploy there and ensure the artifact’s `networks` contains that chain id, then set `RPC_URL` accordingly.
