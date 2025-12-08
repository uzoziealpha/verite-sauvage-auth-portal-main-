const hre = require("hardhat");

// CHANGE THIS to your MetaMask address on Localhost 31337:
const TO_ADDRESS = "0xa2BB67a5912D742B052Bf1ad4CEe47E4FC3F747C";

// How much test ETH to send:
const AMOUNT = "5.0"; // ETH

async function main() {
  if (!TO_ADDRESS || !TO_ADDRESS.startsWith("0x") || TO_ADDRESS.length !== 42) {
    throw new Error("Set TO_ADDRESS to your MetaMask address (0x...)");
  }
  const [faucet] = await hre.ethers.getSigners(); // account[0] has lots of ETH
  console.log(`Sending ${AMOUNT} ETH to ${TO_ADDRESS} from ${await faucet.getAddress()}...`);
  const tx = await faucet.sendTransaction({
    to: TO_ADDRESS,
    value: hre.ethers.parseEther(AMOUNT),
  });
  console.log("Tx:", tx.hash);
  await tx.wait();
  console.log("✅ Confirmed!");
}

main().catch((err) => { console.error(err); process.exit(1); });
