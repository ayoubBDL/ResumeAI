import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { optimizeResume, getRecentResumes, type Resume } from '../services/api';
import ResumeCard from '../components/ResumeCard';

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [jobUrl, setJobUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [recentResumes, setRecentResumes] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchRecentResumes = async () => {
      try {
        setIsLoading(true);
        const resumes = await getRecentResumes(3); // Get only last 3 resumes
        if (isMounted) {
          setRecentResumes(resumes);
        }
      } catch (error) {
        console.error('Error loading resumes:', error);
        if (isMounted) {
          setError(error instanceof Error ? error.message : 'Failed to load resumes');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchRecentResumes();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!isUploading) return;

    const interval = setInterval(async () => {
      try {
        const resumes = await getRecentResumes(3);
        setRecentResumes(resumes);
        
        // Check if the most recent resume is completed
        const latestResume = resumes[0];
        if (latestResume && latestResume.status === 'completed') {
          setIsUploading(false);
          setUploadStatus('Resume optimized successfully!');
          // Clear the form
          resetForm();
        } else if (latestResume && latestResume.status === 'failed') {
          setIsUploading(false);
          setUploadStatus('Failed to optimize resume. Please try again.');
          resetForm();
        }
      } catch (error) {
        console.error('Error checking resume status:', error);
        setUploadStatus('Error checking resume status');
        setIsUploading(false);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isUploading]);

  const resetForm = () => {
    setFile(null);
    setJobUrl('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setFile(file);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!file) {
      setUploadStatus('Please select a file');
      return;
    }

    try {
      setIsUploading(true);
      setUploadStatus('Optimizing your resume...');

      const formData = new FormData();
      formData.append('file', file);
      if (jobUrl) {
        formData.append('job_url', jobUrl);
      }

      await optimizeResume(formData);
      
      // The status will be updated by the interval effect
    } catch (error) {
      console.error('Error uploading resume:', error);
      setUploadStatus('Failed to upload resume');
      setIsUploading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900">Upload Resume</h2>
            <p className="mt-1 text-sm text-gray-600">
              Upload your resume and we'll optimize it for your target job
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Resume (PDF)
              </label>
              <label
                htmlFor="resume-upload"
                className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 ${
                  file ? 'border-indigo-500' : 'border-gray-300 border-dashed'
                } rounded-md cursor-pointer hover:border-indigo-500 transition-colors`}
              >
                <div className="space-y-1 text-center">
                  {!file ? (
                    <>
                      <svg
                        className="mx-auto h-12 w-12 text-gray-400"
                        stroke="currentColor"
                        fill="none"
                        viewBox="0 0 48 48"
                        aria-hidden="true"
                      >
                        <path
                          d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                          strokeWidth={2}
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      <div className="flex text-sm text-gray-600 justify-center">
                        <span className="relative font-medium text-indigo-600 hover:text-indigo-500">
                          Upload a file
                        </span>
                        <input
                          id="resume-upload"
                          name="resume-upload"
                          type="file"
                          accept=".pdf"
                          ref={fileInputRef}
                          onChange={(e) => setFile(e.target.files?.[0] || null)}
                          className="sr-only"
                        />
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className="text-xs text-gray-500">PDF up to 10MB</p>
                    </>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center justify-center">
                        <svg className="h-8 w-8 text-indigo-500" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                          <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="text-sm text-gray-900 font-medium">{file.name}</div>
                      <div className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          resetForm();
                        }}
                        className="text-xs text-red-600 hover:text-red-800"
                      >
                        Remove file
                      </button>
                    </div>
                  )}
                </div>
              </label>
            </div>

            <div>
              <label htmlFor="job-url" className="block text-sm font-medium text-gray-700">
                Job Posting URL (optional)
              </label>
              <div className="mt-1">
                <input
                  type="url"
                  name="job-url"
                  id="job-url"
                  value={jobUrl}
                  onChange={(e) => setJobUrl(e.target.value)}
                  className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  placeholder="https://example.com/job-posting"
                />
              </div>
            </div>

            {isUploading && (
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(Math.round(100), 100)}%` }}
                />
                <div className="text-xs text-gray-500 mt-1 text-center">
                  {Math.min(Math.round(100), 100)}% Complete
                </div>
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={!file || isUploading}
                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                  !file || isUploading 
                    ? 'bg-indigo-400 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-700'
                }`}
              >
                {isUploading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Optimizing...
                  </>
                ) : (
                  'Optimize Resume'
                )}
              </button>
            </div>

            {uploadStatus && !isUploading && (
              <div className={`mt-2 text-sm text-red-600`}>
                {uploadStatus}
              </div>
            )}
          </form>

          {/* Recent Resumes Section */}
          <div className="mt-12">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">Recent Resumes</h2>
              <Link
                to="/my-resumes"
                className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                View all <span aria-hidden="true">→</span>
              </Link>
            </div>

            {isLoading ? (
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-600"></div>
              </div>
            ) : error ? (
              <div className="text-center py-4">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            ) : recentResumes.length === 0 ? (
              <div className="text-center py-4">
                <p className="text-sm text-gray-500">No resumes yet. Upload your first resume to get started!</p>
              </div>
            ) : (
              <div className="grid gap-6 mb-8 md:grid-cols-2 lg:grid-cols-3">
                {recentResumes.map((resume) => (
                  <ResumeCard 
                    key={resume.id} 
                    resume={resume} 
                    onDelete={async () => {
                      const resumes = await getRecentResumes(3);
                      setRecentResumes(resumes);
                    }} 
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}