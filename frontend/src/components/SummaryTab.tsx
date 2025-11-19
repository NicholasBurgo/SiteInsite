/**
 * Summary tab component for overview of extracted data.
 * Shows aggregated statistics and missing content indicators.
 */
import React from 'react';
import { PrimeResponse, PageIndexItem } from '../lib/types.confirm';

interface SummaryTabProps {
  primeData: PrimeResponse;
  pages: PageIndexItem[];
}

const SummaryTab: React.FC<SummaryTabProps> = ({ primeData, pages }) => {
  // Calculate statistics
  const totalPages = pages.length;
  const totalWords = pages.reduce((sum, page) => sum + (page.words || 0), 0);
  const totalMedia = pages.reduce((sum, page) => sum + (page.mediaCount || 0), 0);
  const successfulPages = pages.filter(page => page.status === 200).length;
  const failedPages = pages.filter(page => page.status !== 200).length;

  const loadTimePages = pages.filter(
    page => page.status === 200 && typeof page.loadTimeMs === 'number' && page.loadTimeMs !== null
  );
  const averageLoadMs = loadTimePages.length > 0
    ? Math.round(
        loadTimePages.reduce((sum, page) => sum + (page.loadTimeMs || 0), 0) / loadTimePages.length
      )
    : null;
  const fastestPage = loadTimePages.length > 0
    ? loadTimePages.reduce((fastest, page) =>
        (page.loadTimeMs || Infinity) < (fastest.loadTimeMs || Infinity) ? page : fastest
      )
    : null;
  const slowestPage = loadTimePages.length > 0
    ? loadTimePages.reduce((slowest, page) =>
        (page.loadTimeMs || -Infinity) > (slowest.loadTimeMs || -Infinity) ? page : slowest
      )
    : null;

  // Count navigation items
  const countNavItems = (nav: any[]): number => {
    return nav.reduce((count, item) => {
      return count + 1 + (item.children ? countNavItems(item.children) : 0);
    }, 0);
  };

  const totalNavItems = countNavItems(primeData.nav);
  const totalFooterLinks = primeData.footer.columns.reduce((sum, col) => sum + col.links.length, 0);
  const totalSocialLinks = primeData.footer.socials?.length || 0;

  // Find pages with missing content
  const pagesWithMissingTitles = pages.filter(page => !page.titleGuess || page.titleGuess.trim() === '');
  const pagesWithLowWordCount = pages.filter(page => (page.words || 0) < 50);
  const pagesWithNoMedia = pages.filter(page => (page.mediaCount || 0) === 0);

  const StatCard: React.FC<{ title: string; value: string | number; subtitle?: string; color?: 'blue' | 'green' | 'yellow' | 'red' }> = ({ 
    title, 
    value, 
    subtitle, 
    color = 'blue' 
  }) => {
    const colorClasses = {
      blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-300',
      green: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-300',
      yellow: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-300',
      red: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-300'
    };

    return (
      <div className={`border rounded-lg p-4 ${colorClasses[color]}`}>
        <div className="text-2xl font-bold">{value}</div>
        <div className="text-sm font-medium">{title}</div>
        {subtitle && <div className="text-xs opacity-75 mt-1">{subtitle}</div>}
      </div>
    );
  };

  const IssueCard: React.FC<{ title: string; items: PageIndexItem[]; description: string }> = ({ 
    title, 
    items, 
    description 
  }) => {
    if (items.length === 0) return null;

    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-300">{title}</h3>
          <span className="text-xs bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-300 px-2 py-1 rounded-full">
            {items.length}
          </span>
        </div>
        <p className="text-xs text-yellow-700 dark:text-yellow-400 mb-3">{description}</p>
        <div className="space-y-1">
          {items.slice(0, 5).map((page) => (
            <div key={page.pageId} className="text-xs text-yellow-600 dark:text-yellow-400">
              • {page.titleGuess || 'Untitled'} ({page.path})
            </div>
          ))}
          {items.length > 5 && (
            <div className="text-xs text-yellow-600 dark:text-yellow-400">
              ... and {items.length - 5} more
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Extraction Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard 
            title="Pages" 
            value={totalPages} 
            subtitle={`${successfulPages} successful, ${failedPages} failed`}
            color={failedPages > 0 ? 'yellow' : 'green'}
          />
          <StatCard 
            title="Total Words" 
            value={totalWords.toLocaleString()} 
            subtitle={`${Math.round(totalWords / totalPages)} avg per page`}
            color="blue"
          />
          <StatCard 
            title="Media Items" 
            value={totalMedia} 
            subtitle={`${Math.round(totalMedia / totalPages)} avg per page`}
            color="blue"
          />
          <StatCard 
            title="Navigation Items" 
            value={totalNavItems} 
            subtitle={`${totalFooterLinks} footer links`}
            color="blue"
          />
        </div>
      </div>

      {/* Site Structure */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Site Structure</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Navigation</h3>
            <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
              <div>• {totalNavItems} navigation items</div>
              <div>• {primeData.nav.length} top-level items</div>
              {primeData.nav.length > 0 && (
                <div className="mt-2">
                  <div className="text-xs font-medium text-gray-700 dark:text-gray-300">Top-level items:</div>
                  {primeData.nav.slice(0, 3).map((item, index) => (
                    <div key={index} className="text-xs text-gray-600 dark:text-gray-400 ml-2">
                      • {item.label}
                    </div>
                  ))}
                  {primeData.nav.length > 3 && (
                    <div className="text-xs text-gray-500 dark:text-gray-500 ml-2">
                      ... and {primeData.nav.length - 3} more
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Footer</h3>
            <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
              <div>• {primeData.footer.columns.length} columns</div>
              <div>• {totalFooterLinks} footer links</div>
              <div>• {totalSocialLinks} social links</div>
              {primeData.footer.contact && (
                <div className="mt-2">
                  <div className="text-xs font-medium text-gray-700 dark:text-gray-300">Contact info:</div>
                  {primeData.footer.contact.email && (
                    <div className="text-xs text-gray-600 dark:text-gray-400 ml-2">• Email found</div>
                  )}
                  {primeData.footer.contact.phone && (
                    <div className="text-xs text-gray-600 dark:text-gray-400 ml-2">• Phone found</div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Base URL</h3>
            <div className="text-xs text-gray-600 dark:text-gray-400 break-all">
              {primeData.baseUrl || 'Not specified'}
            </div>
          </div>
        </div>
      </div>

      {/* Page Load Performance */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Page Load Performance</h2>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3">
          {loadTimePages.length === 0 ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              No load time data available yet.
            </div>
          ) : (
            <>
              <div className="flex justify-between text-sm text-gray-700 dark:text-gray-300">
                <span className="font-medium">Average Load Time</span>
                <span>{averageLoadMs?.toLocaleString()} ms</span>
              </div>
              <div className="flex justify-between text-sm text-gray-700 dark:text-gray-300">
                <span className="font-medium">Fastest Page</span>
                <span>
                  {fastestPage?.path || fastestPage?.url} ·{' '}
                  {fastestPage?.loadTimeMs?.toLocaleString()} ms
                </span>
              </div>
              <div className="flex justify-between text-sm text-gray-700 dark:text-gray-300">
                <span className="font-medium">Slowest Page</span>
                <span>
                  {slowestPage?.path || slowestPage?.url} ·{' '}
                  {slowestPage?.loadTimeMs?.toLocaleString()} ms
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Content Quality Issues */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Content Quality</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <IssueCard
            title="Missing Titles"
            items={pagesWithMissingTitles}
            description="Pages without extracted titles"
          />
          <IssueCard
            title="Low Word Count"
            items={pagesWithLowWordCount}
            description="Pages with less than 50 words"
          />
          <IssueCard
            title="No Media"
            items={pagesWithNoMedia}
            description="Pages without images, videos, or GIFs"
          />
        </div>
      </div>

      {/* Page Status Breakdown */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Page Status</h2>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">{successfulPages}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Successful (200)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600 dark:text-red-400">{failedPages}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Failed (4xx/5xx)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">{totalPages}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Pages</div>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Recommendations</h2>
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="space-y-2">
            {pagesWithMissingTitles.length > 0 && (
              <div className="text-sm text-blue-800 dark:text-blue-300">
                • Review and add titles for {pagesWithMissingTitles.length} pages
              </div>
            )}
            {pagesWithLowWordCount.length > 0 && (
              <div className="text-sm text-blue-800 dark:text-blue-300">
                • Consider adding more content to {pagesWithLowWordCount.length} pages with low word count
              </div>
            )}
            {pagesWithNoMedia.length > 0 && (
              <div className="text-sm text-blue-800 dark:text-blue-300">
                • Add images or media to {pagesWithNoMedia.length} pages for better visual appeal
              </div>
            )}
            {failedPages > 0 && (
              <div className="text-sm text-blue-800 dark:text-blue-300">
                • Investigate and fix {failedPages} pages that failed to load
              </div>
            )}
            {totalNavItems === 0 && (
              <div className="text-sm text-blue-800 dark:text-blue-300">
                • No navigation structure found - consider adding navigation elements
              </div>
            )}
            {totalFooterLinks === 0 && (
              <div className="text-sm text-blue-800 dark:text-blue-300">
                • No footer links found - consider adding footer content
              </div>
            )}
            {pagesWithMissingTitles.length === 0 && pagesWithLowWordCount.length === 0 && pagesWithNoMedia.length === 0 && failedPages === 0 && (
              <div className="text-sm text-blue-800 dark:text-blue-300">
                • Great! All pages have good content quality
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryTab;
