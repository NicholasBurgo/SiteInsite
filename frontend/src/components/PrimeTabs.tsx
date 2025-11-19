/**
 * Prime tabs component for navigation, footer, and pages management.
 */
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { PrimeResponse, PrimeSubTab, NavNode } from '../lib/types.confirm';
import { confirmationUtils, confirmationApi } from '../lib/api.confirm';
import NavigationTree from './NavigationTree';

interface PrimeTabsProps {
  data: PrimeResponse;
  onNavigationUpdate: (nav: NavNode[]) => void;
  onFooterUpdate: (footer: any) => void;
  saving: boolean;
}

const PrimeTabs: React.FC<PrimeTabsProps> = ({
  data,
  onNavigationUpdate,
  onFooterUpdate,
  saving
}) => {
  const { runId } = useParams<{ runId: string }>();
  const [activeSubTab, setActiveSubTab] = useState<PrimeSubTab>('nav');
  const [editingFooter, setEditingFooter] = useState(false);
  const [footerData, setFooterData] = useState(data.footer);
  const [pagesData, setPagesData] = useState(data.pages);
  const [editingPageTypes, setEditingPageTypes] = useState(false);
  
  const PAGE_TYPES = [
    { value: 'article', label: 'Article' },
    { value: 'landing', label: 'Landing' },
    { value: 'catalog', label: 'Catalog' },
    { value: 'product', label: 'Product' },
    { value: 'media_gallery', label: 'Media Gallery' },
    { value: 'contact', label: 'Contact' },
    { value: 'utility', label: 'Utility' },
    { value: 'generic', label: 'Generic' }
  ];

  const handleFooterSave = () => {
    onFooterUpdate(footerData);
    setEditingFooter(false);
  };

  return (
    <div>
      {/* Sub-tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'nav', label: 'Navigation Bar' },
            { id: 'footer', label: 'Footer' },
            { id: 'pages', label: 'All Pages' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id as PrimeSubTab)}
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

      {/* Navigation Tab */}
      {activeSubTab === 'nav' && (
        <div>
          <div className="mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Navigation Structure</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Hierarchical tree view with sorting and editing capabilities
            </p>
          </div>

          <NavigationTree
            nodes={data.nav}
            onUpdate={onNavigationUpdate}
            saving={saving}
          />
        </div>
      )}

      {/* Footer Tab */}
      {activeSubTab === 'footer' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Footer Content</h3>
            <div className="space-x-2">
              {editingFooter ? (
                <>
                  <button
                    onClick={() => {
                      setFooterData(data.footer);
                      setEditingFooter(false);
                    }}
                    className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleFooterSave}
                    disabled={saving}
                    className="px-3 py-1 bg-blue-600 dark:bg-blue-700 text-white rounded text-sm hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditingFooter(true)}
                  className="px-3 py-1 bg-blue-600 dark:bg-blue-700 text-white rounded text-sm hover:bg-blue-700 dark:hover:bg-blue-600"
                >
                  Edit Footer
                </button>
              )}
            </div>
          </div>

          {editingFooter ? (
            <div className="space-y-4">
              {/* Footer Columns */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Columns</h4>
                <div className="space-y-2">
                  {footerData.columns.map((column, index) => (
                    <div key={index} className="border border-gray-300 dark:border-gray-600 rounded p-3 bg-white dark:bg-gray-800">
                      <input
                        type="text"
                        value={column.heading || ''}
                        onChange={(e) => {
                          const updated = { ...footerData };
                          updated.columns[index].heading = e.target.value;
                          setFooterData(updated);
                        }}
                        className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm mb-2"
                        placeholder="Column heading"
                      />
                      <div className="space-y-1">
                        {column.links.map((link, linkIndex) => (
                          <div key={linkIndex} className="flex space-x-2">
                            <input
                              type="text"
                              value={link.label}
                              onChange={(e) => {
                                const updated = { ...footerData };
                                updated.columns[index].links[linkIndex].label = e.target.value;
                                setFooterData(updated);
                              }}
                              className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                              placeholder="Link label"
                            />
                            <input
                              type="text"
                              value={link.href}
                              onChange={(e) => {
                                const updated = { ...footerData };
                                updated.columns[index].links[linkIndex].href = e.target.value;
                                setFooterData(updated);
                              }}
                              className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                              placeholder="Link URL"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Social Links */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Social Links</h4>
                <div className="space-y-2">
                  {footerData.socials?.map((social, index) => (
                    <div key={index} className="flex space-x-2">
                      <input
                        type="text"
                        value={social.platform}
                        onChange={(e) => {
                          const updated = { ...footerData };
                          if (updated.socials) {
                            updated.socials[index].platform = e.target.value;
                            setFooterData(updated);
                          }
                        }}
                        className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                        placeholder="Platform"
                      />
                      <input
                        type="text"
                        value={social.url}
                        onChange={(e) => {
                          const updated = { ...footerData };
                          if (updated.socials) {
                            updated.socials[index].url = e.target.value;
                            setFooterData(updated);
                          }
                        }}
                        className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                        placeholder="URL"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded">
              {data.footer.columns.length === 0 && (!data.footer.socials || data.footer.socials.length === 0) ? (
                <p className="text-gray-500 dark:text-gray-400 text-center py-8">No footer content found</p>
              ) : (
                <div className="space-y-4">
                  {data.footer.columns.map((column, index) => (
                    <div key={index}>
                      {column.heading && <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">{column.heading}</h4>}
                      <div className="space-y-1">
                        {column.links.map((link, linkIndex) => (
                          <div key={linkIndex} className="text-sm">
                            <a href={link.href} className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
                              {link.label}
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                  
                  {data.footer.socials && data.footer.socials.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Social Links</h4>
                      <div className="space-y-1">
                        {data.footer.socials.map((social, index) => (
                          <div key={index} className="text-sm">
                            <span className="font-medium text-gray-900 dark:text-gray-100">{social.platform}:</span>{' '}
                            <a href={social.url} className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
                              {social.url}
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* All Pages Tab */}
      {activeSubTab === 'pages' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">All Pages</h3>
            <div className="space-x-2">
              {editingPageTypes ? (
                <>
                  <button
                    onClick={() => {
                      setPagesData(data.pages);
                      setEditingPageTypes(false);
                    }}
                    className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={async () => {
                      // Save page_type changes
                      if (!runId) {
                        alert('Run ID not found');
                        return;
                      }
                      try {
                        for (const page of pagesData) {
                          const originalPage = data.pages.find(p => p.pageId === page.pageId);
                          if (originalPage && originalPage.page_type !== page.page_type) {
                            await confirmationApi.updatePageType(runId, page.pageId, page.page_type || 'generic');
                          }
                        }
                        // Reload data
                        const updatedData = await confirmationApi.getPrime(runId);
                        setPagesData(updatedData.pages);
                        setEditingPageTypes(false);
                      } catch (error) {
                        console.error('Error saving page types:', error);
                        alert('Error saving page types');
                      }
                    }}
                    disabled={saving}
                    className="px-3 py-1 bg-blue-600 dark:bg-blue-700 text-white rounded text-sm hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save Page Types'}
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditingPageTypes(true)}
                  className="px-3 py-1 bg-blue-600 dark:bg-blue-700 text-white rounded text-sm hover:bg-blue-700 dark:hover:bg-blue-600"
                >
                  Edit Page Types
                </button>
              )}
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">#</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Title</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Path</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Page Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Words</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Media</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {pagesData.map((page, index) => (
                  <tr key={page.pageId} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{index + 1}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                      {page.titleGuess || 'Untitled'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{page.path}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {editingPageTypes ? (
                        <select
                          value={page.page_type || 'generic'}
                          onChange={(e) => {
                            const updated = [...pagesData];
                            updated[index] = { ...updated[index], page_type: e.target.value };
                            setPagesData(updated);
                          }}
                          className="px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded text-sm"
                        >
                          {PAGE_TYPES.map(type => (
                            <option key={type.value} value={type.value}>{type.label}</option>
                          ))}
                        </select>
                      ) : (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300">
                          {PAGE_TYPES.find(t => t.value === (page.page_type || 'generic'))?.label || 'Generic'}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        page.status === 200 ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300' : 'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300'
                      }`}>
                        {page.status || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{page.words || 0}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{page.mediaCount || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrimeTabs;
