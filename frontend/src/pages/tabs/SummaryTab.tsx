import React from 'react';
import { CheckCircle, XCircle, Clock, AlertTriangle, BarChart3, Image, FileText, Users, MapPin } from 'lucide-react';
import { DraftModel } from '../lib/types';

interface SummaryTabProps {
  draft: DraftModel;
  confirmedFields: Set<string>;
  onToggleConfirmation: (fieldId: string) => void;
  runSummary?: any;
}

export default function SummaryTab({ draft, confirmedFields, onToggleConfirmation, runSummary }: SummaryTabProps) {
  const totalPages = runSummary?.pages?.total || 0;
  const totalWords = runSummary?.extraction?.words || 0;
  const totalImages = runSummary?.extraction?.images || 0;
  const runtime = runSummary?.runtime || "Unknown";
  const errors = runSummary?.pages?.failed || 0;

  const stats = [
    { label: 'Pages Crawled', value: totalPages, icon: FileText, color: 'text-blue-600' },
    { label: 'Words Extracted', value: totalWords.toLocaleString(), icon: FileText, color: 'text-green-600' },
    { label: 'Images Found', value: totalImages, icon: Image, color: 'text-purple-600' },
    { label: 'Team Members', value: draft.team.length, icon: Users, color: 'text-orange-600' },
    { label: 'Locations', value: draft.locations.length, icon: MapPin, color: 'text-red-600' },
    { label: 'Runtime', value: runtime, icon: Clock, color: 'text-gray-600' }
  ];

  const confidenceStats = [
    { label: 'High Confidence (80%+)', count: runSummary?.confidence?.distribution?.high || 0, 
      color: 'bg-green-500' },
    { label: 'Medium Confidence (50-80%)', count: runSummary?.confidence?.distribution?.medium || 0, 
      color: 'bg-yellow-500' },
    { label: 'Low Confidence (<50%)', count: runSummary?.confidence?.distribution?.low || 0, 
      color: 'bg-red-500' }
  ];

  const handleConfirmAllHighConfidence = () => {
    // Confirm all high confidence items
    const highConfidenceItems = [
      ...draft.services.filter(s => s.confidence > 0.8).map(s => `service_${s.id}`),
      ...draft.products.filter(p => p.confidence > 0.8).map(p => `product_${p.id}`),
      ...draft.locations.filter(l => l.confidence > 0.8).map(l => `location_${l.id}`),
      ...draft.team.filter(t => t.confidence > 0.8).map(t => `team_${t.id}`)
    ];
    
    highConfidenceItems.forEach(itemId => {
      if (!confirmedFields.has(itemId)) {
        onToggleConfirmation(itemId);
      }
    });
  };

  const handleReviewLowConfidence = () => {
    // Navigate to filtered view for low confidence items
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Extraction Summary</h2>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Run Overview</span>
        </div>
      </div>

      {/* Key Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 text-center shadow-sm hover:shadow-md transition-shadow">
              <Icon className={`w-8 h-8 mx-auto mb-3 ${stat.color}`} />
              <div className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</div>
              <div className="text-sm text-gray-600 font-medium">{stat.label}</div>
            </div>
          );
        })}
      </div>

      {/* Business Profile Summary */}
      <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <Building2 className="w-6 h-6 text-blue-600" />
          <h3 className="text-xl font-semibold text-blue-900">Business Profile</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <label className="block text-sm font-medium text-blue-800 mb-2">Business Name</label>
            <div className="flex items-center gap-3">
              <span className="text-blue-900 font-medium flex-1">{draft.business.name || 'Not extracted'}</span>
              <button
                onClick={() => onToggleConfirmation('business_name')}
                className={`p-2 rounded-lg transition-colors ${confirmedFields.has('business_name') ? 'text-green-600 bg-green-50' : 'text-gray-400 bg-gray-50'}`}
              >
                {confirmedFields.has('business_name') ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
              </button>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <label className="block text-sm font-medium text-blue-800 mb-2">Tagline</label>
            <div className="flex items-center gap-3">
              <span className="text-blue-900 flex-1">{draft.business.tagline || 'Not extracted'}</span>
              <button
                onClick={() => onToggleConfirmation('business_tagline')}
                className={`p-2 rounded-lg transition-colors ${confirmedFields.has('business_tagline') ? 'text-green-600 bg-green-50' : 'text-gray-400 bg-gray-50'}`}
              >
                {confirmedFields.has('business_tagline') ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
              </button>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <label className="block text-sm font-medium text-blue-800 mb-2">Phone Numbers</label>
            <div className="flex items-center gap-3">
              <span className="text-blue-900 font-medium flex-1">{draft.business.phones.length} found</span>
              <button
                onClick={() => onToggleConfirmation('business_phones')}
                className={`p-2 rounded-lg transition-colors ${confirmedFields.has('business_phones') ? 'text-green-600 bg-green-50' : 'text-gray-400 bg-gray-50'}`}
              >
                {confirmedFields.has('business_phones') ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
              </button>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <label className="block text-sm font-medium text-blue-800 mb-2">Email Addresses</label>
            <div className="flex items-center gap-3">
              <span className="text-blue-900 font-medium flex-1">{draft.business.emails.length} found</span>
              <button
                onClick={() => onToggleConfirmation('business_emails')}
                className={`p-2 rounded-lg transition-colors ${confirmedFields.has('business_emails') ? 'text-green-600 bg-green-50' : 'text-gray-400 bg-gray-50'}`}
              >
                {confirmedFields.has('business_emails') ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Confidence Distribution */}
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <BarChart3 className="w-6 h-6 text-gray-600" />
          <h3 className="text-xl font-semibold text-gray-900">Confidence Distribution</h3>
        </div>
        <div className="space-y-4">
          {confidenceStats.map((stat, index) => (
            <div key={index} className="flex items-center justify-between bg-white rounded-lg p-4 shadow-sm">
              <span className="text-sm font-medium text-gray-700">{stat.label}</span>
              <div className="flex items-center gap-3">
                <div className="w-32 bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full ${stat.color}`}
                    style={{ width: `${(stat.count / Math.max(...confidenceStats.map(s => s.count), 1)) * 100}%` }}
                  ></div>
                </div>
                <span className="text-sm font-bold text-gray-900 w-8 text-right">{stat.count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Errors and Warnings */}
      {errors > 0 && (
        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-8 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="w-6 h-6 text-red-600" />
            <h3 className="text-xl font-semibold text-red-900">Extraction Issues</h3>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-red-700 font-medium">Found {errors} errors during extraction. Some data may be incomplete.</p>
            <p className="text-sm text-red-600 mt-2">Review the extraction logs for more details about specific issues.</p>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl p-8 shadow-sm border border-gray-200">
        <div className="flex items-center gap-3 mb-6">
          <CheckCircle className="w-6 h-6 text-green-600" />
          <h3 className="text-xl font-semibold text-gray-900">Quick Actions</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <button 
            onClick={handleConfirmAllHighConfidence}
            className="flex items-center gap-3 p-4 bg-blue-50 text-blue-700 rounded-xl hover:bg-blue-100 transition-colors shadow-sm hover:shadow-md"
          >
            <CheckCircle className="w-5 h-5" />
            <div className="text-left">
              <div className="font-medium">Confirm All High Confidence</div>
              <div className="text-xs text-blue-600">Auto-confirm items with 80%+ confidence</div>
            </div>
          </button>
          <button 
            onClick={handleReviewLowConfidence}
            className="flex items-center gap-3 p-4 bg-yellow-50 text-yellow-700 rounded-xl hover:bg-yellow-100 transition-colors shadow-sm hover:shadow-md"
          >
            <AlertTriangle className="w-5 h-5" />
            <div className="text-left">
              <div className="font-medium">Review Low Confidence</div>
              <div className="text-xs text-yellow-600">Focus on items needing review</div>
            </div>
          </button>
          <button className="flex items-center gap-3 p-4 bg-green-50 text-green-700 rounded-xl hover:bg-green-100 transition-colors shadow-sm hover:shadow-md">
            <BarChart3 className="w-5 h-5" />
            <div className="text-left">
              <div className="font-medium">View Detailed Stats</div>
              <div className="text-xs text-green-600">Export extraction analytics</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
