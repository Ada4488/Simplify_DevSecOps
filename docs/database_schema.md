# Database Schema (PostgreSQL)

This document defines the core database schemas for the AI-powered DevSecOps platform. PostgreSQL is selected as the relational database.

## Schemas

### 1. User Projects

Stores information about projects created by users.

-   `project_id`: SERIAL PRIMARY KEY
-   `user_id`: VARCHAR(255) NOT NULL (or INTEGER, depending on user management system)
-   `project_name`: VARCHAR(255) NOT NULL
-   `description`: TEXT
-   `nlp_input`: TEXT (stores the natural language input from the user)
-   `creation_date`: TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-   `last_modified_date`: TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP

**Indexes:**
-   `idx_project_user_id`: ON `user_projects` (`user_id`)

### 2. Pipeline Definitions

Stores information about the generated CI/CD pipelines and associated IaC.

-   `pipeline_id`: SERIAL PRIMARY KEY
-   `project_id`: INTEGER NOT NULL REFERENCES UserProjects(project_id)
-   `generated_iac_path`: VARCHAR(1024) (Path to the stored IaC files, e.g., S3 URI)
-   `generated_pipeline_path`: VARCHAR(1024) (Path to the stored CI/CD pipeline configuration, e.g., S3 URI or Git repo link)
-   `creation_date`: TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-   `status`: VARCHAR(50) (e.g., PENDING, GENERATING, COMPLETED, FAILED)
-   `version`: INTEGER DEFAULT 1

**Indexes:**
-   `idx_pipeline_project_id`: ON `pipeline_definitions` (`project_id`)

### 3. Security Findings

Stores results from various security scanning tools.

-   `finding_id`: SERIAL PRIMARY KEY
-   `pipeline_id`: INTEGER NOT NULL REFERENCES PipelineDefinitions(pipeline_id)
-   `tool_name`: VARCHAR(100) (e.g., Bandit, Trivy, SonarQube)
-   `vulnerability_id`: VARCHAR(255) (CVE ID or tool-specific ID)
-   `vulnerability_description`: TEXT
-   `severity`: VARCHAR(50) (e.g., CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL)
-   `file_path`: VARCHAR(1024) (File where the vulnerability was found)
-   `line_number`: INTEGER
-   `status`: VARCHAR(50) (e.g., NEW, ACKNOWLEDGED, RESOLVED, IGNORED)
-   `reported_date`: TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP

**Indexes:**
-   `idx_finding_pipeline_id`: ON `security_findings` (`pipeline_id`)
-   `idx_finding_severity`: ON `security_findings` (`severity`)
-   `idx_finding_status`: ON `security_findings` (`status`)

### 4. Audit Logs

Records significant actions performed within the system for security and compliance.

-   `log_id`: SERIAL PRIMARY KEY
-   `timestamp`: TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-   `user_id`: VARCHAR(255) (or INTEGER, if applicable)
-   `action_type`: VARCHAR(100) (e.g., CREATE_PROJECT, DEPLOY_PIPELINE, UPDATE_SETTINGS)
-   `target_resource_type`: VARCHAR(100) (e.g., PROJECT, PIPELINE, USER)
-   `target_resource_id`: VARCHAR(255)
-   `details`: JSONB (Stores context-specific information about the event)
-   `status_code`: INTEGER (e.g., 200 for success, 500 for failure)
-   `ip_address`: VARCHAR(45)

**Indexes:**
-   `idx_audit_log_timestamp`: ON `audit_logs` (`timestamp`)
-   `idx_audit_log_user_id`: ON `audit_logs` (`user_id`)
-   `idx_audit_log_action_type`: ON `audit_logs` (`action_type`)

---

**Note:** These schemas are initial designs for the MVP. They will likely evolve as the platform matures and more features are added. Considerations for future enhancements include versioning of pipeline definitions, more detailed tracking of IaC resources, and richer relationships between entities.
