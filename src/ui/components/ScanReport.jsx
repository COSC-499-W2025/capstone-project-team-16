import React, { useEffect, useMemo, useState } from "react";

function parseList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item && item !== "NA" && item !== "Unknown");
  }
  return [];
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

function MetricBar({ label, value, maxValue, accent = "var(--mint-500)", subtitle }) {
  const numericValue = Number(value || 0);
  const width = maxValue > 0 ? Math.max((numericValue / maxValue) * 100, numericValue > 0 ? 8 : 0) : 0;

  return (
    <div className="metric-bar">
      <div className="metric-bar-head">
        <span>{label}</span>
        <strong>{subtitle || formatNumber(numericValue)}</strong>
      </div>
      <div className="metric-bar-track">
        <div className="metric-bar-fill" style={{ width: `${width}%`, background: accent }} />
      </div>
    </div>
  );
}

export default function ScanReport({ isActive, selectedScanId, fetchJson, setActiveTab, formatTimestamp, isNoise }) {
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedProjectIndex, setSelectedProjectIndex] = useState(0);

  useEffect(() => {
    if (!isActive || !selectedScanId) {
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchJson(`/scans/${selectedScanId}`)
      .then((data) => {
        if (!cancelled) {
          setScan(data.scan || null);
          setSelectedProjectIndex(0);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setScan(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [isActive, selectedScanId, fetchJson]);

  const projectSummaries = scan?.scan_data?.project_summaries || [];
  const selectedProject = projectSummaries[selectedProjectIndex] || projectSummaries[0] || null;
  const contributorProfiles = scan?.scan_data?.contributor_profiles || {};
  const validContributorEntries = Object.entries(contributorProfiles).filter(([name]) => !isNoise(name));
  const scanSkillTimeline = scan?.scan_data?.skills_chronological || [];

  const scanSummary = useMemo(() => {
    const uniqueLanguages = new Set();
    const uniqueFrameworks = new Set();
    const uniqueSkills = new Set();
    let cumulativeScore = 0;

    projectSummaries.forEach((project) => {
      parseList(project.languages).forEach((entry) => uniqueLanguages.add(entry));
      parseList(project.frameworks).forEach((entry) => uniqueFrameworks.add(entry));
      parseList(project.skills).forEach((entry) => uniqueSkills.add(entry));
      cumulativeScore += Number(project.score || 0);
    });

    return {
      uniqueLanguageCount: uniqueLanguages.size,
      uniqueFrameworkCount: uniqueFrameworks.size,
      uniqueSkillCount: uniqueSkills.size,
      cumulativeScore,
      topSkills: Array.from(uniqueSkills).slice(0, 10),
      topLanguages: Array.from(uniqueLanguages).slice(0, 10),
    };
  }, [projectSummaries]);

  const projectScoreBars = useMemo(() => {
    return projectSummaries
      .map((project, idx) => ({
        id: `${project.project || project.name || idx}`,
        label: project.project || project.name || `Project ${idx + 1}`,
        value: Number(project.score || 0),
      }))
      .sort((a, b) => b.value - a.value);
  }, [projectSummaries]);

  const contributorAggregate = useMemo(() => {
    return validContributorEntries
      .map(([name, profile]) => {
        const projects = profile.projects || [];
        const projectCount = projects.length;
        const filesWorked = projects.reduce((sum, project) => sum + Number(project.files_worked || 0), 0);
        const commits = projects.reduce((sum, project) => sum + Number(project.commit_count || 0), 0);
        const insertions = projects.reduce((sum, project) => sum + Number(project.insertions || 0), 0);
        const deletions = projects.reduce((sum, project) => sum + Number(project.deletions || 0), 0);
        const impact = projects.reduce((sum, project) => sum + Number(project.score || 0), 0);
        return {
          name,
          projectCount,
          filesWorked,
          commits,
          insertions,
          deletions,
          impact,
          skills: Array.isArray(profile.skills) ? profile.skills : [],
        };
      })
      .sort((a, b) => b.impact - a.impact);
  }, [validContributorEntries]);

  const projectContributorBars = useMemo(() => {
    if (!selectedProject) {
      return [];
    }
    const pctMap = selectedProject.per_contributor_pct || {};
    const scoreMap = selectedProject.per_contributor_scores || {};
    const skillsMap = selectedProject.per_contributor_skills || {};
    return Object.keys(pctMap)
      .filter((name) => !isNoise(name))
      .map((name) => ({
        name,
        pct: Number(pctMap[name] || 0),
        impact: Number(scoreMap[name] || 0),
        skills: Array.isArray(skillsMap[name]) ? skillsMap[name] : [],
      }))
      .sort((a, b) => b.pct - a.pct);
  }, [selectedProject, isNoise]);

  const activityBreakdown = selectedProject
    ? [
        { label: "Code files", value: Number(selectedProject.code_files || 0), accent: "var(--peach-500)" },
        { label: "Test files", value: Number(selectedProject.test_files || 0), accent: "var(--mint-500)" },
        { label: "Documentation", value: Number(selectedProject.doc_files || 0), accent: "#60a5fa" },
        { label: "Design files", value: Number(selectedProject.design_files || 0), accent: "#f59e0b" },
      ]
    : [];

  const maxProjectScore = Math.max(...projectScoreBars.map((item) => item.value), 0);
  const maxContributorImpact = Math.max(...contributorAggregate.map((item) => item.impact), 0);
  const maxProjectPct = Math.max(...projectContributorBars.map((item) => item.pct), 0);
  const maxProjectImpact = Math.max(...projectContributorBars.map((item) => item.impact), 0);
  const maxActivity = Math.max(...activityBreakdown.map((item) => item.value), 0);

  return (
    <section className="panel report-shell">
      <div className="report-header">
        <div>
          <button type="button" className="btn btn-ghost" onClick={() => setActiveTab("scan-manager")}>
            &larr; Back to Scan Manager
          </button>
          <h2 style={{ marginBottom: "0.4rem" }}>Full Scan Report</h2>
          <p className="muted" style={{ margin: 0 }}>
            Deep-dive view of scan #{scan?.summary_id || selectedScanId}
          </p>
        </div>
        {scan && (
          <div className="result-card">
            <p className="muted" style={{ margin: 0 }}>
              <strong>Mode:</strong> {scan.analysis_mode}
            </p>
            <p className="muted" style={{ margin: 0 }}>
              <strong>Date:</strong> {formatTimestamp(scan.timestamp)}
            </p>
          </div>
        )}
      </div>

      {loading ? <p>Loading scan report...</p> : null}
      {error ? <p className="error-text">{error}</p> : null}

      {!loading && !error && scan && (
        <div className="report-grid">
          <div className="report-main">
            <div className="stats-grid">
              <div className="result-card">
                <p className="muted">Projects</p>
                <h3>{projectSummaries.length}</h3>
              </div>
              <div className="result-card">
                <p className="muted">Contributors</p>
                <h3>{contributorAggregate.length}</h3>
              </div>
              <div className="result-card">
                <p className="muted">Unique Skills</p>
                <h3>{scanSummary.uniqueSkillCount}</h3>
              </div>
              <div className="result-card">
                <p className="muted">Portfolio Score</p>
                <h3>{Math.round(scanSummary.cumulativeScore)}</h3>
              </div>
            </div>

            <div className="result-card">
              <h3>Scan Overview</h3>
              <div className="tag-wrap" style={{ marginBottom: "0.75rem" }}>
                {scanSummary.topLanguages.map((language) => (
                  <span className="tag" key={language}>{language}</span>
                ))}
              </div>
              <div className="tag-wrap">
                {scanSummary.topSkills.map((skill) => (
                  <span className="tag" key={skill}>{skill}</span>
                ))}
              </div>
            </div>

            <div className="report-two-column">
              <div className="result-card">
                <h3>Project Rankings</h3>
                <div className="metric-stack">
                  {projectScoreBars.map((item) => (
                    <MetricBar key={item.id} label={item.label} value={item.value} maxValue={maxProjectScore} subtitle={`${item.value.toFixed(1)} score`} />
                  ))}
                </div>
              </div>

              <div className="result-card">
                <h3>Contributors Across Scan</h3>
                <div className="metric-stack">
                  {contributorAggregate.map((entry) => (
                    <MetricBar key={entry.name} label={entry.name} value={entry.impact} maxValue={maxContributorImpact} subtitle={`${entry.projectCount} projects`} accent="var(--peach-500)" />
                  ))}
                </div>
              </div>
            </div>

            <div className="result-card">
              <div className="report-section-head">
                <div>
                  <h3 style={{ marginBottom: "0.3rem" }}>Project Detail</h3>
                  <p className="muted" style={{ margin: 0 }}>Select a project from the sidebar to inspect every metric we extracted.</p>
                </div>
                <select value={selectedProjectIndex} onChange={(e) => setSelectedProjectIndex(Number(e.target.value))} style={{ maxWidth: "320px" }}>
                  {projectSummaries.map((project, idx) => (
                    <option key={`${project.project || project.name || idx}`} value={idx}>
                      {project.project || project.name || `Project ${idx + 1}`}
                    </option>
                  ))}
                </select>
              </div>

              {selectedProject ? (
                <div className="detail-stack">
                  <div className="detail-grid">
                    <div className="detail-card">
                      <span className="muted">Project</span>
                      <strong>{selectedProject.project || selectedProject.name || "Untitled project"}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="muted">Type</span>
                      <strong>{selectedProject.project_type || "Unknown"}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="muted">Duration</span>
                      <strong>{selectedProject.duration_days || 0} days</strong>
                    </div>
                    <div className="detail-card">
                      <span className="muted">Commit Frequency</span>
                      <strong>{selectedProject.commit_frequency || "Unknown"}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="muted">Project Score</span>
                      <strong>{Number(selectedProject.score || 0).toFixed(1)}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="muted">Collaboration</span>
                      <strong>{selectedProject.is_collaborative || "Unknown"}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="muted">Repository</span>
                      <strong>{selectedProject.repo_name || "No repo detected"}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="muted">Root Path</span>
                      <strong>{selectedProject.repo_root || "Unknown"}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="muted">Branches / Merges</span>
                      <strong>{selectedProject.branch_count || 0} / {selectedProject.has_merges || "Unknown"}</strong>
                    </div>
                    <div className="detail-card">
                      <span className="muted">Timeline</span>
                      <strong>{String(selectedProject.first_modified || "").split("T")[0] || "Unknown"} to {String(selectedProject.last_modified || "").split("T")[0] || "Unknown"}</strong>
                    </div>
                  </div>

                  <div className="report-two-column">
                    <div className="result-card">
                      <h3>Languages & Frameworks</h3>
                      <p className="muted"><strong>Languages:</strong> {selectedProject.languages || "Unknown"}</p>
                      <p className="muted"><strong>Frameworks:</strong> {selectedProject.frameworks || "NA"}</p>
                      <div className="tag-wrap">
                        {parseList(selectedProject.languages).concat(parseList(selectedProject.frameworks)).map((item) => (
                          <span className="tag" key={item}>{item}</span>
                        ))}
                      </div>
                    </div>

                    <div className="result-card">
                      <h3>Skills</h3>
                      <div className="tag-wrap">
                        {parseList(selectedProject.skills).map((skill) => (
                          <span className="tag" key={skill}>{skill}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="report-two-column">
                    <div className="result-card">
                      <h3>Activity Breakdown</h3>
                      <div className="metric-stack">
                        {activityBreakdown.map((item) => (
                          <MetricBar key={item.label} label={item.label} value={item.value} maxValue={maxActivity} accent={item.accent} />
                        ))}
                      </div>
                    </div>

                    <div className="result-card">
                      <h3>Contribution Share</h3>
                      {projectContributorBars.length > 0 ? (
                        <div className="metric-stack">
                          {projectContributorBars.map((entry) => (
                            <MetricBar key={entry.name} label={entry.name} value={entry.pct} maxValue={maxProjectPct} subtitle={`${entry.pct.toFixed(1)}%`} accent="var(--mint-500)" />
                          ))}
                        </div>
                      ) : (
                        <p className="muted">No contributor percentages available for this project.</p>
                      )}
                    </div>
                  </div>

                  <div className="report-two-column">
                    <div className="result-card">
                      <h3>Contributor Impact Score</h3>
                      {projectContributorBars.length > 0 ? (
                        <div className="metric-stack">
                          {projectContributorBars.map((entry) => (
                            <MetricBar key={entry.name} label={entry.name} value={entry.impact} maxValue={maxProjectImpact} subtitle={`${entry.impact.toFixed(1)} pts`} accent="var(--peach-500)" />
                          ))}
                        </div>
                      ) : (
                        <p className="muted">Impact scores were not generated for this project.</p>
                      )}
                    </div>

                    <div className="result-card">
                      <h3>Contributor Skills</h3>
                      {projectContributorBars.length > 0 ? (
                        <div className="detail-stack">
                          {projectContributorBars.map((entry) => (
                            <div key={entry.name} className="detail-card">
                              <strong>{entry.name}</strong>
                              <div className="tag-wrap">
                                {entry.skills.length > 0 ? entry.skills.map((skill) => <span className="tag" key={`${entry.name}-${skill}`}>{skill}</span>) : <span className="muted">No skill list available</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="muted">No per-contributor skill data available.</p>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="muted">No projects were found in this scan.</p>
              )}
            </div>
          </div>

          <aside className="report-side">
            <div className="result-card">
              <h3>Projects</h3>
              <ul className="simple-list">
                {projectSummaries.map((project, idx) => (
                  <li key={`${project.project || project.name || idx}`}>
                    <button type="button" className={`inline-link ${selectedProjectIndex === idx ? "active" : ""}`} onClick={() => setSelectedProjectIndex(idx)}>
                      {project.project || project.name || `Project ${idx + 1}`}
                    </button>
                    <p className="muted" style={{ marginTop: "0.2rem" }}>
                      {project.project_type || "Unknown"} | {Number(project.score || 0).toFixed(1)} score
                    </p>
                  </li>
                ))}
              </ul>
            </div>

            <div className="result-card">
              <h3>Contributor Directory</h3>
              {contributorAggregate.length > 0 ? (
                <div className="detail-stack">
                  {contributorAggregate.map((entry) => (
                    <div key={entry.name} className="detail-card">
                      <strong>{entry.name}</strong>
                      <p className="muted">Projects: {entry.projectCount}</p>
                      <p className="muted">Commits: {formatNumber(entry.commits)}</p>
                      <p className="muted">Files worked: {formatNumber(entry.filesWorked)}</p>
                      <p className="muted">Lines: +{formatNumber(entry.insertions)} / -{formatNumber(entry.deletions)}</p>
                      <div className="tag-wrap">
                        {entry.skills.slice(0, 8).map((skill) => (
                          <span className="tag" key={`${entry.name}-${skill}`}>{skill}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No contributor profiles were detected for this scan.</p>
              )}
            </div>

            <div className="result-card">
              <h3>Skill Timeline</h3>
              {scanSkillTimeline.length > 0 ? (
                <div className="detail-stack">
                  {scanSkillTimeline.map((entry) => (
                    <div key={`${entry.skill}-${entry.first_used}`} className="detail-card">
                      <strong>{entry.skill}</strong>
                      <p className="muted">First used: {entry.first_used}</p>
                      <p className="muted">Last used: {entry.last_used}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No chronological skill data was generated for this scan.</p>
              )}
            </div>
          </aside>
        </div>
      )}
    </section>
  );
}
