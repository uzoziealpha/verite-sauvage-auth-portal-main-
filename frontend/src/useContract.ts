// src/useContract.ts

import Web3 from "web3";
import { getArtifact } from "./api";

export async function loadContract(web3: Web3) {
  // 1) Get ABI + networks from backend
  const artifact: any = await getArtifact();

  if (!artifact || !artifact.abi) {
    throw new Error("Invalid contract artifact from backend.");
  }

  // 2) Detect network ID from current web3 provider (MetaMask / Hardhat / etc.)
  const networkId = await web3.eth.net.getId();

  // 3) Try to find a matching deployed network in the artifact
  let address: string | undefined;

  if (artifact.networks && artifact.networks[networkId]) {
    // e.g. networks["31337"]
    address = artifact.networks[networkId].address;
  } else if (artifact.networks && artifact.networks["31337"]) {
    // fallback to hardhat default if running locally
    address = artifact.networks["31337"].address;
  }

  if (!address) {
    throw new Error(
      `No contract address found in artifact for network ${networkId}.`
    );
  }

  // 4) Return a ready-to-use contract instance
  return new web3.eth.Contract(artifact.abi, address);
}
