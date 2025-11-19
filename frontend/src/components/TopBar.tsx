interface TopBarProps {
  runId?: string;
  baseUrl?: string;
  onExportSeed?: () => void;
  onExportReport?: () => void;
  onBack?: () => void;
  saving?: boolean;
}

export function TopBar({ runId, baseUrl, onExportSeed, onExportReport, onBack, saving }: TopBarProps) {
  return (
    <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center space-x-2 px-3 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-sm transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span>Back</span>
            </button>
          )}
          <div>
            <h1 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
              {runId ? `Audit Review - Run ${runId}` : 'SiteInsite'}
            </h1>
            {baseUrl && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{baseUrl}</p>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <a href="http://localhost:5051/docs" target="_blank" className="underline hover:text-gray-700 dark:hover:text-gray-300">
              API Docs
            </a>
          </div>
          {onExportReport && (
            <button
              onClick={onExportReport}
              disabled={saving}
              className="px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-full text-sm hover:bg-green-700 dark:hover:bg-green-600 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Generating...' : 'Export Report (PDF)'}
            </button>
          )}
          {onExportSeed && (
            <button
              onClick={onExportSeed}
              disabled={saving}
              className="px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-full text-sm hover:bg-green-700 dark:hover:bg-green-600 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Processing...' : 'Confirm & Continue'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}