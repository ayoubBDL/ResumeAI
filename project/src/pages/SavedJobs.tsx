import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getJobApplications, updateJobApplicationStatus, deleteJobApplication, JobApplication, getResumeDownloadUrl, downloadCoverLetter } from '../services/api';
import { format } from 'date-fns';
import { Building2, Calendar, ExternalLink, Search, BookOpen, Download, FileText, Trash2 } from 'lucide-react';
import AnalysisModal from '../components/AnalysisModal';
import ConfirmModal from '../components/ConfirmModal';
import { useToast } from '../context/ToastContext';
import Layout from '../components/Layout';

function SavedJobs() {
  const [isLoading, setIsLoading] = useState(true);
  const [jobs, setJobs] = useState<JobApplication[]>([]);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState('');
  const [isDownloading, setIsDownloading] = useState(false);
  const [isDownloadingCoverLetter, setIsDownloadingCoverLetter] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const { user } = useAuth();
  const { showToast } = useToast();

  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const fetchJobs = async () => {
      if (!user?.id) {
        setError('User not authenticated');
        setIsLoading(false);
        return;
      }
      
      try {
        setIsLoading(true);
        setError(null);
        const jobsData = await getJobApplications(user.id);
        if (isMounted) {
          setJobs(jobsData);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Error fetching jobs:', err);
          setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    // Debounce the fetch call
    timeoutId = setTimeout(fetchJobs, 100);

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [user?.id]);

  const handleDownload = async (resumeId: string, jobTitle: string, userId: string) => {
    try {
      setIsDownloading(true);
      setError(null);
      
      // Get the signed URL from the backend
      const response = await fetch(`/api/resumes/${resumeId}/download`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
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
      link.setAttribute('download', `${jobTitle || 'resume'}.pdf`);
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

  const handleCoverLetterDownload = async (resumeId: string, jobTitle: string) => {
    try {
      setIsDownloadingCoverLetter(true);
      setError(null);
      
      // Get the cover letter PDF blob
      const pdfBlob = await downloadCoverLetter(resumeId);
      
      // Create a download link
      const blobUrl = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', `cover_letter_${jobTitle || 'document'}.pdf`);
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('Error downloading cover letter:', error);
      setError(error instanceof Error ? error.message : 'Failed to download cover letter');
    } finally {
      setIsDownloadingCoverLetter(false);
    }
  };

  const handleDeleteJob = async () => {
    if (!selectedJobId) return;
    
    try {
      await deleteJobApplication(selectedJobId);
      showToast('Job application deleted successfully', 'success');
      
      // Refresh the jobs list
      if (user?.id) {
        const updatedJobs = await getJobApplications(user.id);
        setJobs(updatedJobs);
      }
    } catch (error) {
      console.error('Error deleting job:', error);
      showToast(error instanceof Error ? error.message : 'Failed to delete job application', 'error');
    } finally {
      setSelectedJobId(null);
      setShowDeleteConfirm(false);
    }
  };

  const filteredJobs = jobs.filter((job) => {
    if (!searchTerm) return true;
    return job.job_title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.job_description?.toLowerCase().includes(searchTerm.toLowerCase());
  });

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-semibold text-gray-900">Saved Jobs</h1>
            <div className="relative">
              <input
                type="text"
                placeholder="Search jobs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-64 px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
              <Search className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
          </div>

          {error && (
            <div className="mb-4 p-4 text-red-700 bg-red-100 rounded-md">
              {error}
            </div>
          )}

          {filteredJobs.length > 0 ? (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {filteredJobs.map((job) => (
                  <li key={job.id} className="px-6 py-4 hover:bg-gray-50">
                    <div className="space-y-3">
                      {/* Title and Company */}
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">{job.job_title}</h3>
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Building2 className="h-4 w-4" />
                            <span>{job.company}</span>
                            <span className="text-gray-400">•</span>
                            <Calendar className="h-4 w-4" />
                            <span>Added {format(new Date(job.created_at), 'MMM d, yyyy')}</span>
                          </div>
                        </div>
                        <span className={`px-2 py-1 text-sm rounded-full ${
                          job.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          job.status === 'applied' ? 'bg-blue-100 text-blue-800' :
                          job.status === 'interviewing' ? 'bg-purple-100 text-purple-800' :
                          job.status === 'offered' ? 'bg-green-100 text-green-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                        </span>
                      </div>

                      {/* Description */}
                      {job.job_description && (
                        <div className="text-sm text-gray-600 line-clamp-3">
                          {job.job_description}
                        </div>
                      )}

                      {/* Links and Actions */}
                      <div className="flex flex-wrap gap-4">
                        {job.job_url && (
                          <a
                            href={job.job_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                          >
                            View Job Post <ExternalLink className="ml-2 -mr-0.5 h-4 w-4" />
                          </a>
                        )}

                        {job.resume?.analysis && (
                          <button
                            onClick={() => {
                              setSelectedAnalysis(job.resume?.analysis || '');
                              setIsAnalysisOpen(true);
                            }}
                            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                          >
                            <BookOpen className="h-5 w-5 mr-2" />
                            View Analysis
                          </button>
                        )}

                        <select
                          value={job.status}
                          onChange={async (e) => {
                            try {
                              if (!user?.id) {
                                throw new Error('User not authenticated');
                              }
                              const newStatus = e.target.value as JobApplication['status'];
                              await updateJobApplicationStatus(job.id, newStatus);
                              // Refresh the jobs list
                              const updatedJobs = await getJobApplications(user.id);
                              setJobs(updatedJobs);
                              showToast('Status updated successfully', 'success');
                            } catch (error) {
                              console.error('Error updating job status:', error);
                              setError(error instanceof Error ? error.message : 'Failed to update status');
                              showToast(error instanceof Error ? error.message : 'Failed to update status', 'error');
                            }
                          }}
                          className="mt-1 block w-40 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                        >
                          <option value="pending">Pending</option>
                          <option value="applied">Applied</option>
                          <option value="interviewing">Interviewing</option>
                          <option value="offered">Offered</option>
                          <option value="rejected">Rejected</option>
                        </select>

                        {job.resume_id && (
                          <>
                            <button
                              onClick={() => handleDownload(job.resume_id!, job.job_title, user?.id || '')}
                              disabled={isDownloading}
                              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <Download className="h-5 w-5 mr-2" />
                              Download Resume
                            </button>
                            <button
                              onClick={() => handleCoverLetterDownload(job.resume_id!, job.job_title)}
                              disabled={isDownloadingCoverLetter}
                              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <FileText className="h-5 w-5 mr-2" />
                              Download Cover Letter
                            </button>
                          </>
                        )}

                        <button
                          onClick={() => {
                            setSelectedJobId(job.id);
                            setShowDeleteConfirm(true);
                          }}
                          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        >
                          <Trash2 className="h-5 w-5 mr-2" />
                          Delete
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="text-center py-12 bg-white shadow overflow-hidden sm:rounded-md">
              <div className="mx-auto h-12 w-12 text-gray-400">
                <Building2 className="h-12 w-12" />
              </div>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No saved jobs</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm 
                  ? "No jobs match your search criteria"
                  : "Start by optimizing your resume for a job posting!"
                }
              </p>
            </div>
          )}

          <AnalysisModal
            isOpen={isAnalysisOpen}
            onClose={() => setIsAnalysisOpen(false)}
            analysis={selectedAnalysis}
          />

          <ConfirmModal
            isOpen={showDeleteConfirm}
            onClose={() => setShowDeleteConfirm(false)}
            onConfirm={handleDeleteJob}
            title="Delete Job Application"
            message="Are you sure you want to delete this job application? This action cannot be undone."
            confirmText="Delete"
            cancelText="Cancel"
          />
        </div>
      </div>
    </Layout>
  );
}

export default SavedJobs;