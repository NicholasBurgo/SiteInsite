import React, { useState } from 'react';
import { CheckCircle, XCircle, Table, BarChart3, Filter, Search, SortAsc, SortDesc } from 'lucide-react';
import { DraftModel } from '../lib/types';

interface TruthTableTabProps {
  draft: DraftModel;
  confirmedFields: Set<string>;
  onToggleConfirmation: (fieldId: string) => void;
}

export default function TruthTableTab({ draft, confirmedFields, onToggleConfirmation }: TruthTableTabProps) {
  const [sortField, setSortField] = useState<string>('confidence');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filterConfidence, setFilterConfidence] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Flatten all data into a unified table format
  const allData = [
    // Business profile fields
    ...Object.entries(draft.business).map(([key, value]) => ({
      id: `business_${key}`,
      category: 'Business',
      subcategory: 'Profile',
      field: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: Array.isArray(value) ? value.join(', ') : String(value || ''),
      confidence: 0.8, // Default confidence for business fields
      sources: draft.business.sources,
      type: 'text'
    })),
    
    // Services
    ...draft.services.map(service => ({
      id: `service_${service.id}`,
      category: 'Business',
      subcategory: 'Services',
      field: service.title,
      value: service.description || '',
      confidence: service.confidence,
      sources: service.sources,
      type: 'service'
    })),
    
    // Products
    ...draft.products.map(product => ({
      id: `product_${product.id}`,
      category: 'Business',
      subcategory: 'Products',
      field: product.title,
      value: product.description || '',
      confidence: product.confidence,
      sources: product.sources,
      type: 'product'
    })),
    
    // Locations
    ...draft.locations.map(location => ({
      id: `location_${location.id}`,
      category: 'Business',
      subcategory: 'Locations',
      field: location.name || 'Location',
      value: location.address || '',
      confidence: location.confidence,
      sources: location.sources,
      type: 'location'
    })),
    
    // Team
    ...draft.team.map(member => ({
      id: `team_${member.id}`,
      category: 'Business',
      subcategory: 'Team',
      field: member.title,
      value: member.description || '',
      confidence: member.confidence,
      sources: member.sources,
      type: 'team'
    })),
    
    // Media
    ...draft.media.map((media, index) => ({
      id: `media_${index}`,
      category: 'Assets',
      subcategory: 'Media',
      field: media.alt || 'Media Asset',
      value: media.src,
      confidence: 0.9, // Default confidence for media
      sources: [media.page_id || 'unknown'],
      type: 'media'
    }))
  ];

  // Filter and sort data
  const filteredData = allData
    .filter(item => {
      const matchesSearch = searchTerm === '' || 
        item.field.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.value.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesConfidence = filterConfidence === 'all' ||
        (filterConfidence === 'high' && item.confidence > 0.8) ||
        (filterConfidence === 'medium' && item.confidence > 0.5 && item.confidence <= 0.8) ||
        (filterConfidence === 'low' && item.confidence <= 0.5);
      
      return matchesSearch && matchesConfidence;
    })
    .sort((a, b) => {
      const aVal = a[sortField as keyof typeof a];
      const bVal = b[sortField as keyof typeof b];
      
      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
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

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'bg-green-100 text-green-800';
    if (confidence > 0.5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'service': return '🔧';
      case 'product': return '📦';
      case 'location': return '📍';
      case 'team': return '👥';
      case 'media': return '🖼️';
      default: return '📄';
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Table className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Truth Table</h2>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>{filteredData.length} items</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search all fields..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
            />
          </div>
        </div>

        {/* Confidence Filter */}
        <select
          value={filterConfidence}
          onChange={(e) => setFilterConfidence(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
        >
          <option value="all">All Confidence</option>
          <option value="high">High (80%+)</option>
          <option value="medium">Medium (50-80%)</option>
          <option value="low">Low (&lt;50%)</option>
        </select>
      </div>

      {/* Statistics */}
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 shadow-sm">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">{allData.length}</div>
            <div className="text-sm text-gray-600 font-medium">Total Fields</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {allData.filter(item => item.confidence > 0.8).length}
            </div>
            <div className="text-sm text-gray-600 font-medium">High Confidence</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {allData.filter(item => item.confidence > 0.5 && item.confidence <= 0.8).length}
            </div>
            <div className="text-sm text-gray-600 font-medium">Medium Confidence</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {allData.filter(item => item.confidence <= 0.5).length}
            </div>
            <div className="text-sm text-gray-600 font-medium">Low Confidence</div>
          </div>
        </div>
      </div>

      {/* Truth Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left p-3 font-medium text-gray-900">
                  <button
                    onClick={() => handleSort('category')}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    Category
                    {sortField === 'category' && (
                      sortDirection === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />
                    )}
                  </button>
                </th>
                <th className="text-left p-3 font-medium text-gray-900">
                  <button
                    onClick={() => handleSort('subcategory')}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    Subcategory
                    {sortField === 'subcategory' && (
                      sortDirection === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />
                    )}
                  </button>
                </th>
                <th className="text-left p-3 font-medium text-gray-900">
                  <button
                    onClick={() => handleSort('field')}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    Field
                    {sortField === 'field' && (
                      sortDirection === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />
                    )}
                  </button>
                </th>
                <th className="text-left p-3 font-medium text-gray-900">Value</th>
                <th className="text-center p-3 font-medium text-gray-900">
                  <button
                    onClick={() => handleSort('confidence')}
                    className="flex items-center gap-1 hover:text-gray-700"
                  >
                    Confidence
                    {sortField === 'confidence' && (
                      sortDirection === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />
                    )}
                  </button>
                </th>
                <th className="text-center p-3 font-medium text-gray-900">Sources</th>
                <th className="text-center p-3 font-medium text-gray-900">Confirm</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((item) => (
                <tr key={item.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getTypeIcon(item.type)}</span>
                      <span className="text-gray-900">{item.category}</span>
                    </div>
                  </td>
                  <td className="p-3 text-gray-600">{item.subcategory}</td>
                  <td className="p-3">
                    <div className="font-medium text-gray-900">{item.field}</div>
                    <div className="text-xs text-gray-500">ID: {item.id}</div>
                  </td>
                  <td className="p-3">
                    <div className="max-w-xs truncate text-gray-700" title={item.value}>
                      {item.value}
                    </div>
                  </td>
                  <td className="p-3 text-center">
                    <span className={`text-xs px-2 py-1 rounded ${getConfidenceColor(item.confidence)}`}>
                      {Math.round(item.confidence * 100)}%
                    </span>
                  </td>
                  <td className="p-3 text-center text-gray-600">
                    {item.sources.length}
                  </td>
                  <td className="p-3 text-center">
                    <ConfirmationToggle fieldId={item.id}>
                      <div></div>
                    </ConfirmationToggle>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
            <span className="font-medium">Confirm High Confidence</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-3 bg-green-50 text-green-700 rounded-xl hover:bg-green-100 transition-colors shadow-sm hover:shadow-md">
            <BarChart3 className="w-4 h-4" />
            <span className="font-medium">Export Data</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-3 bg-gray-50 text-gray-700 rounded-xl hover:bg-gray-100 transition-colors shadow-sm hover:shadow-md">
            <Filter className="w-4 h-4" />
            <span className="font-medium">Filter Low Confidence</span>
          </button>
        </div>
      </div>
    </div>
  );
}

