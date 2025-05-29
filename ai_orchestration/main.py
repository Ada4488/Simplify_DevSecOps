import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic

# Initialize FastAPI app
app = FastAPI()

# Construct the prompt template from the document
# Ensure to handle the {{user_request}} placeholder
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
            
            # Clean the output if it's wrapped in markdown code block
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

    except anthropic.APIError as e: # More specific error handling for Anthropic API errors
        raise HTTPException(status_code=500, detail=f"Anthropic API Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {str(e)}")

@app.get("/")
async def root():
    return {"message": "AI Orchestration Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
