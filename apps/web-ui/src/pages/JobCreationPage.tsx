import React, { useState } from 'react';
import { PhaseTimeline } from '../components/PhaseTimeline';
import '../styles/JobCreationPage.css';

export const JobCreationPage: React.FC = () => {
  const [targetUrl, setTargetUrl] = useState('');
  const [scope, setScope] = useState<'read-only' | 'sandbox'>('read-only');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!targetUrl.trim()) {
      setError('Please enter a target URL');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      // Call backend to create job
      const response = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetUrl, scope }),
      });

      if (!response.ok) {
        throw new Error('Failed to create job');
      }

      // Navigate to job overview (in real app)
      const job = await response.json();
      window.location.href = `/job/${job.jobId}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job');
      setIsSubmitting(false);
    }
  };

  const phaseDescriptions: Record<string, string> = {
    preflight: 'Verifying the target website is accessible and follows security policies',
    extraction: 'Parsing HTML and extracting the DOM structure',
    semantics: 'Analyzing UI elements and understanding their roles (buttons, inputs, forms, etc)',
    generation: 'Using AI to generate test steps based on the semantic model',
    execution: 'Running the generated tests with Playwright browser automation',
    reporting: 'Collecting results and generating a comprehensive test report',
  };

  return (
    <div className="job-creation-page">
      <div className="creation-container">
        <div className="form-section">
          <div className="form-header">
            <h1>Create New Test Job</h1>
            <p className="form-description">
              Provide a target website URL and we'll automatically generate and run tests to verify it works correctly.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="creation-form">
            <div className="form-group">
              <label htmlFor="targetUrl" className="form-label">
                Target Website URL
              </label>
              <p className="field-description">
                Enter the URL of the website you want to test. 
                We'll analyze it and generate tests automatically.
              </p>
              <input
                id="targetUrl"
                type="url"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://example.com"
                className="form-input"
                disabled={isSubmitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="scope" className="form-label">
                Test Scope
              </label>
              <p className="field-description">
                Choose how extensively the system interacts with your website.
              </p>
              <div className="scope-options">
                <label className="scope-option">
                  <input
                    type="radio"
                    value="read-only"
                    checked={scope === 'read-only'}
                    onChange={(e) => setScope(e.target.value as any)}
                    disabled={isSubmitting}
                  />
                  <span className="option-label">Read-Only (Recommended)</span>
                  <span className="option-description">
                    Only examine the page without making any changes or submissions
                  </span>
                </label>
                <label className="scope-option">
                  <input
                    type="radio"
                    value="sandbox"
                    checked={scope === 'sandbox'}
                    onChange={(e) => setScope(e.target.value as any)}
                    disabled={isSubmitting}
                  />
                  <span className="option-label">Sandbox Mode</span>
                  <span className="option-description">
                    Allow form submissions and interactions (only for test/sandbox environments)
                  </span>
                </label>
              </div>
            </div>

            {error && (
              <div className="error-alert">
                <span className="error-icon">⚠️</span>
                <span className="error-message">{error}</span>
              </div>
            )}

            <button
              type="submit"
              className="submit-button"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating Job...' : 'Start Test Analysis'}
            </button>
          </form>
        </div>

        <div className="info-section">
          <div className="what-happens-box">
            <h2>What Will Happen</h2>
            <p className="box-description">
              When you start a test job, we'll run through these phases to analyze your website 
              and generate comprehensive tests:
            </p>
            <div className="phase-descriptions">
              {Object.entries(phaseDescriptions).map(([phase, description]) => (
                <div key={phase} className="phase-description">
                  <span className="phase-icon">→</span>
                  <div className="phase-text">
                    <strong className="phase-name">{phase.charAt(0).toUpperCase() + phase.slice(1)}</strong>
                    <p className="phase-detail">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="tips-box">
            <h3>Tips for Best Results</h3>
            <ul className="tips-list">
              <li>Make sure the URL is publicly accessible</li>
              <li>Test pages with clear interactive elements (forms, buttons)</li>
              <li>Start with production websites, not staging</li>
              <li>Avoid pages with heavy JavaScript rendering delays</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
