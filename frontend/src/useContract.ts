import Web3 from "web3";
import { getArtifact } from "./api";

export async function loadContract(web3: Web3) {
  const artifact = await getArtifact();
  const netId = await web3.eth.getChainId();

  const address =
    artifact.networks?.[String(netId)]?.address ||
    artifact.networks?.[netId]?.address;

  if (!address) {
    throw new Error(`Contract not deployed for network ${netId}.`);
  }

  return new web3.eth.Contract(artifact.abi, address);
}
