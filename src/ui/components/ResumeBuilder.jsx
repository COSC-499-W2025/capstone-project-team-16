import React, { useState, useEffect } from "react";

export default function ResumeBuilder({ isActive, scans, selectedScanId, fetchJson, downloadArtifact, loadProjectsForScan, setActiveTab, formatTimestamp }) {
  const [resumeTitle, setResumeTitle] = useState("Generated Resume");
  const [resumeScanId, setResumeScanId] = useState("");
  const [resumeProjects, setResumeProjects] = useState([]);
  const [resumeSelectedProjectIds, setResumeSelectedProjectIds] = useState([]);
  const [resumeLoadingProjects, setResumeLoadingProjects] = useState(false);
  const [resumeGenerating, setResumeGenerating] = useState(false);
  const [resumeArtifact, setResumeArtifact] = useState(null);
  const [resumeError, setResumeError] = useState("");
  const [resumeExporting, setResumeExporting] = useState(false);

  useEffect(() => {
    if (selectedScanId) {
      setResumeScanId(selectedScanId);
    }
  }, [selectedScanId]);

  useEffect(() => {
    if (!isActive) {
      setResumeArtifact(null);
      setResumeError("");
    }
  }, [isActive]);

  useEffect(() => {
    setResumeArtifact(null);
    setResumeError("");
    setResumeSelectedProjectIds([]);
    setResumeProjects([]);
  }, [resumeScanId]);

  useEffect(() => {
    loadProjectsForScan(resumeScanId, {
      setProjects: setResumeProjects,
      setSelected: setResumeSelectedProjectIds,
      setLoading: setResumeLoadingProjects,
      setError: setResumeError,
      limit: 0,
    });
  }, [resumeScanId, loadProjectsForScan]);

  const toggleResumeProject = (projectId) => {
    setResumeSelectedProjectIds((prev) => {
      const validPrev = prev.filter(id => resumeProjects.some(p => p.project_id === id));
      return validPrev.includes(projectId) ? validPrev.filter((id) => id !== projectId) : [...validPrev, projectId];
    });
  };

  const handleGenerateResume = async () => {
    setResumeError("");
    setResumeArtifact(null);
    if (!resumeScanId) return setResumeError("Select a scan first.");
    if (resumeSelectedProjectIds.length === 0) return setResumeError("Select at least one project.");

    setResumeGenerating(true);
    try {
      const payload = {
        scan_id: Number(resumeScanId),
        title: resumeTitle.trim() || "Generated Resume",
        selected_project_ids: resumeSelectedProjectIds,
        project_order: resumeSelectedProjectIds,
      };
      const data = await fetchJson("/resume/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setResumeArtifact(data.resume);
    } catch (error) {
      setResumeError(error.message);
    } finally {
      setResumeGenerating(false);
    }
  };

  const handleExportResume = async () => {
    if (!resumeArtifact?.resume_id) return;
    setResumeExporting(true);
    setResumeError("");
    try {
      await downloadArtifact(`/resume/${resumeArtifact.resume_id}/export`, "resume.docx");
    } catch (error) {
      setResumeError(error.message);
    } finally {
      setResumeExporting(false);
    }
  };

  return (
    <section className="panel">
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
        <button
          type="button"
          className="btn btn-secondary"
          style={{ padding: "0.25rem 0.5rem" }}
          onClick={() => setActiveTab("scan-manager")}
        >
          &larr; Back
        </button>
        <h2 style={{ margin: 0 }}>Resume Builder</h2>
      </div>

      <div className="grid-form">
        <label className="field">
          <span>Source scan</span>
          <select value={resumeScanId} onChange={(e) => setResumeScanId(e.target.value)}>
            <option value="">Select scan</option>
            {scans.map((scan) => (
              <option key={scan.summary_id} value={scan.summary_id}>Scan {scan.summary_id} - {formatTimestamp(scan.timestamp)} ({scan.analysis_mode})</option>
            ))}
          </select>
        </label>
        <label className="field"><span>Resume title</span><input value={resumeTitle} onChange={(e) => setResumeTitle(e.target.value)} /></label>
        <div className="field">
          <span>Projects for this resume</span>
          {resumeLoadingProjects ? (<p>Loading projects...</p>) : resumeProjects.length === 0 ? (<p>No projects for this scan.</p>) : (
            <ul className="project-list">
              {resumeProjects.map((project) => (
                <li key={project.project_id}>
                  <label>
                    <input type="checkbox" checked={resumeSelectedProjectIds.includes(project.project_id)} onChange={() => toggleResumeProject(project.project_id)} />
                    <span>{project.project_name} <small>score: {project.score ?? "n/a"} | type: {project.project_type ?? "n/a"}</small></span>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </div>
        <button type="button" className="btn btn-primary" onClick={handleGenerateResume} disabled={resumeGenerating}>{resumeGenerating ? "Generating..." : "Generate Resume"}</button>
        {resumeError && <p className="error-text">{resumeError}</p>}
        {resumeArtifact && (
          <div className="result-card">
            <h3>Resume Artifact #{resumeArtifact.resume_id}</h3>
            <p>Selected projects: {(resumeArtifact.data?.selected_project_ids || []).length}</p>
            <ul className="simple-list">{(resumeArtifact.data?.items || []).map((item) => (<li key={item.project_id}><strong>{item.project_name}</strong><p>{item.text}</p></li>))}</ul>
            <button type="button" className="btn btn-secondary" onClick={handleExportResume} disabled={resumeExporting}>{resumeExporting ? "Exporting..." : "Export DOCX"}</button>
          </div>
        )}
      </div>
    </section>
  );
}