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

// Resume optimization service
export const optimizeResume = async (linkedinUrl: string, resumeFile: File, customInstructions?: string) => {
  const formData = new FormData();
  formData.append('resume_file', resumeFile);
  formData.append('linkedin_url', linkedinUrl);
  if (customInstructions) {
    formData.append('custom_instructions', customInstructions);
  }

  const response = await fetch('http://localhost:8000/api/optimize-resume', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to optimize resume');
  }

  return response.json();
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
