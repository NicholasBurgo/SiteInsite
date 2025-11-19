/**
 * CompetitorsTab Component
 * 
 * Displays competitor comparison results with summary tabs for each competitor.
 */
import React, { useState } from 'react';
import { InsightReport as InsightReportType } from '../lib/types';
import InsightReportView from './InsightReportView';

interface CompetitorInfo {
  url: string;
  runId: string;
  report?: InsightReportType;
  loading?: boolean;
  error?: string;
}

interface CompetitorsTabProps {
  comparisonResult: any; // ComparisonReport from API
  primaryRunId: string;
}

const CompetitorsTab: React.FC<CompetitorsTabProps> = ({ comparisonResult, primaryRunId }) => {
  const [competitors, setCompetitors] = useState<CompetitorInfo[]>([]);
  const [selectedCompetitor, setSelectedCompetitor] = useState<string | null>(null);
  const [loadingAll, setLoadingAll] = useState(false);

  // Extract competitor info from comparison result
  React.useEffect(() => {
    if (!comparisonResult || !comparisonResult.siteReports) {
      return;
    }

    // Get all competitors (excluding primary)
    const competitorSites = comparisonResult.siteReports.filter(
      (site: any) => site.url !== comparisonResult.primaryUrl
    );

    const competitorInfos: CompetitorInfo[] = competitorSites.map((site: any) => ({
      url: site.url,
      runId: site.report?.runId || '',
      report: site.report || undefined, // Use report from comparison if available
      loading: false,
      error: undefined
    }));

    setCompetitors(competitorInfos);
    
    // Auto-select first competitor if available
    if (competitorInfos.length > 0 && !selectedCompetitor) {
      setSelectedCompetitor(competitorInfos[0].url);
    }
  }, [comparisonResult]);

  // Reports are already loaded from comparison result, no need to fetch again

  if (!comparisonResult) {
    return (
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
          No Competitor Comparison Yet
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Run a competitor comparison from the CompetitorStep component to see competitor summaries here.
        </p>
      </div>
    );
  }

  if (competitors.length === 0) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
        <p className="text-yellow-800 dark:text-yellow-300">
          No competitors found in comparison result.
        </p>
      </div>
    );
  }

  const selectedCompetitorData = competitors.find(c => c.url === selectedCompetitor);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Competitor Comparison
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Compare your site against {competitors.length} competitor{competitors.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Competitor List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
          Competitors ({competitors.length})
        </h3>
        <div className="space-y-2">
          {competitors.map((competitor) => (
            <button
              key={competitor.url}
              onClick={() => setSelectedCompetitor(competitor.url)}
              className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                selectedCompetitor === competitor.url
                  ? 'bg-blue-50 dark:bg-blue-900/50 border-blue-300 dark:border-blue-700 text-blue-900 dark:text-blue-300'
                  : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium truncate flex-1">{competitor.url}</span>
                {competitor.report && (
                  <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                    Score: {competitor.report.overallScore}/100
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Selected Competitor Summary */}
      {selectedCompetitorData && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {selectedCompetitorData.url}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Competitor Summary Report
            </p>
          </div>
          
          <div className="p-6">
            {selectedCompetitorData.loading && (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-500 mx-auto mb-4"></div>
                <div className="text-gray-500 dark:text-gray-400">Loading competitor report...</div>
              </div>
            )}
            
            {selectedCompetitorData.error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
                <div className="text-red-800 dark:text-red-300 font-medium">Error loading report</div>
                <div className="text-red-600 dark:text-red-400 text-sm mt-2">{selectedCompetitorData.error}</div>
              </div>
            )}
            
            {selectedCompetitorData.report && !selectedCompetitorData.loading && !selectedCompetitorData.error && (
              <InsightReportView report={selectedCompetitorData.report} />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CompetitorsTab;

