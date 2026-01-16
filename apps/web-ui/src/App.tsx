import React, { useState } from "react";
import {
  Artifact,
  createJob,
  generateTest,
  getArtifacts,
  getJob,
  getReport,
  runTest,
} from "./api";

type JobRow = {
  jobId: string;
  status: string;
  createdAt: string;
};

export const App: React.FC = () => {
  const [targetUrl, setTargetUrl] = useState("http://sample-app:3000/sample-app/login");
  const [scope, setScope] = useState<"read-only" | "sandbox">("read-only");
  const [testProfile, setTestProfile] = useState("functional");
  const [ownerId, setOwnerId] = useState("demo_user");

  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [testId, setTestId] = useState<string | null>(null);
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateJob = async () => {
    setLoading(true);
    setError(null);
    try {
      const job = await createJob({ targetUrl, scope, testProfile, ownerId });
      setJobs((prev) => [
        ...prev,
        { jobId: job.jobId, status: job.status, createdAt: job.createdAt },
      ]);
      setSelectedJobId(job.jobId);
      setArtifacts([]);
      setTestId(null);
      setReport(null);
    } catch (e: any) {
      setError(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  const refreshJobStatus = async (jobId: string) => {
    try {
      const job = await getJob(jobId);
      setJobs((prev) =>
        prev.map((j) =>
          j.jobId === jobId ? { jobId: job.jobId, status: job.status, createdAt: job.createdAt } : j,
        ),
      );
    } catch (e: any) {
      setError(e.message ?? String(e));
    }
  };

  const loadArtifacts = async (jobId: string) => {
    try {
      const arts = await getArtifacts(jobId);
      setArtifacts(arts);
    } catch (e: any) {
      setError(e.message ?? String(e));
    }
  };

  const handleGenerateTest = async () => {
    if (!selectedJobId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await generateTest(selectedJobId);
      setTestId(res.testId);
      await loadArtifacts(selectedJobId);
    } catch (e: any) {
      setError(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleRunTest = async () => {
    if (!selectedJobId || !testId) return;
    setLoading(true);
    setError(null);
    try {
      await runTest(selectedJobId, testId);
      // Give the runner some time in real usage; here we just let the user click "Refresh report".
    } catch (e: any) {
      setError(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleLoadReport = async () => {
    if (!selectedJobId) return;
    setLoading(true);
    setError(null);
    try {
      const rep = await getReport(selectedJobId);
      setReport(rep);
    } catch (e: any) {
      setError(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  const currentJob = jobs.find((j) => j.jobId === selectedJobId) ?? null;

  return (
    <div className="app">
      <header className="header">
        <h1>Autonomous QA Automation Demo</h1>
        <p>Submit a URL, generate a test, run it, and inspect artifacts.</p>
      </header>

      <main className="layout">
        <section className="panel">
          <h2>Create job</h2>
          <label>
            <span>Target URL</span>
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
            />
          </label>
          <label>
            <span>Scope</span>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as "read-only" | "sandbox")}
            >
              <option value="read-only">read-only</option>
              <option value="sandbox">sandbox</option>
            </select>
          </label>
          <label>
            <span>Test profile</span>
            <input
              type="text"
              value={testProfile}
              onChange={(e) => setTestProfile(e.target.value)}
            />
          </label>
          <label>
            <span>Owner</span>
            <input
              type="text"
              value={ownerId}
              onChange={(e) => setOwnerId(e.target.value)}
            />
          </label>
          <button onClick={handleCreateJob} disabled={loading}>
            Create job
          </button>
          {error && <div className="error">Error: {error}</div>}
        </section>

        <section className="panel">
          <h2>Jobs</h2>
          {jobs.length === 0 && <p>No jobs created yet.</p>}
          {jobs.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr
                    key={j.jobId}
                    className={j.jobId === selectedJobId ? "selected" : ""}
                  >
                    <td>{j.jobId}</td>
                    <td>{j.status}</td>
                    <td>{new Date(j.createdAt).toLocaleString()}</td>
                    <td>
                      <button
                        onClick={() => {
                          setSelectedJobId(j.jobId);
                          refreshJobStatus(j.jobId);
                          loadArtifacts(j.jobId);
                        }}
                      >
                        Select
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>

      {currentJob && (
        <section className="panel">
          <h2>Job details</h2>
          <p>
            <strong>Job ID:</strong> {currentJob.jobId}
          </p>
          <p>
            <strong>Status:</strong> {currentJob.status}
          </p>
          <div className="actions">
            <button onClick={() => refreshJobStatus(currentJob.jobId)} disabled={loading}>
              Refresh status
            </button>
            <button onClick={handleGenerateTest} disabled={loading}>
              Generate test
            </button>
            <button onClick={handleRunTest} disabled={loading || !testId}>
              Run test
            </button>
            <button onClick={handleLoadReport} disabled={loading}>
              Refresh report
            </button>
          </div>

          <div className="columns">
            <div>
              <h3>Artifacts</h3>
              {artifacts.length === 0 && <p>No artifacts loaded yet.</p>}
              <ul>
                {artifacts.map((a) => (
                  <li key={a.path}>
                    <strong>{a.type}</strong> — {a.name} ({a.path})
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3>Latest test report</h3>
              {!report && <p>No report loaded yet.</p>}
              {report && (
                <div className="report">
                  <p>
                    <strong>Status:</strong> {report.status}
                  </p>
                  <p>
                    <strong>Run ID:</strong> {report.runId}
                  </p>
                  <p>
                    <strong>Started:</strong>{" "}
                    {new Date(report.startedAt).toLocaleString()}
                  </p>
                  <p>
                    <strong>Finished:</strong>{" "}
                    {new Date(report.finishedAt).toLocaleString()}
                  </p>
                  <h4>Steps</h4>
                  <ol>
                    {report.steps.map((s: any) => (
                      <li key={s.step}>
                        Step {s.step}: <strong>{s.status}</strong>
                        {s.error && <span> — {s.error}</span>}
                        {s.screenshot && <div>Screenshot: {s.screenshot}</div>}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </div>
        </section>
      )}
    </div>
  );
};

