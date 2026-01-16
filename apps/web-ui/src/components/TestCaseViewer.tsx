import React, { useState } from 'react';
import { GeneratedTest, TestStep } from '../types';
import '../styles/TestCaseViewer.css';

interface TestCaseViewerProps {
  test: GeneratedTest;
}

export const TestCaseViewer: React.FC<TestCaseViewerProps> = ({ test }) => {
  const [showPlaywrightCode, setShowPlaywrightCode] = useState(false);

  const getActionIcon = (action: string): string => {
    const icons: Record<string, string> = {
      navigate: '🌐',
      click: '🖱️',
      type: '⌨️',
      submit: '📤',
      wait: '⏱️',
      assert: '✓',
      screenshot: '📸',
    };
    return icons[action] || '➡️';
  };

  const generatePlaywrightCode = (): string => {
    let code = 'test(\'Generated Test\', async ({ page }) => {\n';
    
    test.steps.forEach((step) => {
      switch (step.action) {
        case 'navigate':
          code += `  await page.goto(\'${step.url}\');\n`;
          break;
        case 'click':
          code += `  await page.click(\'${step.selector}\');\n`;
          break;
        case 'type':
          code += `  await page.fill(\'${step.selector}\', \'${step.value}\');\n`;
          break;
        case 'assert':
          code += `  expect(page.locator(\'${step.selector}\')).toContainText(\'${step.expectedText}\');\n`;
          break;
      }
    });
    
    code += '});\n';
    return code;
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

    return <span className={`confidence-badge confidence-${color}`}>{label}</span>;
  };

  return (
    <div className="test-case-viewer">
      <div className="viewer-header">
        <div className="header-content">
          <h2>Generated Test Case</h2>
          <p className="test-id">Test ID: {test.testId}</p>
        </div>
        <div className="header-stats">
          <span>Confidence: {getConfidenceBadge(test.confidence)}</span>
        </div>
      </div>

      <div className="viewer-content">
        <div className="explanation-section">
          <h3>What This Test Does</h3>
          <p>{test.explanation}</p>
        </div>

        <div className="steps-section">
          <h3>Test Steps</h3>
          <p className="explanation">
            These are the individual actions that make up this test. Each step is executed in order.
          </p>
          <div className="steps-list">
            {test.steps.map((step, idx) => (
              <div key={idx} className="step-item">
                <div className="step-number">{idx + 1}</div>
                <div className="step-content">
                  <div className="step-header">
                    <span className="step-icon">{getActionIcon(step.action)}</span>
                    <span className="step-action">{step.action.toUpperCase()}</span>
                  </div>
                  {step.selector && (
                    <div className="step-detail">
                      <strong>Element:</strong> <code>{step.selector}</code>
                    </div>
                  )}
                  {step.value && (
                    <div className="step-detail">
                      <strong>Input:</strong> {step.value}
                    </div>
                  )}
                  {step.expectedText && (
                    <div className="step-detail">
                      <strong>Expected:</strong> {step.expectedText}
                    </div>
                  )}
                  {step.url && (
                    <div className="step-detail">
                      <strong>URL:</strong> <code>{step.url}</code>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="viewer-footer">
        <button
          className="toggle-code-btn"
          onClick={() => setShowPlaywrightCode(!showPlaywrightCode)}
        >
          {showPlaywrightCode ? 'Hide' : 'Show'} Playwright Code (Advanced)
        </button>
      </div>

      {showPlaywrightCode && (
        <div className="code-section">
          <h3>Playwright Test Code</h3>
          <pre><code>{generatePlaywrightCode()}</code></pre>
        </div>
      )}
    </div>
  );
};
