import React, { useState } from 'react';
import { FragmentPreview } from './FragmentPreview';

interface ContextCitation {
  id: string;
  nodeId: string;
  nodeLabel: string;
  commitId: string;
  score: number;
  text: string;
  used: boolean;
  metadata?: Record<string, any>;
}

interface ContextCitationsProps {
  citations: ContextCitation[];
  className?: string;
}

export const ContextCitations: React.FC<ContextCitationsProps> = ({ 
  citations, 
  className = 'mt-4'
}) => {
  const [expanded, setExpanded] = useState(true);
  
  // Group citations by usage status
  const usedCitations = citations.filter(c => c.used);
  const unusedCitations = citations.filter(c => !c.used);
  
  const toggleExpanded = () => {
    setExpanded(!expanded);
  };
  
  return (
    <div className={`${className} border-t pt-4`}>
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={toggleExpanded}
      >
        <h4 className="font-medium text-gray-900 flex items-center">
          Retrieved Context
          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {citations.length}
          </span>
        </h4>
        <svg 
          className={`h-5 w-5 text-gray-400 transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      
      {expanded && (
        <div className="mt-3 space-y-3">
          {usedCitations.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-green-700 mb-2 flex items-center">
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Used Context
              </h5>
              <div className="space-y-2">
                {usedCitations.map(citation => (
                  <FragmentPreview 
                    key={citation.id}
                    fragment={citation}
                    className="border-l-4 border-green-500"
                  />
                ))}
              </div>
            </div>
          )}
          
          {unusedCitations.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-gray-500 mb-2 flex items-center">
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Unused Context
              </h5>
              <div className="space-y-2">
                {unusedCitations.map(citation => (
                  <FragmentPreview 
                    key={citation.id}
                    fragment={citation}
                    className="border-l-4 border-gray-300 opacity-75"
                  />
                ))}
              </div>
            </div>
          )}
          
          {citations.length === 0 && (
            <div className="text-sm text-gray-500 italic">
              No context retrieved for this response
            </div>
          )}
        </div>
      )}
    </div>
  );
};
