import React, { useState } from 'react';
import { useAuth } from '../authContext';
import axios from 'axios';

const DashboardPage: React.FC = () => {
  const auth = useAuth(); 
  const [description, setDescription] = useState('');
  
  // State for NLP Intent Parsing
  const [parsedIntentJson, setParsedIntentJson] = useState<string | null>(null);
  const [isLoadingIntent, setIsLoadingIntent] = useState<boolean>(false); // Renamed from isLoading
  const [intentError, setIntentError] = useState<string | null>(null); // Renamed from error

  // State for IaC Generation
  const [generatedHcl, setGeneratedHcl] = useState<string | null>(null);
  const [isGeneratingHcl, setIsGeneratingHcl] = useState<boolean>(false);
  const [hclError, setHclError] = useState<string | null>(null);
  const [hclMessage, setHclMessage] = useState<string | null>(null);


  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    // Reset states for both calls
    setIsLoadingIntent(true);
    setIntentError(null);
    setParsedIntentJson(null);
    
    setGeneratedHcl(null);
    setHclError(null);
    setHclMessage(null);
    setIsGeneratingHcl(false); // Ensure this is reset initially

    try {
      // First API Call: Parse Intent
      const intentResponse = await axios.post('http://localhost:8000/api/v1/orchestration/parse-intent', {
        query: description,
      });
      setParsedIntentJson(JSON.stringify(intentResponse.data, null, 2));
      setIsLoadingIntent(false);

      // If first call is successful, proceed to second API Call: Generate IaC
      setIsGeneratingHcl(true);
      try {
        const iacResponse = await axios.post('http://localhost:8000/api/v1/infra-agent/generate-iac', 
          intentResponse.data // Pass the actual JSON object from the first response
        );
        setGeneratedHcl(iacResponse.data.hcl_code);
        if (iacResponse.data.message) {
          setHclMessage(iacResponse.data.message);
          console.log("IaC Generation Message:", iacResponse.data.message);
        }
      } catch (genError) {
        let errorMessage = 'Failed to generate IaC.';
        if (axios.isAxiosError(genError)) {
          if (genError.response) {
            errorMessage += ` Server responded with: ${genError.response.status} - ${JSON.stringify(genError.response.data, null, 2)}`;
          } else if (genError.request) {
            errorMessage += ' No response received from IaC generation server.';
          } else {
            errorMessage += ` IaC generation request setup error: ${genError.message}`;
          }
        } else if (genError instanceof Error) {
          errorMessage += ` Details: ${genError.message}`;
        }
        setHclError(errorMessage);
        console.error("Error calling generate-iac API:", genError);
      } finally {
        setIsGeneratingHcl(false);
      }

    } catch (parseError) { // Error from the first API call (parse-intent)
      let errorMessage = 'Failed to parse intent. Please ensure the AI Orchestration service is running and accessible.';
      if (axios.isAxiosError(parseError)) {
        if (parseError.response) {
          errorMessage += ` Server responded with: ${parseError.response.status} - ${JSON.stringify(parseError.response.data, null, 2)}`;
        } else if (parseError.request) {
          errorMessage += ' No response received from intent parsing server.';
        } else {
          errorMessage += ` Intent parsing request setup error: ${parseError.message}`;
        }
      } else if (parseError instanceof Error) {
        errorMessage += ` Details: ${parseError.message}`;
      }
      setIntentError(errorMessage);
      console.error("Error calling parse-intent API:", parseError);
      setIsLoadingIntent(false); // Ensure loading is false if first call fails
    }
  };

  return (
    <div>
      <h2>AI-Powered DevSecOps Platform Dashboard</h2>
      {auth.isAuthenticated && <p>Status: Logged in</p>}
      
      <p style={{ marginTop: '20px', marginBottom: '10px' }}>
        Describe your application, desired services, cloud environment, and any specific requirements below.
      </p>
      
      <form onSubmit={handleSubmit}>
        <div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Deploy a Python Flask web app with a PostgreSQL database on AWS. Include SAST scanning in the pipeline."
            rows={10} // Reduced rows slightly
            style={{ 
              width: '90%', 
              maxWidth: '800px', 
              minHeight: '120px', // Reduced min-height
              padding: '10px', 
              marginBottom: '15px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '1rem'
            }}
            required
            disabled={isLoadingIntent || isGeneratingHcl}
          />
        </div>
        <div>
          <button 
            type="submit" 
            style={{ 
              padding: '12px 25px', 
              fontSize: '1rem', 
              color: 'white',
              backgroundColor: '#007bff',
              border: 'none',
              borderRadius: '4px',
              cursor: (isLoadingIntent || isGeneratingHcl) ? 'not-allowed' : 'pointer',
              opacity: (isLoadingIntent || isGeneratingHcl) ? 0.7 : 1
            }}
            disabled={isLoadingIntent || isGeneratingHcl}
          >
            {isLoadingIntent ? 'Parsing Intent...' : isGeneratingHcl ? 'Generating IaC...' : 'Generate Configuration'}
          </button>
        </div>
      </form>

      {isLoadingIntent && <p style={{ marginTop: '20px' }}>Parsing your intent with AI...</p>}
      
      {intentError && (
        <div style={{ marginTop: '20px', color: 'red', border: '1px solid red', padding: '10px', borderRadius: '4px', backgroundColor: '#ffebee' }}>
          <h3>Intent Parsing Error</h3>
          <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>{intentError}</pre>
        </div>
      )}
      
      {parsedIntentJson && !intentError && ( // Only show if no intent error
        <div style={{ marginTop: '20px' }}>
          <h3>Parsed Intent (JSON Response from Backend):</h3>
          <pre style={{ 
            backgroundColor: '#f0f0f0', // Light grey background
            padding: '15px', 
            borderRadius: '4px', 
            border: '1px solid #ddd', // Lighter border
            whiteSpace: 'pre-wrap', 
            wordWrap: 'break-word',
            maxHeight: '300px', // Max height with scroll
            overflowY: 'auto'
          }}>
            {parsedIntentJson}
          </pre>
        </div>
      )}

      {isGeneratingHcl && <p style={{ marginTop: '20px' }}>Generating Infrastructure as Code (IaC)...</p>}

      {hclError && (
        <div style={{ marginTop: '20px', color: 'red', border: '1px solid red', padding: '10px', borderRadius: '4px', backgroundColor: '#ffebee' }}>
          <h3>IaC Generation Error</h3>
          <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>{hclError}</pre>
        </div>
      )}

      {generatedHcl && !hclError && ( // Only show if no HCL error
        <div style={{ marginTop: '20px' }}>
          <h3>Generated IaC (Terraform HCL):</h3>
          {hclMessage && <p><em>Backend Message: {hclMessage}</em></p>}
          <pre style={{ 
            backgroundColor: '#e8f5e9', // Light green background for HCL
            color: '#2e7d32', // Darker green text
            padding: '15px', 
            borderRadius: '4px', 
            border: '1px solid #c8e6c9', // Lighter green border
            whiteSpace: 'pre-wrap', 
            wordWrap: 'break-word',
            maxHeight: '400px', // Max height with scroll
            overflowY: 'auto'
          }}>
            {generatedHcl}
          </pre>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
