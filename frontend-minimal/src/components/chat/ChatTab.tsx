interface ChatTabProps {
  title: string;
  isActive: boolean;
  onClick: () => void;
  onClose: () => void;
}

export function ChatTab({ title, isActive, onClick, onClose }: ChatTabProps) {
  return (
    <div 
      className={`flex items-center px-3 py-2 text-sm border-r cursor-pointer ${isActive ? 'bg-white border-t border-b border-r-0' : 'bg-gray-100 hover:bg-gray-200'}`}
      onClick={onClick}
    >
      <span className="truncate max-w-xs">{title}</span>
      <button 
        className="ml-2 text-gray-500 hover:text-gray-700"
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
