// src/CustomerApp.tsx
import React, { useEffect, useState } from "react";
import { BACKEND, fetchJSON } from "./api";
import { QrReader } from "react-qr-reader";
import jsQR from "jsqr";
import "./CustomerApp.css";

type Verdict = {
  status: string;
  reason: string;
};

type PublicVerifyResponse = {
  success: boolean;
  product: Record<string, any>;
  verdict: Verdict;
};

export default function CustomerApp() {
  const [productId, setProductId] = useState("");
  const [shortCode, setShortCode] = useState("");
  const [result, setResult] = useState<PublicVerifyResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [showScanner, setShowScanner] = useState(false);
  const [scanStatus, setScanStatus] = useState<string | null>(null);
  const [qrPreview, setQrPreview] = useState<string | null>(null);

  // Auto-fill product ID from ?id= in QR link
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const pid = params.get("id");
    const code = params.get("code");

    if (pid) setProductId(pid);
    if (code) setShortCode(code.toUpperCase());
  }, []);

  // -------- QR handling (live camera) --------

  const handleScan = (data: string | null) => {
    if (!data) return;

    console.log("[CustomerApp] QR scan data:", data);
    setScanStatus("QR detected. Parsing…");

    let extracted = data.trim();

    // If the QR encodes a full URL, pull out ?id=
    try {
      const url = new URL(extracted);
      const pid = url.searchParams.get("id");
      if (pid) {
        extracted = pid.trim();
      }
    } catch {
      // Not a URL – raw productId is fine
    }

    setProductId(extracted);
    setScanStatus("Product ID captured from QR.");
  };

  const handleScanError = (err: any) => {
    console.error("[CustomerApp] QR scan error:", err);
    setScanStatus("Unable to access camera or read QR.");
  };

  const closeScanner = () => {
    setShowScanner(false);
    setScanStatus("Scanner closed.");
  };

  // -------- QR from uploaded image --------

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setScanStatus("Reading image…");

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        // Show image preview in QR frame
        setQrPreview(reader.result);
      }

      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          setScanStatus("Unable to read image canvas.");
          return;
        }

        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

        const code = jsQR(imageData.data, imageData.width, imageData.height);
        if (code && code.data) {
          console.log("[CustomerApp] QR from image:", code.data);
          handleScan(code.data);
          setScanStatus("QR code read from image.");
        } else {
          setScanStatus("No QR code detected in the uploaded image.");
        }
      };

      if (typeof reader.result === "string") {
        img.src = reader.result;
      } else {
        setScanStatus("Could not load image.");
      }
    };

    reader.onerror = () => {
      setScanStatus("Failed to read image file.");
    };

    reader.readAsDataURL(file);
  };

  // -------- Verification call --------

  const doVerify = async () => {
    const pid = productId.trim();
    const code = shortCode.trim();

    if (!pid || !code) {
      alert("Please enter both Authentication Code and Final 6 Digits.");
      return;
    }

    setBusy(true);
    setResult(null);
    setErrorMsg(null);

    try {
      console.log("[CustomerApp] POST", `${BACKEND}/customer-verify`);
      const data = (await fetchJSON(`${BACKEND}/customer-verify`, {
        method: "POST",
        body: JSON.stringify({
          product_id: pid,
          short_code: code,
        }),
      })) as PublicVerifyResponse;

      console.log("[CustomerApp] verify result:", data);
      setResult(data);
    } catch (e: any) {
      console.error("[CustomerApp] Error verifying", e);
      setErrorMsg(e?.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  // -------- Verdict block --------

  const renderVerdict = () => {
    if (!result || !result.verdict) return null;
    const { status, reason } = result.verdict;

    if (status === "authentic") {
      return (
        <div className="vs-verdict vs-verdict--ok">
          <div className="vs-verdict-title">
            ✅ Authentic Vérité Sauvage Product
          </div>
          <div className="vs-verdict-sub">
            This item is verified on-chain with CITES compliance.
          </div>
          {reason && <div className="vs-verdict-reason">{reason}</div>}
        </div>
      );
    }

    return (
      <div className="vs-verdict vs-verdict--bad">
        <div className="vs-verdict-title">
          ❌ Unable to verify this product as authentic.
        </div>
        <div className="vs-verdict-sub">
          The authentication code and final digits do not match our records.
        </div>
        {reason && <div className="vs-verdict-reason">{reason}</div>}
      </div>
    );
  };

  // -------- Main render --------

  return (
    <div className="vs-auth-root">
      <div className="vs-auth-overlay" />

      {/* Decorative side images – responsive in CSS */}
      <div className="vs-side-image vs-side-image--left" />
      <div className="vs-side-image vs-side-image--right" />

      <div className="vs-auth-shell">
        {/* Header with modern logo pill */}
        <header className="vs-header">
          <div className="vs-logo-pill">
            <div className="vs-logo-pill-glow" />
            <div className="vs-logo-pill-inner">
              <img
                src="/vs-logo.jpg"
                alt="Vérité Sauvage Logo"
                className="vs-logo-img"
              />
            </div>
          </div>
          <div className="vs-header-sub">
            Authenticity • Transparency • CITES Certified - Blockchain-backed
          </div>
        </header>

        {/* Main card */}
        <main className="vs-main">
          <section className="vs-card">
            <div className="vs-card-glow" />

            <div className="vs-card-inner">
              {/* QR Column */}
              <div className="vs-qr-panel">
                <div className="vs-qr-frame">
                  {showScanner ? (
                    <>
                      <button
                        type="button"
                        className="vs-qr-close"
                        onClick={closeScanner}
                      >
                        ✕
                      </button>
                      <QrReader
                        constraints={{ facingMode: "environment" }}
                        onResult={(result, error) => {
                          if (!!result) {
                            // @ts-ignore different versions
                            const text = result?.text || result?.getText?.();
                            if (text) {
                              handleScan(text);
                            }
                          }
                          if (!!error) {
                            // ignore continuous "no QR" errors
                          }
                        }}
                        onError={handleScanError}
                        containerStyle={{ width: "100%", height: "100%" }}
                        videoContainerStyle={{
                          width: "100%",
                          height: "100%",
                        }}
                      />
                    </>
                  ) : qrPreview ? (
                    <div className="vs-qr-uploaded">
                      <img src={qrPreview} alt="Uploaded QR" />
                      <div className="vs-qr-overlay-border" />
                    </div>
                  ) : (
                    <div className="vs-qr-placeholder">
                      <div className="vs-qr-border" />
                      <div className="vs-qr-square" />
                      <div className="vs-qr-square vs-qr-square--inner" />
                    </div>
                  )}
                </div>

                <div className="vs-qr-actions">
                  <button
                    type="button"
                    className="vs-ghost-btn"
                    onClick={() => {
                      setShowScanner(true);
                      setScanStatus(null);
                      setQrPreview(null);
                    }}
                  >
                    Scan QR with Camera
                  </button>

                  <label className="vs-ghost-btn vs-ghost-btn--file">
                    Upload QR Image
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                    />
                  </label>
                </div>

                {scanStatus && (
                  <div className="vs-scan-status">{scanStatus}</div>
                )}

                <div className="vs-qr-caption">
                  Scan your Vérité Sauvage QR Code
                  <span>Verified instantly on blockchain</span>
                </div>
              </div>

              {/* Form Column */}
              <div className="vs-form-panel">
                <div className="vs-field-block">
                  <div className="vs-field-label">
                    Enter 32-Digit Authentication Code
                  </div>
                  <input
                    className="vs-input vs-input--long"
                    value={productId}
                    onChange={(e) => setProductId(e.target.value)}
                    placeholder="0x294977fc166091f4c6…"
                    style={{ fontFamily: "monospace" }}
                  />
                  <div className="vs-field-hint">
                    The full authentication / product code encoded in your QR.
                  </div>
                </div>

                <div className="vs-field-block vs-field-block--short">
                  <div className="vs-field-label">Enter Final 6 Digits</div>
                  <input
                    className="vs-input vs-input--short"
                    value={shortCode}
                    onChange={(e) => setShortCode(e.target.value.toUpperCase())}
                    placeholder="VS2BOF"
                    maxLength={8}
                  />
                  <div className="vs-field-hint">
                    6-character VS Security Code printed on your card.
                  </div>
                </div>

                <button
                  type="button"
                  className="vs-primary-btn"
                  onClick={doVerify}
                  disabled={busy}
                >
                  {busy ? "Verifying…" : "Verify Authenticity"}
                </button>

                {errorMsg && (
                  <div className="vs-error-msg">Debug: {errorMsg}</div>
                )}
              </div>
            </div>
          </section>

          {/* Verdict + details */}
          {renderVerdict()}

{result?.product && (
  <div className="vs-details">
    <div className="vs-details-title">Product Details</div>
    <ul className="vs-product-list">
      {Object.entries(result.product).map(([key, value]) => {
        const formatKey = (k: string) =>
          k
            .replace(/([A-Z])/g, " $1")
            .replace(/^./, (s) => s.toUpperCase());
        return (
          <li key={key} className="vs-product-item">
            <strong className="vs-product-key">{formatKey(key)}:</strong>{" "}
            <span className="vs-product-value">{value.toString()}</span>
          </li>
        );
      })}
    </ul>
  </div>
)}

        </main>

        <footer className="vs-footer">
          © {new Date().getFullYear()} Vérité Sauvage • Blockchain-Backed
          Authenticity
        </footer>
      </div>
    </div>
  );
}
