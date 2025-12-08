import React, { useEffect, useState } from "react";

type Props = {
  onConnected: (account: string) => void;
};

export default function ConnectButton({ onConnected }: Props) {
  const [hasMetaMask, setHasMetaMask] = useState<boolean | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [account, setAccount] = useState<string>("");
  const [lastMessage, setLastMessage] = useState<string>("");
  const [showPopup, setShowPopup] = useState(false);

  // On mount, check if window.ethereum exists
  useEffect(() => {
    const eth = (window as any).ethereum;
    if (eth) {
      console.log("[ConnectButton] window.ethereum detected:", eth);
      setHasMetaMask(true);
      setLastMessage("MetaMask detected.");
    } else {
      console.log("[ConnectButton] window.ethereum NOT found");
      setHasMetaMask(false);
      setLastMessage("MetaMask not detected in this browser.");
    }
  }, []);

  // Helper: subscribe to account changes
  const subscribeToAccountChanges = () => {
    const eth = (window as any).ethereum;
    if (eth && eth.on) {
      eth.removeAllListeners?.("accountsChanged");
      eth.on("accountsChanged", (accs: string[]) => {
        console.log("[ConnectButton] accountsChanged:", accs);
        if (accs && accs.length > 0) {
          const next = accs[0];
          setAccount(next);
          setLastMessage(`Connected: ${next}`);
          onConnected(next);
        } else {
          // No accounts = disconnected
          setAccount("");
          setLastMessage("Disconnected (no accounts in MetaMask).");
          onConnected("");
        }
      });
    }
  };

  const connect = async () => {
    console.log("[ConnectButton] connect() clicked");
    const eth = (window as any).ethereum;

    if (!eth) {
      alert("MetaMask not detected. Use a browser with the MetaMask extension installed.");
      setLastMessage("MetaMask not detected on connect attempt.");
      return;
    }

    setConnecting(true);
    setLastMessage("Requesting accounts from MetaMask...");
    try {
      const accounts: string[] = await eth.request({
        method: "eth_requestAccounts",
      });
      console.log("[ConnectButton] eth_requestAccounts result:", accounts);

      if (!accounts || accounts.length === 0) {
        setLastMessage("No accounts returned from MetaMask.");
        alert("No accounts returned from MetaMask.");
        return;
      }

      const addr = accounts[0];
      setAccount(addr);
      setLastMessage(`Connected: ${addr}`);
      onConnected(addr);
      subscribeToAccountChanges();

      // Show a small popup window confirming connection
      setShowPopup(true);
    } catch (err: any) {
      console.error("[ConnectButton] MetaMask connection error:", err);
      setLastMessage(`Error: ${err?.message || String(err)}`);
      alert(err?.message || "Failed to connect to MetaMask. See console for details.");
    } finally {
      setConnecting(false);
    }
  };

  const disconnect = () => {
    console.log("[ConnectButton] disconnect() clicked");
    // We cannot programmatically "disconnect" MetaMask,
    // but we can clear our app state and let the user disconnect in MetaMask if they want.
    setAccount("");
    setLastMessage("Disconnected from wallet in this app.");
    onConnected("");
    setShowPopup(false);
  };

  const shortAccount =
    account && account.length > 10
      ? `${account.slice(0, 6)}...${account.slice(-4)}`
      : account;

  return (
    <>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-end",
          gap: 4,
        }}
      >
        <div style={{ display: "flex", gap: 8 }}>
          {!account && (
            <button onClick={connect} disabled={connecting}>
              {connecting ? "Connecting…" : "Connect MetaMask"}
            </button>
          )}
          {account && (
            <>
              <button onClick={disconnect}>
                Disconnect
              </button>
              <button onClick={() => setShowPopup(true)}>
                Wallet Info
              </button>
            </>
          )}
        </div>

        <div
          style={{
            fontSize: "0.75rem",
            color: "#a1a1aa",
            maxWidth: 260,
            textAlign: "right",
          }}
        >
          {hasMetaMask === false && "MetaMask not detected in this browser."}
          {hasMetaMask === true && (account ? `Connected: ${shortAccount}` : lastMessage)}
          {hasMetaMask === null && "Checking for MetaMask..."}
        </div>
      </div>

      {/* Simple popup window */}
      {showPopup && account && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: "#111827",
              borderRadius: 8,
              padding: "1.5rem",
              maxWidth: 400,
              width: "90%",
              border: "1px solid rgba(255,255,255,0.1)",
              boxShadow: "0 20px 50px rgba(0,0,0,0.6)",
              color: "#e5e7eb",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: "0.75rem", fontSize: "1.1rem" }}>
              Wallet Connected
            </h2>
            <p style={{ fontSize: "0.9rem", marginBottom: "0.75rem" }}>
              Your MetaMask wallet is now linked to the
              <br />
              <strong>Vérité Sauvage Admin Console</strong>.
            </p>

            <div
              style={{
                fontSize: "0.85rem",
                background: "#020617",
                padding: "0.75rem",
                borderRadius: 6,
                border: "1px solid rgba(255,255,255,0.08)",
                wordBreak: "break-all",
                marginBottom: "1rem",
              }}
            >
              <div style={{ opacity: 0.7, marginBottom: 4 }}>Connected address</div>
              <div>{account}</div>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: 8,
              }}
            >
              <button
                onClick={disconnect}
                style={{
                  background: "transparent",
                  border: "1px solid rgba(248,113,113,0.8)",
                  color: "#fecaca",
                  padding: "0.35rem 0.75rem",
                  borderRadius: 4,
                  fontSize: "0.85rem",
                }}
              >
                Disconnect
              </button>
              <button
                onClick={() => setShowPopup(false)}
                style={{
                  background: "#fbbf24",
                  border: "none",
                  color: "#111827",
                  padding: "0.35rem 0.75rem",
                  borderRadius: 4,
                  fontSize: "0.85rem",
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}