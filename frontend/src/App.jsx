import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Play,
  Code2,
  Copy,
  Check,
  Cpu,
  Clock,
  Database,
  Sparkles,
  AlertCircle,
  RotateCcw,
  Layers,
  ChevronDown,
  Zap,
  Info,
  Sliders
} from 'lucide-react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_URL || '';

const DEFAULT_CODE = `def process_elements(arr):
    for i in range(10):
        for j in range(5):
            print(i, j)
`;

const FALLBACK_EXAMPLES = [
  {
    id: "sample_test",
    name: "Sample from tests (O(n) Time, O(n²) Space)",
    code: DEFAULT_CODE,
  },
  {
    id: "constant_time",
    name: "O(1) Constant Time",
    code: `def get_first_element(arr):
    if len(arr) == 0:
        return None
    first = arr[0]
    return first * 2
`,
  },
  {
    id: "linear_search",
    name: "O(n) Linear Search",
    code: `def linear_search(arr, target):
    for item in arr:
        if item == target:
            return True
    return False
`,
  },
  {
    id: "binary_search",
    name: "O(log n) Binary Search",
    code: `def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
`,
  },
  {
    id: "bubble_sort",
    name: "O(n²) Nested Loops",
    code: `def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
`,
  },
  {
    id: "matrix_mult",
    name: "O(n³) Matrix Cubic Time",
    code: `def matrix_multiply(A, B):
    n = len(A)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                pass
    return 0
`,
  },
  {
    id: "linear_space",
    name: "O(n) Auxiliary Space",
    code: `def clone_with_allocation(arr):
    # Single allocation outside loop
    clone = [0] * len(arr)
    for i in range(len(arr)):
        clone[i] = arr[i]
    return clone
`,
  },
];

const LADDER_STEPS = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n^2)", "O(n^3)", "O(2^n)"];

export default function App() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [autoAnalyze, setAutoAnalyze] = useState(true);
  const [examples, setExamples] = useState(FALLBACK_EXAMPLES);
  const [selectedExample, setSelectedExample] = useState("sample_test");
  const [copied, setCopied] = useState(false);
  const [analysisDuration, setAnalysisDuration] = useState(null);

  const textareaRef = useRef(null);
  const lineNumbersRef = useRef(null);
  const debounceTimerRef = useRef(null);

  // Fetch presets from backend API on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/examples`)
      .then((res) => {
        if (!res.ok) throw new Error("Could not fetch examples");
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setExamples(data);
        }
      })
      .catch(() => {
        // Fallback examples already initialized
      });
  }, []);

  // Compute line count
  const lines = useMemo(() => {
    return code.split('\n');
  }, [code]);

  // Synchronize scroll between line numbers and code textarea
  const handleScroll = (e) => {
    if (lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = e.target.scrollTop;
    }
  };

  // Perform Analysis
  const runAnalysis = async (codeToAnalyze = code) => {
    if (!codeToAnalyze.trim()) {
      setAnalysisResult(null);
      setError("Please paste or type some Python code to analyze.");
      return;
    }

    setLoading(true);
    setError(null);
    const startTime = performance.now();

    try {
      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: codeToAnalyze }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      const elapsed = Math.round(performance.now() - startTime);
      setAnalysisDuration(elapsed);

      if (data.success) {
        setAnalysisResult(data);
        setError(null);
      } else {
        setAnalysisResult(null);
        setError(data.error || "Analysis failed");
      }
    } catch (err) {
      setError(
        `Connection failed: Ensure backend server is running on port 8000. (${err.message})`
      );
      setAnalysisResult(null);
    } finally {
      setLoading(false);
    }
  };

  // Trigger analysis on initial load
  useEffect(() => {
    runAnalysis(code);
  }, []);

  // Handle Code Change with optional auto-analyze debounce
  const handleCodeChange = (e) => {
    const val = e.target.value;
    setCode(val);

    if (autoAnalyze) {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = setTimeout(() => {
        runAnalysis(val);
      }, 500);
    }
  };

  // Handle Tab key and Ctrl+Enter keyboard shortcuts
  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      runAnalysis(code);
      return;
    }

    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = textareaRef.current;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const spaces = "    "; // 4 spaces for standard Python indent

      const newCode = code.substring(0, start) + spaces + code.substring(end);
      setCode(newCode);

      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + spaces.length;
      }, 0);
    }
  };

  // Handle preset selection
  const handlePresetChange = (e) => {
    const presetId = e.target.value;
    setSelectedExample(presetId);
    const found = examples.find((ex) => ex.id === presetId);
    if (found) {
      setCode(found.code);
      runAnalysis(found.code);
    }
  };

  // Copy code to clipboard
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Determine color styling grade based on Big-O string
  const getGradeClass = (complexity) => {
    if (!complexity) return "grade-o1";
    const clean = complexity.replace(/\s+/g, '');
    if (clean === "O(1)") return "grade-o1";
    if (clean === "O(logn)") return "grade-ologn";
    if (clean === "O(n)") return "grade-on";
    if (clean === "O(n^2)") return "grade-on2";
    if (clean.includes("^3") || clean.includes("2^n")) return "grade-on3";
    return "grade-on";
  };

  const getTierLabel = (complexity) => {
    if (!complexity) return "Constant";
    const clean = complexity.replace(/\s+/g, '');
    if (clean === "O(1)") return "Constant";
    if (clean === "O(logn)") return "Logarithmic";
    if (clean === "O(n)") return "Linear";
    if (clean === "O(n^2)") return "Quadratic";
    if (clean === "O(n^3)") return "Cubic";
    return "Polynomial";
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">
            <Cpu size={20} />
          </div>
          <div>
            <span className="brand-title">Complexity Analyzer</span>
          </div>
          <span className="brand-badge">AST Engine</span>
        </div>

        <div className="header-actions">
          {/* Preset Selector */}
          <div className="preset-select-wrapper">
            <select
              className="preset-select"
              value={selectedExample}
              onChange={handlePresetChange}
            >
              <option value="" disabled>Load Example Algorithm...</option>
              {examples.map((ex) => (
                <option key={ex.id} value={ex.id}>
                  {ex.name}
                </option>
              ))}
            </select>
            <ChevronDown size={14} className="preset-select-icon" />
          </div>

          {/* Auto-analyze toggle */}
          <label className="toggle-label" title="Automatically re-run analysis as you type">
            <input
              type="checkbox"
              className="toggle-checkbox"
              checked={autoAnalyze}
              onChange={(e) => setAutoAnalyze(e.target.checked)}
            />
            <span>Auto-analyze</span>
          </label>

          {/* Clear Code */}
          <button
            className="btn btn-secondary"
            onClick={() => {
              setCode("");
              setAnalysisResult(null);
            }}
            title="Clear editor"
          >
            <RotateCcw size={14} />
            <span>Clear</span>
          </button>

          {/* Analyze Button */}
          <button
            className="btn btn-primary"
            onClick={() => runAnalysis(code)}
            disabled={loading}
          >
            {loading ? (
              <>
                <Zap size={15} className="spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Play size={14} fill="currentColor" />
                <span>Analyze</span>
                <span className="kbd-shortcut">Ctrl+↵</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* Split Workspace Layout: Left Editor, Right Output */}
      <main className="workspace-layout">
        {/* ================= LEFT PANE: CODE EDITOR ================= */}
        <section className="editor-pane">
          <div className="pane-header">
            <div className="pane-tab">
              <Code2 size={16} className="pane-tab-icon" />
              <span>solution.py</span>
            </div>

            <div className="editor-header-actions">
              <span className="editor-stat">{lines.length} lines</span>
              <span className="editor-stat">{code.length} chars</span>
              <button
                className="btn-icon-text"
                onClick={handleCopy}
                title="Copy code to clipboard"
              >
                {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>
          </div>

          <div className="editor-container">
            {/* Synchronized Line Numbers */}
            <div className="line-numbers" ref={lineNumbersRef}>
              {lines.map((_, i) => (
                <div key={i}>{i + 1}</div>
              ))}
            </div>

            {/* Code Input Textarea */}
            <textarea
              ref={textareaRef}
              className="code-textarea"
              value={code}
              onChange={handleCodeChange}
              onKeyDown={handleKeyDown}
              onScroll={handleScroll}
              placeholder={`// Paste your Python code here...\ndef my_algorithm(arr):\n    for item in arr:\n        pass\n    return 0`}
              spellCheck="false"
              autoCapitalize="off"
              autoComplete="off"
            />
          </div>

          <div className="editor-footer">
            <div className="editor-footer-hint">
              <span>Press <kbd>Tab</kbd> for 4 spaces</span>
              <span>•</span>
              <span><kbd>Ctrl+Enter</kbd> to analyze</span>
            </div>
            <div>
              <span>Python 3 AST Parser</span>
            </div>
          </div>
        </section>

        {/* ================= RIGHT PANE: COMPLEXITY OUTPUT ================= */}
        <section className="output-pane">
          <div className="pane-header">
            <div className="pane-tab">
              <Sparkles size={16} color="#38bdf8" />
              <span>Complexity Report</span>
            </div>

            <div>
              {loading && (
                <div className="output-status-pill loading">
                  <Zap size={12} className="spin" />
                  <span>Computing AST...</span>
                </div>
              )}
              {!loading && error && (
                <div className="output-status-pill error">
                  <AlertCircle size={12} />
                  <span>Error</span>
                </div>
              )}
              {!loading && analysisResult && (
                <div className="output-status-pill">
                  <Check size={12} />
                  <span>Ready ({analysisDuration}ms)</span>
                </div>
              )}
            </div>
          </div>

          <div className="output-content">
            {/* Error Message */}
            {error && (
              <div className="error-box">
                <div className="error-title">
                  <AlertCircle size={18} />
                  <span>Analysis Error</span>
                </div>
                <div className="error-msg">{error}</div>
              </div>
            )}

            {/* Hero Complexity Cards: TC and SPC (Wireframe Match) */}
            {analysisResult && (
              <>
                <div className="hero-complexity-grid">
                  {/* Time Complexity Card */}
                  <div className={`complexity-card ${getGradeClass(analysisResult.time_complexity)}`}>
                    <div className="card-top-row">
                      <span className="card-label">
                        <Clock size={15} />
                        <span>TC (Time Complexity)</span>
                      </span>
                      <span className="card-badge">
                        {getTierLabel(analysisResult.time_complexity)}
                      </span>
                    </div>

                    <div className="big-o-display">
                      {analysisResult.time_complexity}
                    </div>

                    <div className="complexity-desc">
                      Asymptotic runtime bound based on loop traversal and operational scaling.
                    </div>
                  </div>

                  {/* Space Complexity Card */}
                  <div className={`complexity-card ${getGradeClass(analysisResult.space_complexity)}`}>
                    <div className="card-top-row">
                      <span className="card-label">
                        <Database size={15} />
                        <span>SPC (Space Complexity)</span>
                      </span>
                      <span className="card-badge">
                        {getTierLabel(analysisResult.space_complexity)}
                      </span>
                    </div>

                    <div className="big-o-display">
                      {analysisResult.space_complexity}
                    </div>

                    <div className="complexity-desc">
                      Auxiliary memory consumption based on collections and allocated structures.
                    </div>
                  </div>
                </div>

                {/* Explanation Box */}
                {analysisResult.explanation && (
                  <div className="explanation-box">
                    <div className="explanation-header">
                      <Info size={15} color="#38bdf8" />
                      <span>Analysis Breakdown & Derivation</span>
                    </div>
                    <div className="explanation-text">
                      {analysisResult.explanation}
                    </div>
                  </div>
                )}

                {/* Structural Metrics */}
                {analysisResult.metrics && (
                  <div className="metrics-section">
                    <div className="metric-card">
                      <span className="metric-title">Max Loop Depth</span>
                      <span className="metric-value">{analysisResult.metrics.max_loop_depth}</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-title">Input Loop Depth</span>
                      <span className="metric-value">{analysisResult.metrics.max_input_loop_depth ?? analysisResult.metrics.max_loop_depth}</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-title">Constant Loops</span>
                      <span className="metric-value">{analysisResult.metrics.constant_loops ?? 0}</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-title">Logarithmic Loops</span>
                      <span className="metric-value">{analysisResult.metrics.logarithmic_loops}</span>
                    </div>
                  </div>
                )}

                {/* Allocations Table */}
                {analysisResult.metrics?.allocations && analysisResult.metrics.allocations.length > 0 && (
                  <div className="allocations-card">
                    <div className="card-section-title">
                      <Layers size={15} color="#818cf8" />
                      <span>Tracked Memory Allocations</span>
                    </div>
                    <table className="allocations-table">
                      <thead>
                        <tr>
                          <th>Variable</th>
                          <th>Complexity</th>
                          <th>Loop Depth</th>
                          <th>Retained</th>
                          <th>Reason</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysisResult.metrics.allocations.map((alloc, idx) => (
                          <tr key={idx}>
                            <td>
                              <span className="var-badge">{alloc.variable}</span>
                            </td>
                            <td>
                              <strong>{alloc.complexity}</strong>
                            </td>
                            <td>{alloc.loop_depth}</td>
                            <td>
                              <span className={`retained-badge ${alloc.retained ? 'yes' : 'no'}`}>
                                {alloc.retained ? 'Yes (Retained)' : 'No (Temporary)'}
                              </span>
                            </td>
                            <td>{alloc.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Big-O Growth Reference Spectrum */}
                <div className="ladder-card">
                  <div className="card-section-title">
                    <Sliders size={15} color="#0ea5e9" />
                    <span>Big-O Growth Reference Scale</span>
                  </div>
                  <div className="ladder-items">
                    {LADDER_STEPS.map((step) => {
                      const isActive =
                        analysisResult.time_complexity === step ||
                        analysisResult.space_complexity === step;
                      return (
                        <div
                          key={step}
                          className={`ladder-step ${isActive ? 'active' : ''}`}
                          title={`Complexity: ${step}`}
                        >
                          {step}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </>
            )}

            {/* Empty State when no code and no error */}
            {!analysisResult && !error && !loading && (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <Code2 size={28} />
                </div>
                <h3>Ready to Analyze</h3>
                <p>Paste your Python algorithm into the editor on the left to calculate Big-O Time & Space complexity.</p>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
