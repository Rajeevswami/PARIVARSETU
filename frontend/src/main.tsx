import React from "react";
import ReactDOM from "react-dom/client";

import { migrateLegacyStorage } from "./lib/migrateLegacyStorage";
import App from "./App";
import "./styles/globals.css";

migrateLegacyStorage();

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  void navigator.serviceWorker.register("/sw.js");
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
