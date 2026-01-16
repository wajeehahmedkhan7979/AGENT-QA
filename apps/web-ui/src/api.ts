export type Job = {
  jobId: string;
  status: string;
  preflight?: { allowed: boolean; robots?: string | null };
  createdAt: string;
};

export type Artifact = {
  name: string;
  type: string;
  path: string;
};

// Always use localhost:8000 when accessed from browser
// (Vite env vars are build-time, but browser needs localhost, not Docker internal hostname)
const API_BASE = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return (await res.json()) as T;
}

export async function createJob(payload: {
  targetUrl: string;
  scope: "read-only" | "sandbox";
  testProfile: string;
  ownerId: string;
}) {
  return request<Job>("/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getJob(jobId: string) {
  return request<Job>(`/jobs/${jobId}`);
}

export async function getArtifacts(jobId: string) {
  return request<Artifact[]>(`/jobs/${jobId}/artifacts`);
}

export async function generateTest(jobId: string) {
  return request<{
    testId: string;
    jobId: string;
    steps: any[];
    confidence: number;
    format: string;
    status: string;
  }>(`/jobs/${jobId}/generate`, { method: "POST" });
}

export async function runTest(jobId: string, testId: string) {
  return request<{ runId: string; testId: string; jobId: string; status: string }>(
    `/tests/${testId}/run`,
    {
      method: "POST",
      body: JSON.stringify({ jobId }),
    },
  );
}

export async function getReport(jobId: string) {
  return request<{
    runId: string;
    testId: string;
    status: string;
    steps: { step: number; status: string; screenshot?: string; error?: string }[];
    artifacts: string[];
    startedAt: string;
    finishedAt: string;
  }>(`/jobs/${jobId}/report`);
}

