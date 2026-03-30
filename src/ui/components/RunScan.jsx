import React, { useState, useEffect } from "react";

export default function RunScan({ fetchJson, loadScans, setSelectedScanId, isNoise, setActiveTab }) {
  const [scanAction, setScanAction] = useState("new");
  const [mergeScanId, setMergeScanId] = useState("");
  const [availableScans, setAvailableScans] = useState([]);
  const [scanZipFile, setScanZipFile] = useState(null);
  const [scanMode, setScanMode] = useState("basic");
  const [advancedOptions, setAdvancedOptions] = useState({
    programming_scan: true,
    framework_scan: true,
    skills_gen: true,
    resume_gen: true,
  });
  const [scanRunning, setScanRunning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [scanError, setScanError] = useState("");

  useEffect(() => {
    if (scanAction === "merge") {
      fetchJson("/scans")
        .then((data) => setAvailableScans(data.scans || []))
        .catch(console.error);
    }
  }, [scanAction, fetchJson]);

  const handleAdvancedOptionToggle = (key) => {
    setAdvancedOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleRunScan = async (event) => {
    event.preventDefault();
    setScanError("");
    setScanResult(null);

    if (!scanZipFile) {
      setScanError("Select a .zip file before scanning.");
      return;
    }

    if (scanAction === "merge" && !mergeScanId) {
      setScanError("Please select an existing scan to merge into.");
      return;
    }

    setScanRunning(true);
    try {
      const buffer = await scanZipFile.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const fileHash = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");

      const checkData = await fetchJson(`/scans/check?file_hash=${encodeURIComponent(fileHash)}`);
      let allowDuplicate = "false";

      if (checkData.exists) {
        const proceed = window.confirm("Warning: This project has already been scanned.\n\nDo you want to scan it again?");
        if (!proceed) {
          setScanRunning(false);
          return;
        }
        allowDuplicate = "true";
      }

      const formData = new FormData();
      formData.append("zip", scanZipFile);
      formData.append("consent", "true");
      formData.append("persist", "true");
      formData.append("allow_duplicate", allowDuplicate);

      if (scanAction === "merge") {
        formData.append("incremental", "true");
        formData.append("existing_scan_id", mergeScanId);
        const targetScan = availableScans.find(s => String(s.summary_id) === mergeScanId);
        formData.append("analysis_mode", targetScan?.analysis_mode || "basic");
      } else {
        formData.append("incremental", "false");
        formData.append("analysis_mode", scanMode);
        if (scanMode === "advanced") {
          formData.append("advanced_options", JSON.stringify(advancedOptions));
        }
      }

      const result = await fetchJson("/projects/upload", {
        method: "POST",
        body: formData,
      });
      setScanResult(result);
      await loadScans();

      if (result.summary_id) {
        setSelectedScanId(String(result.summary_id));
      }
    } catch (error) {
      setScanError(error.message);
    } finally {
      setScanRunning(false);
    }
  };

  return (
    <section className="panel">
      <h2>{scanAction === "new" ? "Run New Scan" : "Merge Project into Scan"}</h2>
      <form className="grid-form" onSubmit={handleRunScan}>
        <div className="field">
          <span>Action</span>
          <div className="inline-options">
            <label><input type="radio" value="new" checked={scanAction === "new"} onChange={() => setScanAction("new")} /> Start new scan</label>
            <label><input type="radio" value="merge" checked={scanAction === "merge"} onChange={() => setScanAction("merge")} /> Add to existing scan (Merge)</label>
          </div>
        </div>

        <label className="field">
          <span>Zip file</span>
          <input
            type="file"
            accept=".zip"
            onChange={(event) => setScanZipFile(event.target.files?.[0] || null)}
          />
        </label>

        {scanAction === "merge" && (
          <label className="field">
            <span>Target scan</span>
            <select value={mergeScanId} onChange={(e) => setMergeScanId(e.target.value)}>
              <option value="">Select a scan...</option>
              {availableScans.map((s) => {
                const ts = s.timestamp ? new Date(s.timestamp.replace("Z", "+00:00")).toLocaleString() : "";
                return <option key={s.summary_id} value={s.summary_id}>Scan {s.summary_id} - {ts} ({s.analysis_mode})</option>;
              })}
            </select>
          </label>
        )}

        {scanAction === "new" && (
          <>
            <div className="field">
              <span>Analysis mode</span>
              <div className="inline-options">
                <label><input type="radio" value="basic" checked={scanMode === "basic"} onChange={() => setScanMode("basic")} /> Basic</label>
                <label><input type="radio" value="advanced" checked={scanMode === "advanced"} onChange={() => setScanMode("advanced")} /> Advanced</label>
              </div>
            </div>

            {scanMode === "advanced" && (
          <div className="field">
            <span>Advanced options</span>
            <div className="inline-options wrap">
              {Object.keys(advancedOptions).map((key) => (
                <label key={key}>
                  <input type="checkbox" checked={advancedOptions[key]} onChange={() => handleAdvancedOptionToggle(key)} />{" "}
                  {key.split("_")
                    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(" ")}
                </label>
              ))}
            </div>
          </div>
        )}
          </>
        )}

        <button 
          type="submit" 
          className="btn btn-primary" 
          disabled={scanRunning}
          style={scanRunning ? { display: "inline-flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" } : {}}
        >
          {scanRunning ? (
            <>
              <svg width="1.2em" height="1.2em" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" style={{ opacity: 0.25 }} />
                <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z">
                  <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite" />
                </path>
              </svg>
              Scanning...
            </>
          ) : (
            "Run Scan"
          )}
        </button>
      </form>

      {scanError && <p className="error-text">{scanError}</p>}

      {scanResult && (
        <div className="result-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
            <div>
              <h3 style={{ marginTop: 0 }}>Scan Complete</h3>
              <p style={{ margin: 0 }}>
                <strong>Scan ID:</strong> #{scanResult.summary_id ?? "not persisted"}{" "}
                {scanResult.duplicate && <span className="tag" style={{ backgroundColor: "#fde8e8", color: "#9b1c1c", borderColor: "#fbd5d5" }}>Duplicate</span>}
                {scanResult.merged && <span className="tag" style={{ backgroundColor: "#e1effe", color: "#1e429f", borderColor: "#c3ddfd" }}>Merged</span>}
              </p>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setActiveTab("scan-manager")}
            >
              View in Scan Manager
            </button>
          </div>

          {(() => {
            const profiles = scanResult.results?.contributor_profiles || {};
            const validContributors = Object.keys(profiles).filter(c => !isNoise(c));
            if (validContributors.length === 0) return null;
            return (
              <div style={{ marginBottom: "1rem" }}>
                <strong>Contributors Detected:</strong>
                <div className="tag-wrap" style={{ marginTop: "0.5rem" }}>
                  {validContributors.map((contributor) => (
                    <span className="tag" key={contributor} style={{ backgroundColor: "#f3f4f6", borderColor: "#e5e7eb" }}>{contributor}</span>
                  ))}
                </div>
              </div>
            );
          })()}

          <strong>Projects Detected: {(scanResult.projects || []).length}</strong>
          <ul className="project-list" style={{ marginTop: "0.5rem" }}>
            {(scanResult.projects || []).map((project, idx) => (
              <li key={project.project_id || idx}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <strong>{project.project_name || project.project || project.name || `Project ${idx + 1}`}</strong>
                  {project.project_type && <span className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>{project.project_type}</span>}
                </div>
                <div className="muted" style={{ marginBottom: "0.5rem" }}>
                  Languages: {[].concat(project.languages || []).join(", ") || "None"} <br />
                  Frameworks: {[].concat(project.frameworks || []).join(", ") || "None"}
                </div>
                {(() => {
                  const skills = Array.isArray(project.skills) ? project.skills : (typeof project.skills === "string" ? project.skills.split(",") : []);
                  return skills.length > 0 ? (
                    <div className="tag-wrap">
                      {skills.slice(0, 8).map((skill, i) => (<span className="tag" key={i}>{String(skill).trim()}</span>))}
                      {skills.length > 8 && (<span className="tag">+{skills.length - 8} more</span>)}
                    </div>
                  ) : null;
                })()}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}