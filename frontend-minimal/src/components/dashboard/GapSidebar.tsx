import React from 'react';
import { useDashboardStore } from '../../stores/dashboardStore';

export const GapSidebar: React.FC = () => {
  const { filters, setFilters } = useDashboardStore();
  
  const timeRangeOptions = [
    { value: '7d', label: 'Last 7 days' },
    { value: '30d', label: 'Last 30 days' },
    { value: '90d', label: 'Last 90 days' },
    { value: 'all', label: 'All time' },
  ];
  
  return (
    <div className="gap-sidebar w-64 bg-white border-l p-4">
      <h2 className="text-lg font-semibold mb-4">Filters</h2>
      
      <div className="space-y-6">
        {/* Unresolved Only Filter */}
        <div>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={filters.unresolvedOnly}
              onChange={(e) => setFilters({ unresolvedOnly: e.target.checked })}
              className="rounded text-blue-600"
            />
            <span className="text-sm font-medium text-gray-700">Show only unresolved</span>
          </label>
        </div>
        
        {/* Critical Only Filter */}
        <div>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={filters.criticalOnly}
              onChange={(e) => setFilters({ criticalOnly: e.target.checked })}
              className="rounded text-blue-600"
            />
            <span className="text-sm font-medium text-gray-700">Show only critical nodes</span>
          </label>
          <p className="text-xs text-gray-500 mt-1">(≥ 3 hallucinations)</p>
        </div>
        
        {/* Time Range Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Time range</label>
          <select
            value={filters.timeRange}
            onChange={(e) => setFilters({ timeRange: e.target.value as any })}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
          >
            {timeRangeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        
        {/* Summary Stats */}
        <div className="pt-4 border-t">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Critical nodes:</span>
              <span className="font-medium">0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">At risk nodes:</span>
              <span className="font-medium">0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Stable nodes:</span>
              <span className="font-medium">0</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
