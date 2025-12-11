// frontend/src/CustomerVerify.tsx
import React, { useState } from "react";
import { BACKEND, fetchJSON } from "./api";

type Verdict = {
  status: string;
  reason: string;
};

type VerifyResponse = {
  success: boolean;
  product: Record<string, any>;
  verdict: Verdict;
};

export default function CustomerVerify({ productId }: { productId: string }) {
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onVerify = async () => {
    const trimmed = code.trim();
    if (trimmed.length !== 6) {
      setError("Please enter the 6 characters printed on your Vérité Sauvage card.");
      return;
    }

    setBusy(true);
    setError(null);
    setResult(null);

    try {
      // Use the customer-verify endpoint (POST) to check both on-chain and short code
      const data = (await fetchJSON(
        `${BACKEND}/customer-verify`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ product_id: productId, short_code: trimmed }),
        }
      )) as VerifyResponse;
      setResult(data);
    } catch (e) {
      console.error(e);
      setError("Unable to verify right now. Please try again in a moment.");
    } finally {
      setBusy(false);
    }
  };

  const renderVerdict = () => {
    if (!result) return null;
    const { verdict, product } = result;

    if (verdict.status === "authentic") {
      return (
        <div style={{ marginTop: "1rem", color: "#22c55e", fontWeight: 600 }}>
          ✅ Authentic Vérité Sauvage Product
          {product.name && (
            <div style={{ marginTop: "0.35rem", fontSize: "0.9rem" }}>
              <div><strong>Model:</strong> {product.name}</div>
              {product.color && <div><strong>Color:</strong> {product.color}</div>}
              {product.material && <div><strong>Material:</strong> {product.material}</div>}
              {product.year !== 0 && <div><strong>Year:</strong> {product.year}</div>}
              {product.price !== 0 && <div><strong>Price:</strong> ${product.price}</div>}
            </div>
          )}
          {verdict.reason && (
            <div style={{ marginTop: "0.4rem", fontSize: "0.8rem", color: "#a5b4fc" }}>
              {verdict.reason}
            </div>
          )}
        </div>
      );
    }

    // Not authentic or fake product
    return (
      <div style={{ marginTop: "1rem", color: "#f97373", fontWeight: 600 }}>
        ❌ Not Authentic Product
        <div style={{ marginTop: "0.35rem", fontSize: "0.9rem" }}>
          Reason: {verdict.reason}
        </div>
      </div>
    );
  };

  return (
    <div className="app-root">
      <div className="container">
        <header className="header">
          <h1>Vérité Sauvage – Product Verification</h1>
          <p>Scan the QR on your authenticity card and enter the last 6 characters printed on it.</p>
        </header>

        <main>
          <div className="content">
            <div className="row">
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="Enter VS Code (e.g. VS2BOF)"
              />
            </div>

            <div className="row" style={{ marginTop: "0.75rem" }}>
              <button onClick={onVerify} disabled={busy}>
                {busy ? "Verifying…" : "Verify Authenticity"}
              </button>
            </div>

            {error && (
              <div style={{ marginTop: "0.5rem", color: "#facc15", fontSize: "0.8rem" }}>
                {error}
              </div>
            )}

            {renderVerdict()}
          </div>
        </main>

        <footer className="footer">
          © {new Date().getFullYear()} Vérité Sauvage • Blockchain-Backed Authenticity
        </footer>
      </div>
    </div>
  );
}