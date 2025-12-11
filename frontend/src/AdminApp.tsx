// src/AdminApp.tsx
import React, { useState } from "react";
import ConnectButton from "./ConnectButton";
import RegisterPanel from "./RegisterPanel";
import QRDisplay from "./QRDisplay";
import VerifyPanel from "./VerifyPanel";

export default function AdminApp() {
  const [account, setAccount] = useState("");
  const [qr, setQr] = useState<{ dataUrl: string | null; id: string | null }>({
    dataUrl: null,
    id: null,
  });

  return (
    <div className="app-root">
      <div className="container">
        <header className="header-card card">
          <div className="brand">
            <div className="brand-logo-wrap">
              <img
                src="/vs-logo.jpg"
                alt="Vérité Sauvage logo"
                className="brand-logo"
              />
            </div>
            <div className="brand-text">
              <h1 className="brand-title">Vérité Sauvage Authenticity Portal</h1>
              <div className="brand-subtitle">
                Register bags, generate QR codes, and verify each piece against
                the on-chain record.
              </div>
            </div>
          </div>

          <div className="header-row">
            <ConnectButton onConnected={setAccount} />
            <div className="wallet-status">
              {account ? `Connected: ${account}` : "Wallet not connected"}
            </div>
          </div>
        </header>

        <main className="grid">
          <section className="col">
            <RegisterPanel
              account={account}
              onQr={(dataUrl, id) => setQr({ dataUrl, id })}
            />
            <VerifyPanel />
          </section>

          <aside className="qr-column">
            <QRDisplay dataUrl={qr.dataUrl} productId={qr.id} />
          </aside>
        </main>

        <footer className="footer">
          © {new Date().getFullYear()} Vérité Sauvage • Leather Goods •
          Blockchain Authenticity
        </footer>
      </div>
    </div>
  );
}