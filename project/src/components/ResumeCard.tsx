import React, { useState } from 'react';
import { Resume, getResumeDownloadUrl } from '../services/api';
import AnalysisModal from './AnalysisModal';
import { supabase } from '../lib/supabaseClient'; // Fixed import path

interface ResumeCardProps {
  resume: Resume;
  onUpdate: () => void;
}

export default function ResumeCard({ resume, onUpdate }: ResumeCardProps) {
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleDownload = async () => {
    if (!resume.optimized_pdf_url || isDownloading) return;
    
    try {
      setIsDownloading(true);
      console.log('Starting download for URL:', resume.optimized_pdf_url);
      
      // Get the PDF directly from the optimized_pdf_url
      const response = await fetch(resume.optimized_pdf_url);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Download response error:', errorText);
        throw new Error(`Failed to download file: ${response.statusText}`);
      }

      // Check content type
      const contentType = response.headers.get('content-type');
      console.log('Response content type:', contentType);

      // Get the file as a blob
      const blob = await response.blob();
      if (blob.size === 0) {
        throw new Error('Downloaded file is empty');
      }

      console.log('Downloaded blob:', {
        size: blob.size,
        type: blob.type
      });

      // Create object URL and trigger download
      const downloadUrl = window.URL.createObjectURL(
        new Blob([blob], { type: 'application/pdf' })
      );
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = resume.title.endsWith('.pdf') ? resume.title : `${resume.title}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up
      setTimeout(() => {
        window.URL.revokeObjectURL(downloadUrl);
      }, 100);
      
      console.log('Download completed successfully');
    } catch (error) {
      console.error('Error downloading resume:', error);
      alert('Failed to download resume. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <svg className="h-8 w-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">{resume.title}</h3>
            <p className="text-sm text-gray-500">
              Created {formatDate(resume.created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {resume.analysis && (
            <button
              onClick={() => setIsAnalysisOpen(true)}
              className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              View Analysis
            </button>
          )}
          {resume.optimized_pdf_url && (
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isDownloading ? 'Downloading...' : 'Download'}
            </button>
          )}
        </div>
      </div>

      <AnalysisModal
        isOpen={isAnalysisOpen}
        onClose={() => setIsAnalysisOpen(false)}
        analysis={resume.analysis || ''}
      />
    </div>
  );
}
