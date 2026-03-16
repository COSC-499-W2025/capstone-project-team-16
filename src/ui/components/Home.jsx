import React from "react";

export default function Home({ setActiveTab, onStartNewScan }) {
  return (
    <section className="panel">
      <div style={{ textAlign: "center", padding: "3rem 1rem" }}>
        <h2>Welcome to Skill Scope!</h2>
        <p style={{ maxWidth: "600px", margin: "1rem auto", lineHeight: "1.6" }}>
          Skill Scope scans a project folder to summarize languages, frameworks, timelines, and contributions, then saves the results for later review.
        </p>
        <div style={{ display: "flex", gap: "1rem", justifyContent: "center", marginTop: "2rem" }}>
          <button
            type="button"
            className="btn btn-primary"
            style={{ padding: "0.75rem 1.5rem", fontSize: "1.1rem" }}
            onClick={onStartNewScan || (() => setActiveTab("scan"))}
          >
            Run a New Scan
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: "0.75rem 1.5rem", fontSize: "1.1rem" }}
            onClick={() => setActiveTab("scan-manager")}
          >
            Scan Manager
          </button>
        </div>
      </div>
    </section>
  );
}