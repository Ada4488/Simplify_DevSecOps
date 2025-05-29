# LLM Selection for Text-to-Configuration (MVP)

This document outlines the research and preliminary selection of a Large Language Model (LLM) for the AI-powered DevSecOps platform, specifically for the task of converting natural language user input into infrastructure and pipeline configurations (text-to-configuration).

## Task Requirements

The primary requirement for the LLM is to accurately:
1.  Parse user intent from natural language descriptions (e.g., "Deploy a Python web app with PostgreSQL on AWS, include SAST").
2.  Extract key entities (application type, desired services, cloud environment, security tools).
3.  Generate structured configuration outputs, primarily:
    -   Infrastructure as Code (IaC) - e.g., Terraform HCL.
    -   CI/CD pipeline definitions - e.g., GitHub Actions YAML.
4.  Handle a degree of ambiguity and ask clarifying questions if necessary (a more advanced feature, but good to keep in mind).
5.  Be reasonably cost-effective for the MVP phase.

## Considered LLMs

Based on the project brief and current AI landscape, the following models were considered:

1.  **OpenAI GPT-4 / GPT-4 Turbo:**
    -   **Pros:** State-of-the-art performance in reasoning, code generation, and instruction following. Widely available API.
    -   **Cons:** Can be relatively expensive, especially for high-volume tasks. Potential data privacy concerns for some users (though API usage typically has data protection clauses).

2.  **Anthropic Claude 3 (Opus, Sonnet, Haiku):**
    -   **Pros:**
        -   **Claude 3 Opus:** Reported to match or exceed GPT-4 in many benchmarks, particularly strong in complex reasoning and code generation.
        -   **Claude 3 Sonnet:** Offers a good balance of performance and speed/cost, making it suitable for enterprise workloads.
        -   **Claude 3 Haiku:** Fastest and most compact model, suitable for simpler tasks or when near real-time responses are critical (less likely for initial config generation).
        -   Generally good at producing structured output and adhering to complex instructions. Competitive pricing. Strong focus on safety and reducing model hallucinations.
    -   **Cons:** Opus can still be relatively expensive, similar to GPT-4. API availability and ecosystem might be slightly less mature than OpenAI's but rapidly improving.

3.  **Meta Llama 3 (e.g., 70B instruct model):**
    -   **Pros:** State-of-the-art open-source model. Offers excellent performance, potentially matching proprietary models. No direct API costs if self-hosted (but incurs infrastructure and operational costs). Allows for deeper customization and fine-tuning.
    -   **Cons:** Requires more effort to deploy and manage if not using a third-party hosted API. Fine-tuning requires significant expertise and data. Ensuring consistent, high-quality output for complex configuration generation might need more prompt engineering or fine-tuning effort compared to leading proprietary models.

## Preliminary Selection for MVP: Claude 3 Sonnet

For the MVP, **Claude 3 Sonnet** is preliminarily selected.

**Rationale:**

1.  **Balanced Performance and Cost:** Sonnet is designed to offer a strong balance between high performance on complex tasks (like code generation and instruction following for structured output) and cost-effectiveness. This is crucial for an MVP where we need reliability without incurring excessive operational expenses.
2.  **Strong Instruction Following:** Generating accurate IaC and YAML configurations requires an LLM that can meticulously follow detailed prompts and output formats. Claude models have shown strength in this area.
3.  **Large Context Window:** Useful for potentially complex user inputs or when providing extensive examples in prompts.
4.  **API Availability:** Anthropic provides a well-documented API, making integration relatively straightforward.
5.  **Scalability to Opus:** If Sonnet proves insufficient for highly complex scenarios, we have an upgrade path to Claude 3 Opus, which is among the most powerful models available. Conversely, for simpler, more frequent tasks, Haiku could be explored later for cost optimization.

## Next Steps

1.  **API Integration:** Develop initial integration with the Claude 3 Sonnet API.
2.  **Prompt Engineering:** Begin developing and testing prompt engineering techniques specifically for generating IaC (Terraform) and CI/CD (GitHub Actions YAML) from natural language inputs (Task 2.1.2).
3.  **Evaluation:** Continuously evaluate the quality of generated configurations, cost, and latency. Be prepared to revisit this selection if Sonnet does not meet the MVP requirements or if other models demonstrate significant advantages.

This selection will be revisited as the project progresses and more empirical data on the model's performance for our specific use case becomes available.

## Initial Prompt Engineering Design (Task 2.1.2)

This section outlines the initial strategies and examples for prompt engineering using the selected LLM (Claude 3 Sonnet) to translate user natural language requests into structured configuration data.

### Core Principles for Prompting

1.  **Clear Role Assignment:** Instruct the LLM to act as an expert DevSecOps engineer or a configuration generator.
2.  **Structured Output Specification:** Clearly define the desired output format. For initial entity extraction, JSON is preferred. For IaC and CI/CD, specify the exact language (HCL for Terraform, YAML for GitHub Actions).
3.  **Few-Shot Examples:** Provide one or two examples within the prompt (few-shot learning) to guide the model's response format and content, especially for complex generation tasks.
4.  **Chain of Thought / Step-by-Step Instructions:** For more complex requests, instruct the model to "think step by step" or break down the problem, which can improve accuracy for generation tasks.
5.  **Iterative Refinement:** Prompts will be iteratively refined based on LLM outputs and testing.

### Example 1: Intent Recognition and Entity Extraction

**Goal:** Convert raw user NLP input into a structured JSON object identifying key parameters.

**User Input:** "I want to deploy a Python Flask web application. It needs a PostgreSQL database. Deploy it on AWS. Also, make sure to include SAST scanning in the pipeline."

**Prompt Structure:**

```
You are an expert DevSecOps platform assistant. Your task is to parse the user's natural language request and extract key information to define a new application deployment project.
The user's request is:
"""
{{user_request}}
"""

Extract the following information and return it as a JSON object:
- "application_type": (e.g., "python_flask_webapp", "nodejs_express_api", "static_website", "java_spring_service")
- "programming_language": (e.g., "python", "javascript", "java", "go")
- "database_type": (e.g., "postgresql", "mysql", "mongodb", "none")
- "cloud_provider": (e.g., "aws", "azure", "gcp")
- "required_security_scans": (list of strings, e.g., ["sast", "dast", "sca"])
- "other_requirements": (any other specific user requests or details)

Example:
User Request: "Deploy a Node.js Express API with a MongoDB database on Azure. I need SAST and DAST."
Expected JSON Output:
{
  "application_type": "nodejs_express_api",
  "programming_language": "javascript",
  "database_type": "mongodb",
  "cloud_provider": "azure",
  "required_security_scans": ["sast", "dast"],
  "other_requirements": "None"
}

Now, parse the following user request:
"""
I want to deploy a Python Flask web application. It needs a PostgreSQL database. Deploy it on AWS. Also, make sure to include SAST scanning in the pipeline.
"""

Return ONLY the JSON object.
```

**Expected LLM Output (for the example):**

```json
{
  "application_type": "python_flask_webapp",
  "programming_language": "python",
  "database_type": "postgresql",
  "cloud_provider": "aws",
  "required_security_scans": ["sast"],
  "other_requirements": "None"
}
```

### Example 2: Generating Basic Terraform (Conceptual)

**Goal:** Once entities are extracted, generate basic Terraform HCL. (This will be a more complex chain, likely involving intermediate steps or more detailed prompts).

**Simplified Prompt Snippet (Illustrative):**

```
You are an expert Terraform configuration generator. Based on the following requirements, generate a basic Terraform HCL configuration for deploying an EC2 instance on AWS.

Requirements:
- Instance Type: t3.micro
- AMI: Latest Amazon Linux 2
- Region: us-east-1
- Tags: { Name = "MyWebAppInstance", Environment = "Dev" }

Generate the HCL code for the aws_instance resource.
```

**Note:** Generating full, correct, and secure IaC will require much more sophisticated prompting, including providing the LLM with templates, specific module information, and potentially a series of chained prompts for different components (VPC, Subnets, Security Groups, DB instances, EC2/ECS/Lambda).

### Example 3: Generating Basic CI/CD Pipeline YAML (Conceptual)

**Goal:** Generate a basic GitHub Actions YAML file.

**Simplified Prompt Snippet (Illustrative):**

```
You are an expert GitHub Actions workflow generator. Create a basic YAML configuration for a Python application with the following stages:
1. Checkout code.
2. Set up Python environment.
3. Install dependencies from requirements.txt.
4. Run SAST scan using Bandit.
5. (Placeholder for Deploy step)

The trigger should be on push to the 'main' branch.
```

### Next Steps for Prompt Development:

-   Develop more detailed prompts for each agent (IaC, Pipeline).
-   Incorporate error handling and validation logic in the prompts (e.g., asking for clarification if input is ambiguous).
-   Experiment with temperature and other LLM parameters to control creativity vs. determinism.
-   Build a library of prompt templates.
-   Test extensively with a variety of user inputs.
```

## Approach for Intent Recognition and Entity Extraction (Task 2.1.3 - Initial Design)

This section details the planned approach for recognizing user intent and extracting key entities from their natural language input. This is a critical first step in the AI Orchestration Layer, transforming free-form text into a structured representation that downstream agents can act upon.

### Methodology

The primary method for intent recognition and entity extraction will be through carefully crafted prompts directed at the selected Large Language Model (LLM), Claude 3 Sonnet. The process will be as follows:

1.  **Input Processing:**
    *   The user's natural language query (e.g., "Deploy a Python web app with PostgreSQL on AWS, include SAST") will be taken as direct input.
    *   Minimal pre-processing might be applied (e.g., trimming whitespace), but the goal is to handle raw natural language effectively.

2.  **LLM-Powered Extraction:**
    *   A specific prompt, like the "Intent Recognition and Entity Extraction" example detailed in the "Initial Prompt Engineering Design" section (Task 2.1.2), will be used.
    *   This prompt instructs the LLM to act as an expert system, identify predefined categories of information, and return them in a structured JSON format.

3.  **Key Entities to Extract (MVP Focus):**
    *   **Core Application Details:**
        *   `application_type`: (e.g., "python_flask_webapp", "nodejs_express_api", "static_website")
        *   `programming_language`: (e.g., "python", "javascript", "java")
    *   **Data Services:**
        *   `database_type`: (e.g., "postgresql", "mysql", "mongodb", "none")
    *   **Deployment Target:**
        *   `cloud_provider`: (Primarily "aws" for MVP, but designed to recognize others like "azure", "gcp")
    *   **Security Requirements:**
        *   `required_security_scans`: (List of scan types, e.g., ["sast", "dast", "sca"])
    *   **Other Specifics:**
        *   `other_requirements`: A field to capture any additional specific requests made by the user that don't fit predefined categories.

4.  **Structured Output (JSON):**
    *   The LLM will be explicitly instructed to return the extracted information as a JSON object. This structured format is crucial for:
        *   **Consistency:** Ensuring data is always in a predictable format.
        *   **Ease of Use:** Allowing backend services (AI Orchestration Layer) to easily parse and utilize this information.
        *   **Validation:** Enabling programmatic validation of the extracted entities.

5.  **Iterative Refinement and Validation:**
    *   The prompts and the list of entities will be iteratively refined based on testing with diverse user inputs.
    *   The AI Orchestration Layer will include logic to validate the JSON output from the LLM. This might involve:
        *   Checking for the presence of mandatory fields.
        *   Validating data types.
        *   For MVP, if critical information is missing or ambiguous, the system might initially default to sensible choices or (in later phases) prompt the user for clarification.

### Example Workflow:

1.  **User Input:** "I need a Go microservice that uses a Redis cache, deployed on AWS. Please add SAST to the pipeline."
2.  **AI Orchestration Layer sends to LLM with Entity Extraction Prompt.**
3.  **LLM Returns JSON:**
    ```json
    {
      "application_type": "go_microservice",
      "programming_language": "go",
      "database_type": "redis", // Or perhaps a new category like "caching_service"
      "cloud_provider": "aws",
      "required_security_scans": ["sast"],
      "other_requirements": "None"
    }
    ```
4.  **AI Orchestration Layer validates and uses this JSON** to trigger subsequent agents (Infrastructure Agent, Pipeline Agent).

This approach leverages the LLM's advanced language understanding capabilities to perform the initial, often challenging, step of converting unstructured user requests into actionable, structured data. The quality of this step directly impacts the effectiveness of all subsequent automation.
