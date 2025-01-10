import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { Upload, FileText } from 'lucide-react';
import { supabase } from '../lib/supabaseClient';
import { optimizeResume } from '../services/api';
import type { Resume } from '../services/api';

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [recentResumes, setRecentResumes] = useState<Resume[]>([]);

  useEffect(() => {
    loadRecentResumes();
  }, []);

  const loadRecentResumes = async () => {
    try {
      const { data: resumes, error } = await supabase
        .from('resumes')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(5);

      if (error) throw error;
      setRecentResumes(resumes || []);
    } catch (error) {
      console.error('Error loading resumes:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !linkedinUrl) {
      setUploadStatus('Please select a file and provide a LinkedIn job URL');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Reading resume file...');
    
    try {
      console.log('Starting resume optimization...');
      
      // Read the file content
      const fileText = await file.text();
      console.log('File content read successfully');
      
      const result = await optimizeResume(linkedinUrl, fileText);
      console.log('Optimization successful');
      
      setUploadStatus('Resume optimized successfully!');
      setFile(null);
      setLinkedinUrl('');
      
      // Reset file input
      const fileInput = document.getElementById('resume-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      console.error('Error details:', error);
      setUploadStatus(error instanceof Error ? error.message : 'Failed to optimize resume');
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      console.log('File selected:', selectedFile.name, 'Type:', selectedFile.type);
      
      if (!selectedFile.type.includes('pdf')) {
        setUploadStatus('Please upload a PDF file');
        e.target.value = ''; // Reset input
        return;
      }
      
      if (selectedFile.size > 10 * 1024 * 1024) { // 10MB limit
        setUploadStatus('File size must be less than 10MB');
        e.target.value = ''; // Reset input
        return;
      }
      
      setFile(selectedFile);
      setUploadStatus(`Selected: ${selectedFile.name}`);
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
        
        <div className="grid md:grid-cols-2 gap-8">
          {/* Create New Resume Section */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Create New Optimized Resume</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Your Resume
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <input
                    type="file"
                    onChange={handleFileChange}
                    className="hidden"
                    id="resume-upload"
                    accept=".pdf"
                  />
                  <label
                    htmlFor="resume-upload"
                    className="cursor-pointer flex flex-col items-center"
                  >
                    <Upload className="h-12 w-12 text-gray-400 mb-2" />
                    <span className="text-sm text-gray-600">
                      Click to upload or drag and drop
                    </span>
                    <span className="text-xs text-gray-500">
                      PDF files only (max. 10MB)
                    </span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  LinkedIn Job URL
                </label>
                <input
                  type="url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="https://www.linkedin.com/jobs/view/..."
                  required
                />
              </div>

              {uploadStatus && (
                <div className={`p-3 rounded-md ${
                  uploadStatus.includes('Error') 
                    ? 'bg-red-50 text-red-700' 
                    : uploadStatus.includes('Success') 
                      ? 'bg-green-50 text-green-700'
                      : 'bg-blue-50 text-blue-700'
                }`}>
                  {uploadStatus}
                </div>
              )}

              <button
                type="submit"
                disabled={isUploading || !file || !linkedinUrl}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? 'Optimizing...' : 'Create Optimized Resume'}
              </button>
            </form>
          </div>

          {/* Recent Resumes Section */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Recent Resumes</h2>
            <div className="space-y-4">
              {recentResumes.map((resume) => (
                <div key={resume.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center">
                    <FileText className="h-6 w-6 text-gray-400 mr-3" />
                    <div>
                      <h3 className="font-medium">{resume.title}</h3>
                      <p className="text-sm text-gray-500">
                        Created on {new Date(resume.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => window.open(`/api/download/${resume.id}`, '_blank')}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    Download
                  </button>
                </div>
              ))}
              {recentResumes.length === 0 && (
                <p className="text-center text-gray-500 py-4">
                  No resumes yet. Create your first one above!
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}