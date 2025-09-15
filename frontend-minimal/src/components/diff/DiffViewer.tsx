import { useState } from 'react';
import { motion } from 'framer-motion';
import Editor from '@monaco-editor/react';

type DiffType = 'unified' | 'split';

interface DiffViewerProps {
  semanticSummary: string;
  textualDiff: string;
  childNodeId: string;
  parentNodeId: string;
  onApprove: () => void;
  onReject: () => void;
  onClose: () => void;
}

export function DiffViewer({ 
  semanticSummary, 
  textualDiff, 
  childNodeId, 
  parentNodeId,
  onApprove,
  onReject,
  onClose
}: DiffViewerProps) {
  const [diffType, setDiffType] = useState<DiffType>('split');
  
  // Parse textual diff into lines for better visualization
  const diffLines = textualDiff.split('\n');
  
  return (
    <motion.div 
      className="flex flex-col h-full bg-white border-l"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <motion.div 
        className="p-4 border-b flex justify-between items-center"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div>
          <h3 className="font-semibold text-gray-900">Merge Preview</h3>
          <p className="text-sm text-gray-500">Reviewing changes from child node to parent</p>
        </div>
        <button 
          className="p-2 text-gray-500 hover:text-gray-700"
          onClick={onClose}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </motion.div>
      
      {/* Node Info */}
      <motion.div 
        className="p-4 border-b bg-gray-50"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <div className="flex justify-between text-sm">
          <div>
            <span className="text-gray-500">Parent: </span>
            <span className="font-mono text-gray-900">{parentNodeId.substring(0, 8)}...</span>
          </div>
          <div>
            <span className="text-gray-500">Child: </span>
            <span className="font-mono text-gray-900">{childNodeId.substring(0, 8)}...</span>
          </div>
        </div>
      </motion.div>
      
      {/* Diff Type Toggle */}
      <motion.div 
        className="p-2 border-b bg-gray-50 flex justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <div className="inline-flex rounded-md shadow-sm" role="group">
          <button
            type="button"
            className={`px-4 py-2 text-sm font-medium rounded-l-lg ${diffType === 'split' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
            onClick={() => setDiffType('split')}
          >
            Split View
          </button>
          <button
            type="button"
            className={`px-4 py-2 text-sm font-medium rounded-r-md ${diffType === 'unified' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
            onClick={() => setDiffType('unified')}
          >
            Unified View
          </button>
        </div>
      </motion.div>
      
      {/* Diff Content */}
      <motion.div 
        className="flex-1 overflow-hidden flex flex-col"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.3 }}
      >
        {/* Semantic Summary */}
        <motion.div 
          className="p-4 border-b"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h4 className="font-medium text-gray-900 mb-2">Semantic Summary</h4>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-gray-700">
            {semanticSummary || 'No semantic summary available.'}
          </div>
        </motion.div>
        
        {/* Textual Diff */}
        <motion.div 
          className="flex-1 overflow-hidden flex flex-col"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <div className="p-4 border-b flex justify-between items-center">
            <h4 className="font-medium text-gray-900">Textual Diff</h4>
            <span className="text-xs text-gray-500">{diffLines.length} lines</span>
          </div>
          
          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              defaultLanguage="diff"
              defaultValue={textualDiff}
              value={textualDiff}
              theme="vs-dark"
              options={{
                readOnly: true,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                automaticLayout: true,
                wordWrap: 'on',
                lineNumbers: 'on',
                folding: true,
                fontSize: 14,
                // renderSideBySide: diffType === 'split',
              }}
            />
          </div>
        </motion.div>
      </motion.div>
      
      {/* Action Buttons */}
      <motion.div 
        className="p-4 border-t bg-gray-50 flex justify-end space-x-3"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.5 }}
      >
        <button
          type="button"
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none"
          onClick={onReject}
        >
          Reject Changes
        </button>
        <button
          type="button"
          className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none"
          onClick={onApprove}
        >
          Approve & Merge
        </button>
      </motion.div>
    </motion.div>
  );
}
