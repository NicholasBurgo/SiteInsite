/**
 * CompetitorsTab Component
 * 
 * Displays competitor comparison results with side-by-side comparison dashboard.
 */
import React, { useState } from 'react';
import { ComparisonReport, ComparisonRow } from '../lib/types';
import InsightReportView from './InsightReportView';

interface CompetitorsTabProps {
  comparisonResult: ComparisonReport | null;
  primaryRunId: string;
}

const CompetitorsTab: React.FC<CompetitorsTabProps> = ({ comparisonResult, primaryRunId }) => {
  const [selectedCompetitor, setSelectedCompetitor] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>('overview');

  // Extract competitor info from comparison result
  const competitors = comparisonResult?.siteReports.filter(
    (site) => site.url !== comparisonResult.primaryUrl
  ) || [];

  const primarySite = comparisonResult?.siteReports.find(
    (site) => site.url === comparisonResult.primaryUrl
  );

  // Auto-select first competitor if available
  React.useEffect(() => {
    if (competitors.length > 0 && !selectedCompetitor) {
      setSelectedCompetitor(competitors[0].url);
    }
  }, [competitors.length]);

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

  const selectedCompetitorSite = competitors.find(c => c.url === selectedCompetitor) || competitors[0];
  const competitorName = selectedCompetitorSite.url;

  // Filter comparisons for selected competitor (for now, compare against first competitor)
  const comparisons = comparisonResult.comparisons || [];

  // Filter comparisons by category
  const getCategoryComparisons = (category: string): ComparisonRow[] => {
    if (category === 'overview') {
      // Show all key metrics
      return comparisons.filter(c => 
        c.metric === 'overall_score' ||
        c.metric.includes('_score') ||
        c.metric === 'content_depth_score' ||
        c.metric === 'nav_type' ||
        c.metric === 'crawlability_score'
      );
    } else if (category === 'performance') {
      return comparisons.filter(c => 
        c.metric.includes('performance') || c.metric.includes('load_time')
      );
    } else if (category === 'seo') {
      return comparisons.filter(c => 
        c.metric.includes('seo') || c.metric.includes('h1')
      );
    } else if (category === 'content') {
      return comparisons.filter(c => 
        c.metric.includes('content')
      );
    } else if (category === 'structure') {
      return comparisons.filter(c => 
        c.metric.includes('structure') || c.metric.includes('nav') || c.metric.includes('crawlability')
      );
    }
    return [];
  };

  const categoryComparisons = getCategoryComparisons(activeCategory);

  const getDirectionColor = (direction: string): string => {
    if (direction === 'better') return 'text-green-600 dark:text-green-400';
    if (direction === 'worse') return 'text-red-600 dark:text-red-400';
    if (direction === 'different') return 'text-yellow-600 dark:text-yellow-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const getDirectionBadge = (direction: string): string => {
    if (direction === 'better') return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300';
    if (direction === 'worse') return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300';
    if (direction === 'different') return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300';
    return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300';
  };

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

      {/* Competitor Selector */}
      {competitors.length > 1 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Select Competitor
          </h3>
          <div className="flex flex-wrap gap-2">
            {competitors.map((competitor) => (
              <button
                key={competitor.url}
                onClick={() => setSelectedCompetitor(competitor.url)}
                className={`px-4 py-2 rounded-lg border transition-colors text-sm ${
                  selectedCompetitor === competitor.url
                    ? 'bg-blue-50 dark:bg-blue-900/50 border-blue-300 dark:border-blue-700 text-blue-900 dark:text-blue-300'
                    : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                {competitor.url}
                {competitor.report && (
                  <span className="ml-2 text-xs opacity-75">
                    ({competitor.report.overallScore}/100)
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Competitive Overview */}
      {comparisons.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Competitive Overview
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Your site: <strong>{comparisonResult.primaryUrl}</strong> vs Competitor: <strong>{competitorName}</strong>
            </p>
          </div>

          {/* Category Tabs */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <div className="flex overflow-x-auto">
              {['overview', 'performance', 'seo', 'content', 'structure'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    activeCategory === cat
                      ? 'border-blue-600 dark:border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Comparison Table */}
          <div className="p-6">
            {categoryComparisons.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Metric</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Your Site</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">{competitorName}</th>
                      <th className="text-right py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Difference</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Verdict</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categoryComparisons.map((comp, idx) => (
                      <tr
                        key={comp.metric}
                        className={`border-b border-gray-100 dark:border-gray-800 ${
                          idx % 2 === 0 ? 'bg-gray-50/50 dark:bg-gray-900/50' : ''
                        }`}
                      >
                        <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                          {comp.label}
                        </td>
                        <td className="py-3 px-4 text-right text-gray-700 dark:text-gray-300">
                          {comp.primaryValue}
                        </td>
                        <td className="py-3 px-4 text-right text-gray-700 dark:text-gray-300">
                          {comp.competitorValue}
                        </td>
                        <td className={`py-3 px-4 text-right font-medium ${getDirectionColor(comp.direction)}`}>
                          {comp.difference !== null ? (
                            comp.difference > 0 ? `+${comp.difference.toFixed(1)}` : comp.difference.toFixed(1)
                          ) : (
                            '—'
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getDirectionBadge(comp.direction)}`}>
                            {comp.verdict}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                No comparison data available for this category.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Competitor Details Section */}
      {selectedCompetitorSite && selectedCompetitorSite.report && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Competitor Details: {selectedCompetitorSite.url}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Full insight report for this competitor
            </p>
          </div>
          
          <div className="p-6">
            <InsightReportView report={selectedCompetitorSite.report} />
          </div>
        </div>
      )}
    </div>
  );
};

export default CompetitorsTab;
