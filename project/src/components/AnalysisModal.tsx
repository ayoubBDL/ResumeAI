import React from 'react';

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: string;
}

export default function AnalysisModal({ isOpen, onClose, analysis }: AnalysisModalProps) {
  if (!isOpen) return null;

  // Parse the analysis sections
  const sections = {
    improvements: analysis.split('1. KEY IMPROVEMENTS MADE:')[1]?.split('2. INTERVIEW PREPARATION ADVICE:')[0]?.trim() || '',
    interview: analysis.split('2. INTERVIEW PREPARATION ADVICE:')[1]?.split('3. NEXT STEPS:')[0]?.trim() || '',
    nextSteps: analysis.split('3. NEXT STEPS:')[1]?.trim() || ''
  };

  const formatBulletPoints = (text: string) => {
    if (!text) return [];
    return text
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && line.startsWith('•'))
      .map(line => line.replace(/^•\s*/, '').trim());
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50 flex" onClick={handleBackdropClick}>
      <div className="relative p-8 bg-white w-full max-w-3xl m-auto rounded-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Resume Analysis
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <span className="text-2xl leading-none">&times;</span>
          </button>
        </div>

        <div className="space-y-6">
          {/* Key Improvements */}
          <section className="bg-white rounded-lg shadow">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Key Improvements Made</h3>
            </div>
            <div className="p-4">
              <ul className="list-disc pl-5 space-y-2">
                {formatBulletPoints(sections.improvements).map((point, index) => (
                  <li key={index} className="text-gray-700">{point}</li>
                ))}
              </ul>
            </div>
          </section>

          {/* Interview Preparation */}
          <section className="bg-white rounded-lg shadow">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Interview Preparation Advice</h3>
            </div>
            <div className="p-4">
              <ul className="list-disc pl-5 space-y-2">
                {formatBulletPoints(sections.interview).map((point, index) => (
                  <li key={index} className="text-gray-700">{point}</li>
                ))}
              </ul>
            </div>
          </section>

          {/* Next Steps */}
          <section className="bg-white rounded-lg shadow">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Next Steps</h3>
            </div>
            <div className="p-4">
              <ul className="list-disc pl-5 space-y-2">
                {formatBulletPoints(sections.nextSteps).map((point, index) => (
                  <li key={index} className="text-gray-700">{point}</li>
                ))}
              </ul>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
