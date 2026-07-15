import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = 'http://127.0.0.1:8001'

const initialForm = {
  victim_id: 'V1001',
  scam_text:
    'This is CBI. Your Aadhaar is linked to money laundering. Join a video call immediately or you will be digitally arrested. Transfer money for verification.',
  channel: 'telegram',
  user_id: 'U1001',
  amount: '50000',
  average_amount: '5000',
  location: 'Mumbai',
  usual_location: 'Delhi',
  device_id: 'D999',
  known_device: false,
  transaction_hour: '2',
  merchant_category: 'wire transfer',
  failed_attempts: '4',
  recent_scam_risk: '70',
}

const initialSummary = {
  total_cases: 0,
  critical_cases: 0,
  high_cases: 0,
  medium_cases: 0,
  low_cases: 0,
  alerts_sent: 0,
  average_risk_score: 0,
}

function LLMAnalysisPanel({ llmResult, hybridAnalysis }) {
  if (!llmResult) {
    return (
      <section className="llm-panel fallback-panel">
        <div className="llm-panel-header">
          <div>
            <p className="label">GEMINI INTELLIGENCE</p>
            <h3>LLM analysis not stored</h3>
          </div>

          <span className="llm-status fallback">Fallback</span>
        </div>

        <p className="llm-description">
          This case was created before Gemini integration. The rule and
          transaction engines remain available.
        </p>
      </section>
    )
  }

  if (llmResult.status !== 'completed' || !llmResult.analysis) {
    return (
      <section className="llm-panel fallback-panel">
        <div className="llm-panel-header">
          <div>
            <p className="label">GEMINI INTELLIGENCE</p>
            <h3>Safe fallback used</h3>
          </div>

          <span className="llm-status fallback">Fallback</span>
        </div>

        <p className="llm-description">
          {llmResult.reason ||
            'Gemini was unavailable, so deterministic analysis was used.'}
        </p>

        <div className="llm-meta-grid">
          <div>
            <span>Provider</span>
            <strong>{llmResult.provider || 'Google Gemini'}</strong>
          </div>

          <div>
            <span>Model</span>
            <strong>{llmResult.model || 'Not available'}</strong>
          </div>
        </div>
      </section>
    )
  }

  const analysis = llmResult.analysis
  const confidence = Math.round((analysis.confidence || 0) * 100)

  return (
    <section className="llm-panel">
      <div className="llm-panel-header">
        <div>
          <p className="label">GEMINI INTELLIGENCE</p>
          <h3>{analysis.scam_type || 'Contextual Fraud Analysis'}</h3>
        </div>

        <span className="llm-status completed">Completed</span>
      </div>

      <div className="llm-score-grid">
        <div>
          <span>Gemini Risk Score</span>
          <strong>{analysis.risk_score ?? 0}/100</strong>
        </div>

        <div>
          <span>Confidence</span>
          <strong>{confidence}%</strong>
        </div>

        <div>
          <span>Verdict</span>
          <strong className="formatted-value">
            {String(analysis.verdict || 'Not available').replaceAll(
              '_',
              ' ',
            )}
          </strong>
        </div>

        <div>
          <span>Analysis Mode</span>
          <strong className="formatted-value">
            {String(
              hybridAnalysis?.analysis_mode || 'hybrid',
            ).replaceAll('_', ' ')}
          </strong>
        </div>
      </div>

      <div className="llm-section">
        <h4>Reasoning Summary</h4>
        <p>{analysis.reasoning_summary}</p>
      </div>

      <div className="llm-section">
        <h4>Gemini Evidence</h4>

        <div className="evidence-list">
          {analysis.evidence?.length > 0 ? (
            analysis.evidence.map((item) => (
              <span key={item}>{item}</span>
            ))
          ) : (
            <p>No Gemini evidence recorded.</p>
          )}
        </div>
      </div>

      <div className="llm-section">
        <h4>Manipulation Tactics</h4>

        <div className="tactic-list">
          {analysis.manipulation_tactics?.length > 0 ? (
            analysis.manipulation_tactics.map((item) => (
              <span key={item}>{item}</span>
            ))
          ) : (
            <p>No manipulation tactics recorded.</p>
          )}
        </div>
      </div>

      <div className="llm-action">
        <span>Gemini Recommended Action</span>
        <p>{analysis.recommended_action}</p>
      </div>

      <div className="llm-footer">
        <span>
          Model: {llmResult.model || 'Google Gemini'}
        </span>

        <span>
          Latency: {llmResult.latency_ms ?? 0} ms
        </span>

        <span>
          Language: {analysis.detected_language || 'Not available'}
        </span>
      </div>
    </section>
  )
}

function HybridScorePanel({ hybridAnalysis }) {
  if (!hybridAnalysis) {
    return null
  }

  return (
    <section className="hybrid-panel">
      <div className="hybrid-heading">
        <div>
          <p className="label">HYBRID RISK ENGINE</p>
          <h3>Explainable Score Composition</h3>
        </div>

        <span className="hybrid-mode">
          {String(hybridAnalysis.analysis_mode || 'hybrid').replaceAll(
            '_',
            ' ',
          )}
        </span>
      </div>

      <div className="hybrid-score-grid">
        <div>
          <span>Rule Engine</span>
          <strong>{hybridAnalysis.rule_engine_score ?? 0}/100</strong>
        </div>

        <div>
          <span>Gemini LLM</span>
          <strong>
            {hybridAnalysis.llm_risk_score === null ||
            hybridAnalysis.llm_risk_score === undefined
              ? 'Unavailable'
              : `${hybridAnalysis.llm_risk_score}/100`}
          </strong>
        </div>

        <div>
          <span>Transaction Engine</span>
          <strong>
            {hybridAnalysis.transaction_risk_score ?? 0}/100
          </strong>
        </div>

        <div>
          <span>Final Hybrid Score</span>
          <strong>
            {hybridAnalysis.final_risk_score ?? 0}/100
          </strong>
        </div>
      </div>

      <p className="hybrid-explanation">
        {hybridAnalysis.explanation}
      </p>
    </section>
  )
}

function App() {
  const [activePage, setActivePage] = useState('analyze')
  const [form, setForm] = useState(initialForm)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [summary, setSummary] = useState(initialSummary)
  const [cases, setCases] = useState([])
  const [selectedCase, setSelectedCase] = useState(null)
  const [dashboardLoading, setDashboardLoading] = useState(false)
  const [dashboardError, setDashboardError] = useState('')

  const [complaintLoading, setComplaintLoading] = useState(false)
  const [complaintError, setComplaintError] = useState('')

  const [searchText, setSearchText] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')
  const [alertFilter, setAlertFilter] = useState('all')

  const filteredCases = cases.filter((caseItem) => {
    const searchValue = searchText.trim().toLowerCase()

    const matchesSearch =
      searchValue === '' ||
      caseItem.case_id?.toLowerCase().includes(searchValue) ||
      caseItem.victim_id?.toLowerCase().includes(searchValue) ||
      caseItem.priority?.toLowerCase().includes(searchValue) ||
      caseItem.scam_verdict?.toLowerCase().includes(searchValue) ||
      caseItem.transaction_decision
        ?.toLowerCase()
        .includes(searchValue)

    const matchesRisk =
      riskFilter === 'all' ||
      caseItem.risk_level?.toLowerCase() === riskFilter

    const matchesAlert =
      alertFilter === 'all' ||
      caseItem.alert_status?.toLowerCase() === alertFilter

    return matchesSearch && matchesRisk && matchesAlert
  })

  function handleChange(event) {
    const { name, value, type, checked } = event.target

    setForm({
      ...form,
      [name]: type === 'checkbox' ? checked : value,
    })
  }

  function clearFilters() {
    setSearchText('')
    setRiskFilter('all')
    setAlertFilter('all')
  }

  async function loadCaseDetails(caseId) {
    setDashboardError('')
    setComplaintError('')

    try {
      const response = await fetch(
        `${API_BASE_URL}/cases/${encodeURIComponent(caseId)}`,
      )

      if (!response.ok) {
        throw new Error('Unable to load case details')
      }

      const caseData = await response.json()
      setSelectedCase(caseData)
    } catch (requestError) {
      setDashboardError(
        requestError.message || 'Unable to load case details',
      )
    }
  }

  async function loadDashboard() {
    setDashboardLoading(true)
    setDashboardError('')

    try {
      const [summaryResponse, casesResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/dashboard-summary`),
        fetch(`${API_BASE_URL}/cases?limit=100`),
      ])

      if (!summaryResponse.ok || !casesResponse.ok) {
        throw new Error('Unable to load dashboard data')
      }

      const summaryData = await summaryResponse.json()
      const casesData = await casesResponse.json()
      const caseList = casesData.cases || []

      setSummary(summaryData)
      setCases(caseList)

      if (caseList.length > 0) {
        const selectedCaseExists = caseList.some(
          (caseItem) => caseItem.case_id === selectedCase?.case_id,
        )

        if (!selectedCaseExists) {
          await loadCaseDetails(caseList[0].case_id)
        }
      } else {
        setSelectedCase(null)
      }
    } catch (requestError) {
      setDashboardError(
        requestError.message || 'Unable to load case history',
      )
    } finally {
      setDashboardLoading(false)
    }
  }

  useEffect(() => {
    if (activePage === 'dashboard') {
      loadDashboard()
    }
  }, [activePage])

  async function handleSubmit(event) {
    event.preventDefault()

    setLoading(true)
    setError('')
    setResult(null)

    const payload = {
      victim_id: form.victim_id,
      scam_text: form.scam_text,
      channel: form.channel,
      transaction: {
        user_id: form.user_id,
        amount: Number(form.amount),
        average_amount: Number(form.average_amount),
        location: form.location,
        usual_location: form.usual_location,
        device_id: form.device_id,
        known_device: form.known_device,
        transaction_hour: Number(form.transaction_hour),
        merchant_category: form.merchant_category,
        failed_attempts: Number(form.failed_attempts),
        recent_scam_risk: Number(form.recent_scam_risk),
      },
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/generate-case-report-with-alert`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail
            ? JSON.stringify(data.detail)
            : 'Fraud analysis request failed',
        )
      }

      setResult(data)
    } catch (requestError) {
      setError(
        requestError.message ||
          'Unable to connect to the SurakshaNet backend',
      )
    } finally {
      setLoading(false)
    }
  }

  async function downloadComplaint(caseId) {
    if (!caseId) {
      return
    }

    setComplaintLoading(true)
    setComplaintError('')

    try {
      const response = await fetch(
        `${API_BASE_URL}/complaints/${encodeURIComponent(
          caseId,
        )}/download`,
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)

        throw new Error(
          errorData?.detail || 'Unable to generate complaint package',
        )
      }

      const complaintFile = await response.blob()
      const downloadUrl = window.URL.createObjectURL(complaintFile)
      const downloadLink = document.createElement('a')

      downloadLink.href = downloadUrl
      downloadLink.download = `${caseId}-cybercrime-complaint.txt`

      document.body.appendChild(downloadLink)
      downloadLink.click()
      downloadLink.remove()

      window.setTimeout(() => {
        window.URL.revokeObjectURL(downloadUrl)
      }, 1000)
    } catch (requestError) {
      setComplaintError(
        requestError.message || 'Unable to download complaint package',
      )
    } finally {
      setComplaintLoading(false)
    }
  }

  function formatDate(value) {
    if (!value) {
      return 'Not available'
    }

    const date = new Date(value)

    if (Number.isNaN(date.getTime())) {
      return value
    }

    return date.toLocaleString()
  }

  function getRiskClass(level) {
    return `risk-${String(level || 'low').toLowerCase()}`
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>SurakshaNet AI</h1>
          <p>
            Hybrid LLM Fraud Intelligence and Automated Response Platform
          </p>
        </div>

        <div className="header-actions">
          <nav className="navigation">
            <button
              type="button"
              className={
                activePage === 'analyze'
                  ? 'navigation-button active'
                  : 'navigation-button'
              }
              onClick={() => setActivePage('analyze')}
            >
              Fraud Analysis
            </button>

            <button
              type="button"
              className={
                activePage === 'dashboard'
                  ? 'navigation-button active'
                  : 'navigation-button'
              }
              onClick={() => setActivePage('dashboard')}
            >
              Investigator Dashboard
            </button>
          </nav>

          <div className="status">
            <span className="status-dot"></span>
            Gemini Online
          </div>
        </div>
      </header>

      {activePage === 'analyze' && (
        <main className="main-content">
          <form className="form-card" onSubmit={handleSubmit}>
            <div className="section-heading">
              <div>
                <p className="label">HYBRID FRAUD ANALYSIS</p>
                <h2>Analyze Suspicious Activity</h2>
              </div>

              <span className="shield">ðŸ›¡ï¸</span>
            </div>

            <div className="engine-strip">
              <span>Rule Engine</span>
              <strong>+</strong>
              <span>Gemini LLM</span>
              <strong>+</strong>
              <span>Transaction Engine</span>
            </div>

            <div className="form-group">
              <label>Victim ID</label>
              <input
                name="victim_id"
                value={form.victim_id}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Suspicious Message</label>
              <textarea
                name="scam_text"
                rows="6"
                value={form.scam_text}
                onChange={handleChange}
                required
              ></textarea>
            </div>

            <div className="form-group">
              <label>Message Channel</label>
              <select
                name="channel"
                value={form.channel}
                onChange={handleChange}
              >
                <option value="whatsapp">WhatsApp</option>
                <option value="sms">SMS</option>
                <option value="email">Email</option>
                <option value="telegram">Telegram</option>
                <option value="phone">Phone Call</option>
              </select>
            </div>

            <h3>Transaction Information</h3>

            <div className="form-grid">
              <div className="form-group">
                <label>User ID</label>
                <input
                  name="user_id"
                  value={form.user_id}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Transaction Amount</label>
                <input
                  name="amount"
                  type="number"
                  min="0"
                  value={form.amount}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Average Amount</label>
                <input
                  name="average_amount"
                  type="number"
                  min="0"
                  value={form.average_amount}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Current Location</label>
                <input
                  name="location"
                  value={form.location}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Usual Location</label>
                <input
                  name="usual_location"
                  value={form.usual_location}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Device ID</label>
                <input
                  name="device_id"
                  value={form.device_id}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Transaction Hour</label>
                <input
                  name="transaction_hour"
                  type="number"
                  min="0"
                  max="23"
                  value={form.transaction_hour}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Merchant Category</label>
                <input
                  name="merchant_category"
                  value={form.merchant_category}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Failed Attempts</label>
                <input
                  name="failed_attempts"
                  type="number"
                  min="0"
                  value={form.failed_attempts}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Recent Scam Risk</label>
                <input
                  name="recent_scam_risk"
                  type="number"
                  min="0"
                  max="100"
                  value={form.recent_scam_risk}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <label className="checkbox-row">
              <input
                name="known_device"
                type="checkbox"
                checked={form.known_device}
                onChange={handleChange}
              />
              This transaction is from a known device
            </label>

            <button
              className="analyze-button"
              type="submit"
              disabled={loading}
            >
              {loading
                ? 'Gemini is analyzing the case...'
                : 'Analyze Fraud Risk'}
            </button>

            <p className="privacy-warning">
              Never enter an OTP, UPI PIN, card PIN, password or complete
              Aadhaar number.
            </p>
          </form>

          <section className="result-card">
            {loading && (
              <div className="empty-result">
                <div className="result-icon loading-icon">âœ¦</div>
                <h2>Hybrid Analysis Running</h2>
                <p>
                  Gemini, fraud rules and transaction signals are being
                  combined into one explainable risk report.
                </p>
              </div>
            )}

            {!loading && error && (
              <div className="empty-result">
                <div className="result-icon">âš ï¸</div>
                <h2>Analysis Failed</h2>
                <p>{error}</p>
              </div>
            )}

            {!loading && !error && !result && (
              <div className="empty-result">
                <div className="result-icon">âœ¦</div>
                <h2>Gemini-Powered Analysis</h2>
                <p>
                  Submit suspicious-message and transaction information
                  to generate a hybrid fraud-intelligence report.
                </p>

                <div className="result-features">
                  <span>Gemini scam classification</span>
                  <span>Explainable hybrid score</span>
                  <span>Transaction decision</span>
                  <span>Automated n8n response</span>
                </div>
              </div>
            )}

            {!loading && result && (
              <div className="analysis-output">
                <div className="result-header">
                  <div>
                    <p className="label">CASE REPORT</p>
                    <h2>{result.case_id}</h2>
                  </div>

                  <span
                    className={`risk-badge ${getRiskClass(
                      result.final_risk_level,
                    )}`}
                  >
                    {result.final_risk_level}
                  </span>
                </div>

                <div className="score-box">
                  <span>Final Hybrid Risk Score</span>
                  <strong>{result.final_risk_score}/100</strong>
                </div>

                <HybridScorePanel
                  hybridAnalysis={result.hybrid_analysis}
                />

                <LLMAnalysisPanel
                  llmResult={result.llm_analysis}
                  hybridAnalysis={result.hybrid_analysis}
                />

                <div className="result-section">
                  <h3>Priority</h3>
                  <p>{result.priority}</p>
                </div>

                <div className="result-section">
                  <h3>Rule-Engine Verdict</h3>
                  <p>{result.scam_analysis?.verdict}</p>
                </div>

                <div className="result-section">
                  <h3>Transaction Decision</h3>
                  <p>{result.transaction_analysis?.decision}</p>
                </div>

                <div className="result-section">
                  <h3>Investigation Summary</h3>
                  <p>{result.investigation_summary}</p>
                </div>

                <div className="result-section">
                  <h3>Recommended Next Steps</h3>

                  <ul>
                    {result.recommended_next_steps?.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ul>
                </div>

                <div className="alert-status">
                  <strong>n8n Alert Status</strong>
                  <span>
                    {result.n8n_alert_status?.status || 'Not available'}
                  </span>
                </div>
              </div>
            )}
          </section>
        </main>
      )}

      {activePage === 'dashboard' && (
        <main className="dashboard-page">
          <div className="dashboard-heading">
            <div>
              <p className="label">INVESTIGATOR DASHBOARD</p>
              <h2>Hybrid Fraud Intelligence</h2>
              <p>
                Review Gemini findings, deterministic rules, transaction
                risk and automated response activity.
              </p>
            </div>

            <button
              type="button"
              className="refresh-button"
              onClick={loadDashboard}
              disabled={dashboardLoading}
            >
              {dashboardLoading
                ? 'Refreshing...'
                : 'Refresh Dashboard'}
            </button>
          </div>

          {dashboardError && (
            <div className="dashboard-error">{dashboardError}</div>
          )}

          <section className="summary-grid">
            <div className="summary-card">
              <span>Total Cases</span>
              <strong>{summary.total_cases}</strong>
            </div>

            <div className="summary-card critical-summary">
              <span>Critical Cases</span>
              <strong>{summary.critical_cases}</strong>
            </div>

            <div className="summary-card high-summary">
              <span>High Cases</span>
              <strong>{summary.high_cases}</strong>
            </div>

            <div className="summary-card medium-summary">
              <span>Medium Cases</span>
              <strong>{summary.medium_cases}</strong>
            </div>

            <div className="summary-card low-summary">
              <span>Low Cases</span>
              <strong>{summary.low_cases}</strong>
            </div>

            <div className="summary-card">
              <span>Alerts Sent</span>
              <strong>{summary.alerts_sent}</strong>
            </div>

            <div className="summary-card">
              <span>Average Risk</span>
              <strong>{summary.average_risk_score}</strong>
            </div>
          </section>

          <section className="filter-card">
            <div className="filter-heading">
              <div>
                <h3>Search and Filter Cases</h3>
                <p>
                  Showing {filteredCases.length} of {cases.length} cases
                </p>
              </div>

              <button
                type="button"
                className="clear-filter-button"
                onClick={clearFilters}
              >
                Clear Filters
              </button>
            </div>

            <div className="filter-grid">
              <div className="filter-group search-filter">
                <label>Search Cases</label>
                <input
                  type="text"
                  value={searchText}
                  onChange={(event) => setSearchText(event.target.value)}
                  placeholder="Search case ID, victim ID or verdict"
                />
              </div>

              <div className="filter-group">
                <label>Risk Level</label>
                <select
                  value={riskFilter}
                  onChange={(event) =>
                    setRiskFilter(event.target.value)
                  }
                >
                  <option value="all">All Risk Levels</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div className="filter-group">
                <label>Alert Status</label>
                <select
                  value={alertFilter}
                  onChange={(event) =>
                    setAlertFilter(event.target.value)
                  }
                >
                  <option value="all">All Alert Statuses</option>
                  <option value="sent">Sent</option>
                  <option value="failed">Failed</option>
                  <option value="not sent">Not Sent</option>
                </select>
              </div>
            </div>
          </section>

          <section className="dashboard-content">
            <div className="case-history-card">
              <div className="card-heading">
                <div>
                  <h3>Case History</h3>
                  <p>{filteredCases.length} matching cases</p>
                </div>
              </div>

              {dashboardLoading && cases.length === 0 && (
                <div className="dashboard-empty">
                  Loading case history...
                </div>
              )}

              {!dashboardLoading && cases.length === 0 && (
                <div className="dashboard-empty">
                  No fraud cases have been stored yet.
                </div>
              )}

              {!dashboardLoading &&
                cases.length > 0 &&
                filteredCases.length === 0 && (
                  <div className="dashboard-empty">
                    No cases match your current filters.
                  </div>
                )}

              <div className="case-list">
                {filteredCases.map((caseItem) => (
                  <button
                    type="button"
                    key={caseItem.case_id}
                    className={
                      selectedCase?.case_id === caseItem.case_id
                        ? 'case-list-item selected'
                        : 'case-list-item'
                    }
                    onClick={() => loadCaseDetails(caseItem.case_id)}
                  >
                    <div className="case-list-header">
                      <strong>{caseItem.case_id}</strong>

                      <span
                        className={`risk-badge ${getRiskClass(
                          caseItem.risk_level,
                        )}`}
                      >
                        {caseItem.risk_level}
                      </span>
                    </div>

                    <div className="case-list-information">
                      <span>Victim: {caseItem.victim_id}</span>
                      <span>Score: {caseItem.risk_score}/100</span>
                      <span>Alert: {caseItem.alert_status}</span>
                    </div>

                    <small>{formatDate(caseItem.created_at)}</small>
                  </button>
                ))}
              </div>
            </div>

            <div className="case-detail-card">
              {!selectedCase && (
                <div className="dashboard-empty">
                  Select a fraud case to view full investigation details.
                </div>
              )}

              {selectedCase && (
                <div className="case-detail-content">
                  <div className="result-header">
                    <div>
                      <p className="label">CASE DETAILS</p>
                      <h2>{selectedCase.case_id}</h2>
                      <p className="case-date">
                        {formatDate(selectedCase.created_at)}
                      </p>
                    </div>

                    <span
                      className={`risk-badge ${getRiskClass(
                        selectedCase.final_risk_level,
                      )}`}
                    >
                      {selectedCase.final_risk_level}
                    </span>
                  </div>

                  <div className="score-box">
                    <span>Final Hybrid Risk Score</span>
                    <strong>
                      {selectedCase.final_risk_score}/100
                    </strong>
                  </div>

                  <HybridScorePanel
                    hybridAnalysis={selectedCase.hybrid_analysis}
                  />

                  <LLMAnalysisPanel
                    llmResult={selectedCase.llm_analysis}
                    hybridAnalysis={selectedCase.hybrid_analysis}
                  />

                  <div className="complaint-actions">
                    <button
                      type="button"
                      className="complaint-download-button"
                      onClick={() =>
                        downloadComplaint(selectedCase.case_id)
                      }
                      disabled={complaintLoading}
                    >
                      {complaintLoading
                        ? 'Generating Complaint Package...'
                        : 'Download Complaint Package'}
                    </button>

                    <a
                      className="complaint-preview-link"
                      href={`${API_BASE_URL}/complaints/${encodeURIComponent(
                        selectedCase.case_id,
                      )}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Preview Complaint Data
                    </a>
                  </div>

                  {complaintError && (
                    <div className="complaint-error">
                      {complaintError}
                    </div>
                  )}

                  <div className="case-information-grid">
                    <div>
                      <span>Victim ID</span>
                      <strong>{selectedCase.victim_id}</strong>
                    </div>

                    <div>
                      <span>Priority</span>
                      <strong>{selectedCase.priority}</strong>
                    </div>

                    <div>
                      <span>Rule Score</span>
                      <strong>
                        {selectedCase.scam_analysis?.risk_score ?? 0}/100
                      </strong>
                    </div>

                    <div>
                      <span>Transaction Score</span>
                      <strong>
                        {selectedCase.transaction_analysis?.risk_score ??
                          0}
                        /100
                      </strong>
                    </div>
                  </div>

                  <div className="result-section">
                    <h3>Rule-Engine Verdict</h3>
                    <p>{selectedCase.scam_analysis?.verdict}</p>
                  </div>

                  <div className="result-section">
                    <h3>Transaction Decision</h3>
                    <p>
                      {selectedCase.transaction_analysis?.decision}
                    </p>
                  </div>

                  <div className="result-section">
                    <h3>Rule-Engine Patterns</h3>

                    <div className="pattern-list">
                      {selectedCase.scam_analysis?.detected_patterns
                        ?.length > 0 ? (
                        selectedCase.scam_analysis.detected_patterns.map(
                          (pattern) => (
                            <span key={pattern}>{pattern}</span>
                          ),
                        )
                      ) : (
                        <p>No patterns recorded.</p>
                      )}
                    </div>
                  </div>

                  <div className="result-section">
                    <h3>Transaction Risk Factors</h3>

                    <ul>
                      {selectedCase.transaction_analysis?.risk_factors
                        ?.length > 0 ? (
                        selectedCase.transaction_analysis.risk_factors.map(
                          (factor) => (
                            <li key={factor}>{factor}</li>
                          ),
                        )
                      ) : (
                        <li>No transaction risk factors recorded.</li>
                      )}
                    </ul>
                  </div>

                  <div className="result-section">
                    <h3>Investigation Summary</h3>
                    <p>{selectedCase.investigation_summary}</p>
                  </div>

                  <div className="result-section">
                    <h3>Recommended Next Steps</h3>

                    <ul>
                      {selectedCase.recommended_next_steps?.map(
                        (step) => (
                          <li key={step}>{step}</li>
                        ),
                      )}
                    </ul>
                  </div>

                  <div className="alert-status">
                    <strong>n8n Alert Status</strong>
                    <span>
                      {selectedCase.n8n_alert_status?.status ||
                        'Not available'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </section>
        </main>
      )}
    </div>
  )
}

export default App
