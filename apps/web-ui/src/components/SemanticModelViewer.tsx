import React, { useState } from 'react';
import { SemanticModel, UIElement } from '../types';
import '../styles/SemanticModelViewer.css';

interface SemanticModelViewerProps {
  model: SemanticModel;
}

export const SemanticModelViewer: React.FC<SemanticModelViewerProps> = ({ model }) => {
  const [showRawJSON, setShowRawJSON] = useState(false);

  const getElementRoleIcon = (role: string): string => {
    const icons: Record<string, string> = {
      login_button: '🔓',
      username_input: '👤',
      password_input: '🔑',
      form: '📋',
      button: '🔘',
      input: '📝',
      text: '📄',
      link: '🔗',
      dropdown: '▼',
      checkbox: '☑️',
    };
    return icons[role] || '📦';
  };

  const getConfidenceBadge = (confidence: number): React.ReactNode => {
    let color = 'high';
    let label = 'High';
    
    if (confidence < 0.6) {
      color = 'low';
      label = 'Low';
    } else if (confidence < 0.8) {
      color = 'medium';
      label = 'Medium';
    }

    return <span className={`confidence-badge confidence-${color}`}>{label} ({Math.round(confidence * 100)}%)</span>;
  };

  return (
    <div className="semantic-model-viewer">
      <div className="viewer-header">
        <h2>Semantic Model Analysis</h2>
        <div className="header-stats">
          <span className="stat">
            <strong>{model.elements.length}</strong> UI Elements
          </span>
          <span className="stat">
            <strong>{model.flows.length}</strong> Flows
          </span>
          <span className="stat">
            Overall Confidence: {getConfidenceBadge(model.confidence)}
          </span>
        </div>
      </div>

      <div className="viewer-content">
        <div className="elements-section">
          <h3>Extracted UI Elements</h3>
          <p className="explanation">
            These are the key interactive elements we found on the page. Each element has been 
            identified and labeled based on its visual and structural properties.
          </p>
          <div className="elements-list">
            {model.elements.map((element) => (
              <div key={element.id} className="element-card">
                <div className="element-header">
                  <span className="element-icon">{getElementRoleIcon(element.role)}</span>
                  <div className="element-info">
                    <h4>{element.label}</h4>
                    <p className="element-role">Role: {element.role}</p>
                  </div>
                  {getConfidenceBadge(element.confidence)}
                </div>
                <div className="element-selector">
                  <code>{element.selector}</code>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flows-section">
          <h3>Inferred User Flows</h3>
          <p className="explanation">
            Based on the semantic structure, we identified these typical user interactions:
          </p>
          <div className="flows-list">
            {model.flows.length === 0 ? (
              <p className="no-flows">No flows detected in current model</p>
            ) : (
              model.flows.map((flow, idx) => (
                <div key={idx} className="flow-item">
                  <span className="flow-number">{idx + 1}</span>
                  <span className="flow-description">{flow}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="viewer-footer">
        <button
          className="toggle-json-btn"
          onClick={() => setShowRawJSON(!showRawJSON)}
        >
          {showRawJSON ? 'Hide Raw JSON' : 'Show Raw JSON (Advanced)'}
        </button>
      </div>

      {showRawJSON && (
        <div className="raw-json-section">
          <h3>Raw JSON (Advanced)</h3>
          <pre>{JSON.stringify(model, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
