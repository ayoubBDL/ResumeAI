import React, { useState } from 'react';
import { Resume, deleteResume } from '../services/api';
import AnalysisModal from './AnalysisModal';
import ConfirmModal from './ConfirmModal';
import { Download, FileText, Trash2 } from 'lucide-react';
import { format } from 'date-fns';

interface ResumeCardProps {
  resume: Resume;
  onUpdate: () => void;
}

export default function ResumeCard({ resume, onUpdate }: ResumeCardProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      setError(null);
      
      // Get the signed URL from the backend
      const response = await fetch(`/api/resumes/${resume.id}/download`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': resume.user_id
        }
      });

      if (!response.ok) {
        throw new Error('Failed to get download URL');
      }

      const data = await response.json();
      if (!data.success || !data.url) {
        throw new Error(data.error || 'Failed to get download URL');
      }

      // Fetch the actual PDF content
      const pdfResponse = await fetch(data.url);
      if (!pdfResponse.ok) {
        throw new Error('Failed to download PDF');
      }

      const pdfBlob = await pdfResponse.blob();
      const blobUrl = window.URL.createObjectURL(pdfBlob);

      // Create a temporary link element to trigger download
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', `${resume.job_title || 'resume'}.pdf`);
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('Error downloading resume:', error);
      setError(error instanceof Error ? error.message : 'Failed to download resume');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleViewAnalysis = () => {
    console.log('[DEBUG] Opening analysis modal with data:', resume.analysis);
    setIsAnalysisOpen(true);
  };

  const handleDelete = async () => {
    try {
      console.log('Starting delete process for resume:', resume.id);
      setIsDeleting(true);
      setError(null);
      
      await deleteResume(resume.id);
      console.log('Resume deleted successfully, calling onUpdate');
      
      // Close the modal and refresh the list
      setShowDeleteConfirm(false);
      onUpdate();
    } catch (error) {
      console.error('Error in handleDelete:', error);
      setError(error instanceof Error ? error.message : 'Failed to delete resume');
    } finally {
      console.log('Delete process finished');
      setIsDeleting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4 relative">
      {/* Loading overlay */}
      {(isDeleting || isDownloading) && (
        <div className="absolute inset-0 bg-white/50 flex items-center justify-center rounded-lg">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="absolute top-0 left-0 right-0 p-4 bg-red-100 text-red-700 rounded-t-lg">
          {error}
          <button 
            onClick={() => setError(null)}
            className="float-right text-red-700 hover:text-red-900"
          >
            ×
          </button>
        </div>
      )}

      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{resume.title}</h3>
          <p className="text-sm text-gray-500">
            Created on {format(new Date(resume.created_at), 'MMM d, yyyy h:mm a')}
          </p>
        </div>
        <div className="flex space-x-2">
          {resume.optimized_pdf_url && (
            <button
              onClick={handleDownload}
              disabled={isDownloading || isDeleting}
              className="p-2 text-gray-600 hover:text-indigo-600 transition-colors disabled:opacity-50"
              title="Download PDF"
            >
              <Download className="w-5 h-5" />
            </button>
          )}
          {resume.analysis && (
            <button
              onClick={handleViewAnalysis}
              disabled={isDeleting}
              className="p-2 text-gray-600 hover:text-indigo-600 transition-colors disabled:opacity-50"
              title="View Analysis"
            >
              <FileText className="w-5 h-5" />
            </button>
          )}
          <button
            onClick={() => setShowDeleteConfirm(true)}
            disabled={isDeleting || isDownloading}
            className="p-2 text-gray-600 hover:text-red-600 transition-colors disabled:opacity-50"
            title="Delete Resume"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {resume.job_url && (
        <a
          href={resume.job_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-indigo-600 hover:text-indigo-800"
        >
          View Job Posting
        </a>
      )}

      {resume.status === 'processing' && (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          Processing
        </span>
      )}
      {resume.status === 'failed' && (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          Failed
        </span>
      )}

      <AnalysisModal
        isOpen={isAnalysisOpen}
        onClose={() => setIsAnalysisOpen(false)}
        analysis={resume.analysis || ''}
      />

      <ConfirmModal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Resume"
        message="Are you sure you want to delete this resume? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
      />
    </div>
  );
}
