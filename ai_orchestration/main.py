import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
from typing import List, Optional, Dict

import tempfile
import subprocess
import shutil
import re # For sanitization
import random # For Azure name suffix
import string # For Azure name suffix

# Initialize FastAPI app
app = FastAPI()

# --- Sanitization Helper ---
def sanitize_resource_name(name: str, cloud_provider: str, resource_type: str = "default") -> str:
    name_lower = name.lower()
    
    if cloud_provider == "aws":
        if resource_type == "s3_bucket":
            # AWS S3: 3-63 chars, no uppercase, no underscores (can use hyphens), not IP address format
            # Must start and end with a letter or number.
            sanitized = re.sub(r'[^a-z0-9-]', '-', name_lower)
            sanitized = re.sub(r'-+', '-', sanitized)
            sanitized = sanitized.strip('-')
            if not re.match(r'^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$', sanitized): # Check start/end and length
                 # If complex sanitization fails, generate a simpler valid name
                return f"bucket-{os.urandom(4).hex()}"
            return sanitized[:63]
        else: # General AWS resource (e.g., for tags, SG names)
            sanitized = re.sub(r'[^a-zA-Z0-9_.:/=+\-@]', '-', name) # Allowed AWS tag chars + common resource name chars
            sanitized = re.sub(r'-+', '-', sanitized)
            return sanitized.strip('-')[:255]

    elif cloud_provider == "azure":
        if resource_type == "storage_account":
            # Azure Storage Account: 3-24 chars, lowercase letters and numbers only. Globally unique.
            sanitized = re.sub(r'[^a-z0-9]', '', name_lower)
            sanitized = sanitized[:18] # Max 18 to leave room for 6 char random suffix
            if len(sanitized) < 3: # Ensure base name is at least somewhat meaningful or long enough
                sanitized = f"sa{sanitized}" # Prepend if too short
            while len(sanitized) < 3:
                sanitized += random.choice(string.ascii_lowercase + string.digits)
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            return f"{sanitized}{suffix}"
        elif resource_type == "storage_container":
             # Azure Storage Container: 3-63 chars, lowercase letters, numbers, and hyphens. Must start/end with letter/number. No consecutive hyphens.
            sanitized = re.sub(r'[^a-z0-9-]', '-', name_lower)
            sanitized = re.sub(r'-+', '-', sanitized)
            sanitized = sanitized.strip('-')
            if not re.match(r'^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$', sanitized):
                return f"container-{os.urandom(4).hex()}"
            return sanitized[:63]
        else: # General Azure resource (e.g., RG name)
            sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '-', name)
            sanitized = re.sub(r'-+', '-', sanitized)
            return sanitized.strip('-')[:90]


    elif cloud_provider == "gcp":
        if resource_type == "gcs_bucket":
            # GCP GCS Bucket: 3-63 chars, lowercase alphanumeric, underscores, hyphens, dots.
            # Globally unique. Cannot start/end with dot. Cannot contain 'google' or 'goog'.
            # For simplicity, we'll stick to lowercase alphanumeric and hyphens.
            sanitized = re.sub(r'[^a-z0-9-]', '-', name_lower)
            sanitized = re.sub(r'-+', '-', sanitized)
            sanitized = sanitized.strip('-')
            # Avoid 'google' or 'goog' and starting with 'gcs-' which can be problematic
            if "google" in sanitized or "goog" in sanitized or sanitized.startswith("gcs-"):
                 sanitized = f"gcp-bucket-{os.urandom(4).hex()}" # fallback
            if not re.match(r'^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$', sanitized):
                return f"gcp-bucket-{os.urandom(4).hex()}"
            return sanitized[:63]
        else: # General GCP resource
            sanitized = re.sub(r'[^a-z0-9-]', '-', name_lower) # Often lowercase alphanumeric and hyphens
            sanitized = re.sub(r'-+', '-', sanitized)
            return sanitized.strip('-')[:63]
            
    # Default fallback if cloud provider not matched
    return re.sub(r'[^a-zA-Z0-9-]', '-', name_lower).strip('-')[:63]


# --- LLM Integration for Intent Parsing ---
PROMPT_TEMPLATE = """
You are an expert DevSecOps platform assistant. Your task is to parse the user's natural language request and extract key information to define a new application deployment project.
The user's request is:
"""
{{user_request}}
"""

Extract the following information and return it as a JSON object:
- "application_type": (e.g., "python_flask_webapp", "nodejs_express_api", "static_website", "java_spring_service", "none" if just a resource request)
- "programming_language": (e.g., "python", "javascript", "java", "go", "none")
- "database_type": (e.g., "postgresql", "mysql", "mongodb", "none")
- "cloud_provider": (e.g., "aws", "azure", "gcp")
- "resource_type": (e.g., "ec2_instance", "storage_bucket", "kubernetes_cluster", "serverless_function")
- "resource_name": (the desired name for the primary resource, e.g., bucket name, instance name)
- "region": (the desired cloud region, e.g., "us-east-1", "East US", "europe-west1")
- "required_security_scans": (list of strings, e.g., ["sast", "dast", "sca"])
- "other_requirements": (any other specific user requests or details)

Examples:
User Request: "Deploy a Node.js Express API with a MongoDB database on Azure in West US. I need SAST and DAST."
Expected JSON Output:
{
  "application_type": "nodejs_express_api",
  "programming_language": "javascript",
  "database_type": "mongodb",
  "cloud_provider": "azure",
  "resource_type": "nodejs_express_api", 
  "resource_name": "my-node-app", 
  "region": "West US",
  "required_security_scans": ["sast", "dast"],
  "other_requirements": "None"
}

User Request: "Create an AWS S3 bucket named my-photo-storage-bucket in us-east-1."
Expected JSON Output:
{
  "application_type": "none",
  "programming_language": "none",
  "database_type": "none",
  "cloud_provider": "aws",
  "resource_type": "storage_bucket",
  "resource_name": "my-photo-storage-bucket",
  "region": "us-east-1",
  "required_security_scans": [],
  "other_requirements": "None"
}

User Request: "I need a new Azure blob storage container called 'my-azure-backup-data' in East US."
Expected JSON Output:
{
  "application_type": "none",
  "programming_language": "none",
  "database_type": "none",
  "cloud_provider": "azure",
  "resource_type": "storage_bucket", 
  "resource_name": "my-azure-backup-data",
  "region": "East US",
  "required_security_scans": [],
  "other_requirements": "None"
}

User Request: "Make a Google Cloud Storage bucket. Call it 'gcp-project-artifacts'. Use us-central1."
Expected JSON Output:
{
  "application_type": "none",
  "programming_language": "none",
  "database_type": "none",
  "cloud_provider": "gcp",
  "resource_type": "storage_bucket",
  "resource_name": "gcp-project-artifacts",
  "region": "us-central1",
  "required_security_scans": [],
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
    prompt_filled = PROMPT_TEMPLATE.replace("{{user_request}}", request.query, 1)
    prompt_filled = prompt_filled.replace("{{user_request}}", request.query, 1)  

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229", max_tokens=1024,
            messages=[{"role": "user", "content": prompt_filled}]
        )
        if response.content and response.content[0].text:
            raw_json_output = response.content[0].text
            if raw_json_output.startswith("```json"): raw_json_output = raw_json_output[len("```json"):]
            if raw_json_output.endswith("```"): raw_json_output = raw_json_output[:-len("```")]
            raw_json_output = raw_json_output.strip()
            try: return json.loads(raw_json_output)
            except json.JSONDecodeError as e: raise HTTPException(status_code=500, detail=f"LLM JSON parse error: {e}. Response: {raw_json_output}")
        else: raise HTTPException(status_code=500, detail="LLM no valid content.")
    except anthropic.APIError as e: raise HTTPException(status_code=500, detail=f"Anthropic API Error: {e}")
    except Exception as e: raise HTTPException(status_code=500, detail=f"LLM call error: {e}")

# --- Basic Infrastructure Agent ---

class ParsedIntentInput(BaseModel):
    application_type: Optional[str] = None
    programming_language: Optional[str] = None
    database_type: Optional[str] = None
    cloud_provider: Optional[str] = None
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    region: Optional[str] = None
    required_security_scans: Optional[List[str]] = []
    other_requirements: Optional[str] = None

class IaCResponse(BaseModel):
    hcl_code: str
    message: Optional[str] = None

@app.post("/api/v1/infra-agent/generate-iac", response_model=IaCResponse)
async def generate_iac(intent_data: ParsedIntentInput):
    hcl_string = ""
    message = "IaC generation request processed."
    provider_region = "" # To store resolved region

    if not intent_data.cloud_provider:
        return IaCResponse(hcl_code="# Cloud provider info missing.", message="Failed: Cloud provider info missing.")

    cloud_provider_lower = intent_data.cloud_provider.lower()
    resource_name_original = intent_data.resource_name if intent_data.resource_name else "default-resource"
    
    if cloud_provider_lower == "aws":
        provider_region = intent_data.region if intent_data.region else "us-east-1"
        message += f" Using AWS region: {provider_region}."
        
        if intent_data.resource_type == "storage_bucket":
            bucket_name = sanitize_resource_name(resource_name_original, "aws", "s3_bucket")
            hcl_string = f'''variable "aws_region" {{
  description = "AWS region for resources"
  type        = string
  default     = "{provider_region}"
}}

provider "aws" {{
  region = var.aws_region
}}

resource "aws_s3_bucket" "{bucket_name}" {{
  bucket = "{bucket_name}"
  # acl    = "private" # ACL is deprecated for new buckets, use bucket policy and block public access instead for fine-grained control.

  versioning {{
    enabled = true
  }}

  # Recommended: Block all public access by default
  # aws_s3_bucket_public_access_block can be used for more granular control.
  # For simplicity, not adding it here but highly recommended for real buckets.

  tags = {{
    Name      = "{resource_name_original}" # User-provided name for tag
    BucketName = "{bucket_name}" # Sanitized name
    ManagedBy = "AI-DevSecOps-Platform"
  }}
}}
'''
            message = f"Successfully generated HCL for AWS S3 Bucket '{bucket_name}' in region '{provider_region}'."
        
        elif intent_data.application_type and intent_data.application_type != "none":
            app_name_sanitized = sanitize_resource_name(intent_data.application_type, "aws", "ec2_instance_prefix")
            ami_example = "ami-0c55b31ad2c5695c5" # Example, should be region-specific
            instance_type_example = "t2.micro"
            hcl_string = f'''variable "aws_region" {{
  description = "AWS region for resources"
  type        = string
  default     = "{provider_region}"
}}

provider "aws" {{
  region = var.aws_region
}}

resource "aws_security_group" "sg_{app_name_sanitized}" {{
  name        = "sg-{app_name_sanitized}"
  description = "Allow SSH and HTTP for {app_name_sanitized}"
  ingress {{
    from_port   = 22; to_port = 22; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; ipv6_cidr_blocks = ["::/0"];
  }}
  ingress {{
    from_port   = 80; to_port = 80; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"]; ipv6_cidr_blocks = ["::/0"];
  }}
  egress {{
    from_port   = 0; to_port = 0; protocol = "-1"; cidr_blocks = ["0.0.0.0/0"]; ipv6_cidr_blocks = ["::/0"];
  }}
  tags = {{ Name = "sg-{app_name_sanitized}", ManagedBy = "AI-DevSecOps-Platform" }}
}}

resource "aws_instance" "server_{app_name_sanitized}" {{
  ami           = "{ami_example}"
  instance_type = "{instance_type_example}"
  vpc_security_group_ids = [aws_security_group.sg_{app_name_sanitized}.id]
  tags = {{
    Name        = "WebAppServer-{app_name_sanitized}"
    Application = "{intent_data.application_type}"
    ManagedBy   = "AI-DevSecOps-Platform"
  }}
}}
'''
            message = f"Successfully generated HCL for AWS EC2 Instance and Security Group in region '{provider_region}'."
        else:
            message = f"AWS: Resource type '{intent_data.resource_type}' or application type '{intent_data.application_type}' not fully supported for HCL generation. Basic provider block generated for region '{provider_region}'."
            hcl_string = f'''variable "aws_region" {{ default = "{provider_region}" }}\nprovider "aws" {{ region = var.aws_region }}'''

    elif cloud_provider_lower == "azure":
        provider_region = intent_data.region if intent_data.region else "East US"
        message += f" Using Azure region: {provider_region}."
        
        if intent_data.resource_type == "storage_bucket":
            storage_account_name = sanitize_resource_name(resource_name_original, "azure", "storage_account")
            container_name = sanitize_resource_name(resource_name_original, "azure", "storage_container") # Or a fixed name like 'default'
            rg_name = f"rg-{storage_account_name}" # Resource group name

            hcl_string = f'''variable "azure_location" {{
  description = "Azure region for resources"
  type        = string
  default     = "{provider_region}"
}}

provider "azurerm" {{
  features {{}}
  # Ensure Azure CLI login or Service Principal env vars are set for auth
}}

resource "azurerm_resource_group" "main" {{
  name     = "{rg_name}"
  location = var.azure_location
  tags = {{
    ManagedBy = "AI-DevSecOps-Platform"
  }}
}}

resource "azurerm_storage_account" "main" {{
  name                     = "{storage_account_name}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS" # Locally-redundant storage

  tags = {{
    Name      = "{resource_name_original}"
    AccountName = "{storage_account_name}"
    ManagedBy = "AI-DevSecOps-Platform"
  }}
}}

resource "azurerm_storage_container" "main" {{
  name                  = "{container_name}"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private" 
  
  # depends_on = [azurerm_storage_account.main] # Implicit dependency
}}
'''
            message = f"Successfully generated HCL for Azure Storage Account '{storage_account_name}' and Container '{container_name}' in region '{provider_region}'."
        else:
            message = f"Azure: Resource type '{intent_data.resource_type}' not fully supported. Basic provider block generated for region '{provider_region}'."
            hcl_string = f'''variable "azure_location" {{ default = "{provider_region}" }}\nprovider "azurerm" {{ features {{}} \n  # location = var.azure_location \n}}'''
            
    elif cloud_provider_lower == "gcp":
        gcp_project_id = os.getenv("GCP_PROJECT_ID")
        if not gcp_project_id:
            return IaCResponse(hcl_code="# GCP_PROJECT_ID environment variable not set. Cannot generate GCP HCL.", 
                               message="Error: GCP_PROJECT_ID environment variable must be set for GCP IaC generation.")
        
        provider_region = intent_data.region if intent_data.region else "us-central1"
        message += f" Using GCP region: {provider_region} and Project ID: {gcp_project_id}."

        if intent_data.resource_type == "storage_bucket":
            bucket_name = sanitize_resource_name(resource_name_original, "gcp", "gcs_bucket")
            hcl_string = f'''variable "gcp_project_id" {{
  description = "GCP Project ID"
  type        = string
  default     = "{gcp_project_id}"
}}

variable "gcp_region" {{
  description = "GCP region for resources"
  type        = string
  default     = "{provider_region}"
}}

provider "google" {{
  project = var.gcp_project_id
  region  = var.gcp_region
  # Ensure GOOGLE_APPLICATION_CREDENTIALS env var is set for auth
}}

resource "google_storage_bucket" "{bucket_name}" {{
  name                        = "{bucket_name}" # Must be globally unique
  location                    = var.gcp_region # Or specific like "US-CENTRAL1" for GCS standard locations
  uniform_bucket_level_access = true
  storage_class               = "STANDARD"

  versioning {{
    enabled = true
  }}

  labels = {{
    name        = "{resource_name_original}"
    bucket_name = "{bucket_name}" # Sanitized name
    managed_by  = "ai-devsecops-platform"
  }}
}}
'''
            message = f"Successfully generated HCL for GCP Storage Bucket '{bucket_name}' in region '{provider_region}' (Project: {gcp_project_id})."
        else:
            message = f"GCP: Resource type '{intent_data.resource_type}' not fully supported. Basic provider block generated for region '{provider_region}' and project '{gcp_project_id}'."
            hcl_string = f'''variable "gcp_project_id" {{ default = "{gcp_project_id}" }}\nvariable "gcp_region" {{ default = "{provider_region}" }}\nprovider "google" {{\n  project = var.gcp_project_id\n  region = var.gcp_region\n}}'''
    else:
        message = f"Cloud provider '{intent_data.cloud_provider}' not recognized/supported for IaC."
        hcl_string = f"# Cloud provider '{intent_data.cloud_provider}' not recognized."
        
    return IaCResponse(hcl_code=hcl_string.strip(), message=message)

# --- HCL Validation and Apply Agent ---
class HCLContentRequest(BaseModel): hcl_code: str
class TerraformCommandOutput(BaseModel): command: str; stdout: str; stderr: str; exit_code: int
class HCLValidationResponse(BaseModel): validation_passed: bool; init_output: Optional[TerraformCommandOutput]=None; validate_output: Optional[TerraformCommandOutput]=None; message: Optional[str]=None
class HCLApplyResponse(BaseModel): apply_successful: bool; init_output: Optional[TerraformCommandOutput]=None; apply_output: Optional[TerraformCommandOutput]=None; message: Optional[str]=None

def _run_terraform_command(command: List[str], wd: str) -> TerraformCommandOutput:
    try:
        p = subprocess.run(command, cwd=wd, capture_output=True, text=True, check=False)
        return TerraformCommandOutput(command=" ".join(p.args), stdout=p.stdout.strip(), stderr=p.stderr.strip(), exit_code=p.returncode)
    except FileNotFoundError: return TerraformCommandOutput(command=" ".join(command), stdout="", stderr=f"Err: Cmd '{command[0]}' not found.", exit_code=127)
    except Exception as e: return TerraformCommandOutput(command=" ".join(command), stdout="", stderr=f"Unexpected err: {e}", exit_code=1)

@app.post("/api/v1/infra-agent/validate-hcl", response_model=HCLValidationResponse)
def validate_hcl_code(request: HCLContentRequest):
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir, "main.tf"), "w") as f: f.write(request.hcl_code)
        init_out = _run_terraform_command(["terraform", "init", "-input=false", "-no-color"], tmpdir)
        if init_out.exit_code != 0: return HCLValidationResponse(validation_passed=False, init_output=init_out, message=f"Init fail: {init_out.stderr}")
        val_out = _run_terraform_command(["terraform", "validate", "-no-color", "-json"], tmpdir)
        passed, msg = False, "Validation output processed."
        if val_out.exit_code == 0:
            try:
                val_json = json.loads(val_out.stdout)
                if val_json.get("valid", False):
                    passed=True; msg=f"Validation successful." + (f" Warnings: {val_json.get('warning_count',0)}" if val_json.get('warning_count',0)>0 else "")
                else: msg=f"Validation failed: {val_json.get('error_count',0)} errors."
            except json.JSONDecodeError: msg="Validation output not JSON."
        else: msg=f"Validate cmd fail. Exit: {val_out.exit_code}. Err: {val_out.stderr}"
        return HCLValidationResponse(validation_passed=passed, init_output=init_out, validate_output=val_out, message=msg)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: 
        if tmpdir and os.path.exists(tmpdir): shutil.rmtree(tmpdir)

@app.post("/api/v1/infra-agent/apply-hcl", response_model=HCLApplyResponse)
def apply_hcl_code(request: HCLContentRequest):
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir, "main.tf"), "w") as f: f.write(request.hcl_code)
        init_out = _run_terraform_command(["terraform", "init", "-input=false", "-no-color"], tmpdir)
        if init_out.exit_code != 0:
            return HCLApplyResponse(apply_successful=False, init_output=init_out, 
                                    apply_output=TerraformCommandOutput(command="tf apply (not executed)", stdout="", stderr="Init failed", exit_code=-1),
                                    message=f"Init failed. Apply not attempted. Err: {init_out.stderr}")
        apply_out = _run_terraform_command(["terraform", "apply", "-auto-approve", "-input=false", "-no-color"], tmpdir)
        ok = apply_out.exit_code == 0
        msg = f"Apply {'succeeded' if ok else 'failed'}. " + (apply_out.stderr if apply_out.stderr and not ok else (apply_out.stdout if not ok else ""))
        return HCLApplyResponse(apply_successful=ok, init_output=init_out, apply_output=apply_out, message=msg.strip())
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: 
        if tmpdir and os.path.exists(tmpdir): shutil.rmtree(tmpdir)

# --- Root and Health Endpoints ---
@app.get("/")
async def root(): return {"message": "AI Orchestration Service is running"}
@app.get("/health")
async def health_check(): return {"status": "ok"}
