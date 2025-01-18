import React from 'react';

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: string;
}

export default function AnalysisModal({ isOpen, onClose, analysis }: AnalysisModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Resume Analysis</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div className="mt-2 space-y-4">
            {analysis.split('\n').map((line, index) => {
              if (line.trim().length === 0) return null;
              
              // Check if it's a section header
              if (line.includes(':')) {
                const [header, content] = line.split(':');
                return (
                  <div key={index}>
                    <h4 className="font-medium text-indigo-600">{header.trim()}</h4>
                    <p className="text-gray-600 mt-1">{content.trim()}</p>
                  </div>
                );
              }
              
              // Regular line
              return (
                <p key={index} className="text-gray-600">
                  {line.trim()}
                </p>
              );
            })}
          </div>

          <div className="mt-4">
            <button
              onClick={onClose}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
