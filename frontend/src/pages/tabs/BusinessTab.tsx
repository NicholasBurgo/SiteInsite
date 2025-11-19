import React, { useState } from 'react';
import { CheckCircle, XCircle, Building2, Phone, Mail, Globe, MapPin, Scale, Edit3, ExternalLink, Image } from 'lucide-react';
import { DraftModel } from '../lib/types';

interface BusinessTabProps {
  draft: DraftModel;
  confirmedFields: Set<string>;
  onToggleConfirmation: (fieldId: string) => void;
}

export default function BusinessTab({ draft, confirmedFields, onToggleConfirmation }: BusinessTabProps) {
  const [activeSubTab, setActiveSubTab] = useState('identity');

  const subTabs = [
    { id: 'identity', label: 'Identity', icon: Building2 },
    { id: 'services', label: 'Services', icon: Globe },
    { id: 'contact', label: 'Contact', icon: Phone },
    { id: 'legal', label: 'Legal', icon: Scale }
  ];

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

  const IdentitySection = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Building2 className="w-6 h-6 text-blue-600" />
        <h3 className="text-xl font-semibold text-gray-900">Business Identity</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Business Name</label>
            <ConfirmationToggle fieldId="business_name">
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  value={draft.business.name || ''}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
                  readOnly
                />
              </div>
            </ConfirmationToggle>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Tagline</label>
            <ConfirmationToggle fieldId="business_tagline">
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  value={draft.business.tagline || ''}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
                  readOnly
                />
              </div>
            </ConfirmationToggle>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Logo</label>
            <ConfirmationToggle fieldId="business_logo">
              <div className="flex items-center gap-3">
                {draft.business.logo ? (
                  <>
                    <img src={draft.business.logo} alt="Logo" className="w-16 h-16 object-contain border border-gray-200 rounded-lg" />
                    <div className="flex-1">
                      <span className="text-sm text-gray-600 block truncate">{draft.business.logo}</span>
                      <span className="text-xs text-gray-500">Logo detected</span>
                    </div>
                  </>
                ) : (
                  <div className="flex items-center gap-3 text-gray-500">
                    <div className="w-16 h-16 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
                      <Image className="w-6 h-6" />
                    </div>
                    <span className="text-sm">No logo found</span>
                  </div>
                )}
              </div>
            </ConfirmationToggle>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Brand Colors</label>
            <ConfirmationToggle fieldId="business_colors">
              <div className="space-y-3">
                {draft.business.brand_colors.length > 0 ? (
                  draft.business.brand_colors.map((color, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <div 
                        className="w-8 h-8 rounded-lg border border-gray-200 shadow-sm" 
                        style={{ backgroundColor: color }}
                      ></div>
                      <span className="text-sm text-gray-600 font-mono">{color}</span>
                    </div>
                  ))
                ) : (
                  <span className="text-sm text-gray-500">No brand colors found</span>
                )}
              </div>
            </ConfirmationToggle>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Social Media</label>
            <ConfirmationToggle fieldId="business_socials">
              <div className="space-y-3">
                {Object.keys(draft.business.socials).length > 0 ? (
                  Object.entries(draft.business.socials).map(([platform, url]) => (
                    <div key={platform} className="flex items-center gap-3">
                      <span className="text-sm text-gray-600 w-20 capitalize font-medium">{platform}:</span>
                      <a 
                        href={url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:text-blue-800 truncate flex-1"
                      >
                        {url}
                      </a>
                    </div>
                  ))
                ) : (
                  <span className="text-sm text-gray-500">No social media links found</span>
                )}
              </div>
            </ConfirmationToggle>
          </div>
        </div>
      </div>
    </div>
  );

  const ServicesSection = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Globe className="w-6 h-6 text-blue-600" />
        <h3 className="text-xl font-semibold text-gray-900">Services</h3>
        <span className="text-sm text-gray-500">({draft.services.length} services)</span>
      </div>
      
      <div className="space-y-4">
        {draft.services.length > 0 ? (
          draft.services.map((service, index) => (
            <div key={service.id} className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
              <ConfirmationToggle fieldId={`service_${service.id}`}>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-gray-900 text-lg">{service.title}</h4>
                    <div className="flex items-center gap-3">
                      <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                        service.confidence > 0.8 ? 'bg-green-100 text-green-800' :
                        service.confidence > 0.5 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {Math.round(service.confidence * 100)}% confidence
                      </span>
                      <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                        <Edit3 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  {service.description && (
                    <p className="text-sm text-gray-700 leading-relaxed">{service.description}</p>
                  )}
                  
                  {service.image && (
                    <div className="flex justify-center">
                      <img src={service.image} alt={service.title} className="max-w-full h-32 object-cover rounded-lg" />
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                    <div className="flex items-center gap-4">
                      <span>Sources: {service.sources.length}</span>
                      <span>ID: {service.id}</span>
                    </div>
                    {service.price && (
                      <span className="font-medium text-green-600">{service.price}</span>
                    )}
                  </div>
                </div>
              </ConfirmationToggle>
            </div>
          ))
        ) : (
          <div className="text-center py-12 text-gray-500">
            <Globe className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h4 className="text-lg font-medium mb-2">No Services Found</h4>
            <p className="text-sm">No services were detected during extraction.</p>
          </div>
        )}
      </div>
    </div>
  );

  const ContactSection = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Phone className="w-6 h-6 text-blue-600" />
        <h3 className="text-xl font-semibold text-gray-900">Contact Information</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-3">Phone Numbers</label>
            <ConfirmationToggle fieldId="business_phones">
              <div className="space-y-2">
                {draft.business.phones.length > 0 ? (
                  draft.business.phones.map((phone, index) => (
                    <div key={index} className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200">
                      <Phone className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium">{phone}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <Phone className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <span className="text-sm">No phone numbers found</span>
                  </div>
                )}
              </div>
            </ConfirmationToggle>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-3">Email Addresses</label>
            <ConfirmationToggle fieldId="business_emails">
              <div className="space-y-2">
                {draft.business.emails.length > 0 ? (
                  draft.business.emails.map((email, index) => (
                    <div key={index} className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200">
                      <Mail className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium">{email}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <Mail className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <span className="text-sm">No email addresses found</span>
                  </div>
                )}
              </div>
            </ConfirmationToggle>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-700 mb-3">Business Locations</label>
            <ConfirmationToggle fieldId="business_locations">
              <div className="space-y-3">
                {draft.locations.length > 0 ? (
                  draft.locations.map((location, index) => (
                    <div key={location.id} className="bg-white border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-gray-900">{location.name || 'Unnamed Location'}</h4>
                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                          location.confidence > 0.8 ? 'bg-green-100 text-green-800' :
                          location.confidence > 0.5 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {Math.round(location.confidence * 100)}%
                        </span>
                      </div>
                      
                      <div className="space-y-2">
                        {location.address && (
                          <div className="flex items-center gap-2">
                            <MapPin className="w-4 h-4 text-gray-400" />
                            <span className="text-sm text-gray-600">{location.address}</span>
                          </div>
                        )}
                        {location.phone && (
                          <div className="flex items-center gap-2">
                            <Phone className="w-4 h-4 text-gray-400" />
                            <span className="text-sm text-gray-600">{location.phone}</span>
                          </div>
                        )}
                        {location.hours && (
                          <div className="text-xs text-gray-500 mt-2">
                            Hours: {JSON.stringify(location.hours)}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <MapPin className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <span className="text-sm">No locations found</span>
                  </div>
                )}
              </div>
            </ConfirmationToggle>
          </div>
        </div>
      </div>
    </div>
  );

  const LegalSection = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Scale className="w-6 h-6 text-blue-600" />
        <h3 className="text-xl font-semibold text-gray-900">Legal & Policies</h3>
        <span className="text-sm text-gray-500">({draft.policies.length} documents)</span>
      </div>
      
      <div className="space-y-4">
        {draft.policies.length > 0 ? (
          draft.policies.map((policy, index) => (
            <div key={index} className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
              <ConfirmationToggle fieldId={`policy_${index}`}>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-gray-900 text-lg">{policy.title || 'Policy Document'}</h4>
                    <div className="flex items-center gap-3">
                      <span className="text-xs px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">
                        {policy.type || 'policy'}
                      </span>
                      <span className="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded-full">
                        {Math.round((policy.confidence || 0.8) * 100)}% confidence
                      </span>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <ExternalLink className="w-4 h-4 text-gray-400" />
                      <span className="text-sm font-medium text-gray-700">Document URL:</span>
                    </div>
                    <a 
                      href={policy.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="text-sm text-blue-600 hover:text-blue-800 hover:underline break-all"
                    >
                      {policy.url}
                    </a>
                  </div>
                  
                  {policy.description && (
                    <p className="text-sm text-gray-700 leading-relaxed">{policy.description}</p>
                  )}
                  
                  <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                    <span>Policy ID: {index + 1}</span>
                    <span>Last updated: {policy.lastUpdated || 'Unknown'}</span>
                  </div>
                </div>
              </ConfirmationToggle>
            </div>
          ))
        ) : (
          <div className="text-center py-12 text-gray-500">
            <Scale className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h4 className="text-lg font-medium mb-2">No Legal Documents Found</h4>
            <p className="text-sm">No legal documents or policies were detected during extraction.</p>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Business Information</h2>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Building2 className="w-4 h-4" />
          <span>Company Details</span>
        </div>
      </div>

      {/* Sub-tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {subTabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={`flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeSubTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Sub-tab content */}
      <div className="border-t border-gray-200 mt-4 pt-4">
        {activeSubTab === 'identity' && <IdentitySection />}
        {activeSubTab === 'services' && <ServicesSection />}
        {activeSubTab === 'contact' && <ContactSection />}
        {activeSubTab === 'legal' && <LegalSection />}
      </div>
    </div>
  );
}

