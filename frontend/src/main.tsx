import React from "react";
import ReactDOM from "react-dom/client";

import App from "./app/App";
import { ConnectionProvider } from "./app/context";
import "@fontsource-variable/fraunces";
import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConnectionProvider>
      <App />
    </ConnectionProvider>
  </React.StrictMode>,
);
