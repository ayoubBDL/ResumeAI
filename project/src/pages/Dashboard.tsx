import React, { useState } from 'react';
import { Layout } from '../components/Layout';
import { Upload, FileText, Plus } from 'lucide-react';

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [jobUrl, setJobUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !jobUrl) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('resume', file);
    formData.append('jobUrl', jobUrl);

    try {
      const response = await fetch('/api/optimize-resume', {
        method: 'POST',
        body: formData,
      });
      const data = await response.blob();
      const url = window.URL.createObjectURL(data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'optimized-resume.pdf';
      a.click();
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsUploading(false);
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
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="resume-upload"
                    accept=".pdf,.doc,.docx"
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
                      PDF, DOC, DOCX (max. 10MB)
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
                  value={jobUrl}
                  onChange={(e) => setJobUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="https://www.linkedin.com/jobs/..."
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isUploading}
                className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {isUploading ? 'Optimizing...' : 'Create Optimized Resume'}
              </button>
            </form>
          </div>

          {/* Recent Resumes Section */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Recent Resumes</h2>
            <div className="space-y-4">
              {/* We'll populate this with actual data from Supabase */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center">
                  <FileText className="h-6 w-6 text-gray-400 mr-3" />
                  <div>
                    <h3 className="font-medium">Software Engineer - Google</h3>
                    <p className="text-sm text-gray-500">Created on March 15, 2024</p>
                  </div>
                </div>
                <button className="text-indigo-600 hover:text-indigo-800">
                  Download
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}