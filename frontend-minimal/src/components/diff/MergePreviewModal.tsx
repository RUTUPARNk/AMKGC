import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { DiffViewer } from './DiffViewer';
import { MergeService, MergePreview } from '../../services/mergeService';

interface MergePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  childNodeId: string;
  parentNodeId?: string;
  onApprove: () => void;
  onReject: () => void;
}

export function MergePreviewModal({ 
  isOpen, 
  onClose, 
  childNodeId, 
  parentNodeId,
  onApprove,
  onReject
}: MergePreviewModalProps) {
  const [mergePreview, setMergePreview] = useState<MergePreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (isOpen && childNodeId) {
      fetchMergePreview();
    }
  }, [isOpen, childNodeId]);
  
  const fetchMergePreview = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const mergeService = MergeService.getInstance();
      const preview = await mergeService.getMergePreview(childNodeId);
      setMergePreview(preview);
    } catch (err: any) {
      console.error('Error fetching merge preview:', err);
      setError(err.message || 'Failed to fetch merge preview');
    } finally {
      setLoading(false);
    }
  };
  
  if (!isOpen) return null;
  
  if (loading) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          {/* Background overlay */}
          <div 
            className="fixed inset-0 transition-opacity" 
            aria-hidden="true"
            onClick={onClose}
          >
            <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
          </div>
          
          {/* Modal panel */}
          <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full sm:h-5/6 h-[90vh] flex items-center justify-center">
            <div className="text-center p-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-4 text-gray-700">Loading merge preview...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          {/* Background overlay */}
          <div 
            className="fixed inset-0 transition-opacity" 
            aria-hidden="true"
            onClick={onClose}
          >
            <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
          </div>
          
          {/* Modal panel */}
          <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full sm:h-5/6 h-[90vh] flex items-center justify-center">
            <div className="text-center p-8">
              <div className="text-red-500 text-2xl mb-4">⚠️</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Merge Preview</h3>
              <p className="text-gray-700 mb-4">{error}</p>
              <div className="flex justify-center space-x-4">
                <button
                  onClick={fetchMergePreview}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Retry
                </button>
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        
        {/* Background overlay */}
        <motion.div 
          className="fixed inset-0 transition-opacity" 
          aria-hidden="true"
          onClick={onClose}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </motion.div>
        
        {/* Modal panel */}
        <motion.div 
          className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full sm:h-5/6 h-[90vh]"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
        >
          <DiffViewer 
            semanticSummary={mergePreview?.diff_summary || ''}
            textualDiff={mergePreview?.text_diff || ''}
            childNodeId={childNodeId}
            parentNodeId={parentNodeId || ''}
            onApprove={onApprove}
            onReject={onReject}
            onClose={onClose}
          />
        </motion.div>
      </div>
    </div>
  );
}
