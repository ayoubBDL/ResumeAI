import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../context/AuthContext';
import { Resume, getRecentResumes } from '../services/api';
import ResumeCard from '../components/ResumeCard';
import { Loader } from 'lucide-react';

const MyResumes = () => {
  const { user } = useAuth();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResumes = async () => {
      try {
        const data = await getRecentResumes();
        setResumes(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch resumes');
      } finally {
        setLoading(false);
      }
    };

    fetchResumes();
  }, []);

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">My Resumes</h1>
        
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <Loader className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>
        ) : error ? (
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
              <ResumeCard key={resume.id} resume={resume} />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default MyResumes;