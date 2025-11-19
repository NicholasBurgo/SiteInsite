import React from 'react';
import { RunProgress } from '../lib/types';

interface RunSummaryProps {
  progress: RunProgress | null;
  isRunning: boolean;
}

export function RunSummary({ progress, isRunning }: RunSummaryProps) {
  if (!progress) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 dark:text-gray-100">Run Summary</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">No active run</p>
      </div>
    );
  }

  const { queued, visited, errors, etaSeconds } = progress;
  const total = queued + visited;
  const progressPercent = total > 0 ? (visited / total) * 100 : 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium text-gray-900 dark:text-gray-100">Run Progress</h3>
        <span className={`px-2 py-1 rounded text-xs ${
          isRunning ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
        }`}>
          {isRunning ? 'Running' : 'Completed'}
        </span>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-700 dark:text-gray-300">
          <span>Progress</span>
          <span>{visited} / {total}</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div 
            className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-gray-500 dark:text-gray-400">Queued</div>
            <div className="font-medium text-gray-900 dark:text-gray-100">{queued}</div>
          </div>
          <div>
            <div className="text-gray-500 dark:text-gray-400">Visited</div>
            <div className="font-medium text-green-600 dark:text-green-400">{visited}</div>
          </div>
          <div>
            <div className="text-gray-500 dark:text-gray-400">Errors</div>
            <div className="font-medium text-red-600 dark:text-red-400">{errors}</div>
          </div>
        </div>
        
        {etaSeconds && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            ETA: {Math.round(etaSeconds / 60)} minutes
          </div>
        )}
      </div>
    </div>
  );
}