import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
from typing import List, Optional, Dict

# New imports for HCL validation endpoint
import tempfile
import subprocess
import shutil

# Initialize FastAPI app
app = FastAPI()

# --- LLM Integration for Intent Parsing ---

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
    prompt = PROMPT_TEMPLATE.replace("{{user_request}}", request.query, 1)
    prompt = prompt.replace("{{user_request}}", request.query, 1)

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        if response.content and response.content[0].text:
            raw_json_output = response.content[0].text
            if raw_json_output.startswith("```json"):
                raw_json_output = raw_json_output[len("```json"):]
            if raw_json_output.endswith("```"):
                raw_json_output = raw_json_output[:-len("```")]
            raw_json_output = raw_json_output.strip()
            try:
                return json.loads(raw_json_output)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=500, detail=f"Failed to parse JSON from LLM: {str(e)}. Response: {raw_json_output}")
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

class IaCResponse(BaseModel):
    hcl_code: str
    message: Optional[str] = None

@app.post("/api/v1/infra-agent/generate-iac", response_model=IaCResponse)
async def generate_iac(intent_data: ParsedIntentInput):
    hcl_string = ""
    message = "Successfully generated HCL."
    if not intent_data.cloud_provider:
        hcl_string = "# Cloud provider info missing."
        message = "Failed: Cloud provider info missing."
        return IaCResponse(hcl_code=hcl_string, message=message)

    cloud_provider_lower = intent_data.cloud_provider.lower()
    if cloud_provider_lower == "aws":
        if intent_data.application_type:
            ami_example = "ami-0c55b31ad2c5695c5"
            instance_type_example = "t2.micro"
            project_name_tag_base = intent_data.application_type.lower().replace("_", "-").replace(" ", "-")
            project_name_tag = "".join(c if c.isalnum() or c in ['-', '_'] else '' for c in project_name_tag_base).strip('-') or "app"
            
            hcl_string = f'''provider "aws" {{
  region = "us-east-1"
}}

resource "aws_security_group" "sg_{project_name_tag}" {{
  name        = "sg-{project_name_tag}"
  description = "Allow SSH and HTTP for {project_name_tag}"
  ingress {{
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }}
  ingress {{
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }}
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }}
  tags = {{ Name = "sg-{project_name_tag}", ManagedBy = "AI-DevSecOps-Platform" }}
}}

resource "aws_instance" "server_{project_name_tag}" {{
  ami           = "{ami_example}"
  instance_type = "{instance_type_example}"
  vpc_security_group_ids = [aws_security_group.sg_{project_name_tag}.id]
  tags = {{
    Name        = "WebAppServer-{project_name_tag}"
    Application = "{intent_data.application_type}"
    Database    = "{intent_data.database_type if intent_data.database_type else "none"}"
    ManagedBy   = "AI-DevSecOps-Platform"
  }}
}}
'''
        else:
            message = "Partial HCL: No app type for AWS."
            hcl_string = '''provider "aws" {\n  region = "us-east-1"\n}\n# App type needed for instance/SG.'''
    elif cloud_provider_lower in ["azure", "gcp"]:
        message = f"IaC for {intent_data.cloud_provider} not implemented. Placeholder provider generated."
        hcl_string = f'''provider "{cloud_provider_lower}" {{
  # region = "..." 
}}\n# {intent_data.cloud_provider.upper()} resources here.'''
    else:
        message = f"Failed: Cloud provider '{intent_data.cloud_provider}' not recognized/supported."
        hcl_string = f"# Cloud provider '{intent_data.cloud_provider}' not recognized."
    return IaCResponse(hcl_code=hcl_string, message=message)

# --- HCL Validation and Apply Agent ---

class HCLContentRequest(BaseModel): # Generic request for HCL code
    hcl_code: str

class TerraformCommandOutput(BaseModel):
    command: str
    stdout: str
    stderr: str
    exit_code: int

class HCLValidationResponse(BaseModel):
    validation_passed: bool
    init_output: Optional[TerraformCommandOutput] = None
    validate_output: Optional[TerraformCommandOutput] = None
    message: Optional[str] = None

class HCLApplyResponse(BaseModel):
    apply_successful: bool
    init_output: Optional[TerraformCommandOutput] = None # Optional in case of early failure
    apply_output: Optional[TerraformCommandOutput] = None # Optional in case init fails
    message: Optional[str] = None


def _run_terraform_command(command: List[str], working_dir: str) -> TerraformCommandOutput:
    try:
        process = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=False 
        )
        return TerraformCommandOutput(
            command=" ".join(command),
            stdout=process.stdout.strip(),
            stderr=process.stderr.strip(),
            exit_code=process.returncode
        )
    except FileNotFoundError:
        return TerraformCommandOutput(
            command=" ".join(command),
            stdout="",
            stderr=f"Error: Command '{command[0]}' not found. Ensure Terraform is installed and in PATH.",
            exit_code=127
        )
    except Exception as e:
         return TerraformCommandOutput(
            command=" ".join(command),
            stdout="",
            stderr=f"An unexpected error occurred while running command: {str(e)}",
            exit_code=1 
        )

@app.post("/api/v1/infra-agent/validate-hcl", response_model=HCLValidationResponse)
def validate_hcl_code(request: HCLContentRequest): # Changed to use HCLContentRequest
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        main_tf_path = os.path.join(temp_dir, "main.tf")
        with open(main_tf_path, "w") as f:
            f.write(request.hcl_code)

        init_command = ["terraform", "init", "-input=false", "-no-color"]
        init_output = _run_terraform_command(init_command, temp_dir)

        if init_output.exit_code != 0:
            return HCLValidationResponse(
                validation_passed=False,
                init_output=init_output,
                message=f"Terraform init failed. Errors: {init_output.stderr}"
            )

        validate_command = ["terraform", "validate", "-no-color", "-json"]
        validate_output = _run_terraform_command(validate_command, temp_dir)
        
        validation_passed = False
        validation_message = "Terraform validation output processed."

        if validate_output.exit_code == 0:
            try:
                validate_json = json.loads(validate_output.stdout)
                if validate_json.get("valid", False):
                    validation_passed = True
                    validation_message = "Terraform validation successful."
                else:
                    error_count = validate_json.get("error_count", 0)
                    warning_count = validate_json.get("warning_count", 0)
                    if error_count > 0:
                         validation_message = f"Terraform validation failed with {error_count} errors."
                    elif warning_count > 0:
                        validation_message = f"Terraform validation passed with {warning_count} warnings."
                        validation_passed = True 
                    else:
                        validation_message = "Validation reported not valid, but no errors/warnings in JSON."
            except json.JSONDecodeError:
                validation_message = "Validation output was not valid JSON. Check stderr."
        else: 
            validation_message = f"Validate command failed. Exit: {validate_output.exit_code}. Errors: {validate_output.stderr}"
            
        return HCLValidationResponse(
            validation_passed=validation_passed,
            init_output=init_output,
            validate_output=validate_output,
            message=validation_message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.post("/api/v1/infra-agent/apply-hcl", response_model=HCLApplyResponse)
def apply_hcl_code(request: HCLContentRequest): # Changed to use HCLContentRequest
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        main_tf_path = os.path.join(temp_dir, "main.tf")
        with open(main_tf_path, "w") as f:
            f.write(request.hcl_code)

        init_command = ["terraform", "init", "-input=false", "-no-color"]
        init_output = _run_terraform_command(init_command, temp_dir)

        if init_output.exit_code != 0:
            # Create a placeholder for apply_output if init fails
            placeholder_apply_output = TerraformCommandOutput(
                command="terraform apply (not executed due to init failure)",
                stdout="",
                stderr="Init failed, apply not attempted.",
                exit_code=-1 
            )
            return HCLApplyResponse(
                apply_successful=False,
                init_output=init_output,
                apply_output=placeholder_apply_output,
                message=f"Terraform init failed. Apply not attempted. Errors: {init_output.stderr}"
            )

        # Run terraform apply
        apply_command = ["terraform", "apply", "-auto-approve", "-input=false", "-no-color"]
        apply_output = _run_terraform_command(apply_command, temp_dir)

        apply_successful = apply_output.exit_code == 0
        message = f"Terraform apply {'completed successfully' if apply_successful else 'failed or had errors'}."
        if not apply_successful and apply_output.stderr:
            message += f" Errors: {apply_output.stderr}"
        elif not apply_successful and apply_output.stdout: # Sometimes errors go to stdout for apply
             message += f" Details: {apply_output.stdout}"


        return HCLApplyResponse(
            apply_successful=apply_successful,
            init_output=init_output,
            apply_output=apply_output,
            message=message
        )
    except Exception as e:
        # For unexpected errors in this endpoint's logic
        # Log e for server-side details
        # Create dummy/error outputs if they are not set due to early exception
        dummy_init_output = TerraformCommandOutput(command="terraform init", stdout="", stderr=str(e), exit_code=-2)
        dummy_apply_output = TerraformCommandOutput(command="terraform apply", stdout="", stderr=str(e), exit_code=-2)
        # It's better to raise HTTPException for endpoint errors than returning a HCLApplyResponse with error state
        # as the error is not from Terraform but from the service itself.
        raise HTTPException(status_code=500, detail=f"An internal server error occurred during HCL apply process: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

# --- Root and Health Endpoints ---

@app.get("/")
async def root():
    return {"message": "AI Orchestration Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
