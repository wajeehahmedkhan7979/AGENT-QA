import React, { useState } from 'react';
import { TestResult, TestStep } from '../types';
import '../styles/TestResultPage.css';

interface TestResultPageProps {
  result: TestResult;
  steps?: TestStep[];
  artifacts?: Array<{ name: string; url: string }>;
}

export const TestResultPage: React.FC<TestResultPageProps> = ({
  result,
  steps = [],
  artifacts = [],
}) => {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  const getStatusIcon = (status: 'passed' | 'failed' | 'skipped'): string => {
    const icons = {
      passed: '✓',
      failed: '✕',
      skipped: '⊘',
    };
    return icons[status];
  };

  const passRate = (result.passed / (result.passed + result.failed)) * 100;

  return (
    <div className="test-result-page">
      <div className="result-header">
        <h2>Test Execution Result</h2>
        <div className="result-summary">
          <div className={`result-status ${result.status}`}>
            <span className="status-icon">{getStatusIcon(result.status as any)}</span>
            <span className="status-text">
              {result.status === 'passed' ? 'Test Passed' : 'Test Failed'}
            </span>
          </div>
          <div className="result-stats">
            <span className="stat">
              Duration: {result.duration}ms
            </span>
            <span className="stat">
              Pass Rate: {Math.round(passRate)}%
            </span>
          </div>
        </div>
      </div>

      <div className="result-content">
        <div className="steps-breakdown">
          <h3>Step-by-Step Execution</h3>
          <p className="explanation">
            Here's what happened at each step of the test. Failed steps are highlighted.
          </p>
          <div className="steps-list">
            {steps.map((step, idx) => {
              const stepStatus = result.errors?.some(e => e.includes(`Step ${idx + 1}`))
                ? 'failed'
                : 'passed';

              return (
                <div
                  key={idx}
                  className={`result-step ${stepStatus}`}
                  onClick={() =>
                    setExpandedStep(expandedStep === idx ? null : idx)
                  }
                >
                  <div className="step-header">
                    <span className="step-status-icon">
                      {getStatusIcon(stepStatus as any)}
                    </span>
                    <span className="step-number">Step {idx + 1}</span>
                    <span className="step-action">{step.action}</span>
                    <span className="expand-icon">
                      {expandedStep === idx ? '▼' : '▶'}
                    </span>
                  </div>
                  {expandedStep === idx && (
                    <div className="step-details">
                      <div className="detail-row">
                        <strong>Action:</strong> {step.action}
                      </div>
                      {step.selector && (
                        <div className="detail-row">
                          <strong>Element:</strong> <code>{step.selector}</code>
                        </div>
                      )}
                      {step.value && (
                        <div className="detail-row">
                          <strong>Value:</strong> {step.value}
                        </div>
                      )}
                      {stepStatus === 'failed' && (
                        <div className="error-details">
                          <strong>Error:</strong>
                          <p>
                            {result.errors
                              ?.find(e => e.includes(`Step ${idx + 1}`))
                              ?.replace(`Step ${idx + 1}: `, '')}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {artifacts.length > 0 && (
          <div className="artifacts-section">
            <h3>Test Artifacts</h3>
            <p className="explanation">
              Screenshots and logs collected during test execution:
            </p>
            <div className="artifacts-list">
              {artifacts.map((artifact, idx) => (
                <div key={idx} className="artifact-item">
                  <span className="artifact-icon">📎</span>
                  <a href={artifact.url} target="_blank" rel="noopener noreferrer">
                    {artifact.name}
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {result.errors && result.errors.length > 0 && (
          <div className="errors-section">
            <h3>Errors</h3>
            <div className="errors-list">
              {result.errors.map((error, idx) => (
                <div key={idx} className="error-item">
                  <span className="error-icon">⚠️</span>
                  <p>{error}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
