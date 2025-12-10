// solidity/scripts/deploy.js// solidity/scripts/deploy.js
const hre = require("hardhat");

async function main() {
  const network = await hre.ethers.provider.getNetwork();
  console.log("Deploying FakeProdDetector to network:", network.name || network.chainId);

  const FakeProdDetector = await hre.ethers.getContractFactory("FakeProdDetector");
  const contract = await FakeProdDetector.deploy();

  await contract.waitForDeployment();
  const address = await contract.getAddress();

  console.log("FakeProdDetector deployed to:", address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
