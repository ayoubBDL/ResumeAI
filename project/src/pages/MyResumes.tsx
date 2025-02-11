import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { Resume, getRecentResumes } from '../services/api';
import ResumeCard from '../components/ResumeCard';

export default function MyResumes() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const data = await getRecentResumes();
      setResumes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch resumes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      </Layout>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">My Resumes</h1>
      </div>

      {error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
          {error}
        </div>
      ) : resumes.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-gray-500">You haven't uploaded any resumes yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {resumes.map((resume) => (
            <ResumeCard 
              key={resume.id} 
              resume={resume} 
              onUpdate={fetchResumes}
            />
          ))}
        </div>
      )}
    </div>
  );
};