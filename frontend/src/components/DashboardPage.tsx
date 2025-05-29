import React, { useState } from 'react';
import { useAuth } from '../authContext';
import axios from 'axios';

// Define a type for the HCLValidationResponse to use in state
interface TerraformCommandOutput {
  command: string;
  stdout: string;
  stderr: string;
  exit_code: number;
}

interface HCLValidationResult {
  validation_passed: boolean;
  init_output?: TerraformCommandOutput; // Made optional for initial state
  validate_output?: TerraformCommandOutput; // Made optional for initial state
  message?: string;
}

const DashboardPage: React.FC = () => {
  const auth = useAuth(); 
  const [description, setDescription] = useState('');
  
  const [parsedIntentJson, setParsedIntentJson] = useState<string | null>(null);
  const [isLoadingIntent, setIsLoadingIntent] = useState<boolean>(false);
  const [intentError, setIntentError] = useState<string | null>(null);

  const [generatedHcl, setGeneratedHcl] = useState<string | null>(null);
  const [isGeneratingHcl, setIsGeneratingHcl] = useState<boolean>(false);
  const [hclError, setHclError] = useState<string | null>(null); // Error during HCL generation
  const [hclMessage, setHclMessage] = useState<string | null>(null); // Message from HCL generation

  // New states for HCL Validation
  const [isValidatingHcl, setIsValidatingHcl] = useState<boolean>(false);
  const [hclValidationResult, setHclValidationResult] = useState<HCLValidationResult | null>(null);
  const [hclValidationError, setHclValidationError] = useState<string | null>(null); // Error from validation API call


  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    setIsLoadingIntent(true);
    setIntentError(null);
    setParsedIntentJson(null);
    
    setGeneratedHcl(null);
    setHclError(null);
    setHclMessage(null);
    setIsGeneratingHcl(false);

    setIsValidatingHcl(false); // Reset validation state
    setHclValidationResult(null);
    setHclValidationError(null);

    try {
      const intentResponse = await axios.post('http://localhost:8000/api/v1/orchestration/parse-intent', {
        query: description,
      });
      setParsedIntentJson(JSON.stringify(intentResponse.data, null, 2));
      setIsLoadingIntent(false);

      setIsGeneratingHcl(true);
      try {
        const iacResponse = await axios.post('http://localhost:8000/api/v1/infra-agent/generate-iac', 
          intentResponse.data
        );
        setGeneratedHcl(iacResponse.data.hcl_code);
        if (iacResponse.data.message) {
          setHclMessage(iacResponse.data.message);
        }
      } catch (genError) {
        let errorMessage = 'Failed to generate IaC.';
        if (axios.isAxiosError(genError) && genError.response) {
          errorMessage += ` Server responded with: ${genError.response.status} - ${JSON.stringify(genError.response.data, null, 2)}`;
        } else if (genError instanceof Error) {
          errorMessage += ` Details: ${genError.message}`;
        }
        setHclError(errorMessage);
        console.error("Error calling generate-iac API:", genError);
      } finally {
        setIsGeneratingHcl(false);
      }

    } catch (parseError) {
      let errorMessage = 'Failed to parse intent.';
      if (axios.isAxiosError(parseError) && parseError.response) {
        errorMessage += ` Server responded with: ${parseError.response.status} - ${JSON.stringify(parseError.response.data, null, 2)}`;
      } else if (parseError instanceof Error) {
        errorMessage += ` Details: ${parseError.message}`;
      }
      setIntentError(errorMessage);
      console.error("Error calling parse-intent API:", parseError);
      setIsLoadingIntent(false);
    }
  };

  const handleValidateHcl = async () => {
    if (!generatedHcl) {
      setHclValidationError("No HCL code available to validate.");
      return;
    }
    setIsValidatingHcl(true);
    setHclValidationResult(null);
    setHclValidationError(null);

    try {
      const response = await axios.post('http://localhost:8000/api/v1/infra-agent/validate-hcl', {
        hcl_code: generatedHcl,
      });
      setHclValidationResult(response.data);
    } catch (err) {
      let errorMessage = 'Failed to call HCL validation API.';
      if (axios.isAxiosError(err) && err.response) {
        errorMessage += ` Server responded with: ${err.response.status} - ${JSON.stringify(err.response.data, null, 2)}`;
      } else if (err instanceof Error) {
        errorMessage += ` Details: ${err.message}`;
      }
      setHclValidationError(errorMessage);
      console.error("Error calling validate-hcl API:", err);
    } finally {
      setIsValidatingHcl(false);
    }
  };

  const mainButtonDisabled = isLoadingIntent || isGeneratingHcl || isValidatingHcl;

  return (
    <div>
      <h2>AI-Powered DevSecOps Platform Dashboard</h2>
      {auth.isAuthenticated && <p>Status: Logged in</p>}
      
      <form onSubmit={handleSubmit}>
        <div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Deploy a Python Flask web app with a PostgreSQL database on AWS..."
            rows={10}
            style={{ width: '90%', maxWidth: '800px', minHeight: '120px', padding: '10px', marginBottom: '15px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '1rem' }}
            required
            disabled={mainButtonDisabled}
          />
        </div>
        <div>
          <button 
            type="submit" 
            style={{ padding: '12px 25px', fontSize: '1rem', color: 'white', backgroundColor: '#007bff', border: 'none', borderRadius: '4px', cursor: mainButtonDisabled ? 'not-allowed' : 'pointer', opacity: mainButtonDisabled ? 0.7 : 1 }}
            disabled={mainButtonDisabled}
          >
            {isLoadingIntent ? 'Parsing Intent...' : isGeneratingHcl ? 'Generating IaC...' : 'Generate Configuration'}
          </button>
        </div>
      </form>

      {isLoadingIntent && <p style={{ marginTop: '20px' }}>Parsing your intent with AI...</p>}
      {intentError && <div style={{ marginTop: '20px', color: 'red', border: '1px solid red', padding: '10px', borderRadius: '4px', backgroundColor: '#ffebee' }}><h3>Intent Parsing Error</h3><pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>{intentError}</pre></div>}
      
      {parsedIntentJson && !intentError && (
        <div style={{ marginTop: '20px' }}>
          <h3>Parsed Intent (JSON):</h3>
          <pre style={{ backgroundColor: '#f0f0f0', padding: '15px', borderRadius: '4px', border: '1px solid #ddd', whiteSpace: 'pre-wrap', wordWrap: 'break-word', maxHeight: '300px', overflowY: 'auto' }}>{parsedIntentJson}</pre>
        </div>
      )}

      {isGeneratingHcl && <p style={{ marginTop: '20px' }}>Generating Infrastructure as Code (IaC)...</p>}
      {hclError && <div style={{ marginTop: '20px', color: 'red', border: '1px solid red', padding: '10px', borderRadius: '4px', backgroundColor: '#ffebee' }}><h3>IaC Generation Error</h3><pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>{hclError}</pre></div>}
      
      {generatedHcl && !hclError && (
        <div style={{ marginTop: '20px' }}>
          <h3>Generated IaC (Terraform HCL):</h3>
          {hclMessage && <p><em>Backend Message: {hclMessage}</em></p>}
          <pre style={{ backgroundColor: '#e8f5e9', color: '#2e7d32', padding: '15px', borderRadius: '4px', border: '1px solid #c8e6c9', whiteSpace: 'pre-wrap', wordWrap: 'break-word', maxHeight: '400px', overflowY: 'auto' }}>{generatedHcl}</pre>
          {!isValidatingHcl && (
            <button 
              onClick={handleValidateHcl} 
              disabled={mainButtonDisabled}
              style={{ marginTop: '10px', padding: '10px 15px', fontSize: '0.9rem', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: mainButtonDisabled ? 'not-allowed' : 'pointer', opacity: mainButtonDisabled ? 0.7 : 1 }}
            >
              Validate HCL with Terraform
            </button>
          )}
        </div>
      )}

      {isValidatingHcl && <p style={{ marginTop: '20px' }}>Validating HCL with Terraform...</p>}
      {hclValidationError && <div style={{ marginTop: '20px', color: 'red', border: '1px solid red', padding: '10px', borderRadius: '4px', backgroundColor: '#ffebee' }}><h3>HCL Validation API Call Error</h3><pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>{hclValidationError}</pre></div>}

      {hclValidationResult && (
        <div style={{ marginTop: '20px', border: '1px solid #ccc', padding: '15px', borderRadius: '4px' }}>
          <h4>HCL Validation Results:</h4>
          <p style={{ fontWeight: hclValidationResult.validation_passed ? 'bold' : 'bold', color: hclValidationResult.validation_passed ? 'green' : 'red' }}>
            <strong>Overall Validation Passed:</strong> {hclValidationResult.validation_passed ? 'Yes' : 'No'}
          </p>
          {hclValidationResult.message && <p><strong>Message:</strong> {hclValidationResult.message}</p>}
          
          {hclValidationResult.init_output && (
            <div style={{ marginTop: '10px' }}>
              <h5>Terraform Init Output:</h5>
              <p>Command: <code>{hclValidationResult.init_output.command}</code></p>
              <p>Exit Code: {hclValidationResult.init_output.exit_code}</p>
              <strong>Stdout:</strong>
              <pre style={{ backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '3px', maxHeight: '200px', overflowY: 'auto' }}>{hclValidationResult.init_output.stdout || '(empty)'}</pre>
              <strong>Stderr:</strong>
              <pre style={{ backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '3px', color: hclValidationResult.init_output.stderr ? 'orange' : 'inherit', maxHeight: '200px', overflowY: 'auto' }}>{hclValidationResult.init_output.stderr || '(empty)'}</pre>
            </div>
          )}
          
          {hclValidationResult.validate_output && (
             <div style={{ marginTop: '10px' }}>
              <h5>Terraform Validate Output:</h5>
              <p>Command: <code>{hclValidationResult.validate_output.command}</code></p>
              <p>Exit Code: {hclValidationResult.validate_output.exit_code}</p>
              <strong>Stdout:</strong>
              <pre style={{ backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '3px', maxHeight: '200px', overflowY: 'auto' }}>{hclValidationResult.validate_output.stdout || '(empty)'}</pre>
              <strong>Stderr:</strong>
              <pre style={{ backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '3px', color: hclValidationResult.validate_output.stderr ? 'orange' : 'inherit', maxHeight: '200px', overflowY: 'auto' }}>{hclValidationResult.validate_output.stderr || '(empty)'}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
