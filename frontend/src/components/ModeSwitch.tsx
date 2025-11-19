/**
 * Mode switch component for switching between Audit Runner and Previous Runs modes.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface RunInfo {
  runId: string;
  status: string;
  started_at: number;
  completed_at?: number;
  url?: string;
}

interface ModeSwitchProps {
  className?: string;
  onModeChange?: (isPreviousRunsMode: boolean) => void;
  generatorForm?: React.ReactNode;
}

const ModeSwitch: React.FC<ModeSwitchProps> = ({ className = "", onModeChange, generatorForm }) => {
  const navigate = useNavigate();
  const [isPreviousRunsMode, setIsPreviousRunsMode] = useState(false);
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isPreviousRunsMode) {
      loadRuns();
    }
  }, [isPreviousRunsMode]);

  const loadRuns = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/runs/list');
      if (response.ok) {
        const runsData = await response.json();
        setRuns(runsData);
      }
    } catch (error) {
      console.error('Error loading runs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSelect = (runId: string) => {
    navigate(`/runs/${runId}/previous`);
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300';
      case 'running':
        return 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300';
      case 'stopped':
        return 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
    }
  };

  const handleModeChange = (newMode: boolean) => {
    setIsPreviousRunsMode(newMode);
    if (onModeChange) {
      onModeChange(newMode);
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Mode Toggle Switch */}
      <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-full p-1 mb-6">
        <button
          onClick={() => handleModeChange(false)}
          className={`px-4 py-2 text-sm font-medium rounded-full transition-all duration-200 ${
            !isPreviousRunsMode
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
        >
          Run Insight Scan
        </button>
        <button
          onClick={() => handleModeChange(true)}
          className={`px-4 py-2 text-sm font-medium rounded-full transition-all duration-200 flex items-center gap-2 ${
            isPreviousRunsMode
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
        >
          <span>🕒</span>
          Previous Runs
        </button>
      </div>

      {/* Content Area - Shows runs list when in Previous Runs mode, audit form when in Run Insight Scan mode */}
      {isPreviousRunsMode ? (
        <>
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Available Runs</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Select a run to view its details</p>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-500 mx-auto mb-4"></div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Loading runs...</p>
              </div>
            ) : runs.length === 0 ? (
              <div className="p-8 text-center">
                <div className="text-4xl mb-4">📭</div>
                <p className="text-sm text-gray-600 dark:text-gray-400">No runs found</p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">Start a run to see it here</p>
              </div>
            ) : (
              <div className="space-y-2">
                {runs.map((run) => (
                  <button
                    key={run.runId}
                    onClick={() => handleRunSelect(run.runId)}
                    className="w-full text-left p-4 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors rounded-2xl border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Run {run.runId}</span>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(run.status)}`}>
                        {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
                      </span>
                    </div>
                    
                    <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                      <div>Started: {formatTimestamp(run.started_at)}</div>
                      {run.completed_at && (
                        <div>Completed: {formatTimestamp(run.completed_at)}</div>
                      )}
                      {run.url && (
                        <div className="truncate max-w-xs">
                          <span className="text-blue-600 dark:text-blue-400">{run.url}</span>
                        </div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </>
      ) : (
        generatorForm
      )}
    </div>
  );
};

export default ModeSwitch;
