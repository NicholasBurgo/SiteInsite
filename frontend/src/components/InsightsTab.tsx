/**
 * Insights tab component.
 * Fetches and displays the insight report summary.
 */
import React, { useState, useEffect } from 'react';
import { fetchInsightSummary } from '../lib/api';
import { InsightReport as InsightReportType } from '../lib/types';
import InsightReportView from './InsightReportView';

interface InsightsTabProps {
  runId: string;
}

const InsightsTab: React.FC<InsightsTabProps> = ({ runId }) => {
  const [report, setReport] = useState<InsightReportType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) {
      setError("Run ID is required");
      setLoading(false);
      return;
    }

    const loadReport = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchInsightSummary(runId);
        setReport(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load insight report");
      } finally {
        setLoading(false);
      }
    };

    loadReport();
  }, [runId]);

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-500 mx-auto mb-4"></div>
        <div className="text-gray-500 dark:text-gray-400">Loading insight report...</div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
        <div className="text-red-800 dark:text-red-300 font-medium">Error loading insight report</div>
        <div className="text-red-600 dark:text-red-400 text-sm mt-2">{error || "Unknown error"}</div>
      </div>
    );
  }

  return <InsightReportView report={report} />;
};

export default InsightsTab;

