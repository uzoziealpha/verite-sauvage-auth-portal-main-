// src/App.tsx
import React from "react";
import AdminApp from "./AdminApp";
import CustomerApp from "./CustomerApp";

export default function App() {
  const path = window.location.pathname;

  if (path.startsWith("/admin")) {
    // http://localhost:5173/admin
    return <AdminApp />;
  }

  // http://localhost:5173/
  return <CustomerApp />;
}