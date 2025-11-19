import React, { useState } from 'react';
import { CheckCircle, XCircle, Image, Download, Eye, FileImage, Video, File } from 'lucide-react';
import { DraftModel } from '../lib/types';

interface AssetsTabProps {
  draft: DraftModel;
  confirmedFields: Set<string>;
  onToggleConfirmation: (fieldId: string) => void;
}

export default function AssetsTab({ draft, confirmedFields, onToggleConfirmation }: AssetsTabProps) {
  const [activeView, setActiveView] = useState('grid');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const categories = [
    { id: 'all', label: 'All Assets', count: draft.media.length },
    { id: 'logo', label: 'Logos', count: draft.media.filter(m => m.role === 'logo').length },
    { id: 'hero', label: 'Hero Images', count: draft.media.filter(m => m.role === 'hero').length },
    { id: 'team', label: 'Team Photos', count: draft.media.filter(m => m.role === 'team').length },
    { id: 'product', label: 'Product Images', count: draft.media.filter(m => m.role === 'product').length },
    { id: 'content', label: 'Content Images', count: draft.media.filter(m => m.role === 'content').length }
  ];

  const filteredMedia = selectedCategory === 'all' 
    ? draft.media 
    : draft.media.filter(m => m.role === selectedCategory);

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

  const ImageCard = ({ asset, index }: { asset: any; index: number }) => (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="aspect-square bg-gray-100 flex items-center justify-center">
        <img
          src={asset.src}
          alt={asset.alt || 'Asset'}
          className="max-w-full max-h-full object-contain"
          onError={(e) => {
            e.currentTarget.style.display = 'none';
            e.currentTarget.nextElementSibling!.style.display = 'flex';
          }}
        />
        <div className="hidden items-center justify-center text-gray-400">
          <FileImage className="w-8 h-8" />
        </div>
      </div>
      <div className="p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded capitalize">
            {asset.role || 'content'}
          </span>
          <ConfirmationToggle fieldId={`asset_${index}`}>
            <div></div>
          </ConfirmationToggle>
        </div>
        <div className="text-sm text-gray-600 truncate mb-1">
          {asset.alt || 'No description'}
        </div>
        <div className="text-xs text-gray-500 truncate">
          {asset.src}
        </div>
        <div className="flex items-center gap-2 mt-2">
          <button className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800">
            <Eye className="w-3 h-3" />
            Preview
          </button>
          <button className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-800">
            <Download className="w-3 h-3" />
            Download
          </button>
        </div>
      </div>
    </div>
  );

  const ListView = () => (
    <div className="space-y-3">
      {filteredMedia.map((asset, index) => (
        <div key={index} className="border border-gray-200 rounded-lg p-4">
          <ConfirmationToggle fieldId={`asset_${index}`}>
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                <img
                  src={asset.src}
                  alt={asset.alt || 'Asset'}
                  className="max-w-full max-h-full object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.nextElementSibling!.style.display = 'flex';
                  }}
                />
                <div className="hidden items-center justify-center text-gray-400">
                  <FileImage className="w-6 h-6" />
                </div>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-900">
                    {asset.alt || 'Untitled Asset'}
                  </span>
                  <span className="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded capitalize">
                    {asset.role || 'content'}
                  </span>
                </div>
                <div className="text-xs text-gray-500 truncate mb-2">
                  {asset.src}
                </div>
                <div className="flex items-center gap-3">
                  <button className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800">
                    <Eye className="w-3 h-3" />
                    Preview
                  </button>
                  <button className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-800">
                    <Download className="w-3 h-3" />
                    Download
                  </button>
                </div>
              </div>
            </div>
          </ConfirmationToggle>
        </div>
      ))}
    </div>
  );

  const GridView = () => (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
      {filteredMedia.map((asset, index) => (
        <ImageCard key={index} asset={asset} index={index} />
      ))}
    </div>
  );

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Image className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Assets & Media</h2>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>{draft.media.length} files</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        {/* Category Filter */}
        <div className="flex gap-2">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                selectedCategory === category.id
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {category.label} ({category.count})
            </button>
          ))}
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveView('grid')}
            className={`p-2 rounded ${activeView === 'grid' ? 'bg-blue-100 text-blue-700' : 'text-gray-400'}`}
          >
            <div className="w-4 h-4 grid grid-cols-2 gap-0.5">
              <div className="bg-current rounded-sm"></div>
              <div className="bg-current rounded-sm"></div>
              <div className="bg-current rounded-sm"></div>
              <div className="bg-current rounded-sm"></div>
            </div>
          </button>
          <button
            onClick={() => setActiveView('list')}
            className={`p-2 rounded ${activeView === 'list' ? 'bg-blue-100 text-blue-700' : 'text-gray-400'}`}
          >
            <div className="w-4 h-4 flex flex-col gap-0.5">
              <div className="bg-current rounded-sm h-1"></div>
              <div className="bg-current rounded-sm h-1"></div>
              <div className="bg-current rounded-sm h-1"></div>
            </div>
          </button>
        </div>
      </div>

      {/* Asset Statistics */}
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 shadow-sm">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">{draft.media.length}</div>
            <div className="text-sm text-gray-600 font-medium">Total Assets</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {draft.media.filter(m => m.role === 'logo').length}
            </div>
            <div className="text-sm text-gray-600 font-medium">Logos</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {draft.media.filter(m => m.role === 'hero').length}
            </div>
            <div className="text-sm text-gray-600 font-medium">Hero Images</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {draft.media.filter(m => m.role === 'product').length}
            </div>
            <div className="text-sm text-gray-600 font-medium">Product Images</div>
          </div>
        </div>
      </div>

      {/* Assets Display */}
      {filteredMedia.length > 0 ? (
        activeView === 'grid' ? <GridView /> : <ListView />
      ) : (
        <div className="text-center py-12 text-gray-500">
          <Image className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>No assets found in this category</p>
        </div>
      )}

      {/* Bulk Actions */}
      <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl p-6 shadow-sm border border-gray-200">
        <div className="flex items-center gap-3 mb-4">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-medium text-gray-900">Bulk Actions</h3>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-3 bg-blue-50 text-blue-700 rounded-xl hover:bg-blue-100 transition-colors shadow-sm hover:shadow-md">
            <CheckCircle className="w-4 h-4" />
            <span className="font-medium">Confirm All Logos</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-3 bg-green-50 text-green-700 rounded-xl hover:bg-green-100 transition-colors shadow-sm hover:shadow-md">
            <Download className="w-4 h-4" />
            <span className="font-medium">Download All</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-3 bg-gray-50 text-gray-700 rounded-xl hover:bg-gray-100 transition-colors shadow-sm hover:shadow-md">
            <Eye className="w-4 h-4" />
            <span className="font-medium">Preview Gallery</span>
          </button>
        </div>
      </div>
    </div>
  );
}

