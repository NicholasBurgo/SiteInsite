import React, { useState } from 'react';
import { CheckCircle, XCircle, FileText, BookOpen, Hash, Clock, Eye } from 'lucide-react';
import { DraftModel } from '../lib/types';

interface ParagraphsTabProps {
  draft: DraftModel;
  confirmedFields: Set<string>;
  onToggleConfirmation: (fieldId: string) => void;
}

export default function ParagraphsTab({ draft, confirmedFields, onToggleConfirmation }: ParagraphsTabProps) {
  const [selectedPage, setSelectedPage] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Mock paragraph data - in real implementation, this would come from the backend
  const mockParagraphs = [
    {
      pageId: 'page1',
      pageTitle: 'About Us',
      url: 'https://example.com/about',
      paragraphs: [
        {
          id: 'p1',
          text: 'We are a leading company in the technology industry, providing innovative solutions to businesses worldwide.',
          wordCount: 18,
          confidence: 0.9,
          sources: ['page1']
        },
        {
          id: 'p2',
          text: 'Our team consists of experienced professionals who are passionate about delivering high-quality products and services.',
          wordCount: 19,
          confidence: 0.85,
          sources: ['page1']
        }
      ]
    },
    {
      pageId: 'page2',
      pageTitle: 'Services',
      url: 'https://example.com/services',
      paragraphs: [
        {
          id: 'p3',
          text: 'We offer comprehensive web development services including frontend, backend, and full-stack solutions.',
          wordCount: 16,
          confidence: 0.88,
          sources: ['page2']
        },
        {
          id: 'p4',
          text: 'Our consulting services help businesses optimize their digital presence and improve their online performance.',
          wordCount: 17,
          confidence: 0.82,
          sources: ['page2']
        }
      ]
    }
  ];

  const filteredParagraphs = mockParagraphs.filter(page => 
    selectedPage === null || page.pageId === selectedPage
  ).map(page => ({
    ...page,
    paragraphs: page.paragraphs.filter(p => 
      searchTerm === '' || p.text.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }));

  const totalWords = mockParagraphs.reduce((sum, page) => 
    sum + page.paragraphs.reduce((pageSum, p) => pageSum + p.wordCount, 0), 0
  );

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

  const ParagraphCard = ({ paragraph, pageTitle }: { paragraph: any; pageTitle: string }) => (
    <div className="border border-gray-200 rounded-lg p-4">
      <ConfirmationToggle fieldId={`paragraph_${paragraph.id}`}>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                {pageTitle}
              </span>
              <span className="text-xs text-gray-500">
                {paragraph.wordCount} words
              </span>
            </div>
            <span className={`text-xs px-2 py-1 rounded ${
              paragraph.confidence > 0.8 ? 'bg-green-100 text-green-800' :
              paragraph.confidence > 0.5 ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {Math.round(paragraph.confidence * 100)}% confidence
            </span>
          </div>
          
          <div className="text-sm text-gray-700 leading-relaxed">
            {paragraph.text}
          </div>
          
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <Hash className="w-3 h-3" />
              ID: {paragraph.id}
            </div>
            <div className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              Sources: {paragraph.sources.length}
            </div>
          </div>
        </div>
      </ConfirmationToggle>
    </div>
  );

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Text Content</h2>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>{totalWords.toLocaleString()} words</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        {/* Page Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Page:</label>
          <select
            value={selectedPage || ''}
            onChange={(e) => setSelectedPage(e.target.value || null)}
            className="border border-gray-300 rounded-lg px-3 py-1 text-sm focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
          >
            <option value="">All Pages</option>
            {mockParagraphs.map((page) => (
              <option key={page.pageId} value={page.pageId}>
                {page.pageTitle}
              </option>
            ))}
          </select>
        </div>

        {/* Search */}
        <div className="flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search paragraphs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-1 text-sm focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
          />
        </div>
      </div>

      {/* Statistics */}
      <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 shadow-sm">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">{mockParagraphs.length}</div>
            <div className="text-sm text-gray-600 font-medium">Pages</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {mockParagraphs.reduce((sum, page) => sum + page.paragraphs.length, 0)}
            </div>
            <div className="text-sm text-gray-600 font-medium">Paragraphs</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">{totalWords.toLocaleString()}</div>
            <div className="text-sm text-gray-600 font-medium">Total Words</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {Math.round(totalWords / mockParagraphs.reduce((sum, page) => sum + page.paragraphs.length, 0))}
            </div>
            <div className="text-sm text-gray-600 font-medium">Avg Words/Paragraph</div>
          </div>
        </div>
      </div>

      {/* Paragraphs by Page */}
      <div className="space-y-6">
        {filteredParagraphs.map((page) => (
          <div key={page.pageId}>
            <div className="flex items-center gap-3 mb-4">
              <BookOpen className="w-5 h-5 text-gray-400" />
              <div>
                <h3 className="font-medium text-gray-900">{page.pageTitle}</h3>
                <div className="text-sm text-gray-500">
                  {page.paragraphs.length} paragraphs • {page.paragraphs.reduce((sum, p) => sum + p.wordCount, 0)} words
                </div>
                <a 
                  href={page.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline"
                >
                  {page.url}
                </a>
              </div>
            </div>
            
            <div className="space-y-3">
              {page.paragraphs.map((paragraph) => (
                <ParagraphCard 
                  key={paragraph.id} 
                  paragraph={paragraph} 
                  pageTitle={page.pageTitle}
                />
              ))}
            </div>
          </div>
        ))}
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
            <FileText className="w-4 h-4" />
            <span className="font-medium">Export Text</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-3 bg-gray-50 text-gray-700 rounded-xl hover:bg-gray-100 transition-colors shadow-sm hover:shadow-md">
            <Eye className="w-4 h-4" />
            <span className="font-medium">Preview All</span>
          </button>
        </div>
      </div>
    </div>
  );
}

