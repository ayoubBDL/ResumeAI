import React from 'react';

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: string;
}

export default function AnalysisModal({ isOpen, onClose, analysis }: AnalysisModalProps) {
  if (!isOpen) return null;

  // Helper function to parse bullet points
  const parseBulletPoints = (content: string) => {
    if (!content) return [];
    const lines = content.split('\n').map(line => line.trim()).filter(Boolean);
    const points: { main: string; sub: string[] }[] = [];
    let currentMain: { main: string; sub: string[] } | null = null;

    lines.forEach(line => {
      if (line.startsWith('•')) {
        if (currentMain) {
          points.push(currentMain);
        }
        currentMain = {
          main: line.substring(1).trim(),
          sub: []
        };
      } else if (line.startsWith('-') && currentMain) {
        currentMain.sub.push(line.substring(1).trim());
      }
    });

    if (currentMain) {
      points.push(currentMain);
    }

    return points;
  };

  // Helper function to get section content
  const getSectionContent = (sectionName: string): string => {
    const pattern = new RegExp(`\\[${sectionName}\\]([\\s\\S]*?)\\[\\/SECTION\\]`);
    const match = analysis.match(pattern);
    return match ? match[1].trim() : '';
  };

  // Helper function to render a section
  const renderSection = (title: string, sectionName: string) => {
    const content = getSectionContent(sectionName);
    if (!content) return null;

    const points = parseBulletPoints(content);

    return (
      <section className="bg-white rounded-lg shadow mb-4">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="p-4">
          <ul className="space-y-4">
            {points.map((point, index) => (
              <li key={index} className="text-gray-700">
                <div className="font-medium">{point.main}</div>
                {point.sub.length > 0 && (
                  <ul className="mt-2 ml-6 space-y-2">
                    {point.sub.map((subPoint, subIndex) => (
                      <li key={`${index}-${subIndex}`} className="text-gray-600 list-disc">
                        {subPoint}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </div>
      </section>
    );
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50 flex"
      onClick={handleBackdropClick}
    >
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
            {renderSection('Improvements', 'IMPROVEMENTS')}
            {renderSection('Interview Preparation', 'INTERVIEW')}
            {renderSection('Next Steps', 'NEXTSTEPS')}
          </div>
        </div>
      </div>
    </div>
  );
}
