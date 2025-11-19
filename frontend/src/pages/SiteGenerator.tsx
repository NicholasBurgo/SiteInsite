import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { startRun } from "../lib/api";
import PreviousRunsDropdown from "../components/PreviousRunsDropdown";

export default function SiteGenerator() {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [maxPages, setMaxPages] = useState(20);
  const [timeout, setTimeout] = useState(10);
  const [usePlaywright, setUsePlaywright] = useState(true);
  const [botAvoidanceEnabled, setBotAvoidanceEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    
    if (!url || !url.startsWith('http')) {
      setError('Please enter a valid URL starting with http:// or https://');
      setLoading(false);
      return;
    }
    
    try {
      const body = {
        url,
        maxPages,
        timeout,
        usePlaywright,
        botAvoidanceEnabled: botAvoidanceEnabled || undefined
      };
      const res = await startRun(body);
      
      // Immediately navigate to confirmation page where audit progress is shown
      navigate(`/confirm/${res.runId}`);
      
    } catch (error) {
      console.error("Start run error:", error);
      setError('Unable to connect to the backend server. Please make sure the backend is running.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="w-full max-w-2xl bg-white dark:bg-gray-800 shadow-xl rounded-2xl p-8">
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="text-4xl mb-4">🌐</div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2">SiteInsite</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm text-center mb-6">
            Website Intelligence Engine
          </p>
          
          {/* Header Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-3 mb-8">
            <PreviousRunsDropdown />
          </div>
        </div>

        {/* Generator Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">Start Audit</h2>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Website URL</label>
              <div className="relative">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg px-4 py-3 pr-10 focus:ring-2 focus:ring-blue-400 focus:border-blue-400 focus:outline-none"
                  required
                  autoComplete="url"
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  📋
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <div className="flex items-center gap-2 text-red-800 dark:text-red-300">
                  <span>⚠️</span>
                  <span className="text-sm">{error}</span>
                </div>
              </div>
            )}

            <details className="group">
              <summary className="cursor-pointer text-sm font-medium text-gray-600 dark:text-gray-400 flex items-center mb-4">
                ⚙️ Advanced Options
              </summary>
              <div className="space-y-4 pl-4">
                <div>
                  <label className="block text-sm text-gray-600 dark:text-gray-400 mb-2">Max Pages to Crawl</label>
                  <input
                    type="number"
                    value={maxPages}
                    onChange={(e) => setMaxPages(Number(e.target.value))}
                    className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 dark:text-gray-400 mb-2">Timeout (seconds)</label>
                  <input
                    type="number"
                    value={timeout}
                    onChange={(e) => setTimeout(Number(e.target.value))}
                    className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400 focus:outline-none"
                  />
                </div>
                <div className="flex items-center gap-3">
                  <input
                    id="playwright"
                    type="checkbox"
                    checked={usePlaywright}
                    onChange={(e) => setUsePlaywright(e.target.checked)}
                    className="w-4 h-4 text-blue-600 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 focus:ring-2"
                  />
                  <label htmlFor="playwright" className="text-sm text-gray-600 dark:text-gray-400">
                    Use Playwright for JavaScript sites
                  </label>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    id="botAvoid"
                    type="checkbox"
                    checked={botAvoidanceEnabled}
                    onChange={(e) => setBotAvoidanceEnabled(e.target.checked)}
                    className="w-4 h-4 text-blue-600 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 focus:ring-2"
                  />
                  <label htmlFor="botAvoid" className="text-sm text-gray-600 dark:text-gray-400">
                    Enable bot-avoidance safeguards (slower crawling)
                  </label>
                </div>
              </div>
            </details>

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-4 rounded-full font-medium text-white transition-all text-lg ${
                loading
                  ? "bg-blue-300 dark:bg-blue-800 cursor-not-allowed"
                  : "bg-blue-600 dark:bg-blue-700 hover:bg-blue-700 dark:hover:bg-blue-600 shadow-lg shadow-blue-200 dark:shadow-blue-900"
              }`}
            >
              {loading ? "Starting..." : "▷ Start Audit"}
            </button>
          </form>

        <p className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
          Enter a website URL to generate a comprehensive Website Insight Report.
        </p>
      </div>
    </div>
  );
}
