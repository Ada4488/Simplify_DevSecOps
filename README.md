# AI-Powered No-Code/Low-Code DevSecOps Platform

## Description & Goal

This project aims to build an AI-powered, no-code/low-code DevSecOps platform designed for non-technical users. The goal is to simplify and automate the process of generating secure CI/CD pipelines and deploying applications using natural language inputs. This platform leverages AI, cloud-native technologies, and intuitive user experience design to make DevSecOps practices accessible to a broader audience.

## Current Status & Features (MVP - Phase 1 In Progress)

The project is currently in **Phase 1 (Minimum Viable Product)**, focusing on demonstrating the core value proposition.

**Implemented Features:**

*   **Natural Language Processing (NLP) for Intent Recognition:**
    *   Users can input application requirements in natural language via a web interface.
    *   The backend AI Orchestration service uses an LLM (Anthropic Claude 3 Sonnet) to parse this input and extract key entities (e.g., application type, database, cloud provider, security needs).
*   **Basic Infrastructure as Code (IaC) Generation:**
    *   Based on the parsed intent, a basic Infrastructure Agent in the backend generates a simple Terraform HCL code string (currently supports a basic AWS EC2 instance configuration).
*   **Web-Based User Interface (UI):**
    *   A React/Vite frontend provides:
        *   Mock user authentication (login/registration forms).
        *   A dashboard for inputting application descriptions.
        *   Display of the parsed intent (JSON) from the NLP module.
        *   Display of the generated IaC (Terraform HCL) from the Infrastructure Agent.
*   **Containerized Services:**
    *   Both the backend (FastAPI) and frontend (React served with Nginx) applications are containerized using Docker.
*   **Initial Design Documentation:**
    *   Core architecture, database schema, API specifications, and LLM choice are documented in the `/docs` directory.

## Tech Stack

*   **Backend:** Python, FastAPI
*   **Frontend:** TypeScript, React, Vite
*   **AI/NLP:** Anthropic Claude 3 Sonnet API
*   **IaC Generation (Target):** Terraform (currently generating HCL strings)
*   **Containerization:** Docker
*   **Web Server (for Frontend):** Nginx
*   **Version Control:** Git, GitHub

## Directory Structure

```
.
├── ai_orchestration/ # Backend FastAPI service for AI logic, NLP, agent actions
│   ├── Dockerfile
│   ├── main.py      # FastAPI app, endpoints
│   ├── requirements.txt
│   └── ...
├── docs/             # Project documentation (architecture, schemas, API specs)
├── frontend/         # Frontend React/Vite application
│   ├── Dockerfile
│   ├── src/
│   ├── package.json
│   └── ...
├── .gitignore
├── LICENSE
└── README.md
```

## Setup and Running Instructions

### Prerequisites

*   [Docker](https://www.docker.com/get-started) and Docker Compose (recommended)
*   [Node.js and npm](https://nodejs.org/) (for local frontend development or if not using Docker for frontend)
*   [Python 3.9+](https://www.python.org/downloads/) (for local backend development or if not using Docker for backend)
*   An **Anthropic API Key** (for Claude 3 Sonnet access)

### Backend Service (`ai_orchestration`)

#### Cloud Credentials for `terraform apply`

**Important:** For the `terraform apply` functionality to work and provision resources in your target cloud environment (e.g., AWS), the environment where the `ai_orchestration` service runs (e.g., its Docker container or the local machine if running directly) **must be configured with valid cloud provider credentials.**

*   **For AWS:**
    *   The common way is to set the following environment variables:
        *   `AWS_ACCESS_KEY_ID`
        *   `AWS_SECRET_ACCESS_KEY`
        *   `AWS_SESSION_TOKEN` (if using temporary credentials)
        *   `AWS_DEFAULT_REGION` (e.g., `us-east-1`)
    *   These credentials must have sufficient IAM permissions to create, modify, and delete the resources defined in the generated HCL (e.g., EC2 instances, Security Groups).
    *   When running the Docker container for the backend, pass these environment variables using the `-e` flag. For example, if your `ANTHROPIC_API_KEY` is also an environment variable:
        ```bash
        docker run -d -p 8000:8000 \
          -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
          -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
          -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
          -e AWS_DEFAULT_REGION="us-east-1" \
          # Add -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN if needed
          --name ai_orch_service ai-orchestration-service
        ```
    *   Refer to the official AWS documentation for details on configuring credentials for applications.

*   **For other Cloud Providers (Azure, GCP, etc.):**
    *   Similar mechanisms (typically environment variables or mounted configuration files/service account keys) are used. Consult the specific provider's documentation for Terraform authentication.

Failure to provide valid credentials will result in errors when `terraform apply` is executed by the platform.

1.  **API Key Setup:**
    *   The backend service requires an Anthropic API key. Export it as an environment variable:
        ```bash
        export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
        ```
    *   If using Docker Compose (recommended for future steps), you can set this in a `.env` file.

2.  **Running with Docker (Recommended):**
    *   Navigate to the `ai_orchestration` directory:
        ```bash
        cd ai_orchestration
        ```
    *   Build the Docker image:
        ```bash
        docker build -t ai-orchestration-service .
        ```
    *   Run the Docker container:
        ```bash
        docker run -d -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY --name ai_orch_service ai-orchestration-service
        ```
        The service will be available at `http://localhost:8000`.

3.  **Running Locally (Alternative):**
    *   Navigate to the `ai_orchestration` directory.
    *   Create a virtual environment and install dependencies:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        pip install -r requirements.txt
        ```
    *   Ensure `ANTHROPIC_API_KEY` is set in your shell.
    *   Run the FastAPI application using Uvicorn:
        ```bash
        uvicorn main:app --reload --port 8000
        ```

### Frontend Service (`frontend`)

1.  **Running with Docker (Recommended):**
    *   Navigate to the `frontend` directory:
        ```bash
        cd frontend
        ```
    *   Build the Docker image:
        ```bash
        docker build -t platform-frontend-ui .
        ```
    *   Run the Docker container:
        ```bash
        docker run -d -p 5173:80 --name platform_ui platform-frontend-ui
        ```
        The UI will be available at `http://localhost:5173` (Vite's default port is 5173, Nginx in Docker serves on port 80, which is mapped to 5173 locally). *Note: The Dockerfile for frontend serves on port 80; adjust the `-p` mapping if your local Vite dev server uses a different port or if you want to expose it on a different local port.*

2.  **Running Locally (Alternative):**
    *   Navigate to the `frontend` directory.
    *   Install dependencies:
        ```bash
        npm install
        ```
    *   Run the Vite development server:
        ```bash
        npm run dev
        ```
        The UI will typically be available at `http://localhost:5173`.

### Accessing the Application

*   **Backend API:** `http://localhost:8000` (e.g., `http://localhost:8000/health` for health check)
*   **Frontend UI:** `http://localhost:5173` (or the port Nginx is mapped to if using Docker for frontend)

## Basic Usage

1.  Open your web browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
2.  You will be prompted to "login" or "register". Since authentication is currently mocked, you can use any dummy credentials.
3.  Once "logged in," you'll land on the dashboard.
4.  In the text area provided, describe the application you want to build and its infrastructure requirements. For example:
    > "Deploy a Python Flask web application with a PostgreSQL database on AWS. Include SAST scanning."
5.  Click the "Generate Configuration" (or similarly named) button.
6.  The UI will first display the "Parsed Intent" as a JSON object, showing how the AI understood your request.
7.  Subsequently, it will display the "Generated IaC (Terraform HCL)" based on this parsed intent. Currently, this will be a very basic HCL structure.

## Next Steps & Future Work (Phase 1 Continued)

The immediate next steps involve expanding on the core Phase 1 functionalities:

*   **Enhance Infrastructure Agent:**
    *   Generate more comprehensive and correct Terraform HCL for various AWS services (VPC, security groups, databases, more compute options).
    *   Integrate with Terraform CLI to validate and apply generated IaC.
*   **Develop Basic Pipeline Agent:**
    *   Generate CI/CD pipeline configurations (e.g., GitHub Actions YAML).
    *   Integrate with Git to commit generated configurations.
*   **Zero-Config Security:**
    *   Integrate a basic SAST tool (e.g., Bandit for Python) into the generated pipeline.
*   **Deployment Engine:**
    *   Develop a basic engine to orchestrate Terraform execution and CI/CD pipeline runs.
*   **UI Enhancements:**
    *   Display previews of generated CI/CD pipeline YAML.
    *   Show deployment status.

---

This project is actively under development. Contributions and feedback are welcome as the platform evolves.