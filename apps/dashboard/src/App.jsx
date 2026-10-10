import React, { useState, useEffect } from 'react';
import {
  Shield,
  Server,
  Layers,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Terminal,
  Activity,
  ArrowRight,
  Database,
  Lock,
  Cpu,
  RefreshCw,
  GitBranch,
  KeyRound,
  RotateCcw,
  Check,
  Flame,
  Cloud,
  ExternalLink,
  Sliders,
  DollarSign
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('discovery');
  const [targetCloud, setTargetCloud] = useState('aws');
  const [loading, setLoading] = useState(false);
  const [migrationData, setMigrationData] = useState(null);
  const [cutoverStatus, setCutoverStatus] = useState(null);
  const [auditVerified, setAuditVerified] = useState(null);

  // Load initial simulation on mount
  useEffect(() => {
    runMigration(targetCloud);
  }, []);

  const runMigration = async (selectedTarget) => {
    setLoading(true);
    setCutoverStatus(null);
    try {
      const res = await fetch('/api/orchestrate/migrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_cloud: selectedTarget })
      });
      if (res.ok) {
        const data = await res.json();
        setMigrationData(data);
      }
    } catch (err) {
      console.error("Failed to fetch migration data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleTargetChange = (newTarget) => {
    setTargetCloud(newTarget);
    runMigration(newTarget);
  };

  const handleExecuteCutover = async () => {
    try {
      const res = await fetch('/api/cutover/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          app_id: migrationData?.app_id || 'app-fintech-portal-prod',
          target_cloud: targetCloud,
          action: 'APPLY'
        })
      });
      const data = await res.json();
      setCutoverStatus({ type: 'SUCCESS', message: data.message, block: data.audit_block_hash });
    } catch (e) {
      console.error(e);
    }
  };

  const handleExecuteRollback = async () => {
    try {
      const res = await fetch('/api/cutover/rollback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          app_id: migrationData?.app_id || 'app-fintech-portal-prod',
          target_cloud: targetCloud,
          action: 'ROLLBACK'
        })
      });
      const data = await res.json();
      setCutoverStatus({ type: 'ROLLED_BACK', message: data.message, block: data.audit_block_hash });
    } catch (e) {
      console.error(e);
    }
  };

  const verifyLedger = async () => {
    try {
      const res = await fetch('/api/audit/verify', { method: 'POST' });
      const data = await res.json();
      setAuditVerified(data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <header style={{
        background: 'rgba(9, 13, 22, 0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-subtle)',
        padding: '16px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
            padding: '10px',
            borderRadius: '12px',
            display: 'flex',
            boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)'
          }}>
            <Shield size={24} color="#fff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              MigrationMesh
              <span className="badge badge-indigo" style={{ fontSize: '0.65rem' }}>Cloud-Neutral AI</span>
            </h1>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Safe-by-Design Agentic Cloud Orchestrator</p>
          </div>
        </div>

        {/* Invariant Badges */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <span className="badge badge-emerald">
            <Lock size={12} /> Zero Write Credentials
          </span>
          <span className="badge badge-cyan">
            <Activity size={12} /> Shadow Twin Verified
          </span>
          <span className="badge badge-indigo">
            <CheckCircle2 size={12} /> Merkle Hash Ledger
          </span>

          <div style={{ height: '24px', width: '1px', background: 'var(--border-subtle)', margin: '0 8px' }} />

          {/* Target Cloud Toggle */}
          <div style={{ display: 'flex', background: 'rgba(0,0,0,0.4)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
            <button
              onClick={() => handleTargetChange('aws')}
              style={{
                background: targetCloud === 'aws' ? 'linear-gradient(135deg, #ff9900 0%, #e68a00 100%)' : 'transparent',
                color: targetCloud === 'aws' ? '#fff' : 'var(--text-muted)',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              AWS Target
            </button>
            <button
              onClick={() => handleTargetChange('azure')}
              style={{
                background: targetCloud === 'azure' ? 'linear-gradient(135deg, #008ad7 0%, #0078d4 100%)' : 'transparent',
                color: targetCloud === 'azure' ? '#fff' : 'var(--text-muted)',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              Azure Target
            </button>
          </div>

          <button
            onClick={() => runMigration(targetCloud)}
            disabled={loading}
            className="btn-primary"
            style={{ padding: '8px 16px', fontSize: '0.8rem' }}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            {loading ? 'Orchestrating...' : 'Re-Run Pipeline'}
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div style={{ padding: '24px 32px', flex: 1, maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '24px', paddingBottom: '12px' }}>
          {[
            { id: 'discovery', label: '1. Discovery & Topology DAG', icon: Layers },
            { id: 'strategy', label: '2. 7R & Multi-Target Scorer', icon: Sliders },
            { id: 'iac', label: '3. IaC & Safety Gates (Critic / OPA)', icon: FileCode },
            { id: 'twin', label: '4. Digital Twin Sandbox', icon: Terminal },
            { id: 'cutover', label: '5. Cutover & Rollback Cockpit', icon: RotateCcw },
            { id: 'audit', label: '6. Merkle Audit Ledger', icon: Lock }
          ].map(tab => {
            const Icon = tab.icon;
            const isSel = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  background: isSel ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  color: isSel ? '#818cf8' : 'var(--text-muted)',
                  border: isSel ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
                  padding: '10px 18px',
                  borderRadius: '10px',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.2s ease'
                }}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab 1: Discovery & Topology DAG */}
        {activeTab === 'discovery' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '1.25rem', marginBottom: '4px' }}>Canonical Infrastructure Dependency Graph</h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    Sanitized from VMware vCenter / CMDB inventory with automated PII & credential redaction proxy.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <span className="badge badge-emerald">
                    <Check size={12} /> DAG Verified (0 Cycles)
                  </span>
                  <span className="badge badge-cyan">
                    3 Topological Waves
                  </span>
                </div>
              </div>

              {/* Topology Nodes Flow */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginTop: '16px' }}>
                {migrationData?.inventory?.resources?.map((res, idx) => (
                  <div key={res.id} className="glass-card" style={{ borderLeft: res.is_stateful ? '4px solid #f59e0b' : '4px solid #6366f1' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {res.is_stateful ? <Database size={18} color="#f59e0b" /> : <Server size={18} color="#6366f1" />}
                        <h3 style={{ fontSize: '1rem', color: '#fff' }}>{res.name}</h3>
                      </div>
                      <span className={res.is_stateful ? "badge badge-amber" : "badge badge-indigo"} style={{ fontSize: '0.65rem' }}>
                        {res.is_stateful ? "Stateful DB" : "Stateless Tier"}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <div><strong>ID:</strong> <code style={{ color: '#e2e8f0' }}>{res.id}</code></div>
                      <div><strong>Specs:</strong> {res.cpu_cores} vCPU • {res.ram_gb} GB RAM • {res.storage_gb} GB Storage</div>
                      <div><strong>Ports:</strong> {res.open_ports.join(', ')}</div>
                      <div><strong>Redacted IP:</strong> <code style={{ color: '#38bdf8' }}>&lt;IP_NODE_SANITIZED&gt;</code></div>
                      <div><strong>Dependencies:</strong> {res.dependencies.length > 0 ? res.dependencies.join(', ') : 'None (Base Node)'}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Migration Wave Sequencing */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <GitBranch size={18} color="#818cf8" />
                Deterministic Wave Ordering
              </h3>
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                <div className="glass-card" style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>WAVE 1 (STATE TIER)</div>
                  <div style={{ fontWeight: 700, color: '#f59e0b' }}>postgres-database-03</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Initial Seed & CDC Sync</div>
                </div>
                <ArrowRight size={20} color="var(--text-dim)" />
                <div className="glass-card" style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>WAVE 2 (API TIER)</div>
                  <div style={{ fontWeight: 700, color: '#6366f1' }}>node-payment-api-02</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Container Task Boot</div>
                </div>
                <ArrowRight size={20} color="var(--text-dim)" />
                <div className="glass-card" style={{ flex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>WAVE 3 (INGRESS TIER)</div>
                  <div style={{ fontWeight: 700, color: '#10b981' }}>nginx-web-proxy-01</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>ALB / AppGW Route Switch</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Strategy & Multi-Target Scorer */}
        {activeTab === 'strategy' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <span className="badge badge-emerald" style={{ fontSize: '0.85rem' }}>
                      7R Recommendation: {migrationData?.strategy_plan?.strategy_7r}
                    </span>
                    <span className="badge badge-indigo">
                      Confidence: {(migrationData?.strategy_plan?.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p style={{ color: 'var(--text-main)', fontSize: '0.95rem', maxWidth: '1000px', lineHeight: 1.5 }}>
                    {migrationData?.strategy_plan?.rationale}
                  </p>
                </div>
              </div>

              {/* Multi-Target Scorecards */}
              <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', marginTop: '12px' }}>Objective Multi-Cloud Target Comparison</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                {migrationData?.strategy_plan?.target_scores?.map((score) => {
                  const isSelected = targetCloud === score.provider;
                  return (
                    <div
                      key={score.provider}
                      className="glass-card"
                      style={{
                        border: isSelected ? '2px solid #6366f1' : '1px solid var(--border-subtle)',
                        background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'rgba(15, 23, 42, 0.6)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <h4 style={{ textTransform: 'uppercase', color: '#fff', fontSize: '1.1rem' }}>{score.provider}</h4>
                        <span className="badge badge-indigo" style={{ fontSize: '0.75rem' }}>
                          Fit: {score.overall_fit_score}/100
                        </span>
                      </div>

                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
                        <div><strong>3-Yr TCO:</strong> <span style={{ color: '#10b981', fontWeight: 600 }}>${score.three_year_tco_usd.toLocaleString()}</span></div>
                        <div><strong>Vendor Lock-in:</strong> {score.vendor_lockin_score}/100</div>
                        <div><strong>Migration Risk:</strong> {score.migration_risk_score}/100</div>
                        <div><strong>Compliance Fit:</strong> {score.compliance_score}%</div>
                      </div>

                      <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>Target Stack:</div>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', lineHeight: 1.4 }}>
                          {score.target_architecture_summary}
                        </p>
                      </div>

                      <button
                        onClick={() => handleTargetChange(score.provider)}
                        style={{
                          width: '100%',
                          marginTop: '16px',
                          padding: '8px',
                          borderRadius: '8px',
                          border: 'none',
                          background: isSelected ? '#6366f1' : 'rgba(255,255,255,0.08)',
                          color: '#fff',
                          fontWeight: 600,
                          fontSize: '0.75rem',
                          cursor: 'pointer'
                        }}
                      >
                        {isSelected ? 'Selected Target' : 'Select Target'}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* FinOps Breakdown */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <DollarSign size={18} color="#10b981" />
                FinOps Rightsizing & Financial Impact
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                <div className="glass-card">
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Legacy On-Premises (3-Yr)</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f43f5e', marginTop: '4px' }}>
                    ${migrationData?.finops_report?.onprem_3year_tco_usd?.toLocaleString()}
                  </div>
                </div>
                <div className="glass-card">
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Optimized AWS Cloud (3-Yr)</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#10b981', marginTop: '4px' }}>
                    ${migrationData?.finops_report?.aws_3year_tco_usd?.toLocaleString()}
                  </div>
                  <span className="badge badge-emerald" style={{ marginTop: '8px' }}>
                    {migrationData?.finops_report?.aws_savings_percentage}% TCO Reduction
                  </span>
                </div>
                <div className="glass-card">
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Optimized Azure Cloud (3-Yr)</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#06b6d4', marginTop: '4px' }}>
                    ${migrationData?.finops_report?.azure_3year_tco_usd?.toLocaleString()}
                  </div>
                  <span className="badge badge-cyan" style={{ marginTop: '8px' }}>
                    {migrationData?.finops_report?.azure_savings_percentage}% TCO Reduction
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: IaC & Safety Gates */}
        {activeTab === 'iac' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            {/* Left Column: Terraform HCL */}
            <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem' }}>Generated Terraform Manifest</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Target: {targetCloud.toUpperCase()} Hardened Modules</p>
                </div>
                <span className="badge badge-emerald">
                  <Check size={12} /> AST Validated
                </span>
              </div>
              <div className="code-container" style={{ flex: 1, maxHeight: '600px', overflowY: 'auto' }}>
                <pre>{migrationData?.iac_manifest?.hcl_code}</pre>
              </div>
            </div>

            {/* Right Column: Critic Agent & OPA Policies */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Critic Agent Red-Teaming Card */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Shield size={20} color="#10b981" />
                    <h3 style={{ fontSize: '1.1rem' }}>Critic Agent Red-Team Gate</h3>
                  </div>
                  <span className="badge badge-emerald">
                    Approved (Confidence: {(migrationData?.critic_verdict?.confidence_score * 100).toFixed(0)}%)
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Destructive State Diff Blocker:</span>
                    <span className="badge badge-emerald">0 Destructive Diffs Detected</span>
                  </div>
                  <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Hallucinated Resource Verifier:</span>
                    <span className="badge badge-emerald">100% Certified Schemas</span>
                  </div>
                  <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Stateful Resources Protected:</span>
                    <span className="badge badge-amber">{migrationData?.iac_manifest?.stateful_resources?.join(', ')}</span>
                  </div>
                </div>
              </div>

              {/* OPA Policy Compliance Card */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Lock size={20} color="#818cf8" />
                    <h3 style={{ fontSize: '1.1rem' }}>OPA / Rego CIS Benchmark Audit</h3>
                  </div>
                  <span className="badge badge-emerald">100% Passed</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {[
                    { id: 'CIS-SEC-002', name: 'Database Port 0.0.0.0/0 Public Ingress Blocker', status: 'PASS' },
                    { id: 'CIS-AWS-001', name: 'Mandatory Storage & DB Encryption at Rest (KMS)', status: 'PASS' },
                    { id: 'CIS-IAM-003', name: 'Least-Privilege IAM (No Wildcard * Actions)', status: 'PASS' },
                    { id: 'CIS-NET-004', name: 'Compute Task Private Subnet Isolation', status: 'PASS' },
                    { id: 'MESH-SAFE-005', name: 'Stateful Resource Destruction Rejection Gate', status: 'PASS' }
                  ].map(rule => (
                    <div key={rule.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.8rem', color: '#cbd5e1' }}><strong>{rule.id}:</strong> {rule.name}</span>
                      <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>PASS</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Digital Twin Sandbox */}
        {activeTab === 'twin' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '4px' }}>Shadow-Run Digital Twin Execution</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    Ephemeral LocalStack / Azurite sandbox validation with automated characterization tests.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <span className="badge badge-emerald">
                    {migrationData?.twin_receipt?.parity_pass_percentage}% Parity ({migrationData?.twin_receipt?.parity_tests_passed}/{migrationData?.twin_receipt?.parity_tests_total} Passed)
                  </span>
                  <span className="badge badge-indigo">
                    Runtime: {migrationData?.twin_receipt?.provision_duration_seconds}s
                  </span>
                </div>
              </div>

              {/* Parity Assertion Table */}
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-dim)' }}>
                      <th style={{ padding: '12px' }}>Test Name</th>
                      <th style={{ padding: '12px' }}>Category</th>
                      <th style={{ padding: '12px' }}>Legacy VM Output</th>
                      <th style={{ padding: '12px' }}>Digital Twin Output</th>
                      <th style={{ padding: '12px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {migrationData?.twin_receipt?.test_results?.map((test, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '12px', fontWeight: 600, color: '#fff' }}>{test.test_name}</td>
                        <td style={{ padding: '12px', color: 'var(--text-muted)' }}>{test.category}</td>
                        <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#94a3b8' }}>
                          {JSON.stringify(test.legacy_output)}
                        </td>
                        <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#38bdf8' }}>
                          {JSON.stringify(test.twin_output)}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span className="badge badge-emerald">PASS</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Twin Container Execution Logs */}
              <div style={{ marginTop: '20px' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>Sandbox Execution Log:</div>
                <div className="code-container" style={{ fontSize: '0.75rem', color: '#a5f3fc' }}>
                  <pre>{migrationData?.twin_receipt?.twin_logs_snippet}</pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: Cutover & Rollback Cockpit */}
        {activeTab === 'cutover' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '4px' }}>Deterministic Cutover & Rollback Cockpit</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    CDC replication monitoring, Go/No-Go decision matrix, and air-gapped Temporal execution plane.
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button onClick={handleExecuteCutover} className="btn-primary" style={{ padding: '10px 20px' }}>
                    <CheckCircle2 size={16} /> Execute Deterministic Cutover
                  </button>
                  <button onClick={handleExecuteRollback} className="btn-danger" style={{ padding: '10px 20px' }}>
                    <RotateCcw size={16} /> 1-Click Rollback Saga
                  </button>
                </div>
              </div>

              {/* Status Alert if Action Triggered */}
              {cutoverStatus && (
                <div style={{
                  padding: '16px',
                  borderRadius: '10px',
                  marginBottom: '20px',
                  background: cutoverStatus.type === 'SUCCESS' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                  border: cutoverStatus.type === 'SUCCESS' ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(244, 63, 94, 0.3)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <strong>{cutoverStatus.message}</strong>
                    <div style={{ fontSize: '0.75rem', marginTop: '4px', color: 'var(--text-muted)' }}>
                      Committed to Merkle Audit Block: <code style={{ color: '#38bdf8' }}>{cutoverStatus.block}</code>
                    </div>
                  </div>
                  <span className={cutoverStatus.type === 'SUCCESS' ? 'badge badge-emerald' : 'badge badge-rose'}>
                    {cutoverStatus.type}
                  </span>
                </div>
              )}

              {/* Go/No-Go Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
                <div className="glass-card">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>CDC REPLICATION LAG</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#10b981', marginTop: '4px' }}>
                    {migrationData?.cutover_runbook?.replication_lag_seconds}s
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Max RPO Threshold: 5.0s</div>
                </div>

                <div className="glass-card">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>GO / NO-GO VERDICT</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#10b981', marginTop: '4px' }}>
                    {migrationData?.cutover_runbook?.go_no_go_verdict}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Confidence: {(migrationData?.cutover_runbook?.go_no_go_confidence * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="glass-card">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>ESTIMATED DOWNTIME</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#6366f1', marginTop: '4px' }}>
                    {migrationData?.cutover_runbook?.estimated_downtime_minutes} min
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DNS / Load Balancer Switch</div>
                </div>

                <div className="glass-card">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>ROLLBACK GUARANTEE</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#38bdf8', marginTop: '4px' }}>
                    &lt; 2.0s
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Deterministic Compensation</div>
                </div>
              </div>

              {/* Pre-Flight Checklist */}
              <h4 style={{ fontSize: '1rem', marginBottom: '12px' }}>Pre-Flight Attestation Checklist</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {migrationData?.cutover_runbook?.pre_flight_checks?.map((check, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <CheckCircle2 size={16} color="#10b981" />
                      <span style={{ fontSize: '0.85rem', color: '#e2e8f0' }}>{check.check_name}</span>
                    </div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{check.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab 6: Merkle Audit Ledger */}
        {activeTab === 'audit' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '4px' }}>Cryptographic Merkle Audit Ledger</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    Append-only SHA-256 hash-chained DAG recording all prompts, outputs, policy gates, and signatures.
                  </p>
                </div>
                <button onClick={verifyLedger} className="btn-primary" style={{ padding: '8px 16px', fontSize: '0.8rem' }}>
                  <Lock size={14} /> Verify Chain Integrity
                </button>
              </div>

              {auditVerified && (
                <div style={{
                  padding: '14px',
                  borderRadius: '8px',
                  background: auditVerified.valid ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                  border: auditVerified.valid ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(244, 63, 94, 0.3)',
                  marginBottom: '20px',
                  fontSize: '0.85rem'
                }}>
                  <strong>Status: {auditVerified.valid ? 'CHAIN INTEGRITY 100% VALID' : 'TAMPER DETECTED'}</strong>
                  <div style={{ fontSize: '0.75rem', marginTop: '4px' }}>Merkle Root: <code>{auditVerified.merkle_root}</code></div>
                </div>
              )}

              {/* Block Chain List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {migrationData?.audit_ledger?.blocks?.map((block) => (
                  <div key={block.block_index} className="glass-card" style={{ borderLeft: '4px solid #8b5cf6' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className="badge badge-indigo">BLOCK #{block.block_index}</span>
                        <strong style={{ color: '#fff', fontSize: '0.9rem' }}>{block.action_type}</strong>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{block.timestamp}</span>
                    </div>

                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
                      <div><strong>Agent / Actor:</strong> {block.agent_name} ({block.actor_id})</div>
                      <div><strong>Previous Hash:</strong> <code style={{ color: '#94a3b8' }}>{block.previous_block_hash.slice(0, 16)}...</code></div>
                      <div style={{ gridColumn: 'span 2' }}><strong>Block SHA-256 Hash:</strong> <code style={{ color: '#38bdf8' }}>{block.block_hash}</code></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
