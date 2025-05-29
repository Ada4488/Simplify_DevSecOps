import React, { useState } from 'react';
import { useAuth } from '../authContext'; // Assuming authContext is in src

const DashboardPage: React.FC = () => {
  const auth = useAuth(); 
  const [description, setDescription] = useState('');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    console.log("User application description:", description);
    // Optionally clear the textarea after submission
    // setDescription('');
    alert("Description submitted to console. Backend integration for NLP processing and deployment is pending.");
  };

  return (
    <div>
      <h2>Welcome to the Dashboard!</h2>
      {auth.isAuthenticated && <p>Status: Logged in</p>}
      
      <p style={{ marginTop: '20px', marginBottom: '10px' }}>
        Describe your application, desired services, cloud environment, and any specific requirements below (e.g., security scans).
        Our AI will use this to generate your IaC and CI/CD pipeline.
      </p>
      
      <form onSubmit={handleSubmit}>
        <div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Deploy a Python Flask web app with a PostgreSQL database on AWS. Include SAST scanning in the pipeline."
            rows={12}
            style={{ 
              width: '90%', 
              maxWidth: '800px', 
              minHeight: '150px', 
              padding: '10px', 
              marginBottom: '15px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '1rem'
            }}
            required
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
              cursor: 'pointer'
            }}
          >
            Generate Configuration
          </button>
        </div>
      </form>
      
      {/* 
        The main logout button is in App.tsx's navigation bar.
        No need for an additional logout button here unless specifically desired for UI/UX reasons later.
        If needed, it would look like:
        <button onClick={() => {
          auth.logout(); 
          // Navigation to /login will be handled by ProtectedRoute or App.tsx's root route logic
        }} style={{ marginTop: '30px' }}>
          Logout
        </button>
      */}
    </div>
  );
};

export default DashboardPage;
