// src/VerifyPanel.tsx
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

export default function VerifyPanel() {
  const [pid, setPid] = useState("");
  const [out, setOut] = useState<VerifyResponse | null>(null);
  const [history, setHistory] = useState<VerifyResponse[]>([]);
  const [busy, setBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const go = async () => {
    const trimmed = pid.trim();
    if (!trimmed) return;

    setBusy(true);
    setOut(null);
    setErrorMsg(null);

    const url = `${BACKEND}/verify/${encodeURIComponent(trimmed)}`;
    console.log("[VerifyPanel] Calling backend:", url);

    try {
      const data = (await fetchJSON(url)) as VerifyResponse;

      console.log("[VerifyPanel] Backend response:", data);
      setOut(data);
      setHistory((prev) => [data, ...prev]); // prepend to history
    } catch (e: any) {
      console.error("[VerifyPanel] Error verifying product:", e);
      const msg = e?.message || String(e);
      setErrorMsg(msg);

      const fakeResponse: VerifyResponse = {
        success: false,
        product: {},
        verdict: {
          status: "fake",
          reason: "network_or_server_error — unable to verify",
        },
      };

      setOut(fakeResponse);
      setHistory((prev) => [fakeResponse, ...prev]);
    } finally {
      setBusy(false);
    }
  };

  const renderVerdict = () => {
    if (!out || !out.verdict) return null;

    const { status, reason } = out.verdict;

    if (status === "authentic") {
      return (
        <div
          style={{
            marginTop: "0.75rem",
            color: "#22c55e",
            fontWeight: 600,
            fontSize: "0.95rem",
          }}
        >
          ✅ Authentic — Verified on the blockchain
          {reason && (
            <span
              style={{
                display: "block",
                color: "#a5b4fc",
                fontSize: "0.8rem",
                marginTop: "0.25rem",
              }}
            >
              {reason}
            </span>
          )}
        </div>
      );
    }

    return (
      <div
        style={{
          marginTop: "0.75rem",
          color: "#f97373",
          fontWeight: 600,
          fontSize: "0.95rem",
        }}
      >
        ❌ FAKE — {reason || "cannot verify authenticity"}
      </div>
    );
  };

  return (
    <div className="card" style={{ maxWidth: 600 }}>
      <h2>Verify Vérité Sauvage Product</h2>

      <div
        className="row"
        style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}
      >
        <input
          placeholder="Paste product ID (bytes32)"
          value={pid}
          onChange={(e) => setPid(e.target.value)}
          style={{ flex: 1, padding: "0.35rem 0.5rem" }}
        />
        <button onClick={go} disabled={busy}>
          {busy ? "Checking…" : "Verify"}
        </button>
      </div>

      {errorMsg && (
        <div
          style={{ marginTop: "0.5rem", color: "#facc15", fontSize: "0.8rem" }}
        >
          Debug: {errorMsg}
        </div>
      )}

      {renderVerdict()}

      {out && (
        <div style={{ marginTop: "0.75rem" }}>
          <strong>Raw response:</strong>
          <pre style={{ maxHeight: 200, overflow: "auto" }}>
            {JSON.stringify(out, null, 2)}
          </pre>
        </div>
      )}

      {history.length > 0 && (
        <div style={{ marginTop: "1rem" }}>
          <h3 style={{ fontSize: "0.95rem", marginBottom: "0.25rem" }}>
            Verification History
          </h3>
          <div
            style={{ maxHeight: 200, overflowY: "auto", fontSize: "0.85rem" }}
          >
            {history.map((h, i) => (
              <div
                key={i}
                style={{
                  borderTop: "1px solid #333",
                  paddingTop: "0.35rem",
                  marginTop: "0.35rem",
                }}
              >
                <div>
                  <strong>
                    {h.verdict.status === "authentic" ? "✅ Authentic" : "❌ Fake"}
                  </strong>{" "}
                  — {h.verdict.reason}
                </div>
                {h.product && (h.product.id || h.product.productId) && (
                  <div>PID: {h.product.id || h.product.productId}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}