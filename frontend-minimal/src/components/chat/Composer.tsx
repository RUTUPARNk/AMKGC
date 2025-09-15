import React, { useState, useRef, useEffect } from 'react';

type ComposerProps = {
  onSend: (content: string) => void;
  isSending: boolean;
};

export function Composer({ onSend, isSending }: ComposerProps) {
  const [content, setContent] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  useEffect(() => {
    if (textareaRef.current) {
      // Auto-resize textarea
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [content]);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (content.trim() && !isSending) {
      onSend(content);
      setContent('');
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="flex items-end space-x-2">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          className="w-full border rounded-lg py-3 px-4 pr-12 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 max-h-32"
          disabled={isSending}
          rows={1}
        />
        <div className="absolute right-3 bottom-3 text-gray-400 text-xs">
          {content.length}/1000
        </div>
      </div>
      <button
        type="submit"
        disabled={!content.trim() || isSending}
        className={`p-3 rounded-lg ${content.trim() && !isSending ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-gray-200'} text-white transition-colors`}
      >
        {isSending ? (
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        )}
      </button>
    </form>
  );
}
