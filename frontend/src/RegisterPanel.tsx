import React, { useState } from "react";
import Web3 from "web3";
import QRCode from "qrcode";
import { loadContract } from "./useContract";
import { fetchJSON, BACKEND } from "./api";

// Admin-side options for VS products
const COLOR_OPTIONS = ["Elephant Gray", "Black", "White", "Brown"];

const MATERIAL_OPTIONS = [
  "Crocodile",
  "Ostrich",
  "Togo Leather",
  "Snake",
  "Stingray",
];

// Public verification frontend base URL (used in QR deep link)
const PUBLIC_VERIFY_BASE =
  import.meta.env.VITE_PUBLIC_VERIFY_BASE || "http://localhost:5173/verify";

declare global {
  interface Window {
    ethereum?: any;
  }
}

export default function RegisterPanel({
  account,
  onQr,
}: {
  account: string;
  onQr: (dataUrl: string, id: string) => void;
}) {
  const [form, setForm] = useState({
    name: "",
    price: "",
    color: "",
    material: "",
    year: "",
  });
  const [busy, setBusy] = useState(false);
  const [lastResult, setLastResult] = useState<{
    productId: string | null;
    shortCode: string | null;
    error?: string | null;
  }>({
    productId: null,
    shortCode: null,
    error: null,
  });

  const change = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) =>
    setForm((f) => ({
      ...f,
      [e.target.name]: e.target.value,
    }));

  async function register() {
    if (busy) return;
    setBusy(true);
    setLastResult({ productId: null, shortCode: null, error: null });

    try {
      if (!window.ethereum) {
        alert("MetaMask (or another Web3 wallet) is required.");
        return;
      }

      // 1) Connect Web3 + MetaMask
      const web3 = new Web3(window.ethereum as any);
      await window.ethereum.request({ method: "eth_requestAccounts" });
      const accounts = await web3.eth.getAccounts();
      const from = account || accounts[0];

      if (!from) {
        throw new Error("No Ethereum account available.");
      }

      // 2) Prepare product fields
      const name = form.name.trim();
      const color = form.color.trim();
      const material = form.material.trim();

      if (!name) {
        alert("Please enter a Product / Model Name.");
        return;
      }

      const rawPrice = form.price.replace(/[^\d]/g, "");
      const price = rawPrice ? parseInt(rawPrice, 10) : 0;
      const year = form.year ? parseInt(form.year, 10) : new Date().getFullYear();

      // 3) Compute productId bytes32 (must match Solidity's keccak256)
      const idHex = web3.utils.soliditySha3(
        { type: "string", value: name },
        { type: "string", value: color },
        { type: "string", value: material },
        { type: "uint256", value: price.toString() },
        { type: "uint256", value: year.toString() }
      ) as string | null;

      if (!idHex) {
        throw new Error("Failed to compute productId hash.");
      }

      console.log("[Admin] productId:", idHex);

      // 4) Load contract and send uploadProduct tx
      const contract = await loadContract(web3);

      console.log("[Admin] Sending uploadProduct tx...");
      await contract.methods
        .uploadProduct(idHex, name, color, material, price, year)
        .send({ from });

      console.log("[Admin] uploadProduct tx confirmed.");

      // 5) Register a VS security code in codes.json via backend
      //    This ensures the customer /customer-verify flow will work.
      console.log("[Admin] Calling /codes/register to store VS code…");
      const codeRes = await fetchJSON(`${BACKEND}/codes/register`, {
        method: "POST",
        body: JSON.stringify({
          product_id: idHex,
        }),
      });

      const shortCode: string = codeRes.shortCode;

      console.log("[Admin] Stored VS code:", shortCode);

      // 6) Build public verify URL (for customer QR)
      //    In production: https://www.verify.veritesauvage.com/verify?code=VSXXXX
      const verifyUrl = `${PUBLIC_VERIFY_BASE}?code=${encodeURIComponent(
        shortCode
      )}`;

      // 7) Generate QR PNG on the client for that URL
      const dataUrl = await QRCode.toDataURL(verifyUrl, {
        errorCorrectionLevel: "H",
        margin: 2,
        width: 512,
      });

      // 8) Show QR in admin UI + allow download
      onQr(dataUrl, idHex);

      setLastResult({
        productId: idHex,
        shortCode,
        error: null,
      });
    } catch (err: any) {
      console.error("[Admin] Register error:", err);
      setLastResult({
        productId: null,
        shortCode: null,
        error: err?.message || String(err),
      });
      alert(`Failed to register product: ${err?.message || String(err)}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h2>Register Vérité Sauvage Product</h2>

      {account && (
        <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.5rem" }}>
          Connected wallet: <span style={{ fontWeight: 500 }}>{account}</span>
        </p>
      )}

      <p style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "1rem" }}>
        This flow uses your MetaMask wallet to store a product fingerprint on-chain
        and simultaneously register a private Vérité Sauvage security code in the
        backend. A QR code is then generated that deep-links customers to the
        official verification page.
      </p>

      {/* Name / Model */}
      <div className="row">
        <label style={{ flex: 1 }}>
          Product / Model Name
          <input
            name="name"
            placeholder="Vérité Sauvage Petit (Black) Crocodile & Bamboo Edition"
            onChange={change}
            value={form.name}
          />
        </label>
      </div>

      {/* Price */}
      <div className="row">
        <label style={{ flex: 1 }}>
          Price (optional)
          <input
            name="price"
            placeholder="$18,090.00"
            onChange={change}
            value={form.price}
          />
        </label>
      </div>

      {/* Color & Material (selectable) */}
      <div className="row">
        <select
          name="color"
          value={form.color}
          onChange={change}
          style={{
            flex: 1,
            padding: "0.6rem 0.9rem",
            borderRadius: 999,
            border: "1px solid rgba(148,163,184,0.7)",
            background: "#ffffff",
            color: "#111827",
            fontSize: "0.95rem",
          }}
        >
          <option value="">Select Color</option>
          {COLOR_OPTIONS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <select
          name="material"
          value={form.material}
          onChange={change}
          style={{
            flex: 1,
            padding: "0.6rem 0.9rem",
            borderRadius: 999,
            border: "1px solid rgba(148,163,184,0.7)",
            background: "#ffffff",
            color: "#111827",
            fontSize: "0.95rem",
          }}
        >
          <option value="">Select Material</option>
          {MATERIAL_OPTIONS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      {/* Year */}
      <div className="row">
        <label style={{ flex: 1 }}>
          Year
          <input
            name="year"
            placeholder="2025"
            type="number"
            onChange={change}
            value={form.year}
          />
        </label>
      </div>

      {/* Submit */}
      <div className="row">
        <button className="primary" onClick={register} disabled={busy}>
          {busy ? "Submitting…" : "Register + Generate QR"}
        </button>
      </div>

      {/* Result summary */}
      {lastResult.shortCode && !lastResult.error && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: 12,
            background: "#ecfdf5",
            color: "#065f46",
            fontSize: "0.85rem",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Code Generated</div>
          <div>Product ID: {lastResult.productId}</div>
          <div>VS Code: {lastResult.shortCode}</div>
          <div style={{ marginTop: 4 }}>
            QR deep link:{" "}
            <code
              style={{
                fontSize: "0.75rem",
                background: "#d1fae5",
                padding: "0.15rem 0.3rem",
                borderRadius: 6,
              }}
            >
              {`${PUBLIC_VERIFY_BASE}?code=${lastResult.shortCode}`}
            </code>
          </div>
        </div>
      )}

      {lastResult.error && (
        <div
          style={{
            marginTop: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: 12,
            background: "#fef2f2",
            color: "#b91c1c",
            fontSize: "0.85rem",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Error</div>
          <div>{lastResult.error}</div>
        </div>
      )}
    </div>
  );
}