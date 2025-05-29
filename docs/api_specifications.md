# API Specifications (High-Level Overview - MVP)

This document provides a high-level overview of the primary API endpoints for the AI-powered DevSecOps platform during the MVP phase. These APIs will facilitate communication between the frontend, backend services, and AI orchestration layer. OpenAPI Specification (OAS) will be used for detailed definitions later.

## Guiding Principles

-   **RESTful:** APIs will follow REST principles where appropriate.
-   **Stateless:** Backend services will be stateless, with state managed by clients or persisted in the database.
-   **JSON:** JSON will be the primary data interchange format.
-   **Authentication:** All endpoints (except possibly public status/health checks) will require authentication (e.g., JWT-based).

## Main API Endpoints

### 1. User Project Management

Manages user projects, including creation based on NLP input.

-   **`POST /api/v1/projects`**
    -   **Description:** Creates a new project. The request body will contain the user's natural language input describing their application and requirements.
    -   **Request Body:** `{ "nlp_query": "Deploy a Python web app with PostgreSQL on AWS, include SAST." }`
    -   **Response Body (Success - 202 Accepted):** `{ "project_id": "uuid", "status": "PROCESSING", "message": "Project creation initiated. AI is generating configuration." }`
    -   **Orchestration:** This endpoint will trigger the AI Orchestration Layer to parse the NLP query, generate IaC and CI/CD configurations.

-   **`GET /api/v1/projects/{project_id}`**
    -   **Description:** Retrieves details for a specific project, including its current status and links to generated artifacts.
    -   **Response Body (Success - 200 OK):** `{ "project_id": "uuid", "project_name": "My Web App", "nlp_input": "...", "status": "COMPLETED", "iac_preview_url": "/api/v1/projects/{project_id}/iac", "pipeline_preview_url": "/api/v1/projects/{project_id}/pipeline", "deployment_status_url": "/api/v1/projects/{project_id}/deployment" }`

-   **`GET /api/v1/projects`**
    -   **Description:** Lists all projects for the authenticated user.
    -   **Response Body (Success - 200 OK):** `[ { "project_id": "uuid", "project_name": "...", "status": "..." }, ... ]`

### 2. Configuration Preview

Allows users to view the AI-generated configurations.

-   **`GET /api/v1/projects/{project_id}/iac`**
    -   **Description:** Retrieves the generated Infrastructure as Code (IaC) for preview (e.g., Terraform HCL).
    -   **Response Body (Success - 200 OK):** `{ "format": "hcl", "content": "..." }` (or could be plain text)

-   **`GET /api/v1/projects/{project_id}/pipeline`**
    -   **Description:** Retrieves the generated CI/CD pipeline configuration for preview (e.g., GitHub Actions YAML).
    -   **Response Body (Success - 200 OK):** `{ "format": "yaml", "content": "..." }` (or could be plain text)

### 3. Deployment Control

Manages the deployment process.

-   **`POST /api/v1/projects/{project_id}/deploy`**
    -   **Description:** Initiates the deployment of the generated IaC and CI/CD pipeline for the specified project.
    -   **Response Body (Success - 202 Accepted):** `{ "deployment_id": "uuid", "status": "DEPLOYMENT_STARTED", "message": "Deployment process has been initiated." }`

-   **`GET /api/v1/projects/{project_id}/deployment`** (or `/api/v1/deployments/{deployment_id}`)
    -   **Description:** Retrieves the status of the deployment for a specific project.
    -   **Response Body (Success - 200 OK):** `{ "deployment_id": "uuid", "project_id": "uuid", "status": "SUCCEEDED", "details_url": "/api/v1/deployments/{deployment_id}/logs" }` (Could include logs, start/end times, etc.)

### 4. Security Scan Results

Provides access to security scan results.

-   **`GET /api/v1/projects/{project_id}/security-findings`** (or tied to a specific pipeline run)
    -   **Description:** Retrieves a summary of security findings for a project.
    -   **Response Body (Success - 200 OK):** `{ "project_id": "uuid", "summary": { "sast": { "vulnerabilities": 5, "critical": 1, "high": 2 } }, "findings": [ { "tool": "Bandit", "description": "...", "severity": "HIGH" }, ... ] }`

## Internal APIs (Conceptual)

While not directly user-facing, internal APIs will exist for:

-   **AI Orchestration Service:**
    -   Receiving NLP queries.
    -   Interacting with specific AI Agents (IaC Agent, Pipeline Agent).
    -   Storing and retrieving generated artifacts.
-   **Deployment Engine Service:**
    -   Executing IaC commands (e.g., `terraform apply`).
    -   Triggering CI/CD pipelines.
    -   Reporting deployment status and logs.
-   **Security Agent Service:**
    -   Receiving requests to scan code or artifacts.
    -   Returning scan results in a standardized format.

---
**Note:** This is a preliminary list for the MVP. As the platform evolves, more endpoints and refinements will be necessary. Error handling, pagination, filtering, and detailed request/response schemas will be defined using OpenAPI specifications.
