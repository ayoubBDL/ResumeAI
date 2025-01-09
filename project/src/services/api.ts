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
export const optimizeResume = async (linkedinUrl: string, resumeFile: File) => {
  // Validate inputs
  if (!resumeFile || !linkedinUrl) {
    throw new Error('Both resume file and LinkedIn URL are required');
  }

  if (!resumeFile.type.includes('pdf')) {
    throw new Error('Please upload a PDF file');
  }

  if (resumeFile.size > 10 * 1024 * 1024) { // 10MB limit
    throw new Error('File size must be less than 10MB');
  }

  const formData = new FormData();
  formData.append('resume_file', resumeFile);
  formData.append('linkedin_url', linkedinUrl);

  console.log('Sending request to:', import.meta.env.VITE_RESUME_API_URL);
  console.log('LinkedIn URL:', linkedinUrl);
  console.log('Resume file:', resumeFile.name, 'Size:', resumeFile.size, 'Type:', resumeFile.type);
  
  try {
    const response = await fetch(`${import.meta.env.VITE_RESUME_API_URL}/api/optimize-resume`, {
      method: 'POST',
      body: formData,
    });

    const contentType = response.headers.get('content-type');
    console.log('Response content type:', contentType);
    
    if (!response.ok) {
      let errorMessage = 'Failed to optimize resume';
      try {
        if (contentType?.includes('application/json')) {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } else {
          errorMessage = await response.text();
        }
      } catch (parseError) {
        console.error('Error parsing error response:', parseError);
      }
      throw new Error(errorMessage);
    }

    // Handle successful response
    console.log('Response successful');
    if (contentType?.includes('application/pdf')) {
      console.log('Received PDF response');
      return await response.blob();
    } else if (contentType?.includes('application/json')) {
      console.log('Received JSON response');
      return await response.json();
    } else {
      console.warn('Unexpected content type:', contentType);
      return await response.blob();
    }
  } catch (error) {
    console.error('Error in optimizeResume:', error);
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
