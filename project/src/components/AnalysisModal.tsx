import React from 'react';

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysis: string;
}

export default function AnalysisModal({ isOpen, onClose, analysis }: AnalysisModalProps) {
  if (!isOpen) return null;

  // Parse the analysis sections using the new format
  const parseSection = (content: string, sectionName: string) => {
    const sectionRegex = new RegExp(`\\[SECTION:${sectionName}\\]([\\s\\S]*?)\\[\\/SECTION\\]`);
    const match = content.match(sectionRegex);
    if (!match) {
      console.warn(`Section ${sectionName} not found in analysis`);
      return [];
    }

    const sectionContent = match[1].trim();
    if (!sectionContent) {
      console.warn(`Section ${sectionName} is empty`);
      return [];
    }

    const points = [];
    let currentPoint = null;
    let currentSubPoints = [];

    for (const line of sectionContent.split('\n')) {
      const trimmedLine = line.trim();
      if (!trimmedLine) continue;

      if (trimmedLine.startsWith('•')) {
        if (currentPoint) {
          points.push({ main: currentPoint, sub: currentSubPoints });
          currentSubPoints = [];
        }
        currentPoint = trimmedLine.slice(1).trim();
      } else if (trimmedLine.startsWith('-')) {
        if (!currentPoint) {
          console.warn('Found sub-point without a main point:', trimmedLine);
          continue;
        }
        currentSubPoints.push(trimmedLine.slice(1).trim());
      }
    }

    if (currentPoint) {
      points.push({ main: currentPoint, sub: currentSubPoints });
    }

    return points;
  };

  const sections = {
    improvements: parseSection(analysis, 'IMPROVEMENTS'),
    interview: parseSection(analysis, 'INTERVIEW'),
    nextSteps: parseSection(analysis, 'NEXTSTEPS')
  };

  // Helper function to render a section
  const renderSection = (title: string, points: Array<{ main: string, sub: string[] }>) => {
    if (!points || points.length === 0) return null;

    return (
      <section className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="p-4">
          <ul className="space-y-4">
            {points.map((point, index) => (
              <li key={index} className="text-gray-700">
                <div className="font-medium">{point.main}</div>
                {point.sub.length > 0 && (
                  <ul className="mt-2 ml-4 space-y-1">
                    {point.sub.map((subPoint, subIndex) => (
                      <li key={`${index}-${subIndex}`} className="text-gray-600">
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
    <div className="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50 flex" onClick={handleBackdropClick}>
      <div className="relative p-8 bg-white w-full max-w-4xl m-auto rounded-lg max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Resume Analysis</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <span className="text-2xl leading-none">&times;</span>
          </button>
        </div>

        <div className="space-y-6">
          {renderSection('Key Improvements Made', sections.improvements)}
          {renderSection('Interview Preparation Advice', sections.interview)}
          {renderSection('Next Steps', sections.nextSteps)}
        </div>
      </div>
    </div>
  );
}
