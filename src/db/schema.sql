CREATE DATABASE IF NOT EXISTS project_insight CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE project_insight;

------------------------------------------------------------
-- 1. Users & Consent
------------------------------------------------------------

CREATE TABLE users (
    id              CHAR(36) PRIMARY KEY,
    email           VARCHAR(255) UNIQUE,
    display_name    VARCHAR(255),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE user_consents (
    id              CHAR(36) PRIMARY KEY,
    user_id         CHAR(36) NOT NULL,
    consent_type    VARCHAR(100) NOT NULL,
    granted         BOOLEAN NOT NULL,
    details         TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX (user_id)
) ENGINE=InnoDB;

CREATE TABLE user_config (
    id              CHAR(36) PRIMARY KEY,
    user_id         CHAR(36) NOT NULL,
    config_key      VARCHAR(100) NOT NULL,
    config_value    JSON NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE (user_id, config_key),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

------------------------------------------------------------
-- 2. Uploads & Analysis Runs
------------------------------------------------------------

CREATE TABLE uploads (
    id                  CHAR(36) PRIMARY KEY,
    user_id             CHAR(36) NOT NULL,
    original_filename   VARCHAR(512) NOT NULL,
    storage_path        VARCHAR(1024) NOT NULL,
    uploaded_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    status              VARCHAR(50) DEFAULT 'PENDING',
    error_message       TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE analysis_runs (
    id              CHAR(36) PRIMARY KEY,
    user_id         CHAR(36) NOT NULL,
    upload_id       CHAR(36) NOT NULL,
    started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME,
    status          VARCHAR(50) DEFAULT 'RUNNING',
    config_snapshot JSON,
    notes           TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE,
    INDEX (user_id)
) ENGINE=InnoDB;

------------------------------------------------------------
-- 3. Projects & Collaborators
------------------------------------------------------------

CREATE TABLE projects (
    id                      CHAR(36) PRIMARY KEY,
    user_id                 CHAR(36) NOT NULL,
    analysis_run_id         CHAR(36),
    name                    VARCHAR(255) NOT NULL,
    description             TEXT,
    is_collaborative        BOOLEAN DEFAULT FALSE,
    source_type             VARCHAR(50),
    primary_language        VARCHAR(100),
    primary_framework       VARCHAR(100),
    start_date              DATE,
    end_date                DATE,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE SET NULL,
    INDEX (user_id),
    INDEX (start_date, end_date)
) ENGINE=InnoDB;

CREATE TABLE project_collaborators (
    id                      CHAR(36) PRIMARY KEY,
    project_id              CHAR(36) NOT NULL,
    collaborator_identifier VARCHAR(255) NOT NULL,
    is_primary_user         BOOLEAN DEFAULT FALSE,
    estimated_contribution_pct DECIMAL(5,2),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE (project_id, collaborator_identifier)
) ENGINE=InnoDB;

------------------------------------------------------------
-- 4. Artifacts (Files, Notes, Media, etc.)
------------------------------------------------------------

CREATE TABLE artifacts (
    id              CHAR(36) PRIMARY KEY,
    project_id      CHAR(36) NOT NULL,
    relative_path   VARCHAR(1024) NOT NULL,
    file_name       VARCHAR(512) NOT NULL,
    artifact_type   VARCHAR(50) NOT NULL,
    language        VARCHAR(100),
    framework       VARCHAR(100),
    size_bytes      BIGINT,
    created_ts      DATETIME,
    modified_ts     DATETIME,
    is_shared_across_projects BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE (project_id, relative_path, file_name),
    INDEX (artifact_type)
) ENGINE=InnoDB;

------------------------------------------------------------
-- 5. Contributions & Metrics
------------------------------------------------------------

CREATE TABLE contributions (
    id              CHAR(36) PRIMARY KEY,
    project_id      CHAR(36) NOT NULL,
    artifact_id     CHAR(36),
    actor_label     VARCHAR(255),
    activity_type   VARCHAR(50) NOT NULL,
    event_ts        DATETIME NOT NULL,
    quantity        DECIMAL(18,4),
    source          VARCHAR(50) NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL,
    INDEX (project_id, event_ts),
    INDEX (activity_type)
) ENGINE=InnoDB;

CREATE TABLE project_scores (
    id              CHAR(36) PRIMARY KEY,
    project_id      CHAR(36) NOT NULL,
    score_type      VARCHAR(50) NOT NULL,
    score_value     DECIMAL(18,4) NOT NULL,
    calculated_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE (project_id, score_type)
) ENGINE=InnoDB;

------------------------------------------------------------
-- 6. Skills & Mapping
------------------------------------------------------------

CREATE TABLE skills (
    id              CHAR(36) PRIMARY KEY,
    name            VARCHAR(255) UNIQUE NOT NULL,
    category        VARCHAR(100)
) ENGINE=InnoDB;

CREATE TABLE project_skills (
    project_id      CHAR(36) NOT NULL,
    skill_id        CHAR(36) NOT NULL,
    relevance_score DECIMAL(5,2),
    source          VARCHAR(50),
    PRIMARY KEY (project_id, skill_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB;

------------------------------------------------------------
-- 7. Insights, Résumé, Portfolio
------------------------------------------------------------

CREATE TABLE project_insights (
    id              CHAR(36) PRIMARY KEY,
    project_id      CHAR(36) NOT NULL,
    insight_type    VARCHAR(50) NOT NULL,
    content         TEXT,
    content_json    JSON,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted      BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE resume_items (
    id              CHAR(36) PRIMARY KEY,
    user_id         CHAR(36) NOT NULL,
    project_id      CHAR(36),
    title           VARCHAR(255) NOT NULL,
    description     TEXT NOT NULL,
    bullet_points   JSON,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted      BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE portfolio_items (
    id              CHAR(36) PRIMARY KEY,
    user_id         CHAR(36) NOT NULL,
    project_id      CHAR(36),
    display_title   VARCHAR(255) NOT NULL,
    summary         TEXT,
    metadata        JSON,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted      BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
) ENGINE=InnoDB;

------------------------------------------------------------
-- 8. External Services & Permissions
------------------------------------------------------------

CREATE TABLE external_services (
    id              CHAR(36) PRIMARY KEY,
    name            VARCHAR(100) UNIQUE NOT NULL,
    description     TEXT
) ENGINE=InnoDB;

CREATE TABLE user_external_permissions (
    id              CHAR(36) PRIMARY KEY,
    user_id         CHAR(36) NOT NULL,
    service_id      CHAR(36) NOT NULL,
    allowed         BOOLEAN NOT NULL,
    granted_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    revoked_at      DATETIME,
    UNIQUE (user_id, service_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES external_services(id) ON DELETE CASCADE
) ENGINE=InnoDB;

------------------------------------------------------------
-- 9. Deletion Log
------------------------------------------------------------

CREATE TABLE deletion_log (
    id              CHAR(36) PRIMARY KEY,
    user_id         CHAR(36) NOT NULL,
    target_type     VARCHAR(50) NOT NULL,
    target_id       CHAR(36) NOT NULL,
    deleted_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
