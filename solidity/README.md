# Solidity (Hardhat)

## Quick start (local)

```bash
cd solidity
npm install
npm run node   # in one terminal
# in another:
npm run compile
npm run deploy:local
# artifact will be written to: solidity/dist/FakeProdDetector.json
```

Then copy the artifact to backend:
```
cp solidity/dist/FakeProdDetector.json backend-python/contracts/FakeProdDetector.json
```
and/or to frontend:
```
cp solidity/dist/FakeProdDetector.json frontend/public/contracts/FakeProdDetector.json
```
