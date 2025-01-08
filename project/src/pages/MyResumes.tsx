import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { optimizeResume, saveOptimizedResume, getResumes, Resume } from '../services/api';

export default function MyResumes() {
  const { user } = useAuth();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    loadResumes();
  }, [user]);

  const loadResumes = async () => {
    try {
      if (user) {
        const data = await getResumes(user.id);
        setResumes(data);
      }
    } catch (error) {
      console.error('Error loading resumes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleOptimize = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !linkedinUrl || !user) return;

    setOptimizing(true);
    try {
      // Optimize resume using our Python service
      const optimizedData = await optimizeResume(linkedinUrl, selectedFile);
      
      // Save to Supabase
      await saveOptimizedResume(
        user.id,
        `Optimized Resume - ${new Date().toLocaleDateString()}`,
        optimizedData.optimized_resume
      );

      // Reload resumes
      await loadResumes();
      
      // Clear form
      setLinkedinUrl('');
      setSelectedFile(null);
    } catch (error) {
      console.error('Error optimizing resume:', error);
    } finally {
      setOptimizing(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">My Resumes</h1>

      {/* Optimization Form */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Optimize New Resume</h2>
        <form onSubmit={handleOptimize} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              LinkedIn Job URL
            </label>
            <input
              type="url"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Upload Resume (PDF)
            </label>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="mt-1 block w-full"
              required
            />
          </div>

          <button
            type="submit"
            disabled={optimizing || !selectedFile || !linkedinUrl}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {optimizing ? 'Optimizing...' : 'Optimize Resume'}
          </button>
        </form>
      </div>

      {/* Resumes List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {resumes.map((resume) => (
          <div key={resume.id} className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900">{resume.title}</h3>
            <p className="text-sm text-gray-500">
              Created: {new Date(resume.created_at).toLocaleDateString()}
            </p>
            <div className="mt-4 flex space-x-3">
              <button
                onClick={() => window.open(`/api/resumes/${resume.id}/download`, '_blank')}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200"
              >
                Download
              </button>
              <button
                onClick={() => window.open(`/api/resumes/${resume.id}/preview`, '_blank')}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Preview
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}