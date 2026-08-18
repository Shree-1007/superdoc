import React, { useState } from 'react';

const PIPELINE_STEPS = [
  { id: 'ingest', label: 'Document Ingestion', desc: 'Parsing mixed-format documents' },
  { id: 'extract', label: 'Fact Extraction', desc: 'AI-powered entity & clause extraction' },
  { id: 'check', label: 'Rule Validation', desc: 'Cross-referencing against playbook' },
  { id: 'review', label: 'Human Review', desc: 'Expert validation checkpoint' },
  { id: 'deliver', label: 'Deliverable Generation', desc: 'Grounded compliance report' },
];

function getStepStatus(stepId, appStatus) {
  if (appStatus === 'idle') return 'idle';
  if (appStatus === 'running') {
    const runOrder = ['ingest', 'extract', 'check'];
    if (runOrder.includes(stepId)) return 'done';
    if (stepId === 'review') return 'active';
    return 'idle';
  }
  if (appStatus === 'review') {
    const doneSteps = ['ingest', 'extract', 'check'];
    if (doneSteps.includes(stepId)) return 'done';
    if (stepId === 'review') return 'review';
    return 'idle';
  }
  if (appStatus === 'completed') return 'done';
  return 'idle';
}

function StepIcon({ status }) {
  if (status === 'done') {
    return (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <path d="M2.5 6L5 8.5L9.5 3.5" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (status === 'active' || status === 'review') {
    return <span className="spinner" style={{ width: '10px', height: '10px', borderWidth: '1.5px' }}></span>;
  }
  return <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'rgba(255,255,255,0.15)' }}></div>;
}

function PipelineVisualization({ appStatus }) {
  return (
    <div style={{ marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: appStatus === 'idle' ? 'rgba(255,255,255,0.15)' : '#6366f1' }}></div>
        <span style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)' }}>
          Pipeline Status
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {PIPELINE_STEPS.map((step, i) => {
          const status = getStepStatus(step.id, appStatus);
          return (
            <div key={step.id} className="pipeline-step" style={{ paddingBottom: i < PIPELINE_STEPS.length - 1 ? '0.75rem' : 0 }}>
              <div className={`step-dot step-dot-${status}`}>
                <StepIcon status={status} />
              </div>
              <div>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: status === 'idle' ? 400 : 600,
                  color: status === 'idle' ? 'rgba(255,255,255,0.3)' :
                    status === 'done' ? '#4ade80' :
                      status === 'review' ? '#fbbf24' : '#a5b4fc',
                  transition: 'all 0.3s ease',
                }}>
                  {step.label}
                </div>
                <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.2)', marginTop: '0.1rem' }}>
                  {step.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function FindingCard({ finding, onDecision }) {
  return (
    <div className="finding-card animate-fade-in" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 1L12.5 11H1.5L7 1Z" stroke="#fbbf24" strokeWidth="1.2" strokeLinejoin="round" />
            <path d="M7 5.5V7.5" stroke="#fbbf24" strokeWidth="1.2" strokeLinecap="round" />
            <circle cx="7" cy="9.25" r="0.5" fill="#fbbf24" />
          </svg>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e4ea' }}>{finding.issue}</span>
        </div>
        <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.3)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <rect x="1" y="1" width="8" height="8" rx="1.5" stroke="rgba(255,255,255,0.25)" strokeWidth="0.8" />
            <path d="M3 3H7M3 5H6M3 7H5" stroke="rgba(255,255,255,0.25)" strokeWidth="0.6" strokeLinecap="round" />
          </svg>
          {finding.source}
        </div>
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
        <button
          onClick={() => onDecision(finding.id, 'approved')}
          className={`btn-approve ${finding.status === 'approved' ? 'active' : ''}`}
        >
          ✓ Approve
        </button>
        <button
          onClick={() => onDecision(finding.id, 'rejected')}
          className={`btn-reject ${finding.status === 'rejected' ? 'active' : ''}`}
        >
          ✕ Reject
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [threadId, setThreadId] = useState(`run-${Math.floor(Math.random() * 10000)}`);
  const [status, setStatus] = useState('idle');
  const [findings, setFindings] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [injectionFlags, setInjectionFlags] = useState([]);
  const [deliverable, setDeliverable] = useState(null);
  const [costReport, setCostReport] = useState(null);
  const [error, setError] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      for (let f of files) formData.append('files', f);
      const res = await fetch('http://localhost:8000/api/documents/upload', {
        method: 'POST', body: formData
      });
      const data = await res.json();
      setUploadedFiles(prev => [...prev, ...(data.files || [])]);
    } catch (err) {
      setError('Upload failed: ' + err.message);
    }
    setUploading(false);
  };

  const startAgentRun = async () => {
    setStatus('running');
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/api/run/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Start failed');

      setConflicts(data.conflicts || []);
      setInjectionFlags(data.injection_flags || []);

      if (data.status === 'paused_for_review') {
        setFindings(data.findings || []);
        setStatus('review');
      } else if (data.status === 'completed') {
        setDeliverable(data.deliverable);
        setFindings(data.findings || []);
        setStatus('completed');
        fetchCostReport();
      } else if (data.status === 'error') {
        setError(data.error);
        setStatus('idle');
      }
    } catch (err) {
      console.error("Failed to start run:", err);
      setError(err.message);
      setStatus('idle');
    }
  };

  const killAgentRun = async () => {
    try {
      await fetch(`http://localhost:8000/api/run/kill/${threadId}`, { method: 'POST' });
    } catch (err) {
      console.error("Failed to send kill signal:", err);
    }
  };

  const resumeAgentRun = async () => {
    setStatus('running');
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/run/resume/${threadId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Resume failed');
      
      setConflicts(data.conflicts || []);
      setInjectionFlags(data.injection_flags || []);

      if (data.status === 'paused_for_review') {
        setFindings(data.findings || []);
        setStatus('review');
      } else if (data.status === 'completed') {
        setDeliverable(data.deliverable);
        setFindings(data.findings || []);
        setStatus('completed');
        fetchCostReport();
      } else if (data.status === 'error') {
        setError(data.error);
        setStatus('idle');
      }
    } catch (err) {
      console.error("Failed to resume run:", err);
      setError(err.message);
      setStatus('idle');
    }
  };

  const handleDecision = (id, decision) => {
    setFindings(findings.map(f =>
      f.id === id ? { ...f, status: decision } : f
    ));
  };

  const submitReview = async () => {
    setStatus('running');
    try {
      const res = await fetch(`http://localhost:8000/api/run/submit_review/${threadId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ findings, conflicts })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Submit review failed');
      setDeliverable(data.deliverable);
      setStatus('completed');
      fetchCostReport();
    } catch (err) {
      console.error("Failed to submit review:", err);
      setError(err.message);
      setStatus('idle');
    }
  };

  const fetchCostReport = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/run/cost/${threadId}`);
      if (res.ok) setCostReport(await res.json());
    } catch (e) { /* non-critical */ }
  };

  const resetRun = () => {
    setStatus('idle');
    setThreadId(`run-${Math.floor(Math.random() * 10000)}`);
    setFindings([]);
    setConflicts([]);
    setInjectionFlags([]);
    setDeliverable(null);
    setCostReport(null);
    setError(null);
    setUploadedFiles([]);
  };

  const downloadReport = () => {
    if (!deliverable) return;
    const blob = new Blob([deliverable], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SuperDocs_Report_${threadId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-grid" style={{ minHeight: '100vh', position: 'relative', padding: '2rem 1rem' }}>
      {/* Ambient background glows */}
      <div className="bg-glow"></div>
      <div className="bg-glow-2"></div>

      {/* Main Container */}
      <div style={{ maxWidth: '56rem', margin: '0 auto', position: 'relative', zIndex: 1 }}>

        {/* Header */}
        <div style={{ marginBottom: '2rem', animation: 'fade-in 0.6s ease-out' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{
              width: 36, height: 36, borderRadius: '0.75rem',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 24px -4px rgba(99, 102, 241, 0.4)',
            }}>
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M3 5L9 2L15 5V13L9 16L3 13V5Z" stroke="white" strokeWidth="1.3" strokeLinejoin="round" />
                <path d="M3 5L9 8M9 8L15 5M9 8V16" stroke="white" strokeWidth="1.3" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.03em', color: '#ffffff' }}>
                SuperDocs
              </h1>
              <p style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.3)', letterSpacing: '0.05em', textTransform: 'uppercase', fontWeight: 500 }}>
                Agentic Compliance Engine
              </p>
            </div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '1.5rem', alignItems: 'start' }}>

          {/* Left Sidebar - Pipeline + Controls */}
          <div className="glass-elevated" style={{ borderRadius: '1rem', padding: '1.5rem' }}>
            <PipelineVisualization appStatus={status} />

            {/* Start Button */}
            <button
              onClick={startAgentRun}
              disabled={status !== 'idle'}
              className="btn-primary"
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
            >
              {status === 'running' ? (
                <>
                  <span className="spinner"></span>
                  Processing…
                </>
              ) : status === 'idle' ? (
                <>
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M4 2L12 7L4 12V2Z" fill="white" />
                  </svg>
                  Start Analysis
                </>
              ) : (
                'In Progress'
              )}
            </button>

            {/* Kill & Resume Buttons */}
            {status === 'running' && (
              <button
                onClick={killAgentRun}
                style={{
                  width: '100%', marginTop: '0.75rem', padding: '0.6rem',
                  background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)',
                  color: '#f87171', borderRadius: '0.5rem', fontSize: '0.8rem', fontWeight: 600,
                  cursor: 'pointer', transition: 'all 0.2s ease'
                }}
                onMouseEnter={e => e.target.style.background = 'rgba(239, 68, 68, 0.2)'}
                onMouseLeave={e => e.target.style.background = 'rgba(239, 68, 68, 0.1)'}
              >
                ✕ Simulate Server Crash
              </button>
            )}

            {status === 'idle' && error && error.includes('Simulated Crash') && (
              <button
                onClick={resumeAgentRun}
                className="btn-confirm"
                style={{ width: '100%', marginTop: '0.75rem', padding: '0.6rem', fontSize: '0.8rem' }}
              >
                ↻ Resume from Checkpoint
              </button>
            )}

            {/* Status */}
            <div style={{ marginTop: '1rem', textAlign: 'center' }}>
              <span className="status-badge" style={{
                background: status === 'idle' ? 'rgba(255,255,255,0.05)' :
                  status === 'review' ? 'rgba(251, 191, 36, 0.15)' :
                    status === 'completed' ? 'rgba(34, 197, 94, 0.15)' :
                      'rgba(99, 102, 241, 0.15)',
                color: status === 'idle' ? 'rgba(255,255,255,0.4)' :
                  status === 'review' ? '#fbbf24' :
                    status === 'completed' ? '#4ade80' :
                      '#a5b4fc',
              }}>
                {status === 'idle' ? 'Ready' :
                  status === 'running' ? 'Executing' :
                    status === 'review' ? 'Awaiting Review' :
                      'Complete'}
              </span>
            </div>
          </div>

          {/* Right Panel - Content */}
          <div style={{ minHeight: '400px' }}>

            {/* Idle State */}
            {status === 'idle' && (
              <div className="animate-fade-in">
                {/* Upload Area */}
                <div className="glass" style={{
                  borderRadius: '1rem', padding: '2rem', marginBottom: '1rem',
                  border: '1px dashed rgba(99, 102, 241, 0.25)',
                  textAlign: 'center', cursor: 'pointer', transition: 'all 0.3s ease',
                }}
                  onDragOver={e => { e.preventDefault(); e.currentTarget.style.borderColor = 'rgba(99,102,241,0.6)'; e.currentTarget.style.background = 'rgba(99,102,241,0.05)'; }}
                  onDragLeave={e => { e.currentTarget.style.borderColor = 'rgba(99,102,241,0.25)'; e.currentTarget.style.background = ''; }}
                  onDrop={e => {
                    e.preventDefault();
                    e.currentTarget.style.borderColor = 'rgba(99,102,241,0.25)';
                    e.currentTarget.style.background = '';
                    const dt = e.dataTransfer;
                    const input = document.createElement('input');
                    input.type = 'file'; input.files = dt.files;
                    handleFileUpload({ target: input });
                  }}
                  onClick={() => document.getElementById('file-input').click()}
                >
                  <input id="file-input" type="file" multiple accept=".pdf,.docx,.txt,.doc"
                    style={{ display: 'none' }} onChange={handleFileUpload} />
                  <div style={{
                    width: 48, height: 48, borderRadius: '0.75rem',
                    background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.15)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 1rem',
                  }}>
                    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                      <path d="M11 4V14M7 8L11 4L15 8" stroke="rgba(165, 180, 252, 0.6)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      <path d="M4 14V16C4 17.1 4.9 18 6 18H16C17.1 18 18 17.1 18 16V14" stroke="rgba(165, 180, 252, 0.4)" strokeWidth="1.3" strokeLinecap="round" />
                    </svg>
                  </div>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#e2e4ea', marginBottom: '0.35rem' }}>
                    {uploading ? 'Uploading…' : 'Upload Documents'}
                  </h3>
                  <p style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.3)', lineHeight: 1.5 }}>
                    Drag & drop PDF, DOCX, or TXT files here, or click to browse.<br/>
                    Leave empty to use the sample documents in the watched folder.
                  </p>
                </div>

                {/* Uploaded Files List */}
                {uploadedFiles.length > 0 && (
                  <div className="glass" style={{ borderRadius: '0.75rem', padding: '1rem', marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.3)', marginBottom: '0.5rem' }}>
                      {uploadedFiles.length} Document{uploadedFiles.length !== 1 ? 's' : ''} Ready
                    </div>
                    {uploadedFiles.map((f, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', padding: '0.35rem 0', borderTop: i > 0 ? '1px solid rgba(255,255,255,0.04)' : 'none' }}>
                        <span style={{ color: '#a5b4fc' }}>{f.filename}</span>
                        <span style={{ color: 'rgba(255,255,255,0.25)', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.65rem' }}>
                          {f.error ? '⚠ Error' : `${(f.size_bytes / 1024).toFixed(1)} KB`}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Ready Info */}
                <div className="glass" style={{
                  borderRadius: '1rem', padding: '1.5rem', textAlign: 'center',
                }}>
                  <div style={{
                    width: 48, height: 48, borderRadius: '0.75rem',
                    background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.15)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 1rem',
                  }}>
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <rect x="3" y="2" width="10" height="14" rx="1.5" stroke="rgba(165, 180, 252, 0.5)" strokeWidth="1.2" />
                      <rect x="7" y="4" width="10" height="14" rx="1.5" stroke="rgba(165, 180, 252, 0.5)" strokeWidth="1.2" fill="rgba(99,102,241,0.05)" />
                    </svg>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.3)', maxWidth: '20rem', lineHeight: 1.6, margin: '0 auto' }}>
                    Click <strong style={{ color: '#a5b4fc' }}>Start Analysis</strong> to run the AI-powered pipeline with <strong style={{ color: '#a5b4fc' }}>Gemini Flash</strong>.
                    {uploadedFiles.length === 0 && ' Sample documents will be loaded from the watched folder.'}
                  </p>
                </div>
              </div>
            )}

            {/* Running State */}
            {status === 'running' && (
              <div className="glass" style={{
                borderRadius: '1rem', padding: '3rem 2rem', textAlign: 'center',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                minHeight: '400px',
              }}>
                <div style={{ marginBottom: '1.5rem' }}>
                  <span className="spinner" style={{ width: '2.5rem', height: '2.5rem', borderWidth: '2.5px' }}></span>
                </div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#a5b4fc', marginBottom: '0.5rem' }}>
                  Pipeline Executing…
                </h2>
                <p style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.3)' }}>
                  Processing documents through the compliance engine
                </p>
              </div>
            )}

            {/* Review State */}
            {status === 'review' && (
              <div className="animate-slide-up">
                {/* Review Header */}
                <div className="glass-elevated" style={{
                  borderRadius: '1rem', padding: '1.5rem', marginBottom: '1rem',
                  borderColor: 'rgba(251, 191, 36, 0.15)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                    <div style={{
                      width: 32, height: 32, borderRadius: '0.5rem',
                      background: 'rgba(251, 191, 36, 0.1)',
                      border: '1px solid rgba(251, 191, 36, 0.2)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <circle cx="8" cy="8" r="6" stroke="#fbbf24" strokeWidth="1.3" />
                        <path d="M8 5V8.5" stroke="#fbbf24" strokeWidth="1.3" strokeLinecap="round" />
                        <circle cx="8" cy="11" r="0.75" fill="#fbbf24" />
                      </svg>
                    </div>
                    <div>
                      <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#fbbf24' }}>
                        Human Review Required
                      </h2>
                      <p style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.35)' }}>
                        {findings.length} finding{findings.length !== 1 ? 's' : ''} flagged · Approve or reject before generating the deliverable
                      </p>
                    </div>
                  </div>
                </div>

                {/* Finding Cards */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
                  {findings.map((finding) => (
                    <FindingCard key={finding.id} finding={finding} onDecision={handleDecision} />
                  ))}
                </div>

                {/* Conflict Cards */}
                {conflicts.length > 0 && (
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(249,115,22,0.6)', marginBottom: '0.5rem' }}>
                      Document Conflicts
                    </div>
                    {conflicts.map((c) => (
                      <div key={c.id} className="finding-card" style={{ marginBottom: '0.5rem', borderColor: 'rgba(249,115,22,0.15)' }}>
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fb923c', marginBottom: '0.25rem' }}>{c.description}</div>
                        <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.3)' }}>
                          {c.source_a} vs {c.source_b}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Injection Warnings */}
                {injectionFlags.length > 0 && (
                  <div className="finding-card" style={{ marginBottom: '1rem', borderColor: 'rgba(239,68,68,0.2)', background: 'rgba(239,68,68,0.05)' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f87171', marginBottom: '0.25rem' }}>
                      ⚠ {injectionFlags.length} Injection Pattern{injectionFlags.length !== 1 ? 's' : ''} Detected
                    </div>
                    <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.3)' }}>
                      Treated as document data, not system commands.
                    </div>
                  </div>
                )}

                {/* Confirm Button */}
                <button onClick={submitReview} className="btn-confirm">
                  Confirm Decisions & Generate Deliverable →
                </button>
              </div>
            )}

            {/* Completed State */}
            {status === 'completed' && (
              <div className="animate-slide-up">
                {/* Success Header */}
                <div className="glass-elevated" style={{
                  borderRadius: '1rem', padding: '1.5rem', marginBottom: '1rem',
                  borderColor: 'rgba(34, 197, 94, 0.15)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{
                      width: 32, height: 32, borderRadius: '0.5rem',
                      background: 'rgba(34, 197, 94, 0.1)',
                      border: '1px solid rgba(34, 197, 94, 0.2)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <circle cx="8" cy="8" r="6" stroke="#22c55e" strokeWidth="1.3" />
                        <path d="M5.5 8L7 9.5L10.5 6" stroke="#22c55e" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <div>
                      <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#4ade80' }}>
                        Analysis Complete
                      </h2>
                      <p style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.35)' }}>
                        Grounded compliance report generated successfully
                      </p>
                    </div>
                  </div>
                </div>

                {/* Deliverable */}
                <div className="glass" style={{ borderRadius: '1rem', padding: '1.5rem', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <rect x="1" y="1" width="10" height="10" rx="2" stroke="rgba(255,255,255,0.25)" strokeWidth="0.8" />
                        <path d="M3.5 4H8.5M3.5 6H7.5M3.5 8H5.5" stroke="rgba(255,255,255,0.25)" strokeWidth="0.6" strokeLinecap="round" />
                      </svg>
                      <span style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.3)' }}>
                        Generated Report
                      </span>
                    </div>
                    <button
                      onClick={downloadReport}
                      style={{
                        background: 'rgba(99, 102, 241, 0.1)',
                        border: '1px solid rgba(99, 102, 241, 0.2)',
                        color: '#a5b4fc',
                        padding: '0.3rem 0.6rem',
                        borderRadius: '0.5rem',
                        fontSize: '0.65rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        transition: 'all 0.2s ease',
                      }}
                      onMouseEnter={e => e.target.style.background = 'rgba(99, 102, 241, 0.2)'}
                      onMouseLeave={e => e.target.style.background = 'rgba(99, 102, 241, 0.1)'}
                    >
                      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                        <path d="M5 1V7M5 7L2.5 4.5M5 7L7.5 4.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M1 9H9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                      </svg>
                      Download
                    </button>
                  </div>
                  <div className="deliverable-content">
                    {deliverable}
                  </div>
                </div>

                {/* Cost Report (Requirement 10) */}
                {costReport && (
                  <div className="glass" style={{ borderRadius: '1rem', padding: '1.25rem', marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <circle cx="6" cy="6" r="5" stroke="rgba(255,255,255,0.25)" strokeWidth="0.8" />
                        <path d="M6 3V6L8 7.5" stroke="rgba(255,255,255,0.25)" strokeWidth="0.8" strokeLinecap="round" />
                      </svg>
                      <span style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.3)' }}>
                        Cost Report · {costReport.total_duration_seconds}s total
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                      {costReport.stages.map((s, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem' }}>
                          <span style={{ color: 'rgba(255,255,255,0.4)', fontFamily: "'JetBrains Mono', monospace" }}>{s.stage}</span>
                          <span style={{ color: s.status === 'success' ? '#4ade80' : '#f87171', fontFamily: "'JetBrains Mono', monospace" }}>
                            {s.duration_seconds}s
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* New Run Button */}
                <button
                  onClick={resetRun}
                  style={{
                    background: 'transparent',
                    border: '1px solid rgba(255,255,255,0.08)',
                    color: 'rgba(255,255,255,0.5)',
                    padding: '0.75rem 1.5rem',
                    borderRadius: '0.75rem',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    fontWeight: 500,
                    transition: 'all 0.2s ease',
                    width: '100%',
                  }}
                  onMouseEnter={e => { e.target.style.borderColor = 'rgba(99,102,241,0.3)'; e.target.style.color = '#a5b4fc'; }}
                  onMouseLeave={e => { e.target.style.borderColor = 'rgba(255,255,255,0.08)'; e.target.style.color = 'rgba(255,255,255,0.5)'; }}
                >
                  ↻ Start New Analysis
                </button>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="finding-card animate-fade-in" style={{ borderColor: 'rgba(239,68,68,0.2)', background: 'rgba(239,68,68,0.05)', marginTop: '1rem' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f87171', marginBottom: '0.25rem' }}>Error</div>
                <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', fontFamily: "'JetBrains Mono', monospace" }}>{error}</div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: '3rem', fontSize: '0.65rem', color: 'rgba(255,255,255,0.15)' }}>
          SuperDocs Agentic System · Human-in-the-Loop Compliance Engine · v1.0
        </div>
      </div>
    </div>
  );
}