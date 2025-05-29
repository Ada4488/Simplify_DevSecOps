import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
from typing import List, Optional, Dict # Added

# Initialize FastAPI app
app = FastAPI()

# --- LLM Integration for Intent Parsing ---

# Construct the prompt template from the document
PROMPT_TEMPLATE = """
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
{{user_request}}
"""

Return ONLY the JSON object.
"""

class NLPQueryRequest(BaseModel):
    query: str

@app.post("/api/v1/orchestration/parse-intent")
async def parse_intent(request: NLPQueryRequest):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)

    # Replace placeholder with actual user query - first occurrence
    prompt = PROMPT_TEMPLATE.replace("{{user_request}}", request.query, 1)
    # Replace placeholder with actual user query - second occurrence
    prompt = prompt.replace("{{user_request}}", request.query, 1)

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        if response.content and len(response.content) > 0 and response.content[0].text:
            raw_json_output = response.content[0].text
            
            if raw_json_output.startswith("```json"):
                raw_json_output = raw_json_output[len("```json"):]
            if raw_json_output.endswith("```"):
                raw_json_output = raw_json_output[:-len("```")]
            raw_json_output = raw_json_output.strip()
            
            try:
                return json.loads(raw_json_output)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=500, detail=f"Failed to parse JSON from LLM response: {str(e)}. Response was: {raw_json_output}")
        else:
            raise HTTPException(status_code=500, detail="Failed to get valid content from LLM.")

    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"Anthropic API Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {str(e)}")

# --- Basic Infrastructure Agent ---

class ParsedIntentInput(BaseModel):
    application_type: Optional[str] = None
    programming_language: Optional[str] = None
    database_type: Optional[str] = None
    cloud_provider: Optional[str] = None
    required_security_scans: Optional[List[str]] = []
    other_requirements: Optional[str] = None
    # Making required_security_scans default to empty list for safety

class IaCResponse(BaseModel):
    hcl_code: str
    message: Optional[str] = None

@app.post("/api/v1/infra-agent/generate-iac", response_model=IaCResponse)
async def generate_iac(intent_data: ParsedIntentInput):
    hcl_string = ""
    message = "Successfully generated HCL."

    if not intent_data.cloud_provider:
        hcl_string = "# Cloud provider information is missing. Cannot generate IaC."
        message = "Failed to generate HCL: Cloud provider information is missing."
        # For critical missing info, consider raising HTTPException
        # raise HTTPException(status_code=400, detail="Cloud provider information is mandatory for IaC generation.")
        return IaCResponse(hcl_code=hcl_string, message=message)

    cloud_provider_lower = intent_data.cloud_provider.lower()

    if cloud_provider_lower == "aws":
        if intent_data.application_type:
            # Example AMI (Amazon Linux 2 in us-east-1) - should be configured or dynamically chosen
            ami_example = "ami-0c55b31ad2c5695c5" 
            instance_type_example = "t2.micro"
            # Basic naming convention for the tag from application_type
            project_name_tag = intent_data.application_type.replace("_", "-").replace(" ", "-")

            hcl_string = f'''provider "aws" {{
  region = "us-east-1" # Example region, should ideally come from user input or config
}}

resource "aws_instance" "web_app_server" {{
  ami           = "{ami_example}"
  instance_type = "{instance_type_example}"

  tags = {{
    Name        = "WebAppServer-{project_name_tag}"
    Application = "{intent_data.application_type}"
    Database    = "{intent_data.database_type if intent_data.database_type else "none"}"
    ManagedBy   = "AI-DevSecOps-Platform"
  }}
}}

# Note: This is a minimal example. A real server would need
# security groups, networking (VPC, subnets), IAM roles, 
# key pairs for access, user data for bootstrapping, etc.
# If a database like '{intent_data.database_type}' is requested, 
# it would need its own resource block (e.g., aws_db_instance for RDS).
'''
        else:
            hcl_string = "# No specific application type provided for AWS, but generating generic provider block."
            message = "Partial HCL generation: No specific application type provided for AWS."
            hcl_string = '''provider "aws" {
  region = "us-east-1" # Example region
}

# Add AWS resources here based on further details.
'''
    elif cloud_provider_lower in ["azure", "gcp"]:
        hcl_string = f"""# IaC Generation for cloud provider '{intent_data.cloud_provider}' is not yet implemented.
# Basic provider block for {intent_data.cloud_provider.upper()} (conceptual)
provider "{cloud_provider_lower}" {{
  # {cloud_provider_lower}-specific attributes like region, project_id, etc. would go here
  # region = "..."
}}
"""
        message = f"IaC Generation for cloud provider '{intent_data.cloud_provider}' is not yet implemented. Placeholder provider generated."
    else:
        hcl_string = f"# Cloud provider '{intent_data.cloud_provider}' is not recognized or supported for IaC generation at this time."
        message = f"Failed to generate HCL: Cloud provider '{intent_data.cloud_provider}' is not recognized or supported."

    return IaCResponse(hcl_code=hcl_string, message=message)


# --- Root and Health Endpoints ---

@app.get("/")
async def root():
    return {"message": "AI Orchestration Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
