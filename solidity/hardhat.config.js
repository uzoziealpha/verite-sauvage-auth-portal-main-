// solidity/hardhat.config.js

require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const RPC_URL_SEPOLIA = process.env.RPC_URL_SEPOLIA || "";
const PRIVATE_KEY = process.env.PRIVATE_KEY || "";

module.exports = {
  solidity: "0.8.21",
  networks: {
    hardhat: {
      chainId: 31337,
    },
    localhost: {
      url: "http://127.0.0.1:8545",
    },
    sepolia: {
      url: RPC_URL_SEPOLIA,
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
  },
};
