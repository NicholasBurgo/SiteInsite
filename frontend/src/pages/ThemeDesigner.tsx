/**
 * Theme Designer Page
 * Allows users to preview and select theme designs for their generated site
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import ThemeDemos from '../components/ThemeDemos';
import { TopBar } from '../components/TopBar';

const ThemeDesigner: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Top Bar */}
      <TopBar
        onBack={() => navigate('/')}
      />

      {/* Theme Designer Content */}
      <div className="max-w-7xl mx-auto">
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Theme Designer</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Select a theme design for your generated site</p>
        </div>
        
        <div className="px-6 py-4">
          <ThemeDemos />
        </div>
      </div>
    </div>
  );
};

export default ThemeDesigner;

