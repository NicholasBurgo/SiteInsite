/**
 * Insight Report page component.
 * Displays comprehensive Website Insight Report with performance, SEO, content, and structure analysis.
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchInsightSummary } from '../lib/api';
import { InsightReport as InsightReportType } from '../lib/types';
import { TopBar } from '../components/TopBar';

const InsightReport: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
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
        const data = await fetchInsightSummary(runId);
        setReport(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load insight report");
      } finally {
        setLoading(false);
      }
    };

    loadReport();
  }, [runId]);

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number): string => {
    if (score >= 80) return 'bg-green-50 border-green-200';
    if (score >= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const StatCard: React.FC<{ title: string; value: string | number; subtitle?: string }> = ({ 
    title, 
    value, 
    subtitle 
  }) => {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="text-2xl font-bold text-gray-900">{value}</div>
        <div className="text-sm font-medium text-gray-600 mt-1">{title}</div>
        {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <TopBar runId={runId} baseUrl={null} onBack={() => navigate(`/runs/${runId}`)} />
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="text-center py-12">
            <div className="text-gray-500">Loading insight report...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gray-50">
        <TopBar runId={runId} baseUrl={null} onBack={() => navigate(`/runs/${runId}`)} />
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <div className="text-red-800 font-medium">Error loading insight report</div>
            <div className="text-red-600 text-sm mt-2">{error || "Unknown error"}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <TopBar runId={runId} baseUrl={report.baseUrl || undefined} onBack={() => navigate(`/runs/${runId}`)} />
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Overall Score Section */}
        <div className="mb-8">
          <div className={`${getScoreBgColor(report.overallScore)} dark:bg-gray-800 border dark:border-gray-700 rounded-lg p-8 text-center`}>
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
        <div className="mb-8">
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
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Performance Insights</h2>
            <div className={`text-2xl font-bold ${getScoreColor(report.categories.find(c => c.category === 'performance')?.score || 0)}`}>
              {report.categories.find(c => c.category === 'performance')?.score || 0}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <StatCard title="Avg Load Time" value={`${report.stats.avgLoadMs.toFixed(0)} ms`} />
            <StatCard title="Median Load Time" value={`${report.stats.medianLoadMs.toFixed(0)} ms`} />
            <StatCard title="P90 Load Time" value={`${report.stats.p90LoadMs.toFixed(0)} ms`} />
            <StatCard title="P95 Load Time" value={`${report.stats.p95LoadMs.toFixed(0)} ms`} />
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
                    <h3 className="font-medium">{issue.title}</h3>
                    <span className="text-xs px-2 py-1 rounded-full bg-white/50">
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-sm mb-2">{issue.description}</p>
                  {issue.affectedPages.length > 0 && (
                    <div className="text-xs mt-2">
                      <div className="font-medium mb-1">Affected Pages:</div>
                      <div className="space-y-1">
                        {issue.affectedPages.slice(0, 5).map((url, idx) => (
                          <div key={idx} className="truncate">• {url}</div>
                        ))}
                        {issue.affectedPages.length > 5 && (
                          <div>... and {issue.affectedPages.length - 5} more</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SEO Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">SEO Analysis</h2>
            <div className={`text-2xl font-bold ${getScoreColor(report.categories.find(c => c.category === 'seo')?.score || 0)}`}>
              {report.categories.find(c => c.category === 'seo')?.score || 0}
            </div>
          </div>
          {report.categories.find(c => c.category === 'seo')?.issues.length > 0 ? (
            <div className="space-y-2">
              {report.categories.find(c => c.category === 'seo')?.issues.map((issue) => (
                <div key={issue.id} className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{issue.title}</h3>
                    <span className="text-xs px-2 py-1 rounded-full bg-white/50">
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-sm mb-2">{issue.description}</p>
                  {issue.affectedPages.length > 0 && (
                    <div className="text-xs mt-2">
                      <div className="font-medium mb-1">Affected Pages:</div>
                      <div className="space-y-1">
                        {issue.affectedPages.slice(0, 5).map((url, idx) => (
                          <div key={idx} className="truncate">• {url}</div>
                        ))}
                        {issue.affectedPages.length > 5 && (
                          <div>... and {issue.affectedPages.length - 5} more</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-800">
              ✓ No SEO issues detected
            </div>
          )}
        </div>

        {/* Content Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Content Quality</h2>
            <div className={`text-2xl font-bold ${getScoreColor(report.categories.find(c => c.category === 'content')?.score || 0)}`}>
              {report.categories.find(c => c.category === 'content')?.score || 0}
            </div>
          </div>
          {report.categories.find(c => c.category === 'content')?.issues.length > 0 ? (
            <div className="space-y-2">
              {report.categories.find(c => c.category === 'content')?.issues.map((issue) => (
                <div key={issue.id} className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{issue.title}</h3>
                    <span className="text-xs px-2 py-1 rounded-full bg-white/50">
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-sm mb-2">{issue.description}</p>
                  {issue.affectedPages.length > 0 && (
                    <div className="text-xs mt-2">
                      <div className="font-medium mb-1">Affected Pages:</div>
                      <div className="space-y-1">
                        {issue.affectedPages.slice(0, 5).map((url, idx) => (
                          <div key={idx} className="truncate">• {url}</div>
                        ))}
                        {issue.affectedPages.length > 5 && (
                          <div>... and {issue.affectedPages.length - 5} more</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-800">
              ✓ Content quality is good
            </div>
          )}
        </div>

        {/* Structure Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Site Structure</h2>
            <div className={`text-2xl font-bold ${getScoreColor(report.categories.find(c => c.category === 'structure')?.score || 0)}`}>
              {report.categories.find(c => c.category === 'structure')?.score || 0}
            </div>
          </div>
          {report.categories.find(c => c.category === 'structure')?.issues.length > 0 ? (
            <div className="space-y-2">
              {report.categories.find(c => c.category === 'structure')?.issues.map((issue) => (
                <div key={issue.id} className={`border rounded-lg p-4 ${getSeverityColor(issue.severity)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{issue.title}</h3>
                    <span className="text-xs px-2 py-1 rounded-full bg-white/50">
                      {issue.severity}
                    </span>
                  </div>
                  <p className="text-sm mb-2">{issue.description}</p>
                  {issue.affectedPages.length > 0 && (
                    <div className="text-xs mt-2">
                      <div className="font-medium mb-1">Affected Pages:</div>
                      <div className="space-y-1">
                        {issue.affectedPages.slice(0, 5).map((url, idx) => (
                          <div key={idx} className="truncate">• {url}</div>
                        ))}
                        {issue.affectedPages.length > 5 && (
                          <div>... and {issue.affectedPages.length - 5} more</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-800">
              ✓ Site structure is well organized
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InsightReport;

