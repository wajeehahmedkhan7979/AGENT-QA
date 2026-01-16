"""
Phase 2D UI Type Definitions
"""

export interface Phase {
  id: 'preflight' | 'extraction' | 'semantics' | 'generation' | 'execution' | 'reporting';
  label: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  timestamp?: string;
}

export interface Job {
  jobId: string;
  status: string;
  targetUrl: string;
  scope: 'read-only' | 'sandbox';
  createdAt: string;
  phases: Phase[];
  currentPhase?: string;
}

export interface UIElement {
  id: string;
  selector: string;
  role: string;
  label: string;
  confidence: number;
}

export interface SemanticModel {
  jobId: string;
  elements: UIElement[];
  flows: string[];
  confidence: number;
}

export interface TestStep {
  action: string;
  selector?: string;
  value?: string;
  url?: string;
  expectedText?: string;
}

export interface GeneratedTest {
  testId: string;
  steps: TestStep[];
  confidence: number;
  explanation: string;
}

export interface TestResult {
  testId: string;
  status: 'passed' | 'failed' | 'error';
  passed: number;
  failed: number;
  duration: number;
  errors: string[];
}

export interface ErrorState {
  message: string;
  phase?: string;
  details?: string;
  isRecoverable: boolean;
}

export interface LoadingState {
  isLoading: boolean;
  message: string;
  progress?: number;
}
