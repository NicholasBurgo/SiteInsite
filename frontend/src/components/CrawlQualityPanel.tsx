import React, { useState, useEffect } from 'react';

interface CrawlQuality {
  pages_crawled: number;
  unique_paths: number;
  duplicate_pages_detected: number;
  avg_load_time_ms: number;
  p90_load_time_ms: number;
  catalog_pages: number;
  article_pages: number;
  landing_pages: number;
  '404_pages': number;
  broken_internal_links: number;
  thin_content_important_pages: number;
  thin_content_catalog_pages: number;
  nav_discovered: boolean;
  footer_discovered: boolean;
  overall_health: 'GOOD' | 'WARNING' | 'BAD';
}

interface CrawlQualityPanelProps {
  runId: string;
}

export function CrawlQualityPanel({ runId }: CrawlQualityPanelProps) {
  const [quality, setQuality] = useState<CrawlQuality | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchQuality = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/runs/${runId}/meta`);
        if (!response.ok) {
          throw new Error('Failed to fetch run meta');
        }
        const meta = await response.json();
        if (meta.crawl_quality) {
          setQuality(meta.crawl_quality);
        } else {
          setError('Crawl quality data not available');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load crawl quality');
      } finally {
        setLoading(false);
      }
    };

    if (runId) {
      fetchQuality();
    }
  }, [runId]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
        <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Crawl Quality Check</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">Loading...</p>
      </div>
    );
  }

  if (error || !quality) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
        <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Crawl Quality Check</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {error || 'Quality data not available'}
        </p>
      </div>
    );
  }

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'GOOD':
        return 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300';
      case 'WARNING':
        return 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300';
      case 'BAD':
        return 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
    }
  };

  const thinContentPercent = quality.pages_crawled > 0
    ? Math.round((quality.thin_content_important_pages / quality.pages_crawled) * 100)
    : 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium text-gray-900 dark:text-gray-100">Crawl Quality Check</h3>
        <span className={`px-2 py-1 rounded text-xs font-medium ${getHealthColor(quality.overall_health)}`}>
          {quality.overall_health}
        </span>
      </div>

      <div className="space-y-3 text-sm">
        {/* Key Stats */}
        <div>
          <div className="text-gray-500 dark:text-gray-400 mb-1">Pages Crawled</div>
          <div className="font-medium text-gray-900 dark:text-gray-100">{quality.pages_crawled}</div>
        </div>

        {/* Page Type Breakdown */}
        <div>
          <div className="text-gray-500 dark:text-gray-400 mb-1">Page Types</div>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-700 dark:text-gray-300">Catalog:</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">{quality.catalog_pages}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700 dark:text-gray-300">Article:</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">{quality.article_pages}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700 dark:text-gray-300">Landing:</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">{quality.landing_pages}</span>
            </div>
          </div>
        </div>

        {/* Issues */}
        <div>
          <div className="text-gray-500 dark:text-gray-400 mb-1">Issues</div>
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-700 dark:text-gray-300">404 Pages:</span>
              <span className={`font-medium ${quality['404_pages'] > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-gray-100'}`}>
                {quality['404_pages']}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700 dark:text-gray-300">Broken Links:</span>
              <span className={`font-medium ${quality.broken_internal_links > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-gray-100'}`}>
                {quality.broken_internal_links}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700 dark:text-gray-300">Thin Content:</span>
              <span className={`font-medium ${quality.thin_content_important_pages > 0 ? 'text-yellow-600 dark:text-yellow-400' : 'text-gray-900 dark:text-gray-100'}`}>
                {quality.thin_content_important_pages} ({thinContentPercent}%)
              </span>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="pt-2 border-t dark:border-gray-700">
          <div className="space-y-1 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex justify-between">
              <span>Unique Paths:</span>
              <span>{quality.unique_paths}</span>
            </div>
            {quality.duplicate_pages_detected > 0 && (
              <div className="flex justify-between">
                <span>Duplicates:</span>
                <span className="text-yellow-600 dark:text-yellow-400">{quality.duplicate_pages_detected}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span>Nav:</span>
              <span className={quality.nav_discovered ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                {quality.nav_discovered ? '✓' : '✗'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Footer:</span>
              <span className={quality.footer_discovered ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                {quality.footer_discovered ? '✓' : '✗'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

