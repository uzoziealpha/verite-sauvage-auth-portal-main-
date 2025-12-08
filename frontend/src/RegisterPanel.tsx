import React, { useState } from "react";
import Web3 from "web3";
import QRCode from "qrcode";
import { loadContract } from "./useContract";

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
// For local dev, you can point this to your frontend-public dev server.
// For production, set VITE_PUBLIC_VERIFY_BASE in .env.
const PUBLIC_VERIFY_BASE =
  import.meta.env.VITE_PUBLIC_VERIFY_BASE || "http://localhost:5173";

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

  const change = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) =>
    setForm((f) => ({
      ...f,
      [e.target.name]: e.target.value,
    }));

  const register = async () => {
    if (!account) return alert("Connect MetaMask first");
    if (!form.name || !form.price) {
      return alert("Name and price are required");
    }
    if (!form.color || !form.material) {
      return alert("Please select both color and material");
    }

    setBusy(true);
    try {
      const web3 = new Web3(window.ethereum as any);
      const contract = await loadContract(web3);
      const now = Math.floor(Date.now() / 1000);

      // Deterministic-ish productId based on provided fields + timestamp
      const productId = web3.utils.soliditySha3(
        { type: "string", value: form.name },
        { type: "string", value: form.color || "" },
        { type: "string", value: form.material || "" },
        { type: "uint256", value: form.price },
        { type: "uint256", value: form.year || "0" },
        { type: "uint256", value: String(now) }
      )!;

      await contract.methods
        .uploadProduct(
          productId,
          form.name,
          form.color || "",
          form.material || "",
          web3.utils.toBN(form.price),
          Number(form.year || 0)
        )
        .send({ from: account });

      // ✅ QR now points to the PUBLIC verification frontend, not backend API
      const verifyUrl = `${PUBLIC_VERIFY_BASE}/?id=${productId}`;

      const dataUrl = await QRCode.toDataURL(verifyUrl, { width: 420 });
      onQr(dataUrl, productId);
      alert(`Registered. Product ID:\n${productId}`);
    } catch (e: any) {
      alert(e.message || "Transaction failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <h2>Register Product</h2>

      {/* Name & Price */}
      <div className="row">
        <input
          name="name"
          placeholder="Name"
          onChange={change}
          value={form.name}
        />
        <input
          name="price"
          placeholder="Price"
          type="number"
          onChange={change}
          value={form.price}
        />
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
          <option value="">Select color</option>
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
          <option value="">Select material</option>
          {MATERIAL_OPTIONS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      {/* Year */}
      <div className="row">
        <input
          name="year"
          placeholder="Year (optional)"
          type="number"
          onChange={change}
          value={form.year}
        />
      </div>

      {/* Submit */}
      <div className="row">
        <button className="primary" onClick={register} disabled={busy}>
          {busy ? "Submitting…" : "Register + Generate QR"}
        </button>
      </div>
    </div>
  );
}