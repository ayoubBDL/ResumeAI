import React from 'react';

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: string;
}

export default function AnalysisModal({ isOpen, onClose, analysis }: AnalysisModalProps) {
  if (!isOpen) return null;

  // Helper function to parse sections
  const parseSections = (content: string) => {
    const sections = [];
    const sectionRegex = /\[(OPTIMIZATION|INTERVIEW_PREP|NEXT_STEPS)\]([\s\S]*?)(?=\[(?:OPTIMIZATION|INTERVIEW_PREP|NEXT_STEPS)\]|\[\/SECTION\]|$)/g;
    
    let match;
    while ((match = sectionRegex.exec(content)) !== null) {
      const [, title, content] = match;
      const cleanContent = content.trim()
        .replace(/•\s*/g, '• ') // Normalize bullet points
        .replace(/\[\/SECTION\]/g, '') // Remove section end markers
        .trim();

      sections.push({
        title: title.replace(/_/g, ' '),
        content: cleanContent
      });
    }
    
    return sections;
  };

  // Parse the sections
  const sections = parseSections(analysis);

  return (
    <div className="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50 flex">
      <div className="relative w-full max-w-4xl m-auto bg-gray-50 rounded-lg shadow-xl">
        <div className="p-6">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-500"
          >
            <span className="sr-only">Close</span>
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <h2 className="text-2xl font-bold text-gray-900 mb-6">Resume Analysis</h2>
          
          <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-2">
            {sections.map((section, index) => (
              <section key={index} className="bg-white rounded-lg shadow mb-4">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">{section.title}</h3>
                </div>
                <div className="p-4 whitespace-pre-wrap">
                  {section.content}
                </div>
              </section>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
