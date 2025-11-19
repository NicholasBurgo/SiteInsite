import React from 'react';

interface RunFiltersProps {
  onFilterChange: (filters: {
    query: string;
    type: string;
    minWords: number;
  }) => void;
}

export function RunFilters({ onFilterChange }: RunFiltersProps) {
  const [filters, setFilters] = React.useState({
    query: '',
    type: '',
    minWords: 0
  });

  const handleFilterChange = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
      <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Filters</h3>
      
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Search
          </label>
          <input
            type="text"
            placeholder="Search pages..."
            className="w-full border dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded px-3 py-2 text-sm"
            value={filters.query}
            onChange={(e) => handleFilterChange('query', e.target.value)}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Content Type
          </label>
          <select
            className="w-full border dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded px-3 py-2 text-sm"
            value={filters.type}
            onChange={(e) => handleFilterChange('type', e.target.value)}
          >
            <option value="">All Types</option>
            <option value="HTML">HTML</option>
            <option value="PDF">PDF</option>
            <option value="DOCX">DOCX</option>
            <option value="JSON">JSON</option>
            <option value="CSV">CSV</option>
            <option value="IMG">Images</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Min Words
          </label>
          <input
            type="number"
            min="0"
            className="w-full border dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded px-3 py-2 text-sm"
            value={filters.minWords}
            onChange={(e) => handleFilterChange('minWords', parseInt(e.target.value) || 0)}
          />
        </div>
      </div>
    </div>
  );
}