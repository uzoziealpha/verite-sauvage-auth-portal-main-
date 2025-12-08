import React from 'react';
import { BACKEND } from './api';

export default function QRDisplay({ dataUrl, productId }: { dataUrl: string | null; productId: string | null }) {
  if (!dataUrl) return <div className="card"><h2>QR Code</h2><div className="qr">No QR yet</div></div>;
  const png = `${BACKEND}/qr/${productId}.png`;
  return (
    <div className="card">
      <h2>QR Code</h2>
      <div className="row" style={{justifyContent:'space-between'}}>
        <a href={png} target="_blank" rel="noreferrer"><button>Open server PNG</button></a>
        <a href={dataUrl} download={`qr-${productId}.png`}><button>Download PNG</button></a>
      </div>
      <div className="qr">
        <img src={dataUrl} alt="QR" style={{ maxWidth: '100%', height: 'auto' }} />
      </div>
    </div>
  );
}