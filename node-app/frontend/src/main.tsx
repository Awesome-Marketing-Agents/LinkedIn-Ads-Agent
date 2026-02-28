import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Auth } from "./pages/Auth";
import { Sync } from "./pages/Sync";
import { Status } from "./pages/Status";
import { VisualReport } from "./pages/VisualReport";
import { Report } from "./pages/Report";
import "./styles/global.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="auth" element={<Auth />} />
          <Route path="sync" element={<Sync />} />
          <Route path="status" element={<Status />} />
          <Route path="visual" element={<VisualReport />} />
          <Route path="report" element={<Report />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
