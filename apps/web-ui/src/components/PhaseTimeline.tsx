import React from 'react';
import { Phase } from '../types';
import '../styles/PhaseTimeline.css';

interface PhaseTimelineProps {
  phases: Phase[];
  currentPhase?: string;
}

export const PhaseTimeline: React.FC<PhaseTimelineProps> = ({ phases, currentPhase }) => {
  const phaseLabels: Record<string, string> = {
    preflight: 'Pre-flight Check',
    extraction: 'Extract DOM',
    semantics: 'Analyze Semantics',
    generation: 'Generate Tests',
    execution: 'Run Tests',
    reporting: 'Generate Report',
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
    <div className="phase-timeline">
      <h2>Job Execution Timeline</h2>
      <div className="phases">
        {phases.map((phase, index) => (
          <div key={phase.id} className={`phase phase-${phase.status}`}>
            <div className="phase-marker">
              {phase.status === 'completed' && <span className="checkmark">✓</span>}
              {phase.status === 'in_progress' && <span className="spinner"></span>}
              {phase.status === 'failed' && <span className="error">✕</span>}
              {phase.status === 'pending' && <span className="pending">○</span>}
            </div>
            <div className="phase-content">
              <h3>{phaseLabels[phase.id] || phase.label}</h3>
              <p className="description">{phaseDescriptions[phase.id]}</p>
              {phase.timestamp && (
                <span className="timestamp">{new Date(phase.timestamp).toLocaleTimeString()}</span>
              )}
            </div>
            {index < phases.length - 1 && <div className="phase-connector"></div>}
          </div>
        ))}
      </div>
    </div>
  );
};
