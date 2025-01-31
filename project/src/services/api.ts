import { supabase } from '../lib/supabaseClient';

const API_URL = import.meta.env.VITE_RESUME_API_URL || 'http://localhost:5000';
const JOB_API_URL = import.meta.env.VITE_JOB_API_URL;

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
  analysis: string | null;
  resume: Resume | null;
}

export interface Resume {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  optimized_pdf_url: string | null;
  analysis: string | null;
  job_url: string | null;
  status: 'processing' | 'completed' | 'failed';
}

export interface OptimizedResume {
  id: string;
  title: string;
  created_at: string;
  pdf_url: string;
  analysis: string;
  job_url: string;
}

// Resume optimization service
export const optimizeResume = async (formData: FormData): Promise<any> => {
  try {
    // Get the current user and session
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user) {
      throw new Error('User not authenticated');
    }

    // Call the optimization endpoint
    const response = await fetch(`${API_URL}/optimize`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
      headers: {
        'X-User-Id': session.user.id
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      if (response.status === 403 && errorData.error === 'Insufficient credits') {
        throw new Error('Insufficient credits. Please purchase more credits to continue using the resume optimization service.');
      }
      throw new Error(errorData.error || 'Failed to optimize resume');
    }

    const responseData = await response.json();
    if (!responseData.success) {
      throw new Error(responseData.error || 'Failed to optimize resume');
    }

    // Create a blob from the base64 PDF data
    const pdfBlob = base64ToBlob(responseData.pdf_data, 'application/pdf');
    const blobUrl = URL.createObjectURL(pdfBlob);

    // Return the resume data from the backend response
    return {
      id: responseData.resume_id,
      user_id: session.user.id,
      title: responseData.title || 'Optimized Resume',
      created_at: responseData.created_at || new Date().toISOString(),
      optimized_pdf_url: blobUrl,
      analysis: responseData.analysis,
      job_url: responseData.job_url,
      status: responseData.status || 'completed'
    };

  } catch (error) {
    console.error('Error in optimizeResume:', error);
    throw error;
  }
};

// Get recent resumes
export const getRecentResumes = async (limit?: number): Promise<Resume[]> => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user) {
    throw new Error('Not authenticated');
  }

  const url = new URL(`${API_URL}/api/resumes`);
  if (limit) {
    url.searchParams.append('limit', limit.toString());
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': session.user.id
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to get resumes');
  }

  return await response.json();
};

// Delete resume
export async function deleteResume(id: string): Promise<void> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`/api/resumes/${id}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': session.user.id
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to delete resume');
  }
}

// Get resume download URL
export const getResumeDownloadUrl = async (resumeId: string, jobTitle?: string) => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user) {
      throw new Error('Not authenticated');
    }

    // First get the signed URL
    const response = await fetch(`/api/resumes/${resumeId}/download`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': session.user.id
      }
    });

    if (!response.ok) {
      throw new Error('Failed to get download URL');
    }

    const data = await response.json();
    if (!data.success || !data.url) {
      throw new Error(data.error || 'Failed to get download URL');
    }

    // Now fetch the actual PDF using the signed URL
    const pdfResponse = await fetch(data.url);
    if (!pdfResponse.ok) {
      throw new Error('Failed to download PDF');
    }

    const pdfBlob = await pdfResponse.blob();
    const blobUrl = window.URL.createObjectURL(pdfBlob);
    
    // Create and click download link
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = `${jobTitle || 'resume'}.pdf`;
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    window.URL.revokeObjectURL(blobUrl);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Error downloading resume:', error);
    throw error;
  }
};

// Get cover letter download URL and content
export const downloadCoverLetter = async (resumeId: string): Promise<Blob> => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_URL}/api/resumes/${resumeId}/cover-letter/download`, {
    headers: {
      'X-User-Id': session.user.id
    }
  });

  if (!response.ok) {
    throw new Error('Failed to download cover letter');
  }

  return await response.blob();
};

// Helper function to convert base64 to Blob
function base64ToBlob(base64: string, type: string): Blob {
  const byteCharacters = atob(base64);
  const byteArrays = [];

  for (let offset = 0; offset < byteCharacters.length; offset += 512) {
    const slice = byteCharacters.slice(offset, offset + 512);
    const byteNumbers = new Array(slice.length);

    for (let i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i);
    }

    const byteArray = new Uint8Array(byteNumbers);
    byteArrays.push(byteArray);
  }

  return new Blob(byteArrays, { type });
}

// Supabase database operations
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
  const response = await fetch(`${API_URL}/api/jobs`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to get job applications');
  }

  return await response.json();
};

export const saveJob = async (
  jobTitle: string,
  company: string,
  jobDescription: string,
  jobUrl: string
): Promise<JobApplication> => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_URL}/api/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': session.user.id
    },
    body: JSON.stringify({
      job_title: jobTitle,
      company,
      job_description: jobDescription,
      job_url: jobUrl
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to save job');
  }

  return await response.json();
};

export const updateJobApplicationStatus = async (jobId: string, status: JobApplication['status']) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_URL}/api/jobs/${jobId}/status`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': session.user.id
    },
    body: JSON.stringify({ status })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to update job status');
  }

  return await response.json();
};

// Delete job application
export const deleteJobApplication = async (jobId: string): Promise<void> => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': session.user.id
    }
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to delete job application');
  }
};

// Get user credits
export const getUserCredits = async (): Promise<number> => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_URL}/api/credits`, {
      method: 'GET',
      headers: {
        'X-User-Id': session.user.id,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get user credits');
    }

    const data = await response.json();
    return data.credits;
  } catch (error) {
    console.error('Error getting user credits:', error);
    throw error;
  }
};
