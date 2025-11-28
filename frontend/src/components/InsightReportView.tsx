/**
 * Insight Report View component.
 * Displays the insight report data without page wrapper (for use in tabs).
 */
import React from 'react';
import { InsightReport as InsightReportType } from '../lib/types';
import SeoOverviewSection from './SeoOverviewSection';

interface InsightReportViewProps {
  report: InsightReportType;
}

const InsightReportView: React.FC<InsightReportViewProps> = ({ report }) => {
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 dark:text-green-400';
    if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getScoreBgColor = (score: number): string => {
    if (score >= 80) return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
    if (score >= 60) return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
    return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-200 dark:border-red-800';
      case 'medium':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800';
      case 'low':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border-blue-200 dark:border-blue-800';
      default:
        return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700';
    }
  };

  const StatCard: React.FC<{ title: string; value: string | number; subtitle?: string }> = ({ 
    title, 
    value, 
    subtitle 
  }) => {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</div>
        <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mt-1">{title}</div>
        {subtitle && <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">{subtitle}</div>}
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* Overall Score Section */}
      <div>
        <div className={`${getScoreBgColor(report.overallScore)} border rounded-lg p-8 text-center`}>
          <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Overall Website Score</div>
          <div className={`text-6xl font-bold ${getScoreColor(report.overallScore)} mb-4`}>
            {report.overallScore}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Based on performance, SEO, content quality, and structure analysis
          </div>
        </div>
      </div>

      {/* Key Stats Section */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Audit Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard 
            title="Total Pages" 
            value={report.stats.pagesCount}
          />
          <StatCard 
            title="Total Words" 
            value={report.stats.totalWords.toLocaleString()}
            subtitle={`${report.stats.avgWordsPerPage.toFixed(0)} avg per page`}
          />
          <StatCard 
            title="Media Items" 
            value={report.stats.totalMediaItems}
            subtitle={`${report.stats.avgMediaPerPage.toFixed(1)} avg per page`}
          />
          <StatCard 
            title="Status Codes" 
            value={Object.keys(report.stats.statusCounts).length}
            subtitle={Object.entries(report.stats.statusCounts).map(([code, count]) => `${code}: ${count}`).join(', ')}
          />
        </div>
      </div>

      {/* Performance Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Performance Insights</h2>
          <div className={`text-2xl font-bold ${getScoreColor(report.categories.find(c => c.category === 'performance')?.score || 0)}`}>
            {report.categories.find(c => c.category === 'performance')?.score || 0}
          </div>
        </div>
        
        {/* Measurement Mode and Consistency */}
        {(report.perfMode || report.performanceConsistency) && (
          <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="flex flex-wrap gap-4 text-sm">
              {report.perfMode && (
                <div>
                  <span className="font-medium text-gray-700 dark:text-gray-300">Mode:</span>{' '}
                  <span className="text-gray-900 dark:text-gray-100 capitalize">{report.perfMode}</span>
                </div>
              )}
              {report.performanceConsistency && (
                <div>
                  <span className="font-medium text-gray-700 dark:text-gray-300">Variance:</span>{' '}
                  <span className={`font-semibold ${
                    report.performanceConsistency === 'stable' 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-yellow-600 dark:text-yellow-400'
                  }`}>
                    {report.performanceConsistency === 'stable' ? 'LOW' : 'HIGH'}
                  </span>
                </div>
              )}
              {report.consistencyNote && (
                <div className="w-full mt-2 text-xs text-gray-600 dark:text-gray-400 italic">
                  {report.consistencyNote}
                </div>
              )}
            </div>
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <StatCard title="Median Load Time" value={`${report.stats.medianLoadMs.toFixed(0)} ms`} subtitle="50th percentile" />
          <StatCard title="Average Load Time" value={`${report.stats.avgLoadMs.toFixed(0)} ms`} subtitle="Mean" />
          <StatCard title="P90 Load Time" value={`${report.stats.p90LoadMs.toFixed(0)} ms`} subtitle="90th percentile" />
          <StatCard title="P95 Load Time" value={`${report.stats.p95LoadMs.toFixed(0)} ms`} subtitle="95th percentile" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <StatCard 
            title="Slow Pages (>1500ms)" 
            value={report.stats.slowPagesCount}
          />
          <StatCard 
            title="Very Slow Pages (>3000ms)" 
            value={report.stats.verySlowPagesCount}
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StatCard 
            title="Avg Page Size" 
            value={`${report.stats.avgPageSizeKb.toFixed(1)} KB`}
          />
          <StatCard 
            title="Max Page Size" 
            value={`${report.stats.maxPageSizeKb.toFixed(1)} KB`}
          />
        </div>
        
        {/* Performance Issues */}
        {report.categories.find(c => c.category === 'performance')?.issues.length > 0 && (
          <div className="mt-4 space-y-2">
            {report.categories.find(c => c.category === 'performance')?.issues.map((issue) => (
              <div key={issue.id} className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium dark:text-gray-200">{issue.title}</h3>
                  <span className="text-xs px-2 py-1 rounded-full bg-white/50 dark:bg-gray-800/50">
                    {issue.severity}
                  </span>
                </div>
                <p className="text-sm mb-2 dark:text-gray-300">{issue.description}</p>
                {issue.affectedPages && issue.affectedPages.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                      Affected pages ({issue.affectedPages.length}):
                    </p>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1 max-h-40 overflow-y-auto">
                      {issue.affectedPages.slice(0, 20).map((p, idx) => (
                        <li key={idx} className="truncate">
                          <span className="font-mono">{p.url}</span>
                          {p.note && (
                            <span className="text-gray-500 dark:text-gray-400"> — {p.note}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                    {issue.affectedPages.length > 20 && (
                      <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-1">
                        Showing first 20 URLs…
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* [SEO_UI_OVERVIEW_SECTION] Unified SEO Overview Section */}
      <SeoOverviewSection
        seo={report.seo}
        seoCategoryScore={report.categories.find(c => c.category === 'seo')?.score}
        seoCategoryIssues={report.categories.find(c => c.category === 'seo')?.issues}
        seoKeywords={report.seo_keywords}
      />

      {/* Content Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Content Quality</h2>
          <div className={`text-2xl font-bold ${getScoreColor(report.categories.find(c => c.category === 'content')?.score || 0)}`}>
            {report.categories.find(c => c.category === 'content')?.score || 0}
          </div>
        </div>
        {report.categories.find(c => c.category === 'content')?.issues.length > 0 ? (
          <div className="space-y-2">
            {report.categories.find(c => c.category === 'content')?.issues.map((issue) => (
              <div key={issue.id} className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium dark:text-gray-200">{issue.title}</h3>
                  <span className="text-xs px-2 py-1 rounded-full bg-white/50 dark:bg-gray-800/50">
                    {issue.severity}
                  </span>
                </div>
                <p className="text-sm mb-2 dark:text-gray-300">{issue.description}</p>
                {issue.affectedPages && issue.affectedPages.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                      Affected pages ({issue.affectedPages.length}):
                    </p>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1 max-h-40 overflow-y-auto">
                      {issue.affectedPages.slice(0, 20).map((p, idx) => (
                        <li key={idx} className="truncate">
                          <span className="font-mono">{p.url}</span>
                          {p.note && (
                            <span className="text-gray-500 dark:text-gray-400"> — {p.note}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                    {issue.affectedPages.length > 20 && (
                      <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-1">
                        Showing first 20 URLs…
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 text-green-800 dark:text-green-300">
            ✓ Content quality is good
          </div>
        )}
      </div>

      {/* Structure Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Site Structure</h2>
          <div className={`text-2xl font-bold ${getScoreColor(report.categories.find(c => c.category === 'structure')?.score || 0)}`}>
            {report.categories.find(c => c.category === 'structure')?.score || 0}
          </div>
        </div>
        {report.categories.find(c => c.category === 'structure')?.issues.length > 0 ? (
          <div className="space-y-2">
            {report.categories.find(c => c.category === 'structure')?.issues.map((issue) => (
              <div key={issue.id} className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium dark:text-gray-200">{issue.title}</h3>
                  <span className="text-xs px-2 py-1 rounded-full bg-white/50 dark:bg-gray-800/50">
                    {issue.severity}
                  </span>
                </div>
                <p className="text-sm mb-2 dark:text-gray-300">{issue.description}</p>
                {issue.affectedPages && issue.affectedPages.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                      Affected pages ({issue.affectedPages.length}):
                    </p>
                    <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1 max-h-40 overflow-y-auto">
                      {issue.affectedPages.slice(0, 20).map((p, idx) => (
                        <li key={idx} className="truncate">
                          <span className="font-mono">{p.url}</span>
                          {p.note && (
                            <span className="text-gray-500 dark:text-gray-400"> — {p.note}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                    {issue.affectedPages.length > 20 && (
                      <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-1">
                        Showing first 20 URLs…
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 text-green-800 dark:text-green-300">
            ✓ Site structure is well organized
          </div>
        )}
      </div>
    </div>
  );
};

export default InsightReportView;

