import React, { useState } from 'react';
import { useAuth } from '../authContext';
import axios from 'axios';

// Define types for Terraform command outputs and API responses
interface TerraformCommandOutput {
  command: string;
  stdout: string;
  stderr: string;
  exit_code: number;
}

interface HCLValidationResult {
  validation_passed: boolean;
  init_output?: TerraformCommandOutput;
  validate_output?: TerraformCommandOutput;
  message?: string;
}

interface HCLApplyResponse { // New interface for Apply result
  apply_successful: boolean;
  init_output?: TerraformCommandOutput;
  apply_output?: TerraformCommandOutput; // Changed from validate_output
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
  const [hclError, setHclError] = useState<string | null>(null);
  const [hclMessage, setHclMessage] = useState<string | null>(null);

  const [isValidatingHcl, setIsValidatingHcl] = useState<boolean>(false);
  const [hclValidationResult, setHclValidationResult] = useState<HCLValidationResult | null>(null);
  const [hclValidationError, setHclValidationError] = useState<string | null>(null);

  // New states for HCL Apply
  const [isApplyingHcl, setIsApplyingHcl] = useState<boolean>(false);
  const [hclApplyResult, setHclApplyResult] = useState<HCLApplyResponse | null>(null);
  const [hclApplyError, setHclApplyError] = useState<string | null>(null);


  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    setIsLoadingIntent(true);
    setIntentError(null);
    setParsedIntentJson(null);
    setGeneratedHcl(null);
    setHclError(null);
    setHclMessage(null);
    setIsGeneratingHcl(false);
    setIsValidatingHcl(false);
    setHclValidationResult(null);
    setHclValidationError(null);
    setIsApplyingHcl(false); // Reset apply state
    setHclApplyResult(null);
    setHclApplyError(null);

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
        if (iacResponse.data.message) setHclMessage(iacResponse.data.message);
      } catch (genError) {
        handleAxiosError(genError, "Failed to generate IaC.", setHclError);
      } finally {
        setIsGeneratingHcl(false);
      }
    } catch (parseError) {
      handleAxiosError(parseError, "Failed to parse intent.", setIntentError);
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
      handleAxiosError(err, "Failed to call HCL validation API.", setHclValidationError);
    } finally {
      setIsValidatingHcl(false);
    }
  };

  const handleApplyHcl = async () => {
    if (!generatedHcl) {
      alert("No HCL code available to apply.");
      return;
    }
    if (!window.confirm("Are you sure you want to apply this configuration? This may create or modify real cloud resources and could incur costs.")) {
      return;
    }
    setIsApplyingHcl(true);
    setHclApplyResult(null);
    setHclApplyError(null);
    try {
      const response = await axios.post('http://localhost:8000/api/v1/infra-agent/apply-hcl', {
        hcl_code: generatedHcl,
      });
      setHclApplyResult(response.data);
    } catch (err) {
      handleAxiosError(err, "Failed to call HCL apply API.", setHclApplyError);
    } finally {
      setIsApplyingHcl(false);
    }
  };
  
  const handleAxiosError = (error: any, defaultMessage: string, setErrorState: React.Dispatch<React.SetStateAction<string | null>>) => {
    let errorMessage = defaultMessage;
    if (axios.isAxiosError(error)) {
      if (error.response) {
        errorMessage += ` Server responded with: ${error.response.status} - ${JSON.stringify(error.response.data, null, 2)}`;
      } else if (error.request) {
        errorMessage += ' No response received from server. Check network and if the backend is running.';
      } else {
        errorMessage += ` Request setup error: ${error.message}`;
      }
    } else if (error instanceof Error) {
      errorMessage += ` Details: ${error.message}`;
    }
    setErrorState(errorMessage);
    console.error(defaultMessage, error);
  };

  const mainButtonDisabled = isLoadingIntent || isGeneratingHcl || isValidatingHcl || isApplyingHcl;
  const showValidateButton = generatedHcl && !hclError && !isValidatingHcl && !isApplyingHcl;
  const showApplyButton = generatedHcl && hclValidationResult?.validation_passed && !isApplyingHcl && !isLoadingIntent && !isGeneratingHcl && !isValidatingHcl;


  const renderTerraformOutput = (tfOutput: TerraformCommandOutput | undefined, title: string) => {
    if (!tfOutput) return null;
    return (
      <div style={{ marginTop: '10px', border: '1px solid #eee', padding: '10px', borderRadius: '4px' }}>
        <h5>{title}:</h5>
        <p style={{fontSize: '0.9em'}}>Command: <code>{tfOutput.command}</code></p>
        <p style={{fontSize: '0.9em'}}>Exit Code: <span style={{fontWeight: tfOutput.exit_code === 0 ? 'normal' : 'bold', color: tfOutput.exit_code === 0 ? 'inherit' : 'red'}}>{tfOutput.exit_code}</span></p>
        <strong>Stdout:</strong>
        <pre style={{ backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '3px', maxHeight: '200px', overflowY: 'auto', fontSize: '0.85em' }}>{tfOutput.stdout || '(empty)'}</pre>
        <strong>Stderr:</strong>
        <pre style={{ backgroundColor: '#f8f9fa', padding: '10px', borderRadius: '3px', color: tfOutput.stderr ? (tfOutput.exit_code === 0 ? 'orange' : 'red') : 'inherit', maxHeight: '200px', overflowY: 'auto', fontSize: '0.85em' }}>{tfOutput.stderr || '(empty)'}</pre>
      </div>
    );
  };

  return (
    <div style={{paddingBottom: '50px'}}>
      <h2>AI-Powered DevSecOps Platform Dashboard</h2>
      {auth.isAuthenticated && <p>Status: Logged in</p>}
      
      <form onSubmit={handleSubmit}>
        <div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Deploy a Python Flask web app with a PostgreSQL database on AWS..."
            rows={8}
            style={{ width: '90%', maxWidth: '800px', minHeight: '100px', padding: '10px', marginBottom: '15px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '1rem' }}
            required
            disabled={mainButtonDisabled}
          />
        </div>
        <div>
          <button 
            type="submit" 
            style={{ padding: '10px 20px', fontSize: '1rem', color: 'white', backgroundColor: '#007bff', border: 'none', borderRadius: '4px', cursor: mainButtonDisabled ? 'not-allowed' : 'pointer', opacity: mainButtonDisabled ? 0.7 : 1 }}
            disabled={mainButtonDisabled}
          >
            {isLoadingIntent ? 'Parsing Intent...' : isGeneratingHcl ? 'Generating IaC...' : 'Generate Configuration'}
          </button>
        </div>
      </form>

      {isLoadingIntent && <p style={{ marginTop: '15px' }}>Parsing your intent with AI...</p>}
      {intentError && <div style={{ marginTop: '15px', color: 'red', border: '1px solid red', padding: '10px', borderRadius: '4px', backgroundColor: '#ffebee' }}><h3>Intent Parsing Error</h3><pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontSize: '0.9em' }}>{intentError}</pre></div>}
      
      {parsedIntentJson && !intentError && (
        <div style={{ marginTop: '15px' }}>
          <h3>Parsed Intent (JSON):</h3>
          <pre style={{ backgroundColor: '#f0f0f0', padding: '10px', borderRadius: '4px', border: '1px solid #ddd', whiteSpace: 'pre-wrap', wordWrap: 'break-word', maxHeight: '200px', overflowY: 'auto', fontSize: '0.9em' }}>{parsedIntentJson}</pre>
        </div>
      )}

      {isGeneratingHcl && <p style={{ marginTop: '15px' }}>Generating Infrastructure as Code (IaC)...</p>}
      {hclError && <div style={{ marginTop: '15px', color: 'red', border: '1px solid red', padding: '10px', borderRadius: '4px', backgroundColor: '#ffebee' }}><h3>IaC Generation Error</h3><pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontSize: '0.9em' }}>{hclError}</pre></div>}
      
      {generatedHcl && !hclError && (
        <div style={{ marginTop: '15px' }}>
          <h3>Generated IaC (Terraform HCL):</h3>
          {hclMessage && <p><em>Backend Message: {hclMessage}</em></p>}
          <pre style={{ backgroundColor: '#e8f5e9', color: '#155724', padding: '10px', borderRadius: '4px', border: '1px solid #c3e6cb', whiteSpace: 'pre-wrap', wordWrap: 'break-word', maxHeight: '300px', overflowY: 'auto', fontSize: '0.9em' }}>{generatedHcl}</pre>
          {showValidateButton && (
            <button 
              onClick={handleValidateHcl} 
              disabled={mainButtonDisabled}
              style={{ marginTop: '10px', padding: '8px 15px', fontSize: '0.9rem', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: mainButtonDisabled ? 'not-allowed' : 'pointer', opacity: mainButtonDisabled ? 0.7 : 1 }}
            >
              Validate HCL
            </button>
          )}
        </div>
      )}

      {isValidatingHcl && <p style={{ marginTop: '15px' }}>Validating HCL with Terraform...</p>}
      {hclValidationError && <div style={{ marginTop: '15px', color: 'red', border: '1px solid red', padding: '10px', borderRadius: '4px', backgroundColor: '#ffebee' }}><h3>HCL Validation API Call Error</h3><pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontSize: '0.9em' }}>{hclValidationError}</pre></div>}

      {hclValidationResult && (
        <div style={{ marginTop: '15px', border: '1px solid #bee5eb', padding: '10px', borderRadius: '4px', backgroundColor: '#d1ecf1' }}>
          <h4>HCL Validation Results:</h4>
          <p style={{ fontWeight: 'bold', color: hclValidationResult.validation_passed ? 'green' : 'red' }}>
            Overall Validation Passed: {hclValidationResult.validation_passed ? 'Yes' : 'No'}
          </p>
          {hclValidationResult.message && <p><strong>Message:</strong> {hclValidationResult.message}</p>}
          {renderTerraformOutput(hclValidationResult.init_output, "Terraform Init Output (during validation)")}
          {renderTerraformOutput(hclValidationResult.validate_output, "Terraform Validate Output")}
          {showApplyButton && (
             <button 
              onClick={handleApplyHcl} 
              disabled={mainButtonDisabled}
              style={{ marginTop: '15px', padding: '10px 20px', fontSize: '1rem', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: mainButtonDisabled ? 'not-allowed' : 'pointer', opacity: mainButtonDisabled ? 0.7 : 1 }}
            >
              Apply Configuration
            </button>
          )}
        </div>
      )}
      
      {isApplyingHcl && <p style={{ marginTop: '15px' }}>Applying HCL with Terraform... This may take a few minutes.</p>}
      {hclApplyError && <div style={{ marginTop: '15px', color: 'red', border: '1px solid red', padding: '10px', borderRadius: '4px', backgroundColor: '#ffebee' }}><h3>HCL Apply API Call Error</h3><pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontSize: '0.9em' }}>{hclApplyError}</pre></div>}

      {hclApplyResult && (
        <div style={{ marginTop: '15px', border: '1px solid #c3e6cb', padding: '10px', borderRadius: '4px', backgroundColor: hclApplyResult.apply_successful ? '#d4edda' : '#f8d7da' }}>
          <h4>HCL Apply Results:</h4>
           <p style={{ fontWeight: 'bold', color: hclApplyResult.apply_successful ? 'green' : 'red' }}>
            Overall Apply Successful: {hclApplyResult.apply_successful ? 'Yes' : 'No'}
          </p>
          {hclApplyResult.message && <p><strong>Message:</strong> {hclApplyResult.message}</p>}
          {renderTerraformOutput(hclApplyResult.init_output, "Terraform Init Output (during apply)")}
          {renderTerraformOutput(hclApplyResult.apply_output, "Terraform Apply Output")}
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
