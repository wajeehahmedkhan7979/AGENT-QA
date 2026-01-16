import React, { useState, useEffect } from 'react';
import { PhaseTimeline } from '../components/PhaseTimeline';
import { Job, Phase } from '../types';
import '../styles/JobOverviewPage.css';

interface JobOverviewPageProps {
  jobId: string;
}

export const JobOverviewPage: React.FC<JobOverviewPageProps> = ({ jobId }) => {
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const response = await fetch(`/api/jobs/${jobId}`);
        if (!response.ok) throw new Error('Failed to fetch job');
        
        const data = await response.json();
        setJob(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load job');
      } finally {
        setLoading(false);
      }
    };

    fetchJob();

    if (autoRefresh && job?.status !== 'completed' && job?.status !== 'failed') {
      const interval = setInterval(fetchJob, 2000);
      return () => clearInterval(interval);
    }
  }, [jobId, autoRefresh, job?.status]);

  if (loading) {
    return (
      <div className="job-overview-page">
        <div className="loading-state">
          <div className="spinner">⟳</div>
          <p>Loading job details...</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="job-overview-page">
        <div className="error-state">
          <span className="error-icon">⚠️</span>
          <h2>Error Loading Job</h2>
          <p>{error || 'Job not found'}</p>
        </div>
      </div>
    );
  }

  const getJobStatusLabel = (status: string): string => {
    const labels: Record<string, string> = {
      created: 'Queued',
      processing: 'Running Tests',
      completed: 'Finished',
      failed: 'Failed',
    };
    return labels[status] || status;
  };

  return (
    <div className="job-overview-page">
      <div className="overview-header">
        <div className="header-content">
          <h1>Test Job Overview</h1>
          <p className="job-url">Target: {job.targetUrl}</p>
        </div>
        <div className="header-actions">
          <div className="status-badge" data-status={job.status}>
            {getJobStatusLabel(job.status)}
          </div>
          <button
            className="refresh-button"
            onClick={() => window.location.reload()}
            title="Refresh page"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="overview-content">
        <div className="timeline-section">
          <h2>Execution Timeline</h2>
          <p className="section-description">
            This shows the progress of your test job through each phase. 
            Phases execute sequentially - the system waits for each phase to complete before starting the next.
          </p>
          <PhaseTimeline phases={job.phases} />
        </div>

        <div className="details-section">
          <div className="detail-group">
            <h3>Job Information</h3>
            <div className="detail-item">
              <span className="detail-label">Job ID:</span>
              <span className="detail-value">{job.jobId}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Status:</span>
              <span className="detail-value">{getJobStatusLabel(job.status)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Scope:</span>
              <span className="detail-value">
                {job.scope === 'read-only' ? 'Read-Only' : 'Sandbox Mode'}
              </span>
            </div>
          </div>

          <div className="detail-group">
            <h3>What Happens Next</h3>
            <p className="section-description">
              {job.status === 'processing' &&
                "The system is currently analyzing your website and generating tests. This typically takes 1-3 minutes."}
              {job.status === 'completed' &&
                "Test generation and execution are complete. View the semantic model to see what the system learned about your website."}
              {job.status === 'failed' &&
                "An error occurred during processing. Check the error details below."}
              {job.status === 'created' &&
                "Your job is queued and will start processing soon."}
            </p>
          </div>
        </div>

        {job.status === 'completed' && (
          <div className="results-links">
            <h3>View Results</h3>
            <div className="links-grid">
              <a href={`/job/${jobId}/semantic`} className="result-link">
                <span className="link-icon">🧠</span>
                <span className="link-text">Semantic Model</span>
                <span className="link-desc">See what the system learned</span>
              </a>
              <a href={`/job/${jobId}/tests`} className="result-link">
                <span className="link-icon">✓</span>
                <span className="link-text">Generated Tests</span>
                <span className="link-desc">View generated test cases</span>
              </a>
              <a href={`/job/${jobId}/results`} className="result-link">
                <span className="link-icon">📊</span>
                <span className="link-text">Test Results</span>
                <span className="link-desc">Execution results and artifacts</span>
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
