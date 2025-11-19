import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, CheckCircle, Eye, Edit3, Trash2, Plus, ExternalLink } from 'lucide-react';
import { getDraft, confirmDraft, listPages, getPage } from '../lib/api';
import { DraftModel, ItemBase, Location, NavItem } from '../lib/types';

export function Review() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [draft, setDraft] = useState<DraftModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [pages, setPages] = useState<any[]>([]);
  const [selectedPage, setSelectedPage] = useState<any>(null);
  const [editingItem, setEditingItem] = useState<string | null>(null);

  useEffect(() => {
    if (runId) {
      loadDraft();
      loadPages();
    }
  }, [runId]);

  const loadDraft = async () => {
    try {
      const draftData = await getDraft(runId!);
      setDraft(draftData);
    } catch (error) {
      console.error('Error loading draft:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPages = async () => {
    try {
      const pagesData = await listPages(runId!);
      setPages(pagesData);
    } catch (error) {
      console.error('Error loading pages:', error);
    }
  };

  const handleSaveDraft = async () => {
    if (!draft) return;
    
    setSaving(true);
    try {
      await confirmDraft(runId!, draft);
      alert('Draft confirmed and saved successfully!');
    } catch (error) {
      console.error('Error saving draft:', error);
      alert('Error saving draft');
    } finally {
      setSaving(false);
    }
  };

  const handlePageSelect = async (pageId: string) => {
    try {
      const page = await getPage(runId!, pageId);
      setSelectedPage(page);
    } catch (error) {
      console.error('Error loading page:', error);
    }
  };

  const updateBusinessProfile = (field: string, value: any) => {
    if (!draft) return;
    setDraft({
      ...draft,
      business: {
        ...draft.business,
        [field]: value
      }
    });
  };

  const updateItem = (type: 'services' | 'products' | 'menu' | 'team', item: ItemBase) => {
    if (!draft) return;
    setDraft({
      ...draft,
      [type]: draft[type].map(i => i.id === item.id ? item : i)
    });
  };

  const addItem = (type: 'services' | 'products' | 'menu' | 'team') => {
    if (!draft) return;
    const newItem: ItemBase = {
      id: `new_${Date.now()}`,
      title: 'New Item',
      description: '',
      confidence: 0.5,
      sources: []
    };
    setDraft({
      ...draft,
      [type]: [...draft[type], newItem]
    });
    setEditingItem(newItem.id);
  };

  const deleteItem = (type: 'services' | 'products' | 'menu' | 'team', itemId: string) => {
    if (!draft) return;
    setDraft({
      ...draft,
      [type]: draft[type].filter(i => i.id !== itemId)
    });
  };

  const updateLocation = (location: Location) => {
    if (!draft) return;
    setDraft({
      ...draft,
      locations: draft.locations.map(l => l.id === location.id ? location : l)
    });
  };

  const addLocation = () => {
    if (!draft) return;
    const newLocation: Location = {
      id: `new_${Date.now()}`,
      name: 'New Location',
      confidence: 0.5,
      sources: []
    };
    setDraft({
      ...draft,
      locations: [...draft.locations, newLocation]
    });
  };

  const deleteLocation = (locationId: string) => {
    if (!draft) return;
    setDraft({
      ...draft,
      locations: draft.locations.filter(l => l.id !== locationId)
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading draft...</p>
        </div>
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">Error loading draft</p>
          <button 
            onClick={() => navigate('/generator')}
            className="mt-4 px-4 py-2 bg-blue-500 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-600 dark:hover:bg-blue-600"
          >
            Back to Audit
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Eye },
    { id: 'services', label: 'Services', icon: Edit3 },
    { id: 'products', label: 'Products', icon: Edit3 },
    { id: 'menu', label: 'Menu', icon: Edit3 },
    { id: 'locations', label: 'Locations', icon: Edit3 },
    { id: 'media', label: 'Media', icon: Edit3 },
    { id: 'navigation', label: 'Navigation', icon: Edit3 },
    { id: 'pages', label: 'Pages', icon: Edit3 }
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/generator')}
                className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Audit
              </button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Review & Confirm</h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">Run ID: {runId}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={handleSaveDraft}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-green-500 dark:bg-green-700 text-white rounded-lg hover:bg-green-600 dark:hover:bg-green-600 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving...' : 'Save Draft'}
              </button>
              
              <button
                onClick={handleSaveDraft}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-600 dark:hover:bg-blue-600 disabled:opacity-50"
              >
                <CheckCircle className="w-4 h-4" />
                Confirm & Continue
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <span className="text-gray-600 dark:text-gray-400">Pages: {pages.length}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-gray-600 dark:text-gray-400">Services: {draft.services.length}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
              <span className="text-gray-600 dark:text-gray-400">Locations: {draft.locations.length}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
              <span className="text-gray-600 dark:text-gray-400">Media: {draft.media.length}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Tabs */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 mb-4">Sections</h3>
              <nav className="space-y-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded-lg transition-colors ${
                        activeTab === tab.id
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : 'text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {tab.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              {activeTab === 'overview' && (
                <OverviewTab draft={draft} onUpdate={updateBusinessProfile} />
              )}
              {activeTab === 'services' && (
                <ItemsTab
                  title="Services"
                  items={draft.services}
                  onUpdate={(item) => updateItem('services', item)}
                  onAdd={() => addItem('services')}
                  onDelete={(itemId) => deleteItem('services', itemId)}
                />
              )}
              {activeTab === 'products' && (
                <ItemsTab
                  title="Products"
                  items={draft.products}
                  onUpdate={(item) => updateItem('products', item)}
                  onAdd={() => addItem('products')}
                  onDelete={(itemId) => deleteItem('products', itemId)}
                />
              )}
              {activeTab === 'menu' && (
                <ItemsTab
                  title="Menu"
                  items={draft.menu}
                  onUpdate={(item) => updateItem('menu', item)}
                  onAdd={() => addItem('menu')}
                  onDelete={(itemId) => deleteItem('menu', itemId)}
                />
              )}
              {activeTab === 'locations' && (
                <LocationsTab
                  locations={draft.locations}
                  onUpdate={updateLocation}
                  onAdd={addLocation}
                  onDelete={deleteLocation}
                />
              )}
              {activeTab === 'media' && (
                <MediaTab media={draft.media} />
              )}
              {activeTab === 'navigation' && (
                <NavigationTab sitemap={draft.sitemap} />
              )}
              {activeTab === 'pages' && (
                <PagesTab
                  pages={pages}
                  selectedPage={selectedPage}
                  onPageSelect={handlePageSelect}
                />
              )}
            </div>
          </div>

          {/* Right Sidebar - Page Preview */}
          {activeTab === 'pages' && selectedPage && (
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="font-medium text-gray-900 mb-4">Page Preview</h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 break-all mb-2">{selectedPage.summary?.url}</p>
                    <h4 className="font-medium text-gray-900">{selectedPage.summary?.title || 'Untitled'}</h4>
                  </div>
                  <div className="text-sm text-gray-600">
                    <p>Words: {selectedPage.summary?.words || 0}</p>
                    <p>Images: {selectedPage.summary?.images || 0}</p>
                    <p>Type: {selectedPage.summary?.type || 'HTML'}</p>
                  </div>
                  <div className="max-h-40 overflow-y-auto text-sm text-gray-700">
                    {selectedPage.text ? (
                      <p>{selectedPage.text.slice(0, 500)}...</p>
                    ) : (
                      <p className="text-gray-500">No text content</p>
                    )}
                  </div>
                  <a
                    href={selectedPage.summary?.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Open source page
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Tab Components
function OverviewTab({ draft, onUpdate }: { draft: DraftModel; onUpdate: (field: string, value: any) => void }) {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Business Profile</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Business Name</label>
          <input
            type="text"
            value={draft.business.name || ''}
            onChange={(e) => onUpdate('name', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Tagline</label>
          <input
            type="text"
            value={draft.business.tagline || ''}
            onChange={(e) => onUpdate('tagline', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Phone Numbers</label>
          <textarea
            value={draft.business.phones.join('\n')}
            onChange={(e) => onUpdate('phones', e.target.value.split('\n').filter(p => p.trim()))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
            rows={3}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Email Addresses</label>
          <textarea
            value={draft.business.emails.join('\n')}
            onChange={(e) => onUpdate('emails', e.target.value.split('\n').filter(e => e.trim()))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
            rows={3}
          />
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Social Media</label>
        <div className="space-y-2">
          {Object.entries(draft.business.socials).map(([platform, url]) => (
            <div key={platform} className="flex items-center gap-2">
              <span className="text-sm text-gray-600 w-20 capitalize">{platform}:</span>
              <input
                type="url"
                value={url}
                onChange={(e) => onUpdate('socials', { ...draft.business.socials, [platform]: e.target.value })}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ItemsTab({ 
  title, 
  items, 
  onUpdate, 
  onAdd, 
  onDelete 
}: { 
  title: string; 
  items: ItemBase[]; 
  onUpdate: (item: ItemBase) => void; 
  onAdd: () => void; 
  onDelete: (itemId: string) => void; 
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        <button
          onClick={onAdd}
          className="flex items-center gap-2 px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          <Plus className="w-4 h-4" />
          Add {title.slice(0, -1)}
        </button>
      </div>
      
      <div className="space-y-3">
        {items.map((item) => (
          <ItemEditor
            key={item.id}
            item={item}
            onUpdate={onUpdate}
            onDelete={() => onDelete(item.id)}
          />
        ))}
      </div>
    </div>
  );
}

function ItemEditor({ item, onUpdate, onDelete }: { item: ItemBase; onUpdate: (item: ItemBase) => void; onDelete: () => void }) {
  const [isEditing, setIsEditing] = useState(false);
  
  const handleSave = () => {
    setIsEditing(false);
  };
  
  const handleCancel = () => {
    setIsEditing(false);
  };
  
  if (isEditing) {
    return (
      <div className="border border-gray-200 rounded-lg p-4 space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input
            type="text"
            value={item.title}
            onChange={(e) => onUpdate({ ...item, title: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            value={item.description || ''}
            onChange={(e) => onUpdate({ ...item, description: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
            rows={3}
          />
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
          >
            Save
          </button>
          <button
            onClick={handleCancel}
            className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-medium text-gray-900">{item.title}</h3>
          {item.description && (
            <p className="text-sm text-gray-600 mt-1">{item.description}</p>
          )}
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span>Confidence: {Math.round(item.confidence * 100)}%</span>
            <span>Sources: {item.sources.length}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditing(true)}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            <Edit3 className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-gray-400 hover:text-red-600"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function LocationsTab({ locations, onUpdate, onAdd, onDelete }: {
  locations: Location[];
  onUpdate: (location: Location) => void;
  onAdd: () => void;
  onDelete: (locationId: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Locations</h2>
        <button
          onClick={onAdd}
          className="flex items-center gap-2 px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          <Plus className="w-4 h-4" />
          Add Location
        </button>
      </div>
      
      <div className="space-y-3">
        {locations.map((location) => (
          <LocationEditor
            key={location.id}
            location={location}
            onUpdate={onUpdate}
            onDelete={() => onDelete(location.id)}
          />
        ))}
      </div>
    </div>
  );
}

function LocationEditor({ location, onUpdate, onDelete }: {
  location: Location;
  onUpdate: (location: Location) => void;
  onDelete: () => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  
  if (isEditing) {
    return (
      <div className="border border-gray-200 rounded-lg p-4 space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            type="text"
            value={location.name || ''}
            onChange={(e) => onUpdate({ ...location, name: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
          <textarea
            value={location.address || ''}
            onChange={(e) => onUpdate({ ...location, address: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
            rows={2}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
          <input
            type="text"
            value={location.phone || ''}
            onChange={(e) => onUpdate({ ...location, phone: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditing(false)}
            className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
          >
            Save
          </button>
          <button
            onClick={() => setIsEditing(false)}
            className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-medium text-gray-900">{location.name || 'Unnamed Location'}</h3>
          {location.address && (
            <p className="text-sm text-gray-600 mt-1">{location.address}</p>
          )}
          {location.phone && (
            <p className="text-sm text-gray-600">{location.phone}</p>
          )}
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span>Confidence: {Math.round(location.confidence * 100)}%</span>
            <span>Sources: {location.sources.length}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditing(true)}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            <Edit3 className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-gray-400 hover:text-red-600"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function MediaTab({ media }: { media: any[] }) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Media Library</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {media.map((item, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-3">
            <div className="aspect-square bg-gray-100 rounded-lg mb-2 flex items-center justify-center">
              <img
                src={item.src}
                alt={item.alt}
                className="max-w-full max-h-full object-contain"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.nextElementSibling!.style.display = 'flex';
                }}
              />
              <div className="hidden items-center justify-center text-gray-400 text-xs">
                Image
              </div>
            </div>
            <div className="text-xs text-gray-600">
              <p className="truncate">{item.alt || 'No alt text'}</p>
              <p className="text-gray-400 capitalize">{item.role}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function NavigationTab({ sitemap }: { sitemap: any }) {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Navigation Structure</h2>
      
      <div>
        <h3 className="font-medium text-gray-900 mb-3">Primary Navigation</h3>
        <div className="space-y-2">
          {sitemap.primary.map((item: NavItem, index: number) => (
            <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="text-sm text-gray-600">{index + 1}.</span>
              <span className="text-sm font-medium">{item.label}</span>
              {item.href && (
                <span className="text-xs text-gray-500">({item.href})</span>
              )}
            </div>
          ))}
        </div>
      </div>
      
      <div>
        <h3 className="font-medium text-gray-900 mb-3">Secondary Navigation</h3>
        <div className="space-y-2">
          {sitemap.secondary.map((item: NavItem, index: number) => (
            <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="text-sm text-gray-600">{index + 1}.</span>
              <span className="text-sm font-medium">{item.label}</span>
              {item.href && (
                <span className="text-xs text-gray-500">({item.href})</span>
              )}
            </div>
          ))}
        </div>
      </div>
      
      <div>
        <h3 className="font-medium text-gray-900 mb-3">Footer Navigation</h3>
        <div className="space-y-2">
          {sitemap.footer.map((item: NavItem, index: number) => (
            <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span className="text-sm text-gray-600">{index + 1}.</span>
              <span className="text-sm font-medium">{item.label}</span>
              {item.href && (
                <span className="text-xs text-gray-500">({item.href})</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PagesTab({ pages, selectedPage, onPageSelect }: {
  pages: any[];
  selectedPage: any;
  onPageSelect: (pageId: string) => void;
}) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Crawled Pages</h2>
      
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-50 px-4 py-2 border-b">
          <h3 className="font-medium text-gray-900">Pages ({pages.length})</h3>
        </div>
        <div className="max-h-96 overflow-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-white border-b">
              <tr>
                <th className="text-left p-3">Title</th>
                <th className="text-center p-3">Type</th>
                <th className="text-center p-3">Words</th>
                <th className="text-center p-3">Images</th>
                <th className="text-center p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {pages.map((page) => (
                <tr
                  key={page.pageId}
                  className={`hover:bg-gray-50 cursor-pointer border-b ${
                    selectedPage?.summary?.pageId === page.pageId ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => onPageSelect(page.pageId)}
                >
                  <td className="p-3">{page.title || page.url}</td>
                  <td className="text-center p-3">{page.type}</td>
                  <td className="text-center p-3">{page.words}</td>
                  <td className="text-center p-3">{page.images}</td>
                  <td className="text-center p-3">{page.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

