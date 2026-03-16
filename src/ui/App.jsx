import React, { useCallback, useEffect, useState } from "react";
import "./App.css";

import Home from "./components/Home";
import RunScan from "./components/RunScan";
import ScanManager from "./components/ScanManager";
import ResumeBuilder from "./components/ResumeBuilder";
import PortfolioDashboard from "./components/PortfolioDashboard";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

function App() {
  const [activeTab, setActiveTab] = useState("home");
  const [apiStatus, setApiStatus] = useState("checking");
  const [apiMessage, setApiMessage] = useState("");
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [runScanKey, setRunScanKey] = useState(0);

  const [scans, setScans] = useState([]);
  const [scansLoading, setScansLoading] = useState(false);
  const [selectedScanId, setSelectedScanId] = useState("");

  const isNoise = useCallback((author) => {
    if (!author) return true;
    const lower = String(author).toLowerCase();
    const noiseKeywords = ["bot", "dependabot", "snyk", "action", "jenkins"];
    return noiseKeywords.some((kw) => lower.includes(kw));
  }, []);

  const formatTimestamp = useCallback((iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    return isNaN(d.getTime()) ? iso : d.toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" });
  }, []);

  const fetchJson = useCallback(async (path, options = {}) => {
    const response = await fetch(`${API_BASE}${path}`, options);
    const contentType = response.headers.get("content-type") || "";

    let payload = null;
    if (contentType.includes("application/json")) {
      payload = await response.json();
    } else {
      payload = await response.text();
    }

    if (!response.ok) {
      const errorMessage =
        (payload && payload.error) ||
        (typeof payload === "string" && payload) ||
        `Request failed (${response.status})`;
      throw new Error(errorMessage);
    }
    return payload;
  }, []);

  const downloadArtifact = useCallback(async (path, fallbackFileName) => {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) {
      let message = `Download failed (${response.status})`;
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const body = await response.json();
        message = body.error || message;
      }
      throw new Error(message);
    }

    const blob = await response.blob();
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    const disposition = response.headers.get("content-disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/i);
    const fileName = match?.[1] || fallbackFileName;
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }, []);

  const loadScans = useCallback(async () => {
    setScansLoading(true);
    try {
      const data = await fetchJson("/scans");
      const nextScans = data.scans || [];
      setScans(nextScans);
      if (nextScans.length > 0) {
        const firstId = String(nextScans[0].summary_id);
        setSelectedScanId((prev) => prev || firstId);
      } else {
        setSelectedScanId("");
      }
    } catch (error) {
      setApiStatus("offline");
      setApiMessage(error.message);
    } finally {
      setScansLoading(false);
    }
  }, [fetchJson]);

  const loadProjectsForScan = useCallback(
    async (scanId, config) => {
      if (!scanId) {
        config.setError("");
        config.setProjects([]);
        config.setSelected([]);
        return;
      }
      config.setLoading(true);
      try {
        config.setError("");
        const data = await fetchJson(`/projects?scan_id=${encodeURIComponent(scanId)}`);
        const projects = data.projects || [];
        config.setProjects(projects);
        config.setSelected(config.limit ? projects.slice(0, config.limit).map((p) => p.project_id) : projects.map((p) => p.project_id));
      } catch (error) {
        config.setError(error.message);
      } finally {
        config.setLoading(false);
      }
    },
    [fetchJson]
  );

  useEffect(() => {
    let cancelled = false;
    const checkApi = async () => {
      try {
        const data = await fetchJson("/health");
        if (!cancelled) {
          setApiStatus(data.status === "ok" ? "online" : "offline");
          setApiMessage(data.status === "ok" ? "API ready" : "API health check failed");

          if (data.status === "ok") {
            try {
              const privacyData = await fetchJson("/privacy-consent");
              if (!privacyData.privacy?.consent) {
                setShowConsentModal(true);
              }
            } catch (e) {
              console.error("Failed to check privacy consent", e);
            }
          }
        }
      } catch (error) {
        if (!cancelled) {
          setApiStatus("offline");
          setApiMessage(error.message);
        }
      }
    };

    checkApi();
    loadScans();
    return () => {
      cancelled = true;
    };
  }, [fetchJson, loadScans]);

  const handleAcceptConsent = async () => {
    try {
      await fetchJson("/privacy-consent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ consent: true }),
      });
      setShowConsentModal(false);
    } catch (error) {
      alert("Failed to save consent: " + error.message);
    }
  };

  return (
    <div className="app-shell">
      {showConsentModal && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: "rgba(0, 0, 0, 0.7)",
          display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 9999
        }}>
          <div className="panel" style={{ maxWidth: "500px", margin: "1rem" }}>
            <h2>Privacy & Data Consent</h2>
            <p>
              Skill Scope requires your consent to process and analyze your project files.
              By proceeding, you agree to allow the system to scan and store metadata about your code.
            </p>
            <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end", marginTop: "1.5rem" }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => alert("You must provide consent to use the application features.")}
              >
                Decline
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleAcceptConsent}
              >
                I Consent
              </button>
            </div>
          </div>
        </div>
      )}

      <header className="masthead">
        <div className="masthead-title-wrap">
          <p className="eyebrow">Milestone 3 Workbench</p>
          <h1>Skill Scope Frontend</h1>
          <p className="subtitle">Build scans, resumes, and portfolio exports from one dashboard.</p>
        </div>
        <div className="status-card">
          <p className="status-label">API Status</p>
          <p className={`status-pill ${apiStatus}`}>{apiStatus}</p>
          <p className="status-message">{apiMessage || "Checking backend availability..."}</p>
          <button type="button" className="btn btn-ghost" onClick={loadScans} disabled={scansLoading}>
            {scansLoading ? "Refreshing..." : "Refresh Scans"}
          </button>
        </div>
      </header>

      <nav className="tab-row">
        <button
          type="button"
          className={`tab ${activeTab === "home" ? "active" : ""}`}
          onClick={() => setActiveTab("home")}
        >
          Home
        </button>
        <button
          type="button"
          className={`tab ${activeTab === "scan" ? "active" : ""}`}
          onClick={() => setActiveTab("scan")}
        >
          Run a new scan
        </button>
        <button
          type="button"
          className={`tab ${activeTab === "scan-manager" ? "active" : ""}`}
          onClick={() => setActiveTab("scan-manager")}
        >
          Scan Manager
        </button>
      </nav>

      <main className="content-grid">
        <div style={{ display: activeTab === "home" ? "block" : "none" }}>
          <Home setActiveTab={setActiveTab} onStartNewScan={() => {
            setRunScanKey((prev) => prev + 1);
            setActiveTab("scan");
          }} />
        </div>
        <div style={{ display: activeTab === "scan" ? "block" : "none" }}>
          <RunScan
            key={runScanKey}
            fetchJson={fetchJson}
            loadScans={loadScans}
            setSelectedScanId={setSelectedScanId}
            isNoise={isNoise}
            setActiveTab={setActiveTab}
          />
        </div>
        <div style={{ display: activeTab === "scan-manager" ? "block" : "none" }}>
          <ScanManager
            isActive={activeTab === "scan-manager"}
            scans={scans}
            selectedScanId={selectedScanId}
            setSelectedScanId={setSelectedScanId}
            fetchJson={fetchJson}
            loadScans={loadScans}
            isNoise={isNoise}
            setActiveTab={setActiveTab}
            formatTimestamp={formatTimestamp}
          />
        </div>
        <div style={{ display: activeTab === "resume" ? "block" : "none" }}>
          <ResumeBuilder
            isActive={activeTab === "resume"}
            scans={scans}
            selectedScanId={selectedScanId}
            fetchJson={fetchJson}
            downloadArtifact={downloadArtifact}
            loadProjectsForScan={loadProjectsForScan}
            setActiveTab={setActiveTab}
            formatTimestamp={formatTimestamp}
          />
        </div>
        <div style={{ display: activeTab === "portfolio" ? "block" : "none" }}>
          <PortfolioDashboard
            isActive={activeTab === "portfolio"}
            scans={scans}
            selectedScanId={selectedScanId}
            fetchJson={fetchJson}
            downloadArtifact={downloadArtifact}
            loadProjectsForScan={loadProjectsForScan}
            setActiveTab={setActiveTab}
            formatTimestamp={formatTimestamp}
            isNoise={isNoise}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
