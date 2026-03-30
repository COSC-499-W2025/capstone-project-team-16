import React, { useState, useEffect, useMemo } from "react";

export default function PortfolioDashboard({ isActive, scans, selectedScanId, fetchJson, downloadArtifact, loadProjectsForScan, setActiveTab, formatTimestamp, isNoise }) {
  const [portfolioTitle, setPortfolioTitle] = useState("Generated Portfolio");
  const [portfolioScanId, setPortfolioScanId] = useState("");
  const [portfolioProjects, setPortfolioProjects] = useState([]);
  const [portfolioSelectedProjectIds, setPortfolioSelectedProjectIds] = useState([]);
  const [portfolioLoadingProjects, setPortfolioLoadingProjects] = useState(false);
  const [portfolioGenerating, setPortfolioGenerating] = useState(false);
  const [portfolioArtifact, setPortfolioArtifact] = useState(null);
  const [portfolioError, setPortfolioError] = useState("");
  const [portfolioExporting, setPortfolioExporting] = useState(false);
  const [portfolioViewMode, setPortfolioViewMode] = useState("edit");
  const [contributors, setContributors] = useState([]);
  const [contributorProfiles, setContributorProfiles] = useState({});
  const [selectedContributor, setSelectedContributor] = useState("");
  const [activeViewProjectId, setActiveViewProjectId] = useState(null);
  const [contributorSelections, setContributorSelections] = useState({});
  const [contributorProjectEdits, setContributorProjectEdits] = useState({});
  const [artifactsByContributor, setArtifactsByContributor] = useState({});
  const [uploadingThumbnails, setUploadingThumbnails] = useState({});
  const [viewSearchQuery, setViewSearchQuery] = useState("");
  const [viewActiveFilter, setViewActiveFilter] = useState("");
  const [showSkillsProgression, setShowSkillsProgression] = useState(false);

  useEffect(() => {
    if (selectedScanId) {
      setPortfolioScanId(selectedScanId);
    }
  }, [selectedScanId]);

  useEffect(() => {
    if (!isActive) {
      setPortfolioArtifact(null);
      setPortfolioError("");
      setActiveViewProjectId(null);
    } else {
      setPortfolioViewMode("edit");
    }
  }, [isActive]);

  useEffect(() => {
    setContributorSelections({});
    setArtifactsByContributor({});
    setContributorProjectEdits({});
    setPortfolioArtifact(null);
    setPortfolioError("");
    setActiveViewProjectId(null);
    setPortfolioSelectedProjectIds([]);
    setPortfolioProjects([]);
    setPortfolioViewMode("edit");
    setUploadingThumbnails({});
    setViewSearchQuery("");
    setViewActiveFilter("");
    setShowSkillsProgression(false);
  }, [portfolioScanId]);

  useEffect(() => {
    setPortfolioError("");
    setActiveViewProjectId(null);
    setPortfolioArtifact(artifactsByContributor[selectedContributor] || null);
  }, [selectedContributor]); // Intentionally omitting artifactsByContributor so it only runs on switch

  useEffect(() => {
    setViewSearchQuery("");
    setViewActiveFilter("");
    setShowSkillsProgression(false);
  }, [portfolioViewMode, selectedContributor]);

  useEffect(() => {
    if (!portfolioScanId || !isActive) return;
    loadProjectsForScan(portfolioScanId, {
      setProjects: setPortfolioProjects,
      setSelected: () => {},
      setLoading: setPortfolioLoadingProjects,
      setError: setPortfolioError,
      limit: 0,
    });
  }, [portfolioScanId, loadProjectsForScan, isActive]);
  
  useEffect(() => {
    if (!portfolioScanId || !isActive) {
      if (!portfolioScanId) {
        setContributors([]);
        setSelectedContributor("");
      }
      return;
    }
    let active = true;
    fetchJson(`/scans/${portfolioScanId}`).then((data) => {
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
  }, [portfolioScanId, fetchJson, isNoise, isActive]);

  const filteredProjects = useMemo(() => {
    if (!selectedContributor || selectedContributor === "general") return portfolioProjects;
    const userProjects = contributorProfiles[selectedContributor]?.projects || [];
    const validNames = new Set(userProjects.map(p => p.name));
    return portfolioProjects.filter(p => {
      const pcts = p.data?.per_contributor_pct || {};
      return validNames.has(p.project_name) || (pcts[selectedContributor] || 0) > 0;
    });
  }, [portfolioProjects, selectedContributor, contributorProfiles]);

  useEffect(() => {
    if (!selectedContributor) return;
    setContributorSelections((curr) => {
      if (curr[selectedContributor]) {
        const validIds = curr[selectedContributor].filter(id => filteredProjects.some(p => p.project_id === id));
        setPortfolioSelectedProjectIds(validIds);
        return { ...curr, [selectedContributor]: validIds };
      }
      const defaultSelection = filteredProjects.map((p) => p.project_id);
      setPortfolioSelectedProjectIds(defaultSelection);
      return { ...curr, [selectedContributor]: defaultSelection };
    });
  }, [filteredProjects, selectedContributor]);

  const togglePortfolioProject = (projectId) => {
    setPortfolioError("");
    setPortfolioSelectedProjectIds((prev) => {
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

  const handleUploadThumbnail = async (projectId, file) => {
    setUploadingThumbnails(prev => ({ ...prev, [projectId]: true }));
    setPortfolioError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const API_BASE = "http://127.0.0.1:5000";
      const res = await fetch(`${API_BASE}/projects/${encodeURIComponent(projectId)}/thumbnail`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) throw new Error("Thumbnail upload failed");
      const data = await res.json();
      updateProjectEdit(projectId, "thumbnail", data.thumbnail);
    } catch (err) {
      console.error(err);
      setPortfolioError(err.message);
    } finally {
      setUploadingThumbnails(prev => ({ ...prev, [projectId]: false }));
    }
  };

  const handleGeneratePortfolio = async () => {
    setPortfolioError("");
    setPortfolioArtifact(null);
    if (!portfolioScanId) return setPortfolioError("Select a scan first.");
    if (portfolioSelectedProjectIds.length === 0) return setPortfolioError("Select at least one project for the showcase.");

    setPortfolioGenerating(true);
    try {
      const currentEdits = contributorProjectEdits[selectedContributor] || {};
      const contributorUpdates = {};

      for (const projectId of portfolioSelectedProjectIds) {
        if (currentEdits[projectId]) {
          const edit = { ...currentEdits[projectId] };
          const projectObj = portfolioProjects.find(p => p.project_id === projectId);
          const pName = projectObj?.project_name;

          if (pName && (edit.custom_portfolio_project_description !== undefined || edit.custom_portfolio_description !== undefined || edit.custom_portfolio_tech_stack !== undefined)) {
            contributorUpdates[pName] = {};
            if (edit.custom_portfolio_project_description !== undefined) {
              contributorUpdates[pName].custom_portfolio_project_description = edit.custom_portfolio_project_description;
            }
            if (edit.custom_portfolio_description !== undefined) {
              contributorUpdates[pName].custom_portfolio_description = edit.custom_portfolio_description;
            }
            if (edit.custom_portfolio_tech_stack !== undefined) {
              let ts = edit.custom_portfolio_tech_stack;
              if (typeof ts === "string") {
                ts = ts.split(",").map(s => s.trim()).filter(Boolean);
              }
              if (ts.length === 0 && (!edit.custom_portfolio_tech_stack || edit.custom_portfolio_tech_stack.trim() === "")) {
                contributorUpdates[pName].reset_custom_portfolio_tech_stack = true;
              } else {
                contributorUpdates[pName].custom_portfolio_tech_stack = ts;
              }
            }
          }
        }
      }

      if (Object.keys(contributorUpdates).length > 0 && selectedContributor && selectedContributor !== "general") {
        await fetchJson(`/scans/${portfolioScanId}/contributors/${encodeURIComponent(selectedContributor)}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ project_updates: contributorUpdates })
        });
        // Refresh profiles to keep UI pre-fills perfectly in sync
        const scanData = await fetchJson(`/scans/${portfolioScanId}`);
        setContributorProfiles(scanData.scan?.scan_data?.contributor_profiles || {});
      }

      const generatePayload = {
        scan_id: Number(portfolioScanId),
        contributor_id: (selectedContributor && selectedContributor !== "general") ? selectedContributor : undefined,
        title: portfolioTitle.trim() || (function() {
          if (selectedContributor && selectedContributor !== "general") {
            let cleanName = selectedContributor;
            const prof = contributorProfiles[cleanName] || {};
            if (prof.custom_name) cleanName = prof.custom_name;
            else if (cleanName.includes("@")) {
              cleanName = cleanName.split("@")[0].replace(/\./g, " ").replace(/_/g, " ");
              cleanName = cleanName.replace(/\b\w/g, c => c.toUpperCase());
            }
            return `${cleanName} Portfolio`;
          }
          return "Project Portfolio";
        })(),
        selected_project_ids: portfolioSelectedProjectIds,
        project_order: portfolioSelectedProjectIds,
      };
      const data = await fetchJson("/portfolio/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(generatePayload),
      });

      let artifact = data.portfolio;

      setPortfolioArtifact(artifact);

      if (selectedContributor) {
        setArtifactsByContributor((prev) => ({ ...prev, [selectedContributor]: artifact }));
      }
      setPortfolioViewMode("view");
    } catch (error) {
      setPortfolioError(error.message);
    } finally {
      setPortfolioGenerating(false);
    }
  };

  const handleExportPortfolio = async () => {
    if (!portfolioArtifact?.portfolio_id) return;
    setPortfolioExporting(true);
    setPortfolioError("");
    try {
      const fileName = portfolioArtifact.title ? `${portfolioArtifact.title}.md` : "portfolio.md";
      await downloadArtifact(`/portfolio/${portfolioArtifact.portfolio_id}/export`, fileName);
    } catch (error) {
      setPortfolioError(error.message);
    } finally {
      setPortfolioExporting(false);
    }
  };

  const visiblePortfolioItems = portfolioArtifact?.data?.items || [];
  
  // Filter items for Public View Mode based on search and skill filters
  const filteredViewItems = useMemo(() => {
    let items = visiblePortfolioItems;
    if (viewSearchQuery) {
      const q = viewSearchQuery.toLowerCase();
      items = items.filter(i => 
        i.project_name?.toLowerCase().includes(q) || 
        i.project_description?.toLowerCase().includes(q) || 
        i.role_description?.toLowerCase().includes(q)
      );
    }
    if (viewActiveFilter) {
      const f = viewActiveFilter.toLowerCase();
      items = items.filter(i => {
        const stack = i.tech_stack || [];
        const arr = Array.isArray(stack) ? stack : [stack];
        return arr.some(s => String(s).toLowerCase() === f);
      });
    }
    return items;
  }, [visiblePortfolioItems, viewSearchQuery, viewActiveFilter]);

  const activeViewItem = filteredViewItems.find(i => i.project_id === activeViewProjectId) || filteredViewItems[0];

  const renderTimeline = () => {
    const times = filteredViewItems.map((item) => {
      const hasGlobalDates = item.first_modified && item.last_modified;
      const dates = Object.keys(item.daily_commits || {}).sort();
      
      if (!hasGlobalDates && dates.length === 0) return null;

      // Normalize all dates to midnight UTC safely, handling both 'T' and space separators
      const getDayTime = (dStr) => {
        if (!dStr) return 0;
        const datePart = String(dStr).split('T')[0].split(' ')[0];
        const parsed = new Date(`${datePart}T00:00:00Z`).getTime();
        return isNaN(parsed) ? 0 : parsed;
      };

      let globalStart = hasGlobalDates ? getDayTime(item.first_modified) : getDayTime(dates[0]);
      let globalEnd = hasGlobalDates ? getDayTime(item.last_modified) : getDayTime(dates[dates.length - 1]);

      const userStart = dates.length > 0 ? getDayTime(dates[0]) : globalStart;
      const userEnd = dates.length > 0 ? getDayTime(dates[dates.length - 1]) : globalEnd;

      // Ensure global bounds fully encapsulate the user bounds
      globalStart = Math.min(globalStart, userStart);
      globalEnd = Math.max(globalEnd, userEnd);

      return { 
        id: item.project_id, 
        name: item.project_name, 
        globalStart, 
        globalEnd, 
        userStart, 
        userEnd 
      };
    }).filter(Boolean);

    if (times.length === 0) {
      return <p className="muted" style={{ textAlign: "center", margin: 0 }}>No date data available for selected projects.</p>;
    }

    const minT = Math.min(...times.map((t) => Math.min(t.globalStart, t.userStart)));
    const maxT = Math.max(...times.map((t) => Math.max(t.globalEnd, t.userEnd)));
    const range = maxT - minT || 86400000; // default 1 day if instant

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "18px", width: "100%", marginTop: "10px" }}>
        {times.map((t) => {
          let globalLeft = ((t.globalStart - minT) / range) * 100;
          let globalWidth = Math.max(((t.globalEnd - t.globalStart) / range) * 100, 1);
          if (globalLeft + globalWidth > 100) {
            globalLeft = Math.min(globalLeft, 99);
            globalWidth = 100 - globalLeft;
          }
          
          let userLeft = ((t.userStart - minT) / range) * 100;
          let userWidth = Math.max(((t.userEnd - t.userStart) / range) * 100, 1);
          if (userLeft + userWidth > 100) {
            userLeft = Math.min(userLeft, 99);
            userWidth = 100 - userLeft;
          }

          const isActive = t.id === activeViewItem?.project_id;
          
          return (
            <div key={t.id} style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "0.85rem", cursor: "pointer" }} onClick={() => setActiveViewProjectId(t.id)}>
              <div style={{ width: "120px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", opacity: isActive ? 1 : 0.6, fontWeight: isActive ? "700" : "500", color: "var(--ink-900)" }} title={t.name}>
                {t.name}
              </div>
              <div style={{ flex: 1, height: "18px", background: "transparent", borderBottom: "1px dashed rgba(70, 98, 130, 0.25)", position: "relative" }}>
                {/* Global Duration Bar (Faded Background) */}
                <div style={{ position: "absolute", left: `${globalLeft}%`, width: `${globalWidth}%`, height: "100%", background: isActive ? "rgba(240, 122, 74, 0.2)" : "rgba(36, 179, 154, 0.2)", borderRadius: "8px", transition: "all 0.3s ease" }} title={`Project Lifetime: ${new Date(t.globalStart).toLocaleDateString()} to ${new Date(t.globalEnd).toLocaleDateString()}`} />
                
                {/* Contributor Duration Bar (Dark Foreground) */}
                <div style={{ position: "absolute", left: `${userLeft}%`, width: `${userWidth}%`, height: "100%", background: isActive ? "var(--peach-500)" : "var(--mint-500)", borderRadius: "8px", transition: "all 0.3s ease", boxShadow: isActive ? "0 2px 8px rgba(240, 122, 74, 0.4)" : "none" }} title={`Contributor Active: ${new Date(t.userStart).toLocaleDateString()} to ${new Date(t.userEnd).toLocaleDateString()}`} />
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderHeatmap = () => {
    if (!activeViewItem) return <p className="muted" style={{ textAlign: "center", margin: 0 }}>Select a project</p>;
    const totalCommits = activeViewItem.commits || 0;
    const dailyCommits = activeViewItem.daily_commits || {};
    const commitDates = Object.keys(dailyCommits).sort();
    
    const cells = [];

    if (commitDates.length > 0) {
      // REAL DATA MODE: 84 days leading up to their last actual commit
      const lastCommitDate = new Date(commitDates[commitDates.length - 1]);
      const maxDaily = Math.max(...Object.values(dailyCommits), 1);
      
      for (let i = 83; i >= 0; i--) {
        const d = new Date(lastCommitDate);
        d.setDate(d.getDate() - i);
        const dateStr = d.toISOString().split('T')[0];
        const count = dailyCommits[dateStr] || 0;
        
        let bg = "#ebedf0";
        if (count > 0) {
          const intensity = count / maxDaily;
          if (intensity > 0.75) bg = "#116345"; 
          else if (intensity > 0.5) bg = "#12826e"; 
          else if (intensity > 0.25) bg = "var(--mint-500)"; 
          else bg = "var(--mint-200)";
        }
        cells.push(<div key={i} title={`${count} commits on ${dateStr}`} style={{ aspectRatio: "1", backgroundColor: bg, borderRadius: "2px" }} />);
      }
    } else {
      // Empty grid if no daily data exists
      for (let i = 0; i < 84; i++) {
        cells.push(<div key={i} style={{ aspectRatio: "1", backgroundColor: "#ebedf0", borderRadius: "2px" }} />);
      }
    }
    
    return (
      <div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gap: "4px" }}>
          {cells}
        </div>
      </div>
    );
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
          <h2 style={{ margin: 0 }}>Portfolio Dashboard</h2>
        </div>
        
        <div className="inline-options" style={{ background: "#f3f4f6", padding: "4px", borderRadius: "8px" }}>
          <button 
            type="button"
            className={`btn ${portfolioViewMode === 'edit' ? 'btn-primary' : 'btn-ghost'}`} 
            onClick={() => setPortfolioViewMode('edit')}
            style={{ margin: 0, padding: "6px 12px", borderRadius: "6px", fontSize: "0.9rem" }}>
            ✏️ Edit Mode
          </button>
          <button 
            type="button"
            className={`btn ${portfolioViewMode === 'view' ? 'btn-primary' : 'btn-ghost'}`} 
            onClick={() => setPortfolioViewMode('view')}
            style={{ margin: 0, padding: "6px 12px", borderRadius: "6px", fontSize: "0.9rem" }}>
            👁️ View Mode
          </button>
        </div>
      </div>

      {portfolioViewMode === "edit" && (
        <div className="grid-form">
          {contributors.length > 0 && (
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
                  setPortfolioTitle(`${cleanName} Portfolio`);
                } else {
                  setPortfolioTitle("Project Portfolio");
                }
              }}>
                <option value="" disabled>Select a contributor...</option>
                <option value="general">No Contributor (General Scan Portfolio)</option>
                {contributors.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
          )}

          {selectedContributor === "" ? (
            <div className="result-card" style={{ textAlign: "center", padding: "2rem" }}>
              <p className="muted" style={{ margin: 0 }}>Please select a contributor to continue building the portfolio.</p>
            </div>
          ) : (
            <>
          <label className="field"><span>Portfolio title</span><input value={portfolioTitle} onChange={(e) => setPortfolioTitle(e.target.value)} /></label>
          <div className="field">
            <span>Showcase projects</span>
            {portfolioLoadingProjects ? (<p>Loading projects...</p>) : filteredProjects.length === 0 ? (<p>No projects found for this contributor.</p>) : (
              <ul className="project-list">
                {filteredProjects.map((project) => (
                  <li key={project.project_id}>
                    <label>
                      <input type="checkbox" checked={portfolioSelectedProjectIds.includes(project.project_id)} onChange={() => togglePortfolioProject(project.project_id)} />
                      <span>{project.project_name} <small>score: {project.score ?? "n/a"}</small></span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {portfolioSelectedProjectIds.map((projectId) => {
            const project = portfolioProjects.find((p) => p.project_id === projectId);
            if (!project) return null;
            const currentEdits = contributorProjectEdits[selectedContributor] || {};
            const current = currentEdits[projectId] || {};
            const userStats = contributorProfiles[selectedContributor]?.projects?.find(p => p.name === project?.project_name) || {};

            // 1. Generate a default role description (codebase percentage)
            let defaultRole = project.role || "";
            if (selectedContributor && selectedContributor !== "general") {
                const pcts = project.data?.per_contributor_pct || {};
                const pct = pcts[selectedContributor];
                if (pct !== undefined) {
                    defaultRole = `${pct.toFixed(1)}% of codebase`;
                }
            }

            // 2. Generate a default combined tech stack
            let defaultTechArr = [];
            const pContext = project.data || {};
            let langs = pContext.languages || [];
            let fworks = pContext.frameworks || [];
            let combined = [];
            const flattenSkills = (val) => {
              if (typeof val === "string" && val) return val.split(",").map(s => s.trim());
              if (Array.isArray(val)) return val.flatMap(v => typeof v === "string" ? v.split(",").map(s => s.trim()) : [String(v).trim()]);
              return [];
            };
            combined.push(...flattenSkills(langs));
            combined.push(...flattenSkills(fworks));
            
            if (combined.length > 0) {
                defaultTechArr = [...new Set(combined)].filter(t => t && !["NA", "NONE", "UNKNOWN"].includes(t.toUpperCase()));
            } else {
                const hs = project.highlighted_skills || project.skills || [];
                if (Array.isArray(hs)) defaultTechArr = hs;
                else if (typeof hs === "string" && hs) defaultTechArr = hs.split(",").map(s => s.trim());
            }
            const defaultTech = defaultTechArr.join(", ");

            // 3. Generate a default project description
            let defaultDesc = project?.customization?.custom_portfolio_project_description || "";
            if (!defaultDesc) {
                const pType = pContext.project_type || "software";
                const dateStr = pContext.last_modified ? ` (last updated ${String(pContext.last_modified).split("T")[0].split(" ")[0]})` : "";
                defaultDesc = `${project.project_name} is a ${pType.toLowerCase()} project${dateStr}.`;
            }

            const desc = current.custom_portfolio_project_description ?? userStats.custom_portfolio_project_description ?? defaultDesc ?? "";
            const role = current.custom_portfolio_description ?? userStats.custom_portfolio_description ?? defaultRole ?? "";
            const techRaw = current.custom_portfolio_tech_stack ?? userStats.custom_portfolio_tech_stack ?? defaultTech ?? "";
            const tech = Array.isArray(techRaw) ? techRaw.join(", ") : techRaw;

            return (
              <div className="result-card" key={projectId}>
                <h3>{project?.project_name || projectId}</h3>
                <label className="field"><span>Project Description</span><textarea value={desc} onChange={(e) => updateProjectEdit(projectId, "custom_portfolio_project_description", e.target.value)} rows={2} placeholder={defaultDesc} /></label>
                <label className="field"><span>Role / Contribution</span><input value={role} onChange={(e) => updateProjectEdit(projectId, "custom_portfolio_description", e.target.value)} placeholder={defaultRole || "E.g. 50% of codebase, Lead Developer"} /></label>
                <label className="field"><span>Tech Stack (comma separated)</span><input value={tech} onChange={(e) => updateProjectEdit(projectId, "custom_portfolio_tech_stack", e.target.value)} placeholder={defaultTech || "React, Node.js, Python"} /></label>
                <label className="field">
                  <span>Project Thumbnail</span>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={(e) => {
                        if (e.target.files?.length) {
                          handleUploadThumbnail(projectId, e.target.files[0]);
                        }
                      }} 
                    />
                    {uploadingThumbnails[projectId] && <span className="muted" style={{ fontSize: "0.85rem" }}>Uploading...</span>}
                    {(current.thumbnail || project.customization?.thumbnail) && !uploadingThumbnails[projectId] && (
                      <span style={{ color: "var(--mint-600)", fontWeight: "bold", fontSize: "0.85rem" }}>✓ Saved</span>
                    )}
                  </div>
                </label>
              </div>
            );
          })}

          <button type="button" className="btn btn-primary" onClick={handleGeneratePortfolio} disabled={portfolioGenerating}>{portfolioGenerating ? "Saving & Generating..." : "Save & Generate"}</button>
          {portfolioError && <p className="error-text">{portfolioError}</p>}
            </>
          )}
        </div>
      )}

      {portfolioViewMode === "view" && (
        <div className="portfolio-showroom">
          {portfolioArtifact ? (
            <>
              <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
                <h1 style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>{portfolioArtifact.title || portfolioTitle}</h1>
                {portfolioArtifact.data?.global_skills?.length > 0 && (
                  <div className="tag-wrap" style={{ justifyContent: "center" }}>
                    {portfolioArtifact.data.global_skills.map((skill) => {
                      const isSelected = viewActiveFilter === skill;
                      return (
                        <button 
                          key={skill} 
                          onClick={() => setViewActiveFilter(isSelected ? "" : skill)}
                          style={{ 
                            backgroundColor: isSelected ? "#111827" : "white", 
                            color: isSelected ? "white" : "#4b5563", 
                            border: `1px solid ${isSelected ? "#111827" : "#d1d5db"}`,
                            borderRadius: "16px",
                            padding: "6px 14px", 
                            fontSize: "0.95rem",
                            cursor: "pointer",
                            transition: "all 0.2s ease"
                          }}
                          title={`Filter by ${skill}`}
                        >
                          {skill}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              <div style={{ display: "flex", justifyContent: "center", marginBottom: "2rem", gap: "1rem" }}>
                <input
                    type="text"
                    placeholder="Search projects by name or description..."
                    value={viewSearchQuery}
                    onChange={(e) => setViewSearchQuery(e.target.value)}
                    style={{ padding: "0.75rem 1rem", width: "100%", maxWidth: "500px", borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "1rem" }}
                />
                { (viewSearchQuery || viewActiveFilter) && (
                    <button type="button" className="btn btn-secondary" onClick={() => { setViewSearchQuery(""); setViewActiveFilter(""); }}>Clear Filters</button>
                )}
              </div>

              {portfolioArtifact.data?.skills_progression?.length > 0 && (
                <div className="result-card" style={{ marginBottom: "2rem" }}>
                  <div 
                    style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer", userSelect: "none" }}
                    onClick={() => setShowSkillsProgression(!showSkillsProgression)}
                  >
                    <h3 style={{ margin: 0 }}>Skills Progression & Depth</h3>
                    <span style={{ fontSize: "1.5rem", color: "#6b7280", lineHeight: "1" }}>
                      {showSkillsProgression ? "−" : "+"}
                    </span>
                  </div>
                  {showSkillsProgression && (
                    <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", marginTop: "1rem" }}>
                      <thead>
                        <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
                          <th style={{ padding: "0.5rem" }}>Skill</th>
                          <th style={{ padding: "0.5rem" }}>First Used</th>
                          <th style={{ padding: "0.5rem" }}>Last Used</th>
                          <th style={{ padding: "0.5rem" }}>Projects</th>
                          <th style={{ padding: "0.5rem" }}>Lines Added</th>
                          <th style={{ padding: "0.5rem" }}>Lines Removed</th>
                        </tr>
                      </thead>
                      <tbody>
                        {portfolioArtifact.data.skills_progression.map((s, i) => (
                          <tr key={i} style={{ borderBottom: "1px solid #e5e7eb" }}>
                            <td style={{ padding: "0.5rem" }}><strong>{s.skill}</strong></td>
                            <td style={{ padding: "0.5rem" }}>{s.first_used || "Unknown"}</td>
                            <td style={{ padding: "0.5rem" }}>{s.last_used || "Unknown"}</td>
                            <td style={{ padding: "0.5rem" }}>{s.projects_count}</td>
                            <td style={{ padding: "0.5rem", color: "#047857" }}>{s.insertions > 0 ? `+${s.insertions}` : "-"}</td>
                            <td style={{ padding: "0.5rem", color: "#b91c1c" }}>{s.deletions > 0 ? `-${s.deletions}` : "-"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              <div style={{ display: "flex", gap: "2rem", alignItems: "flex-start", flexWrap: "wrap" }}>
                {/* Left Column: Interactive Project List */}
                <div style={{ flex: "1 1 350px" }}>
                  <h3 style={{ marginTop: 0, marginBottom: "1rem", fontSize: "1.5rem" }}>Project Showcase</h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                    {filteredViewItems.length > 0 ? filteredViewItems.map((item) => {
                      const isActiveCard = activeViewItem?.project_id === item.project_id;
                      return (
                        <article 
                          className="portfolio-card" 
                          key={item.project_id}
                          onClick={() => setActiveViewProjectId(item.project_id)}
                          style={{
                            cursor: "pointer",
                            transition: "all 0.2s ease",
                            border: isActiveCard ? "2px solid var(--peach-500)" : "1px solid rgba(70, 98, 130, 0.25)",
                            boxShadow: isActiveCard ? "0 4px 12px rgba(240, 122, 74, 0.15)" : "none",
                            margin: 0
                          }}
                        >
                        <div style={{ height: "140px", background: "#e5e7eb", borderRadius: "8px", marginBottom: "1rem", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
                          {item.thumbnail ? (
                            <img 
                              src={`http://127.0.0.1:5000/thumbnails/${item.thumbnail}`} 
                              alt={`${item.project_name} thumbnail`} 
                              style={{ width: "100%", height: "100%", objectFit: "cover" }} 
                            />
                          ) : (
                            <p className="muted">🖼️ Thumbnail Placeholder</p>
                          )}
                        </div>
                          <h4 style={{ fontSize: "1.25rem", marginBottom: "0.5rem" }}>{item.project_name}</h4>
                          <p style={{ lineHeight: "1.5" }}>{item.project_description || item.text}</p>
                          
                          {item.role_description ? (
                            <p className="muted"><strong>Role/Contribution:</strong> {item.role_description}</p>
                          ) : item.contribution_display ? (
                            <p className="muted"><strong>Role/Contribution:</strong> {item.contribution_display}</p>
                          ) : item.role ? (
                            <p className="muted"><strong>Role:</strong> {item.role}</p>
                          ) : null}

                          {item.tech_stack?.length > 0 && (
                            <p className="muted"><strong>Tech Stack:</strong> {Array.isArray(item.tech_stack) ? item.tech_stack.join(", ") : item.tech_stack}</p>
                          )}
                          
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginTop: "1rem", background: "#f3f4f6", padding: "10px", borderRadius: "8px" }}>
                            {item.impact_score !== undefined && item.impact_score !== null && (
                              <div className="muted" style={{ margin: 0 }}><strong>Impact:</strong> {item.impact_score}</div>
                            )}
                            {(() => {
                              let duration = item.duration_days;
                              const dates = Object.keys(item.daily_commits || {}).sort();
                              if (dates.length > 0) {
                                const start = new Date(dates[0]);
                                const end = new Date(dates[dates.length - 1]);
                                duration = Math.round((end - start) / (1000 * 60 * 60 * 24)) + 1;
                              }
                              return duration !== undefined && duration !== null ? (
                                <div className="muted" style={{ margin: 0 }}><strong>Duration:</strong> {duration}d</div>
                              ) : null;
                            })()}
                            {item.commits !== undefined && item.commits !== null && (
                              <div className="muted" style={{ margin: 0 }}><strong>Commits:</strong> {item.commits}</div>
                            )}
                            {(item.lines_added !== undefined || item.lines_removed !== undefined) && (
                              <div className="muted" style={{ margin: 0 }}><strong>Lines:</strong> <span style={{ color: "#047857" }}>+{item.lines_added || 0}</span> / <span style={{ color: "#b91c1c" }}>-{item.lines_removed || 0}</span></div>
                            )}
                          </div>
                        </article>
                      );
                    }) : (
                      <p className="muted">No projects match your search or filter criteria.</p>
                    )}
                  </div>
                </div>

                {/* Right Column: Visuals (Sticky) */}
                <div style={{ flex: "2 1 500px", position: "sticky", top: "2rem" }}>
                  {activeViewItem ? (
                    <>
                      <div className="result-card" style={{ marginBottom: "2rem" }}>
                        <h3 style={{ marginTop: 0, marginBottom: "1rem" }}>Activity Heat Map</h3>
                        <div style={{ background: "#f9fafb", border: "1px solid #e5e7eb", padding: "1.5rem", borderRadius: "8px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "1rem" }}>
                            <span className="muted" style={{ margin: 0 }}>Contribution density for <strong>{activeViewItem.project_name}</strong></span>
                            <span style={{ fontSize: "0.85rem", fontWeight: "bold", color: "var(--ink-700)" }}>{activeViewItem.commits || 0} commits</span>
                          </div>
                          {renderHeatmap()}
                        </div>
                      </div>

                      <div className="result-card" style={{ marginBottom: "2rem" }}>
                        <h3 style={{ marginTop: 0, marginBottom: "1rem" }}>Project Timeline</h3>
                        <div style={{ background: "#f9fafb", border: "1px solid #e5e7eb", padding: "1.5rem", borderRadius: "8px" }}>
                          <div style={{ marginBottom: "1rem" }}>
                            <span className="muted" style={{ margin: 0 }}>Relative durations for showcase projects</span>
                          </div>
                          {renderTimeline()}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="result-card" style={{ textAlign: "center", padding: "3rem 1rem" }}>
                      <p className="muted">Select a project to view its visuals.</p>
                    </div>
                  )}
                </div>
              </div>
              
              <div style={{ textAlign: "center", marginTop: "3rem" }}>
                <button type="button" className="btn btn-secondary" style={{ padding: "1rem 2rem", fontSize: "1.1rem" }} onClick={handleExportPortfolio} disabled={portfolioExporting}>
                  {portfolioExporting ? "Exporting..." : "Export Markdown"}
                </button>
              </div>
            </>
          ) : (
            <div className="result-card" style={{ textAlign: "center", padding: "4rem 2rem" }}>
              <h3 style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>No Portfolio Generated</h3>
              <p className="muted" style={{ marginBottom: "2rem", fontSize: "1.1rem" }}>Go to Edit Mode, select your projects, and generate the portfolio to see the preview here.</p>
              <button className="btn btn-primary" onClick={() => setPortfolioViewMode('edit')}>Switch to Edit Mode</button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}