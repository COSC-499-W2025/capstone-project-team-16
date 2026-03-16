import React, { useState, useEffect, useCallback } from "react";

export default function ScanManager({ isActive, scans, selectedScanId, setSelectedScanId, fetchJson, loadScans, isNoise, setActiveTab, formatTimestamp }) {
  const [scanManagerDetails, setScanManagerDetails] = useState(null);
  const [scanManagerLoading, setScanManagerLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [showMerge, setShowMerge] = useState(false);
  const [mergePrimary, setMergePrimary] = useState("");
  const [mergeSecondaries, setMergeSecondaries] = useState([]);
  const [isMerging, setIsMerging] = useState(false);

  const loadScanDetails = useCallback(async (scanId) => {
    if (!scanId) return;
    setScanManagerLoading(true);
    setScanManagerDetails(null);
    try {
      const data = await fetchJson(`/scans/${scanId}`);
      setScanManagerDetails(data.scan);
    } catch (err) {
      console.error("Failed to load scan details", err);
    } finally {
      setScanManagerLoading(false);
    }
  }, [fetchJson]);

  useEffect(() => {
    if (isActive) {
      if (selectedScanId) {
        loadScanDetails(selectedScanId);
        setShowMerge(false);
        setMergePrimary("");
        setMergeSecondaries([]);
      } else {
        setScanManagerDetails(null);
      }
    }
  }, [isActive, selectedScanId, loadScanDetails]);

  const handleDeleteScan = async () => {
    if (!scanManagerDetails) return;
    const confirm = window.confirm(`Are you sure you want to delete Scan #${scanManagerDetails.summary_id}? This action cannot be undone.`);
    if (!confirm) return;

    setDeleteLoading(true);
    try {
      await fetchJson(`/scans/${scanManagerDetails.summary_id}`, { method: "DELETE" });
      setSelectedScanId("");
      await loadScans();
    } catch (error) {
      alert(`Failed to delete scan: ${error.message}`);
    } finally {
      setDeleteLoading(false);
    }
  };

  const submitMerge = async () => {
    setIsMerging(true);
    try {
      await fetchJson(`/scans/${scanManagerDetails.summary_id}/contributors/merge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          primary_contributor: mergePrimary,
          contributors_to_merge: mergeSecondaries,
        }),
      });
      await loadScanDetails(scanManagerDetails.summary_id);
      setShowMerge(false);
    } catch (e) {
      alert("Failed to merge aliases: " + e.message);
    } finally {
      setIsMerging(false);
    }
  };

  return (
    <section className="panel">
      <h2>Scan Manager</h2>
      <div style={{ display: "flex", gap: "1.5rem", alignItems: "flex-start", flexWrap: "wrap", marginTop: "1rem" }}>
        <div className="result-card" style={{ flex: "1 1 300px" }}>
          <h3 style={{ marginTop: 0 }}>Saved Scans</h3>
          {scans.length === 0 ? (
            <p>No saved scans yet.</p>
          ) : (
            <ul className="simple-list">
              {scans.map((scan) => (
                <li key={scan.summary_id}>
                  <button
                    type="button"
                    className={`inline-link ${selectedScanId === String(scan.summary_id) ? "active" : ""}`}
                    onClick={() => {
                      setSelectedScanId(String(scan.summary_id));
                    }}
                  >
                  Scan {scan.summary_id} - {formatTimestamp(scan.timestamp)} ({scan.analysis_mode})
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div style={{ flex: "2 1 500px" }}>
          {scanManagerLoading ? (
            <div className="result-card"><p>Loading details...</p></div>
          ) : scanManagerDetails ? (
            <div className="result-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
                <div>
                  <h3 style={{ marginTop: 0 }}>Scan Details #{scanManagerDetails.summary_id}</h3>
                  <p style={{ margin: 0 }}>
                    <strong>Mode:</strong> {scanManagerDetails.analysis_mode} <br/>
                  <strong>Date:</strong> {formatTimestamp(scanManagerDetails.timestamp)}
                  </p>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => setActiveTab("resume")}
                  >
                    Build Resume
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setActiveTab("portfolio")}
                  >
                    Build Portfolio
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    style={{ color: "var(--danger)", borderColor: "var(--danger)" }}
                    onClick={handleDeleteScan}
                    disabled={deleteLoading}
                  >
                    {deleteLoading ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </div>
              
              {(() => {
                const profiles = scanManagerDetails.scan_data?.contributor_profiles || {};
                const validContributors = Object.keys(profiles).filter(c => !isNoise(c));
                if (validContributors.length === 0) return null;
                return (
                  <div style={{ marginBottom: "1rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong>Contributors Detected:</strong>
                      {validContributors.length > 1 && (
                        <button 
                          type="button" 
                          className="btn btn-ghost" 
                          style={{ padding: "4px 8px", fontSize: "0.8rem", margin: 0 }} 
                          onClick={() => setShowMerge(!showMerge)}
                        >
                          {showMerge ? "Cancel Merge" : "Merge Aliases"}
                        </button>
                      )}
                    </div>
                    <div className="tag-wrap" style={{ marginTop: "0.5rem" }}>
                      {validContributors.map((contributor) => (
                        <span className="tag" key={contributor} style={{ backgroundColor: "#f3f4f6", borderColor: "#e5e7eb" }}>{contributor}</span>
                      ))}
                    </div>

                    {showMerge && (
                      <div className="result-card" style={{ marginTop: "1rem", background: "#fffaf3", borderColor: "var(--peach-300)" }}>
                        <h4 style={{ marginTop: 0 }}>Merge Contributor Aliases</h4>
                        <div className="field">
                          <span>1. Select Primary Identity (Keep this one)</span>
                          <select value={mergePrimary} onChange={e => { setMergePrimary(e.target.value); setMergeSecondaries([]); }}>
                            <option value="">Select primary...</option>
                            {validContributors.map(c => <option key={c} value={c}>{c}</option>)}
                          </select>
                        </div>
                        {mergePrimary && (
                          <div className="field" style={{ marginTop: "1rem" }}>
                            <span>2. Select Aliases to fold into {mergePrimary}:</span>
                            <div className="inline-options wrap">
                              {validContributors.filter(c => c !== mergePrimary).map(c => (
                                <label key={c}><input type="checkbox" checked={mergeSecondaries.includes(c)} onChange={(e) => { if (e.target.checked) setMergeSecondaries([...mergeSecondaries, c]); else setMergeSecondaries(mergeSecondaries.filter(x => x !== c)); }} /> {c}</label>
                              ))}
                            </div>
                          </div>
                        )}
                        <button type="button" className="btn btn-primary" style={{ marginTop: "1rem", width: "100%" }} onClick={submitMerge} disabled={!mergePrimary || mergeSecondaries.length === 0 || isMerging}>
                          {isMerging ? "Merging..." : "Apply Merge"}
                        </button>
                      </div>
                    )}
                  </div>
                );
              })()}

              <strong>Projects Detected: {(scanManagerDetails.scan_data?.project_summaries || []).length}</strong>
              <ul className="project-list" style={{ marginTop: "0.5rem" }}>
                {(scanManagerDetails.scan_data?.project_summaries || []).map((project, idx) => (
                  <li key={idx}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <strong>{project.project || project.name || `Project ${idx + 1}`}</strong>
                      {project.project_type && <span className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>{project.project_type}</span>}
                    </div>
                    <div className="muted" style={{ marginBottom: "0.5rem" }}>
                      Languages: {[].concat(project.languages || []).join(", ") || "None"} <br />
                      Frameworks: {[].concat(project.frameworks || []).join(", ") || "None"}
                    </div>
                    {(() => {
                      const skills = Array.isArray(project.skills) ? project.skills : (typeof project.skills === "string" ? project.skills.split(",") : []);
                      return skills.length > 0 ? (
                        <div className="tag-wrap">{skills.slice(0, 8).map((skill, i) => (<span className="tag" key={i}>{String(skill).trim()}</span>))}{skills.length > 8 && (<span className="tag">+{skills.length - 8} more</span>)}</div>
                      ) : null;
                    })()}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="result-card"><p>Select a scan to view details.</p></div>
          )}
        </div>
      </div>
    </section>
  );
}