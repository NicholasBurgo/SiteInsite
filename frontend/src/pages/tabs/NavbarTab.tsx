import React, { useState } from 'react';
import { CheckCircle, XCircle, Navigation, ChevronRight, ChevronDown, ExternalLink, Globe } from 'lucide-react';
import { DraftModel } from '../lib/types';

interface NavbarTabProps {
  draft: DraftModel;
  confirmedFields: Set<string>;
  onToggleConfirmation: (fieldId: string) => void;
}

export default function NavbarTab({ draft, confirmedFields, onToggleConfirmation }: NavbarTabProps) {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const ConfirmationToggle = ({ fieldId, children }: { fieldId: string; children: React.ReactNode }) => (
    <div className="flex items-center gap-2">
      {children}
      <button
        onClick={() => onToggleConfirmation(fieldId)}
        className={`p-1 rounded ${confirmedFields.has(fieldId) ? 'text-green-600' : 'text-gray-400'}`}
      >
        {confirmedFields.has(fieldId) ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
      </button>
    </div>
  );

  const NavItemComponent = ({ item, level = 0, parentId = '' }: { item: any; level?: number; parentId?: string }) => {
    const itemId = `${parentId}_${item.label}`;
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.has(itemId);

    return (
      <div className={`${level > 0 ? 'ml-6' : ''}`}>
        <div className="flex items-center gap-2 py-2">
          {hasChildren && (
            <button
              onClick={() => toggleExpanded(itemId)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-6"></div>}
          
          <ConfirmationToggle fieldId={`nav_${itemId}`}>
            <div className="flex items-center gap-2 flex-1">
              <span className="text-sm font-medium text-gray-900">{item.label}</span>
              {item.href && (
                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-500">({item.href})</span>
                  <ExternalLink className="w-3 h-3 text-gray-400" />
                </div>
              )}
            </div>
          </ConfirmationToggle>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="space-y-1">
            {item.children.map((child: any, index: number) => (
              <NavItemComponent 
                key={index} 
                item={child} 
                level={level + 1} 
                parentId={itemId}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  const NavigationSection = ({ title, items, type }: { title: string; items: any[]; type: string }) => (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Globe className="w-5 h-5 text-gray-400" />
        <h3 className="font-medium text-gray-900">{title}</h3>
        <span className="text-sm text-gray-500">({items.length} items)</span>
      </div>
      
      <div className="bg-gray-50 rounded-lg p-4">
        <ConfirmationToggle fieldId={`nav_section_${type}`}>
          <div className="space-y-1">
            {items.length > 0 ? (
              items.map((item, index) => (
                <NavItemComponent key={index} item={item} parentId={type} />
              ))
            ) : (
              <div className="text-center py-4 text-gray-500">
                <Navigation className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                <p className="text-sm">No {title.toLowerCase()} items found</p>
              </div>
            )}
          </div>
        </ConfirmationToggle>
      </div>
    </div>
  );

  const totalNavItems = draft.sitemap.primary.length + 
                       draft.sitemap.secondary.length + 
                       draft.sitemap.footer.length;

  const countNestedItems = (items: any[]): number => {
    return items.reduce((count, item) => {
      return count + 1 + (item.children ? countNestedItems(item.children) : 0);
    }, 0);
  };

  const totalNestedItems = countNestedItems(draft.sitemap.primary) +
                          countNestedItems(draft.sitemap.secondary) +
                          countNestedItems(draft.sitemap.footer);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Navigation className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Navigation Structure</h2>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>{totalNestedItems} total items</span>
        </div>
      </div>

      {/* Navigation Statistics */}
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 shadow-sm">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">{draft.sitemap.primary.length}</div>
            <div className="text-sm text-gray-600 font-medium">Primary Items</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">{draft.sitemap.secondary.length}</div>
            <div className="text-sm text-gray-600 font-medium">Secondary Items</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">{draft.sitemap.footer.length}</div>
            <div className="text-sm text-gray-600 font-medium">Footer Items</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">{totalNestedItems}</div>
            <div className="text-sm text-gray-600 font-medium">Total Items</div>
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="space-y-6">
        <NavigationSection 
          title="Primary Navigation" 
          items={draft.sitemap.primary} 
          type="primary"
        />
        
        <NavigationSection 
          title="Secondary Navigation" 
          items={draft.sitemap.secondary} 
          type="secondary"
        />
        
        <NavigationSection 
          title="Footer Navigation" 
          items={draft.sitemap.footer} 
          type="footer"
        />
      </div>

      {/* Navigation Analysis */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-3">Navigation Analysis</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-blue-800">Average items per section:</span>
            <span className="text-blue-900 font-medium">
              {Math.round(totalNavItems / 3)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-blue-800">Deepest nesting level:</span>
            <span className="text-blue-900 font-medium">2</span>
          </div>
          <div className="flex justify-between">
            <span className="text-blue-800">Items with URLs:</span>
            <span className="text-blue-900 font-medium">
              {[...draft.sitemap.primary, ...draft.sitemap.secondary, ...draft.sitemap.footer]
                .filter(item => item.href).length}
            </span>
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl p-6 shadow-sm border border-gray-200">
        <div className="flex items-center gap-3 mb-4">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-medium text-gray-900">Bulk Actions</h3>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-3 bg-blue-50 text-blue-700 rounded-xl hover:bg-blue-100 transition-colors shadow-sm hover:shadow-md">
            <CheckCircle className="w-4 h-4" />
            <span className="font-medium">Confirm All Primary</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-3 bg-green-50 text-green-700 rounded-xl hover:bg-green-100 transition-colors shadow-sm hover:shadow-md">
            <Navigation className="w-4 h-4" />
            <span className="font-medium">Generate Sitemap</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-3 bg-gray-50 text-gray-700 rounded-xl hover:bg-gray-100 transition-colors shadow-sm hover:shadow-md">
            <ExternalLink className="w-4 h-4" />
            <span className="font-medium">Test Links</span>
          </button>
        </div>
      </div>
    </div>
  );
}

