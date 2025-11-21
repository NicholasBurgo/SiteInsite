/**
 * [SEO_UI_OVERVIEW_SECTION] Unified SEO Overview Section Component
 * Combines SEO Health and Keyword Coverage into a single section
 */
import React from 'react';
import { SEOSection } from '../lib/types';

interface SeoOverviewSectionProps {
  seo?: SEOSection | null;
  // Fallback: old format for backward compatibility
  seoCategoryScore?: number;
  seoCategoryIssues?: any[];
  seoKeywords?: any;
}

const SeoOverviewSection: React.FC<SeoOverviewSectionProps> = ({
  seo,
  seoCategoryScore,
  seoCategoryIssues,
  seoKeywords
}) => {
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

  // [SEO_UI_OVERVIEW_SECTION] Use unified SEO structure if available
  if (seo) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">SEO Overview</h2>
          {seo.health && (
            <div className={`text-2xl font-bold ${getScoreColor(seo.health.score)}`}>
              {seo.health.score}
            </div>
          )}
        </div>

        <div className="space-y-6">
          {/* SEO Health Subpanel */}
          {seo.health && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">SEO Health</h3>
              <div className={`${getScoreBgColor(seo.health.score)} border rounded-lg p-4 mb-4`}>
                <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Technical SEO Health Score</div>
                <div className={`text-3xl font-bold ${getScoreColor(seo.health.score)}`}>
                  {seo.health.score}/100
                </div>
              </div>
              {seo.health.issues.length > 0 ? (
                <div className="space-y-2">
                  {seo.health.issues.map((issue) => (
                    <div key={issue.id} className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium dark:text-gray-200">{issue.title}</h4>
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
                          <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1 max-h-32 overflow-y-auto">
                            {issue.affectedPages.slice(0, 10).map((p, idx) => (
                              <li key={idx} className="truncate">
                                <span className="font-mono">{p.url}</span>
                                {p.note && (
                                  <span className="text-gray-500 dark:text-gray-400"> — {p.note}</span>
                                )}
                              </li>
                            ))}
                          </ul>
                          {issue.affectedPages.length > 10 && (
                            <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-1">
                              Showing first 10 URLs…
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 text-green-800 dark:text-green-300">
                  ✓ No SEO health issues detected
                </div>
              )}
            </div>
          )}

          {/* Keyword Coverage & Scoring Subpanel */}
          {seo.keyword_coverage && seo.keyword_coverage.keyword_metrics && seo.keyword_coverage.keyword_metrics.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Keyword Coverage & Scoring</h3>
              
              {/* Overall Score Badge */}
              <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Overall SEO Keyword Score
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      Focus Keywords: {seo.keyword_coverage.focus_keywords.length} | 
                      This score measures how consistently your key topics are used in titles, headings, URLs, links, and content.
                    </p>
                  </div>
                  <div className={`text-3xl font-bold ${getScoreColor(seo.keyword_coverage.overall_score)}`}>
                    {seo.keyword_coverage.overall_score.toFixed(1)}
                  </div>
                </div>
              </div>

              {/* Top Keywords Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">Keyword</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">Pages</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">Title</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">H1</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">H2</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">URL</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">Anchor</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {seo.keyword_coverage.keyword_metrics
                      .sort((a, b) => b.total_score - a.total_score)
                      .slice(0, 10)
                      .map((km, idx) => (
                      <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
                          {km.keyword}
                        </td>
                        <td className="px-4 py-3 text-sm text-center text-gray-700 dark:text-gray-300">
                          {km.pages_used}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {km.title_hits > 0 ? (
                            <span className="text-green-600 dark:text-green-400">✓</span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {km.h1_hits > 0 ? (
                            <span className="text-green-600 dark:text-green-400">✓</span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {km.h2_hits > 0 ? (
                            <span className="text-green-600 dark:text-green-400">✓</span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {km.slug_hits > 0 ? (
                            <span className="text-green-600 dark:text-green-400">✓</span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {km.anchor_hits > 0 ? (
                            <span className="text-green-600 dark:text-green-400">✓</span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`text-sm font-semibold ${getScoreColor(km.total_score)}`}>
                            {km.total_score.toFixed(1)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {seo.keyword_coverage.keyword_metrics.length > 10 && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
                    Showing top 10 keywords (sorted by score). Total: {seo.keyword_coverage.keyword_metrics.length}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Empty State */}
        {!seo.health && !seo.keyword_coverage && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No SEO data available for this run.
          </div>
        )}
      </div>
    );
  }

  // [SEO_UI_OVERVIEW_SECTION] Fallback: backward compatibility with old format
  if (seoCategoryScore !== undefined || seoKeywords) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">SEO Overview</h2>
          {seoCategoryScore !== undefined && (
            <div className={`text-2xl font-bold ${getScoreColor(seoCategoryScore)}`}>
              {seoCategoryScore}
            </div>
          )}
        </div>

        {/* Old SEO Health */}
        {seoCategoryIssues && seoCategoryIssues.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">SEO Health</h3>
            <div className="space-y-2">
              {seoCategoryIssues.map((issue: any) => (
                <div key={issue.id} className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium dark:text-gray-200">{issue.title}</h4>
                    <span className="text-xs px-2 py-1 rounded-full bg-white/50 dark:bg-gray-800/50">
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-sm mb-2 dark:text-gray-300">{issue.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Old Keyword Coverage */}
        {seoKeywords && seoKeywords.keyword_metrics && seoKeywords.keyword_metrics.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Keyword Coverage & Scoring</h3>
            <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                Overall Score: {seoKeywords.overall_keyword_score?.toFixed(1) || 'N/A'}/100
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Focus Keywords: {seoKeywords.total_focus_keywords || seoKeywords.keyword_metrics.length}
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Keyword</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Pages</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 dark:text-gray-300 uppercase">Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {seoKeywords.keyword_metrics
                    .sort((a: any, b: any) => b.total_score - a.total_score)
                    .slice(0, 10)
                    .map((km: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">{km.keyword}</td>
                      <td className="px-4 py-3 text-sm text-center text-gray-700 dark:text-gray-300">{km.pages_used}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`text-sm font-semibold ${getScoreColor(km.total_score)}`}>
                          {km.total_score.toFixed(1)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
};

export default SeoOverviewSection;


