import { supabase } from '../lib/supabaseClient';

export interface JobApplication {
  id: string;
  user_id: string;
  resume_id: string | null;
  job_title: string;
  company: string;
  job_description: string | null;
  job_url: string | null;
  status: 'pending' | 'applied' | 'interviewing' | 'offered' | 'rejected';
  created_at: string;
  updated_at: string;
}

export interface Resume {
  id: string;
  user_id: string;
  title: string;
  content: any;
  is_template: boolean;
  created_at: string;
  updated_at: string;
}

const API_URL = import.meta.env.VITE_RESUME_API_URL;

// Resume optimization service
export const optimizeResume = async (jobUrl: string, resumeText: string) => {
  if (!resumeText || !jobUrl) {
    throw new Error('Both resume text and job URL are required');
  }

  try {
    const response = await fetch(`${API_URL}/optimize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jobUrl,
        resume: resumeText
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to optimize resume');
    }

    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Failed to optimize resume');
    }

    return {
      originalResume: data.data.originalResume,
      optimizedResume: data.data.optimizedResume,
      atsResume: data.data.atsResume,
      jobDetails: data.data.jobDetails
    };
  } catch (error) {
    console.error('Error optimizing resume:', error);
    throw error;
  }
};

// Supabase database operations
export const saveOptimizedResume = async (userId: string, title: string, content: any) => {
  const { data, error } = await supabase
    .from('resumes')
    .insert([
      {
        user_id: userId,
        title,
        content,
        is_template: false
      }
    ])
    .select()
    .single();

  if (error) throw error;
  return data;
};

export const getResumes = async (userId: string) => {
  const { data, error } = await supabase
    .from('resumes')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
};

export const saveJobApplication = async (
  userId: string,
  jobTitle: string,
  company: string,
  jobDescription: string,
  jobUrl: string,
  resumeId?: string
) => {
  const { data, error } = await supabase
    .from('job_applications')
    .insert([
      {
        user_id: userId,
        resume_id: resumeId,
        job_title: jobTitle,
        company,
        job_description: jobDescription,
        job_url: jobUrl,
        status: 'pending'
      }
    ])
    .select()
    .single();

  if (error) throw error;
  return data;
};

export const getJobApplications = async (userId: string) => {
  const { data, error } = await supabase
    .from('job_applications')
    .select('*, resumes(*)')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
};

export const updateJobApplicationStatus = async (jobId: string, status: JobApplication['status']) => {
  const { data, error } = await supabase
    .from('job_applications')
    .update({ status })
    .eq('id', jobId)
    .select()
    .single();

  if (error) throw error;
  return data;
};
