/**
 * CompetitorStep Component
 * 
 * A dedicated step for selecting competitors after primary site extraction.
 * Allows users to:
 * - Fetch suggested competitors
 * - Select/deselect suggested competitors
 * - Add custom competitor URLs
 * - Run comparison audit
 */
import React, { useState, useEffect } from 'react';
import { Play, X } from 'lucide-react';
import { suggestCompetitors, runComparison } from '../lib/api';

export interface CompetitorStepProps {
  /** Primary website URL (from completed extraction) */
  primaryUrl: string;
  /** Callback when comparison is started */
  onComparisonStarted?: (comparisonResult: any) => void;
  /** Optional: Pre-populate suggested competitors */
  defaultSuggested?: string[];
  /** Optional: Pre-populate selected competitors */
  defaultSelected?: string[];
}

export function CompetitorStep({
  primaryUrl,
  onComparisonStarted,
  defaultSuggested = [],
  defaultSelected = []
}: CompetitorStepProps) {
  const [suggested, setSuggested] = useState<string[]>(defaultSuggested);
  const [selected, setSelected] = useState<string[]>(defaultSelected);
  const [customCompetitor, setCustomCompetitor] = useState('');
  const [fetchingSuggestions, setFetchingSuggestions] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [runningComparison, setRunningComparison] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [customInputError, setCustomInputError] = useState<string | null>(null);

  // Auto-fetch suggestions when comparison mode is enabled and we have a primary URL
  useEffect(() => {
    if (comparisonMode && primaryUrl && suggested.length === 0 && !fetchingSuggestions) {
      fetchSuggestions();
    }
  }, [comparisonMode, primaryUrl]);

  const fetchSuggestions = async () => {
    if (!primaryUrl || !primaryUrl.startsWith('http')) {
      setError('Please provide a valid primary URL');
      return;
    }

    setFetchingSuggestions(true);
    setError(null);
    
    try {
      const data = await suggestCompetitors(primaryUrl);
      const suggestions = data.suggested || [];
      setSuggested(suggestions);
      
      // Auto-select top 3 suggestions (if there are 3 or more)
      if (suggestions.length >= 3) {
        setSelected(suggestions.slice(0, 3));
      } else if (suggestions.length > 0) {
        setSelected(suggestions);
      }
    } catch (err) {
      console.error('Failed to fetch suggestions:', err);
      setError('Failed to fetch competitor suggestions. Please try again.');
    } finally {
      setFetchingSuggestions(false);
    }
  };

  const handleAddCustomCompetitor = () => {
    // Reset error state
    setCustomInputError(null);
    
    // Validate URL format
    if (!customCompetitor || !customCompetitor.startsWith('http')) {
      setCustomInputError('URL must start with http:// or https://');
      return;
    }

    // Check for duplicates (case-insensitive)
    const normalizedCustom = customCompetitor.toLowerCase().trim();
    const allCompetitors = [...suggested, ...selected].map(u => u.toLowerCase().trim());
    
    if (allCompetitors.includes(normalizedCustom)) {
      setCustomInputError('This competitor is already added');
      return;
    }

    // Add to selected
    setSelected([...selected, customCompetitor.trim()]);
    setCustomCompetitor('');
    setCustomInputError(null);
  };

  const handleToggleCompetitor = (competitorUrl: string) => {
    if (selected.includes(competitorUrl)) {
      setSelected(selected.filter(u => u !== competitorUrl));
    } else {
      setSelected([...selected, competitorUrl]);
    }
  };

  const handleRemoveCompetitor = (competitorUrl: string) => {
    setSelected(selected.filter(u => u !== competitorUrl));
  };

  const handleRunComparison = async () => {
    if (!primaryUrl || selected.length === 0) {
      setError('Please select at least one competitor');
      return;
    }

    setRunningComparison(true);
    setError(null);

    try {
      const result = await runComparison(primaryUrl, selected);
      
      // Call the callback if provided
      if (onComparisonStarted) {
        onComparisonStarted(result);
      } else {
        // Default behavior: show success message
        alert(`Comparison started for ${primaryUrl} vs ${selected.length} competitor(s).`);
      }
    } catch (err) {
      console.error('Comparison error:', err);
      setError('Failed to start comparison. Please try again.');
    } finally {
      setRunningComparison(false);
    }
  };

  // Validate custom input in real-time
  const validateCustomInput = (value: string) => {
    setCustomCompetitor(value);
    
    if (!value) {
      setCustomInputError(null);
      return;
    }

    if (!value.startsWith('http')) {
      setCustomInputError('URL must start with http:// or https://');
      return;
    }

    // Check for duplicates
    const normalized = value.toLowerCase().trim();
    const allCompetitors = [...suggested, ...selected].map(u => u.toLowerCase().trim());
    
    if (allCompetitors.includes(normalized)) {
      setCustomInputError('This competitor is already added');
      return;
    }

    setCustomInputError(null);
  };

  return (
    <div className="bg-slate-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-2">
          <input
            id="comparison-mode-toggle"
            type="checkbox"
            checked={comparisonMode}
            onChange={(e) => setComparisonMode(e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
          />
          <label htmlFor="comparison-mode-toggle" className="text-lg font-semibold text-gray-800 dark:text-gray-100">
            Compare with competitors
          </label>
        </div>
        <p className="text-sm text-slate-500 dark:text-gray-400 ml-7">
          {comparisonMode 
            ? 'Select competitors to benchmark your site against and identify improvement opportunities.'
            : 'Enable competitor comparison to see how your site stacks up against the competition.'}
        </p>
      </div>

      {/* Competitor Selection UI (shown when comparison mode is enabled) */}
      {comparisonMode && (
        <div className="space-y-4">
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
              <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
            </div>
          )}

          {/* Suggest Competitors Button */}
          <div>
            <button
              type="button"
              onClick={fetchSuggestions}
              disabled={!primaryUrl || fetchingSuggestions}
              className="bg-indigo-600 dark:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {fetchingSuggestions ? (
                <>
                  <span className="inline-block animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2"></span>
                  Loading...
                </>
              ) : (
                'Suggest Competitors'
              )}
            </button>
          </div>

          {/* Suggested Competitors List */}
          {suggested.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-700 dark:text-gray-300 text-sm mb-2">
                Suggested Competitors
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-md p-2 bg-white dark:bg-gray-900">
                {suggested.map((competitorUrl) => (
                  <label
                    key={competitorUrl}
                    className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 p-2 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={selected.includes(competitorUrl)}
                      onChange={() => handleToggleCompetitor(competitorUrl)}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-gray-700 dark:text-gray-300 truncate flex-1">
                      {competitorUrl}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Custom Competitor Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Add Custom Competitor
            </label>
            <div className="flex gap-2">
              <div className="flex-1">
                <input
                  type="text"
                  value={customCompetitor}
                  onChange={(e) => validateCustomInput(e.target.value)}
                  placeholder="https://competitor.com"
                  className={`w-full border rounded-md px-3 py-2 text-sm focus:ring-2 focus:outline-none ${
                    customInputError
                      ? 'border-red-300 dark:border-red-700 focus:ring-red-500 focus:border-red-500'
                      : 'border-gray-300 dark:border-gray-600 focus:ring-blue-400 focus:border-blue-400'
                  } bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100`}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !customInputError && customCompetitor) {
                      e.preventDefault();
                      handleAddCustomCompetitor();
                    }
                  }}
                />
                {customInputError && (
                  <p className="text-xs text-red-600 dark:text-red-400 mt-1">{customInputError}</p>
                )}
              </div>
              <button
                type="button"
                onClick={handleAddCustomCompetitor}
                disabled={!customCompetitor || !!customInputError}
                className="px-4 py-2 bg-gray-600 dark:bg-gray-700 text-white rounded-md text-sm font-medium hover:bg-gray-700 dark:hover:bg-gray-600 disabled:bg-gray-300 dark:disabled:bg-gray-800 disabled:cursor-not-allowed transition-colors"
              >
                Add
              </button>
            </div>
          </div>

          {/* Selected Competitors Summary */}
          {selected.length > 0 && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md border border-blue-200 dark:border-blue-800">
              <p className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">
                {selected.length} competitor{selected.length !== 1 ? 's' : ''} selected
              </p>
              <div className="flex flex-wrap gap-2">
                {selected.map((competitorUrl) => (
                  <span
                    key={competitorUrl}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300 rounded text-xs"
                  >
                    <span className="truncate max-w-[200px]">{competitorUrl}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveCompetitor(competitorUrl)}
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 ml-1"
                      aria-label={`Remove ${competitorUrl}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Run Comparison Button */}
          <div className="pt-2">
            <button
              type="button"
              onClick={handleRunComparison}
              disabled={runningComparison || !primaryUrl || selected.length === 0}
              className={`w-full py-3 rounded-lg font-medium text-white transition-all flex items-center justify-center gap-2 ${
                runningComparison || !primaryUrl || selected.length === 0
                  ? 'bg-green-300 dark:bg-green-900/50 cursor-not-allowed'
                  : 'bg-green-600 dark:bg-green-700 hover:bg-green-700 dark:hover:bg-green-600'
              }`}
            >
              {runningComparison ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Running Comparison...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Comparison Audit
                </>
              )}
            </button>
            {selected.length === 0 && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-center">
                Select at least one competitor to run comparison
              </p>
            )}
          </div>
        </div>
      )}

      {/* Info message when comparison mode is disabled */}
      {!comparisonMode && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            💡 <strong>Tip:</strong> Enable competitor comparison to see side-by-side insights, 
            performance metrics, and identify opportunities to improve your site.
          </p>
        </div>
      )}
    </div>
  );
}

export default CompetitorStep;

