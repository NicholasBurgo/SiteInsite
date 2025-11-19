import React from 'react';
import { PageDetail as PageDetailType } from '../lib/types';

interface PageDetailProps {
  page: PageDetailType | null;
}

export function PageDetail({ page }: PageDetailProps) {
  if (!page) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">Select a page to view details</p>
      </div>
    );
  }

  const { summary, meta, text, headings, images, links, tables, structuredData, stats } = page;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4 h-full overflow-auto">
      <div className="space-y-4">
        {/* Header */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {summary.title || 'Untitled'}
          </h2>
          <div className="text-sm text-gray-500 dark:text-gray-400 break-all">
            {summary.url}
          </div>
          <div className="flex gap-2 mt-2">
            <span className={`px-2 py-1 rounded text-xs ${
              summary.type === 'HTML' ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300' :
              summary.type === 'PDF' ? 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300' :
              summary.type === 'DOCX' ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300' :
              summary.type === 'JSON' ? 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300' :
              summary.type === 'CSV' ? 'bg-purple-100 dark:bg-purple-900/50 text-purple-800 dark:text-purple-300' :
              summary.type === 'IMG' ? 'bg-pink-100 dark:bg-pink-900/50 text-pink-800 dark:text-pink-300' :
              'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
            }`}>
              {summary.type}
            </span>
            <span className="px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">
              {summary.words} words
            </span>
          </div>
        </div>

        {/* Metadata */}
        {Object.keys(meta).length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Metadata</h3>
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-3 text-sm">
              <pre className="whitespace-pre-wrap text-gray-900 dark:text-gray-100">{JSON.stringify(meta, null, 2)}</pre>
            </div>
          </div>
        )}

        {/* Text Content */}
        {text && (
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Content</h3>
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-3 text-sm max-h-96 overflow-auto">
              <pre className="whitespace-pre-wrap text-gray-900 dark:text-gray-100">{text}</pre>
            </div>
          </div>
        )}

        {/* Headings */}
        {headings.length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Headings</h3>
            <div className="space-y-1">
              {headings.map((heading, index) => (
                <div key={index} className="text-sm text-gray-700 dark:text-gray-300">
                  {heading}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Images */}
        {images.length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Images ({images.length})</h3>
            <div className="grid grid-cols-2 gap-2">
              {images.slice(0, 6).map((image, index) => (
                <div key={index} className="text-xs text-gray-600 dark:text-gray-400 truncate">
                  {image}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Links */}
        {links.length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Links ({links.length})</h3>
            <div className="space-y-1 max-h-32 overflow-auto">
              {links.slice(0, 10).map((link, index) => (
                <div key={index} className="text-sm">
                  <a href={link} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">
                    {link}
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Statistics */}
        {Object.keys(stats).length > 0 && (
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Statistics</h3>
            <div className="bg-gray-50 dark:bg-gray-900 rounded p-3 text-sm">
              <pre className="whitespace-pre-wrap text-gray-900 dark:text-gray-100">{JSON.stringify(stats, null, 2)}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}