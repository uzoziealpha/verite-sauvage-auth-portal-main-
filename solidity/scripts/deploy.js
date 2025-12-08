// solidity/scripts/deploy.js
const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const FakeProdDetector = await hre.ethers.getContractFactory("FakeProdDetector");
  const contract = await FakeProdDetector.deploy();
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  console.log("FakeProdDetector deployed to:", address);

  // write artifact + address in a minimal format for backend/frontend use
  const artifact = await hre.artifacts.readArtifact("FakeProdDetector");
  const out = {
    abi: artifact.abi,
    networks: {}
  };
  // Hardhat localhost chainId is 31337
  out.networks["31337"] = { address };
  fs.mkdirSync(path.join(__dirname, "..", "dist"), { recursive: true });
  fs.writeFileSync(path.join(__dirname, "..", "dist", "FakeProdDetector.json"), JSON.stringify(out, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
