import React, { useState, useEffect, useMemo } from "react";

export default function ResumeBuilder({ isActive, scans, selectedScanId, fetchJson, downloadArtifact, loadProjectsForScan, setActiveTab, formatTimestamp, isNoise }) {
  const [resumeTitle, setResumeTitle] = useState("Generated Resume");
  const [resumeScanId, setResumeScanId] = useState("");
  const [resumeProjects, setResumeProjects] = useState([]);
  const [resumeSelectedProjectIds, setResumeSelectedProjectIds] = useState([]);
  const [resumeLoadingProjects, setResumeLoadingProjects] = useState(false);
  const [resumeGenerating, setResumeGenerating] = useState(false);
  const [resumeArtifact, setResumeArtifact] = useState(null);
  const [resumeError, setResumeError] = useState("");
  const [resumeExporting, setResumeExporting] = useState(false);

  const [resumeViewMode, setResumeViewMode] = useState("edit");
  const [contributors, setContributors] = useState([]);
  const [contributorProfiles, setContributorProfiles] = useState({});
  const [selectedContributor, setSelectedContributor] = useState("");
  const [contributorSelections, setContributorSelections] = useState({});
  const [contributorProjectEdits, setContributorProjectEdits] = useState({});
  const [contributorProfileEdits, setContributorProfileEdits] = useState({});
  const [artifactsByContributor, setArtifactsByContributor] = useState({});

  useEffect(() => {
    if (selectedScanId) {
      setResumeScanId(selectedScanId);
    }
  }, [selectedScanId]);

  useEffect(() => {
    if (!isActive) {
      setResumeArtifact(null);
      setResumeError("");
    } else {
      setResumeViewMode("edit");
    }
  }, [isActive]);

  useEffect(() => {
    setContributorSelections({});
    setArtifactsByContributor({});
    setContributorProjectEdits({});
    setContributorProfileEdits({});
    setResumeArtifact(null);
    setResumeError("");
    setResumeSelectedProjectIds([]);
    setResumeProjects([]);
    setResumeViewMode("edit");
  }, [resumeScanId]);

  useEffect(() => {
    setResumeError("");
    setResumeArtifact(artifactsByContributor[selectedContributor] || null);
  }, [selectedContributor]);

  useEffect(() => {
    if (!resumeScanId || !isActive) return;
    loadProjectsForScan(resumeScanId, {
      setProjects: setResumeProjects,
      setSelected: () => {},
      setLoading: setResumeLoadingProjects,
      setError: setResumeError,
      limit: 0,
    });
  }, [resumeScanId, loadProjectsForScan, isActive]);

  useEffect(() => {
    if (!resumeScanId || !isActive) {
      if (!resumeScanId) {
        setContributors([]);
        setSelectedContributor("");
      }
      return;
    }
    let active = true;
    fetchJson(`/scans/${resumeScanId}`).then((data) => {
      if (!active) return;
      const profiles = data.scan?.scan_data?.contributor_profiles || {};
      const valid = Object.keys(profiles).filter(c => {
        if (typeof isNoise === "function") return !isNoise(c);
        const lower = c.toLowerCase();
        return !(lower.includes("[bot]") || lower.includes("dependabot") || lower.includes("github-actions") || lower.includes("github-classroom"));
      });
      setContributorProfiles(profiles);
      setContributors(valid);
      setSelectedContributor(prev => valid.includes(prev) ? prev : "");
    }).catch(console.error);
    return () => { active = false; };
  }, [resumeScanId, fetchJson, isNoise, isActive]);

  const filteredProjects = useMemo(() => {
    if (!selectedContributor || selectedContributor === "general") return resumeProjects;
    const userProjects = contributorProfiles[selectedContributor]?.projects || [];
    const validNames = new Set(userProjects.map(p => p.name));
    return resumeProjects.filter(p => {
      const pcts = p.data?.per_contributor_pct || {};
      return validNames.has(p.project_name) || (pcts[selectedContributor] || 0) > 0;
    });
  }, [resumeProjects, selectedContributor, contributorProfiles]);

  useEffect(() => {
    if (!selectedContributor) return;
    setContributorSelections((curr) => {
      if (curr[selectedContributor]) {
        const validIds = curr[selectedContributor].filter(id => filteredProjects.some(p => p.project_id === id));
        setResumeSelectedProjectIds(validIds);
        return { ...curr, [selectedContributor]: validIds };
      }
      const defaultSelection = filteredProjects.map((p) => p.project_id);
      setResumeSelectedProjectIds(defaultSelection);
      return { ...curr, [selectedContributor]: defaultSelection };
    });
  }, [filteredProjects, selectedContributor]);

  const toggleResumeProject = (projectId) => {
    setResumeError("");
    setResumeSelectedProjectIds((prev) => {
      const validPrev = prev.filter(id => filteredProjects.some(p => p.project_id === id));
      const nextIds = validPrev.includes(projectId) ? validPrev.filter((id) => id !== projectId) : [...validPrev, projectId];
      
      if (selectedContributor) {
        setContributorSelections((curr) => ({ ...curr, [selectedContributor]: nextIds }));
      }
      return nextIds;
    });
  };

  const updateProjectEdit = (projectId, key, value) => {
    setContributorProjectEdits((prev) => {
      const contributorData = prev[selectedContributor] || {};
      const projectData = contributorData[projectId] || {};
      return {
        ...prev,
        [selectedContributor]: {
          ...contributorData,
          [projectId]: {
            ...projectData,
            [key]: value,
          },
        },
      };
    });
  };

  const updateProfileEdit = (key, value) => {
    setContributorProfileEdits((prev) => {
      const contributorData = prev[selectedContributor] || {};
      return {
        ...prev,
        [selectedContributor]: {
          ...contributorData,
          [key]: value,
        },
      };
    });
  };

  const currentProfEdits = contributorProfileEdits[selectedContributor] || {};
  const userProfile = contributorProfiles[selectedContributor] || {};

  let defName = selectedContributor || "";
  if (defName.includes("@")) {
    defName = defName.split("@")[0].replace(/\./g, " ").replace(/_/g, " ");
    defName = defName.replace(/\b\w/g, c => c.toUpperCase());
  }

  let defTitle = "Software Contributor";
  const userSkills = userProfile.skills || [];
  if (userSkills.some(s => s.includes("Development") || s.includes("Programming") || s.includes("Engineering"))) {
    defTitle = "Software Developer";
  }

  let defSummary = `${userProfile.custom_title || defTitle} with a track record of contributions across ${(userProfile.projects || []).length} project(s).`;
  if (userSkills.length > 0) {
    defSummary += ` Proficient in ${userSkills.slice(0, 3).join(", ")}`;
    if (userSkills.length > 3) defSummary += `, along with expertise in ${userSkills.length - 3} other technologies`;
    defSummary += ".";
  }

  const profName = currentProfEdits.custom_name ?? userProfile.custom_name ?? defName;
  const profTitle = currentProfEdits.custom_title ?? userProfile.custom_title ?? defTitle;
  const profSummary = currentProfEdits.custom_summary ?? userProfile.custom_summary ?? defSummary;

  const handleGenerateResume = async () => {
    setResumeError("");
    setResumeArtifact(null);
    if (!resumeScanId) return setResumeError("Select a scan first.");
    if (resumeSelectedProjectIds.length === 0) return setResumeError("Select at least one project.");

    setResumeGenerating(true);
    try {
      const currentProjEdits = contributorProjectEdits[selectedContributor] || {};
      const currentProfEdits = contributorProfileEdits[selectedContributor] || {};
      const contributorUpdates = {};
      const payloadUpdates = {};

      if (currentProfEdits.custom_name !== undefined) payloadUpdates.custom_name = currentProfEdits.custom_name;
      if (currentProfEdits.custom_title !== undefined) payloadUpdates.custom_title = currentProfEdits.custom_title;
      if (currentProfEdits.custom_summary !== undefined) payloadUpdates.custom_summary = currentProfEdits.custom_summary;

      for (const projectId of resumeSelectedProjectIds) {
        if (currentProjEdits[projectId]) {
          const edit = { ...currentProjEdits[projectId] };
          const projectObj = resumeProjects.find(p => p.project_id === projectId);
          const pName = projectObj?.project_name;

          if (pName && (edit.custom_description !== undefined || edit.custom_skills !== undefined)) {
            contributorUpdates[pName] = {};
            if (edit.custom_description !== undefined) {
              contributorUpdates[pName].custom_description = edit.custom_description;
            }
            if (edit.custom_skills !== undefined) {
              let ts = edit.custom_skills;
              if (typeof ts === "string") {
                ts = ts.split(",").map(s => s.trim()).filter(Boolean);
              }
              if (ts.length === 0 && (!edit.custom_skills || edit.custom_skills.trim() === "")) {
                contributorUpdates[pName].reset_custom_skills = true;
              } else {
                contributorUpdates[pName].custom_skills = ts;
              }
            }
          }
        }
      }

      if ((Object.keys(contributorUpdates).length > 0 || Object.keys(payloadUpdates).length > 0) && selectedContributor && selectedContributor !== "general") {
        payloadUpdates.project_updates = contributorUpdates;
        await fetchJson(`/scans/${resumeScanId}/contributors/${encodeURIComponent(selectedContributor)}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payloadUpdates)
        });
        const scanData = await fetchJson(`/scans/${resumeScanId}`);
        setContributorProfiles(scanData.scan?.scan_data?.contributor_profiles || {});
      }

      const payload = {
        scan_id: Number(resumeScanId),
        contributor_id: (selectedContributor && selectedContributor !== "general") ? selectedContributor : undefined,
        title: resumeTitle.trim() || (selectedContributor && selectedContributor !== "general" ? `${profName} Resume` : "Project Portfolio Resume"),
        selected_project_ids: resumeSelectedProjectIds,
        project_order: resumeSelectedProjectIds,
      };
      const data = await fetchJson("/resume/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      let artifact = data.resume;
      setResumeArtifact(artifact);

      if (selectedContributor) {
        setArtifactsByContributor((prev) => ({ ...prev, [selectedContributor]: artifact }));
      }
      setResumeViewMode("view");
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
      const fileName = resumeArtifact.title ? `${resumeArtifact.title}.docx` : "resume.docx";
      await downloadArtifact(`/resume/${resumeArtifact.resume_id}/export`, fileName);
    } catch (error) {
      setResumeError(error.message);
    } finally {
      setResumeExporting(false);
    }
  };

  return (
    <section className="panel">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
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
        
        <div className="inline-options" style={{ background: "#f3f4f6", padding: "4px", borderRadius: "8px" }}>
          <button 
            type="button"
            className={`btn ${resumeViewMode === 'edit' ? 'btn-primary' : 'btn-ghost'}`} 
            onClick={() => setResumeViewMode('edit')}
            style={{ margin: 0, padding: "6px 12px", borderRadius: "6px", fontSize: "0.9rem" }}>
            ✏️ Edit Mode
          </button>
          <button 
            type="button"
            className={`btn ${resumeViewMode === 'view' ? 'btn-primary' : 'btn-ghost'}`} 
            onClick={() => setResumeViewMode('view')}
            style={{ margin: 0, padding: "6px 12px", borderRadius: "6px", fontSize: "0.9rem" }}>
            👁️ View Mode
          </button>
        </div>
      </div>

      {resumeViewMode === "edit" && (
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

          {resumeScanId && (
            <label className="field">
              <span>Contributor</span>
              <select value={selectedContributor} onChange={(e) => {
                setSelectedContributor(e.target.value);
                let cleanName = e.target.value;
                if (cleanName && cleanName !== "general") {
                  const prof = contributorProfiles[cleanName] || {};
                  if (prof.custom_name) {
                    cleanName = prof.custom_name;
                  } else if (cleanName.includes("@")) {
                    cleanName = cleanName.split("@")[0].replace(/\./g, " ").replace(/_/g, " ");
                    cleanName = cleanName.replace(/\b\w/g, c => c.toUpperCase());
                  }
                  setResumeTitle(`${cleanName} Resume`);
                } else {
                  setResumeTitle("Project Portfolio Resume");
                }
              }}>
                <option value="" disabled>Select a contributor...</option>
                <option value="general">No Contributor (General Scan Resume)</option>
                {contributors.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
          )}

          {!resumeScanId ? (
            <div className="result-card" style={{ textAlign: "center", padding: "2rem" }}>
              <p className="muted" style={{ margin: 0 }}>Please select a source scan to begin.</p>
            </div>
          ) : selectedContributor === "" ? (
            <div className="result-card" style={{ textAlign: "center", padding: "2rem" }}>
              <p className="muted" style={{ margin: 0 }}>Please select a contributor to continue building the resume.</p>
            </div>
          ) : (
            <>
          <label className="field"><span>Resume title</span><input value={resumeTitle} onChange={(e) => setResumeTitle(e.target.value)} /></label>

          {selectedContributor && selectedContributor !== "general" && (
            <div className="result-card" style={{ background: "#f9fafb", borderColor: "#e5e7eb" }}>
              <h3 style={{ marginTop: 0, marginBottom: "1rem" }}>Profile Details</h3>
              <div className="grid-form" style={{ gap: "1rem" }}>
                <label className="field"><span>Full Name</span><input value={profName} onChange={(e) => updateProfileEdit("custom_name", e.target.value)} placeholder="e.g. Jane Doe" /></label>
                <label className="field"><span>Professional Title</span><input value={profTitle} onChange={(e) => updateProfileEdit("custom_title", e.target.value)} placeholder="e.g. Full Stack Developer" /></label>
                <label className="field"><span>Professional Summary</span><textarea value={profSummary} onChange={(e) => updateProfileEdit("custom_summary", e.target.value)} rows={3} placeholder="A brief summary of skills and experience" /></label>
              </div>
            </div>
          )}

          <div className="field">
            <span>Projects for this resume</span>
            {resumeLoadingProjects ? (<p>Loading projects...</p>) : filteredProjects.length === 0 ? (<p>No projects found for this contributor.</p>) : (
              <ul className="project-list">
                {filteredProjects.map((project) => (
                  <li key={project.project_id}>
                    <label>
                      <input type="checkbox" checked={resumeSelectedProjectIds.includes(project.project_id)} onChange={() => toggleResumeProject(project.project_id)} />
                      <span>{project.project_name}</span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {resumeSelectedProjectIds.map((projectId) => {
            const project = resumeProjects.find((p) => p.project_id === projectId);
            if (!project) return null;
            const currentProjEdits = contributorProjectEdits[selectedContributor] || {};
            const current = currentProjEdits[projectId] || {};
            const userStats = contributorProfiles[selectedContributor]?.projects?.find(p => p.name === project?.project_name) || {};

            // Generate a default preview description
            let defaultDesc = "";
            if (selectedContributor && selectedContributor !== "general" && Object.keys(userStats).length > 0) {
                const pContext = project.data || {};
                const uCode = userStats.user_code_files || 0;
                const uTest = userStats.user_test_files || 0;
                const uDoc = userStats.user_doc_files || 0;
                const uDesign = userStats.user_design_files || 0;
                const totalWork = uCode + uTest + uDoc + uDesign;
                
                let verb = "Contributed to";
                if (totalWork > 0) {
                    if (uCode >= uTest && uCode >= uDoc && uCode >= uDesign) verb = "Developed key components for";
                    else if (uTest > uCode && uTest > uDoc) verb = "Implemented testing suites for";
                    else if (uDoc > uCode && uDoc > uTest) verb = "Authored technical documentation for";
                    else if (uDesign > uCode) verb = "Designed assets and UI elements for";
                }
                
                const parts = [`${verb} project development`];
                const pct = userStats.pct || 0.0;
                if (pct > 10.0) parts.push(`, contributing ${pct.toFixed(1)}% of the codebase`);
                
                let uFiles = userStats.files_worked || 0;
                if (uFiles === 0 && userStats.files_list) uFiles = userStats.files_list.length;
                if (uFiles > 0) parts.push(`impacting ${uFiles} files`);
                
                const duration = pContext.duration_days || 0;
                if (duration > 14) parts.push(`over a ${duration}-day period`);
                
                const langs = pContext.languages || "Unknown";
                if (langs && langs !== "Unknown") parts.push(`using ${langs}`);
                
                const frameworks = pContext.frameworks || "None";
                if (frameworks && frameworks !== "None" && frameworks !== "NA") parts.push(`utilizing frameworks such as ${frameworks}`);
                
                defaultDesc = parts.join(" ") + ".";
            } else if (!selectedContributor || selectedContributor === "general") {
                const pContext = project.data || {};
                const name = project.project_name || "Unknown";
                const langs = pContext.languages || "Unknown";
                const codeFiles = pContext.code_files || 0;
                const testFiles = pContext.test_files || 0;
                const duration = pContext.duration_days || 0;
                const frameworks = pContext.frameworks || "None";
                const projectType = pContext.project_type || "software";
                
                let main = `Contributed to project '${name}'`;
                if (projectType && projectType.toLowerCase() !== "unknown") main = `Contributed to ${projectType.toLowerCase()} project '${name}'`;
                if (langs && langs.toLowerCase() !== "unknown") main += ` using ${langs}`;
                
                const details = [];
                if (codeFiles) details.push(`${codeFiles} code files`);
                if (testFiles) details.push(`${testFiles} test files`);
                if (duration) details.push(`over ${duration} days`);
                
                const pieces = [main];
                if (details.length > 0) pieces.push("comprising " + details.join(", "));
                if (frameworks && frameworks !== "None" && frameworks !== "NA") pieces.push(`with frameworks such as ${frameworks}`);
                
                defaultDesc = pieces.join("; ") + ".";
            }

            const pcs = project.data?.per_contributor_skills || {};
            const defaultSkillsArr = selectedContributor && selectedContributor !== "general" ? (pcs[selectedContributor] || []) : (project.skills || []);
            const defaultSkillsStr = Array.isArray(defaultSkillsArr) ? defaultSkillsArr.join(", ") : defaultSkillsArr;

            const projDesc = current.custom_description ?? userStats.custom_description ?? defaultDesc ?? "";
            const projSkillsRaw = current.custom_skills ?? userStats.custom_skills ?? defaultSkillsStr ?? "";
            const projSkills = Array.isArray(projSkillsRaw) ? projSkillsRaw.join(", ") : projSkillsRaw;

            return (
              <div className="result-card" key={projectId}>
                <h3>{project?.project_name || projectId}</h3>
                <label className="field"><span>Project Description</span><textarea value={projDesc} onChange={(e) => updateProjectEdit(projectId, "custom_description", e.target.value)} rows={3} placeholder={defaultDesc} /></label>
                <label className="field"><span>Highlighted Skills (comma separated)</span><input value={projSkills} onChange={(e) => updateProjectEdit(projectId, "custom_skills", e.target.value)} placeholder="React, Python, Docker" /></label>
              </div>
            );
          })}

          <button type="button" className="btn btn-primary" onClick={handleGenerateResume} disabled={resumeGenerating}>{resumeGenerating ? "Saving & Generating..." : "Save & Generate"}</button>
          {resumeError && <p className="error-text">{resumeError}</p>}
            </>
          )}
        </div>
      )}

      {resumeViewMode === "view" && (
        <div className="portfolio-showroom">
          {resumeArtifact ? (
            <>
              <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
                <h1 style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>{resumeArtifact.data?.user_name || "Project Portfolio Resume"}</h1>
                {resumeArtifact.data?.user_title && <h2 style={{ color: "var(--ink-700)", fontWeight: "500", marginTop: 0 }}>{resumeArtifact.data.user_title}</h2>}
                {resumeArtifact.data?.user_summary && <p style={{ maxWidth: "800px", margin: "1rem auto", lineHeight: "1.6" }}>{resumeArtifact.data.user_summary}</p>}
              </div>

              {resumeArtifact.data?.skills?.length > 0 && (
                <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: "8px", padding: "2rem", boxShadow: "0 4px 6px rgba(0,0,0,0.05)", marginBottom: "2rem" }}>
                  <h3 style={{ borderBottom: "2px solid #e5e7eb", paddingBottom: "0.5rem", marginBottom: "1.5rem" }}>Technical Skills</h3>
                  <p style={{ margin: 0, lineHeight: "1.6" }}><strong>Languages & Technologies:</strong> {resumeArtifact.data.skills.join(", ")}</p>
                </div>
              )}

              <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: "8px", padding: "2rem", boxShadow: "0 4px 6px rgba(0,0,0,0.05)" }}>
                <h3 style={{ borderBottom: "2px solid #e5e7eb", paddingBottom: "0.5rem", marginBottom: "1.5rem" }}>{resumeArtifact.data?.user_summary ? "Project Experience" : "Top Projects"}</h3>
                
                <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
                  {(resumeArtifact.data?.items || []).map((item) => (
                    <div key={item.project_id}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.5rem" }}>
                        <h4 style={{ margin: 0, fontSize: "1.25rem" }}>{item.project_name}</h4>
                        {item.date_str && <span className="muted" style={{ fontWeight: "500" }}>{item.date_str.replace(/[()]/g, '')}</span>}
                      </div>
                      
                      {item.role && <p style={{ fontStyle: "italic", margin: "0 0 0.5rem 0", color: "var(--ink-700)" }}>{item.role}</p>}
                      
                      <p style={{ margin: "0 0 0.5rem 0", lineHeight: "1.6" }}>{item.text}</p>
                      
                      {item.skills?.length > 0 && (
                        <p className="muted" style={{ fontSize: "0.9rem", margin: 0 }}>
                          <strong>Technologies:</strong> {item.skills.join(", ")}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {resumeArtifact.data?.projects_chronological?.length > 0 && (
                <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: "8px", padding: "2rem", boxShadow: "0 4px 6px rgba(0,0,0,0.05)", marginTop: "2rem" }}>
                  <h3 style={{ borderBottom: "2px solid #e5e7eb", paddingBottom: "0.5rem", marginBottom: "1.5rem" }}>Project Timeline</h3>
                  <ul className="simple-list">
                    {resumeArtifact.data.projects_chronological.map((p, i) => (
                      <li key={i}><strong>{p.name}</strong> &ndash; {p.first_used} &rarr; {p.last_used}</li>
                    ))}
                  </ul>
                </div>
              )}

              {resumeArtifact.data?.skills_chronological?.length > 0 && (
                <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: "8px", padding: "2rem", boxShadow: "0 4px 6px rgba(0,0,0,0.05)", marginTop: "2rem" }}>
                  <h3 style={{ borderBottom: "2px solid #e5e7eb", paddingBottom: "0.5rem", marginBottom: "1.5rem" }}>Skills Used Over Time</h3>
                  <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
                        <th style={{ padding: "0.5rem" }}>Skill</th>
                        <th style={{ padding: "0.5rem" }}>First Used</th>
                        <th style={{ padding: "0.5rem" }}>Last Used</th>
                      </tr>
                    </thead>
                    <tbody>
                      {resumeArtifact.data.skills_chronological.map((s, i) => (
                        <tr key={i} style={{ borderBottom: "1px solid #e5e7eb" }}>
                          <td style={{ padding: "0.5rem" }}>{s.skill}</td>
                          <td style={{ padding: "0.5rem" }}>{s.first_used}</td>
                          <td style={{ padding: "0.5rem" }}>{s.last_used}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div style={{ textAlign: "center", marginTop: "3rem" }}>
                <button type="button" className="btn btn-secondary" style={{ padding: "1rem 2rem", fontSize: "1.1rem" }} onClick={handleExportResume} disabled={resumeExporting}>
                  {resumeExporting ? "Exporting..." : "Export DOCX"}
                </button>
              </div>
            </>
          ) : (
            <div className="result-card" style={{ textAlign: "center", padding: "4rem 2rem" }}>
              <h3 style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>No Resume Generated</h3>
              <p className="muted" style={{ marginBottom: "2rem", fontSize: "1.1rem" }}>Go to Edit Mode, select your projects, edit your profile, and generate the resume to see the preview here.</p>
              <button className="btn btn-primary" onClick={() => setResumeViewMode('edit')}>Switch to Edit Mode</button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}