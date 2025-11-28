/**
 * Content tabs component for editing page content.
 * Provides Media, Files, Words, and Links editing capabilities.
 */
import React, { useState } from 'react';
import { PageContent, ContentSubTab, MediaType, LinkType } from '../lib/types.confirm';
import { confirmationUtils } from '../lib/api.confirm';

interface ContentTabsProps {
  pageContent: PageContent | null;
  onContentUpdate: (content: Partial<PageContent>) => void;
  loading: boolean;
  saving: boolean;
  selectedPagePath?: string;
  onBack?: () => void;
}

const ContentTabs: React.FC<ContentTabsProps> = ({
  pageContent,
  onContentUpdate,
  loading,
  saving,
  selectedPagePath,
  onBack
}) => {
  const [activeSubTab, setActiveSubTab] = useState<ContentSubTab>('media');
  const [editingContent, setEditingContent] = useState(false);
  const [editedContent, setEditedContent] = useState<Partial<PageContent>>({});

  const handleSave = () => {
    onContentUpdate(editedContent);
    setEditingContent(false);
    setEditedContent({});
  };

  const updateField = (field: string, value: any) => {
    setEditedContent(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const updateMediaItem = (type: MediaType, index: number, field: string, value: any) => {
    if (!pageContent) return;
    
    const updatedMedia = { ...pageContent.media };
    const items = [...updatedMedia[type]];
    items[index] = { ...items[index], [field]: value };
    updatedMedia[type] = items;
    
    updateField('media', updatedMedia);
  };

  const updateFileItem = (index: number, field: string, value: any) => {
    if (!pageContent) return;
    
    const updatedFiles = [...pageContent.files];
    updatedFiles[index] = { ...updatedFiles[index], [field]: value };
    
    updateField('files', updatedFiles);
  };

  const updateLinkItem = (type: LinkType, index: number, field: string, value: any) => {
    if (!pageContent) return;
    
    const updatedLinks = { ...pageContent.links };
    const items = [...updatedLinks[type]];
    items[index] = { ...items[index], [field]: value };
    updatedLinks[type] = items;
    
    updateField('links', updatedLinks);
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-500 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading page content...</p>
      </div>
    );
  }

  if (!pageContent) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 dark:text-gray-400">Select a page to view its content</p>
      </div>
    );
  }

  const currentContent = { ...pageContent, ...editedContent };

  return (
    <div>
      {/* Page Info and Tabs Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
        {/* Sub-tab Navigation - Left Side */}
        <div className="flex-shrink-0">
        <nav className="flex space-x-8">
          {[
            { id: 'media', label: 'Images / GIFs / Videos' },
            { id: 'files', label: 'Files' },
            { id: 'words', label: 'Words' },
            { id: 'links', label: 'Links' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id as ContentSubTab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeSubTab === tab.id
                  ? 'border-blue-500 dark:border-blue-400 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
        </div>

        {/* Page Information - Right Side */}
        {pageContent && (
          <div className="flex-1 min-w-0 ml-6 text-right">
            <h2 className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">
              {pageContent.title || 'Untitled Page'}
            </h2>
            <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {pageContent.url || selectedPagePath || 'Unknown'}
            </div>
          </div>
        )}
      </div>

      {/* Save Button */}
      {editingContent && (
        <div className="flex justify-end mb-4">
          <div className="space-x-2">
            <button
              onClick={() => {
                setEditedContent({});
                setEditingContent(false);
              }}
              className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-full text-sm hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}

      {/* Media Tab */}
      {activeSubTab === 'media' && (
        <div className="space-y-6">
          {/* Images */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Images</h3>
              <button
                onClick={() => setEditingContent(true)}
                className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-full text-sm hover:bg-blue-700 dark:hover:bg-blue-600"
              >
                Edit Content
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {currentContent.media.images.map((image, index) => (
                <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800">
                  <img
                    src={image.url}
                    alt={image.alt || ''}
                    className="w-full h-32 object-cover rounded mb-2"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5YTNhZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=';
                    }}
                  />
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={image.alt || ''}
                      onChange={(e) => updateMediaItem('images', index, 'alt', e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                      placeholder="Alt text"
                      disabled={!editingContent}
                    />
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {image.width && image.height ? `${image.width}×${image.height}` : 'Unknown size'}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate" title={image.url}>
                      {image.url}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* GIFs */}
          {currentContent.media.gifs.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">GIFs</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {currentContent.media.gifs.map((gif, index) => (
                  <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800">
                    <img
                      src={gif.url}
                      className="w-full h-32 object-cover rounded mb-2"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5YTNhZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkdpZiBub3QgZm91bmQ8L3RleHQ+PC9zdmc+';
                      }}
                    />
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate" title={gif.url}>
                      {gif.url}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Videos */}
          {currentContent.media.videos.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Videos</h3>
              <div className="space-y-4">
                {currentContent.media.videos.map((video, index) => (
                  <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                      Video {index + 1} ({video.type || 'unknown type'})
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate" title={video.url}>
                      {video.url}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Files Tab */}
      {activeSubTab === 'files' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Downloadable Files</h3>
            <button
              onClick={() => setEditingContent(true)}
              className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-full text-sm hover:bg-blue-700 dark:hover:bg-blue-600"
            >
              Edit Content
            </button>
          </div>
          {currentContent.files.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">No files found</p>
          ) : (
            <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Label</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Size</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">URL</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {currentContent.files.map((file, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="text"
                          value={file.label || ''}
                          onChange={(e) => updateFileItem(index, 'label', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                          disabled={!editingContent}
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {file.type?.toUpperCase() || 'Unknown'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {confirmationUtils.formatFileSize(file.bytes)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs" title={file.url}>
                        {file.url}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Words Tab */}
      {activeSubTab === 'words' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Words</h3>
            <button
              onClick={() => setEditingContent(true)}
              className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-full text-sm hover:bg-blue-700 dark:hover:bg-blue-600"
            >
              Edit Content
            </button>
          </div>
          {/* Title and Description */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Title</label>
              <input
                type="text"
                value={currentContent.title || ''}
                onChange={(e) => updateField('title', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md text-sm"
                disabled={!editingContent}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description</label>
              <textarea
                value={currentContent.description || ''}
                onChange={(e) => updateField('description', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md text-sm"
                disabled={!editingContent}
              />
            </div>
          </div>

          {/* Headings */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Headings Structure</h3>
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded">
              {currentContent.words.headings.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-center py-4">No headings found</p>
              ) : (
                <div className="space-y-2">
                  {currentContent.words.headings.map((heading, index) => (
                    <div key={index} className={`text-sm ${heading.tag === 'h1' ? 'font-bold text-lg' : heading.tag === 'h2' ? 'font-semibold' : 'font-medium'} text-gray-900 dark:text-gray-100`}>
                      <span className="text-gray-500 dark:text-gray-400 text-xs">{heading.tag.toUpperCase()}:</span> {heading.text}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Paragraphs */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Paragraphs</h3>
            <div className="space-y-3">
              {currentContent.words.paragraphs.map((paragraph, index) => (
                <div key={index} className="border border-gray-200 dark:border-gray-700 rounded p-3 bg-white dark:bg-gray-800">
                  <textarea
                    value={paragraph}
                    onChange={(e) => {
                      const updatedParagraphs = [...currentContent.words.paragraphs];
                      updatedParagraphs[index] = e.target.value;
                      updateField('words', { ...currentContent.words, paragraphs: updatedParagraphs });
                    }}
                    rows={3}
                    className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                    disabled={!editingContent}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Word Count */}
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-900 dark:text-blue-300">Word Count</span>
              <span className="text-lg font-bold text-blue-900 dark:text-blue-300">{currentContent.words.wordCount}</span>
            </div>
          </div>
        </div>
      )}

      {/* Links Tab */}
      {activeSubTab === 'links' && (
        <div className="space-y-6">
          {/* Internal Links */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Internal Links</h3>
              <button
                onClick={() => setEditingContent(true)}
                className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-full text-sm hover:bg-blue-700 dark:hover:bg-blue-600"
              >
                Edit Content
              </button>
            </div>
            {currentContent.links.internal.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">No internal links found</p>
            ) : (
              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Label</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">URL</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {currentContent.links.internal.map((link, index) => (
                      <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="text"
                            value={link.label || ''}
                            onChange={(e) => updateLinkItem('internal', index, 'label', e.target.value)}
                            className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                            disabled={!editingContent}
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="text"
                            value={link.href}
                            onChange={(e) => updateLinkItem('internal', index, 'href', e.target.value)}
                            className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                            disabled={!editingContent}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* External Links */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">External Links</h3>
              <button
                onClick={() => setEditingContent(true)}
                className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-full text-sm hover:bg-blue-700 dark:hover:bg-blue-600"
              >
                Edit Content
              </button>
            </div>
            {currentContent.links.external.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">No external links found</p>
            ) : (
              <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Label</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">URL</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {currentContent.links.external.map((link, index) => (
                      <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="text"
                            value={link.label || ''}
                            onChange={(e) => updateLinkItem('external', index, 'label', e.target.value)}
                            className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                            disabled={!editingContent}
                          />
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="text"
                            value={link.href}
                            onChange={(e) => updateLinkItem('external', index, 'href', e.target.value)}
                            className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                            disabled={!editingContent}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Broken Links */}
          {currentContent.links.broken.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Broken Links</h3>
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
                <div className="space-y-2">
                  {currentContent.links.broken.map((link, index) => (
                    <div key={index} className="text-sm">
                      <span className="text-red-600 dark:text-red-400">{link.href}</span>
                      {link.status && <span className="text-red-500 dark:text-red-400 ml-2">(Status: {link.status})</span>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContentTabs;
