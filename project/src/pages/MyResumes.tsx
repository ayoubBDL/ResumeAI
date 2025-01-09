import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { Resume } from '../services/api';
import { Layout } from '../components/Layout';

export default function MyResumes() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async () => {
    try {
      const { data: resumes, error } = await supabase
        .from('resumes')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setResumes(resumes || []);
    } catch (error) {
      console.error('Error loading resumes:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-6">My Resumes</h1>

        <div className="bg-white rounded-lg shadow-sm">
          <div className="divide-y divide-gray-200">
            {resumes.map((resume) => (
              <div key={resume.id} className="p-4 hover:bg-gray-50">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{resume.title}</h3>
                    <p className="text-sm text-gray-500">
                      Created on {new Date(resume.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    onClick={() => window.open(`/api/download/${resume.id}`, '_blank')}
                    className="ml-4 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Download
                  </button>
                </div>
              </div>
            ))}
            {resumes.length === 0 && (
              <div className="p-4 text-center text-gray-500">
                No resumes yet. Go to Dashboard to create one!
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}