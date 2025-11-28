/**
 * SEO tab component.
 * Displays SEO-specific insights including health and keyword coverage.
 */
import React, { useState, useEffect } from 'react';
import { fetchInsightSummary } from '../lib/api';
import { InsightReport as InsightReportType } from '../lib/types';
import SeoOverviewSection from './SeoOverviewSection';

interface SEOTabProps {
  runId: string;
}

const SEOTab: React.FC<SEOTabProps> = ({ runId }) => {
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
        setError(err instanceof Error ? err.message : "Failed to load SEO data");
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
        <div className="text-gray-500 dark:text-gray-400">Loading SEO data...</div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
        <div className="text-red-800 dark:text-red-300 font-medium">Error loading SEO data</div>
        <div className="text-red-600 dark:text-red-400 text-sm mt-2">{error || "Unknown error"}</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">SEO Analysis</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Comprehensive SEO health and keyword coverage analysis for your website.
        </p>
      </div>
      
      <SeoOverviewSection
        seo={report.seo}
        seoCategoryScore={report.categories.find(c => c.category === 'seo')?.score}
        seoCategoryIssues={report.categories.find(c => c.category === 'seo')?.issues}
        seoKeywords={report.seo_keywords}
      />
    </div>
  );
};

export default SEOTab;





